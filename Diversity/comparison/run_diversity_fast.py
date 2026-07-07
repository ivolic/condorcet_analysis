"""
Fast reimplementation of run_diversity.py's elimination loop.

Two structural changes vs. the original:

1. The original converts to/from a votekit PreferenceProfile object every
   round (via remove_and_condense_rank_profile + condense_ballots). Each
   conversion round-trips through votekit's internal pandas DataFrame
   representation, which profiling showed to be ~80% of total runtime.
   Here, the votekit profile is converted to plain (ranking, weight) tuples
   ONCE at the start, and every round operates on that plain Python
   structure directly -- no further votekit object construction happens
   until the very end (if ever).

2. The original recomputes the full pairwise head-to-head matrix from
   scratch every round (via Smith's head2head_count, called twice per
   candidate pair, each a full ballot rescan). The pairwise result between
   two candidates who are BOTH still in the race is invariant to which
   OTHER candidates have been eliminated -- removing a third candidate
   doesn't change whether A ranks ahead of B. So the full matrix is built
   ONCE, up front, from the original ballots and candidate set, and every
   round just looks up the relevant sub-matrix instead of rescanning.

Verified byte-for-byte equivalent tie/absence semantics against the real
head2head_count via direct testing (see test_fast_matches_original.py):
  - both candidates present, tied in the same rank slot -> both credited
    the full ballot weight
  - one present, one entirely absent from the ballot -> the present one
    credited the full weight, absent one gets nothing
  - neither present -> neither credited anything
"""
from collections import defaultdict
from itertools import combinations


def condense_ballots(profile):
    """
    Compatibility shim matching the original condense_ballots(profile) ->
    PreferenceProfile signature, for callers (like the cloning script) that
    still need a real votekit profile back -- e.g. because they pass it on
    to insert_clone_into_profile, which manipulates votekit Ballot objects.
    Only called once per election/hit (not once per round), so it isn't
    part of the hot path this rewrite targets.
    """
    from votekit import Ballot, PreferenceProfile

    weights = defaultdict(float)
    for ballot in profile.ballots:
        weights[ballot.ranking] += ballot.weight

    new_ballots = [
        Ballot(ranking=ranking, weight=weight)
        for ranking, weight in weights.items()
    ]
    return PreferenceProfile(ballots=tuple(new_ballots))


def votekit_profile_to_plain_ballots(vprofile):
    """One-time conversion from a votekit PreferenceProfile to a plain list
    of (ranking, weight) tuples. Pay this cost once, not once per round."""
    return [(tuple(ballot.ranking), ballot.weight) for ballot in vprofile.ballots]


def remove_candidate_and_condense(ballots, candidate):
    """
    Pure-Python equivalent of votekit's remove_cand_rank_ballot +
    condense_rank_ballot, applied to every ballot, PLUS the original
    script's own condense_ballots (merge ballots that now share an
    identical resulting ranking, summing weight). Operates on plain
    tuples -- no votekit object construction at all.
    """
    merged = defaultdict(float)

    for ranking, weight in ballots:
        new_ranking = tuple(
            frozenset(slot - {candidate})
            for slot in ranking
        )
        # Drop ANY empty slot (wherever it occurs), matching
        # condense_rank_ballot's behavior exactly (not just trailing).
        new_ranking = tuple(slot for slot in new_ranking if slot)

        if not new_ranking:
            continue  # remove_empty_ballots=True default
        if weight <= 0:
            continue  # remove_zero_weight_ballots=True default (defensive)

        merged[new_ranking] += weight

    return list(merged.items())


def build_pairwise_matrix(ballots, candidates):
    """
    One-time O(ballots x ranking_length x candidates) precomputation of
    head-to-head weight tallies for every ordered candidate pair, matching
    head2head_count's exact semantics: present-and-earlier beats
    present-and-later; present beats absent; ties (same rank slot) credit
    both directions the full weight; neither-present contributes nothing.
    """
    cand_set = set(candidates)
    matrix = {a: defaultdict(float) for a in candidates}

    for ranking, weight in ballots:
        pos = {}
        for idx, slot in enumerate(ranking):
            for c in slot:
                if c in cand_set and c not in pos:
                    pos[c] = idx

        present = list(pos.keys())
        absent = cand_set - set(present)

        for i in range(len(present)):
            a = present[i]
            for j in range(i + 1, len(present)):
                b = present[j]
                if pos[a] < pos[b]:
                    matrix[a][b] += weight
                elif pos[b] < pos[a]:
                    matrix[b][a] += weight
                else:  # tie -> both credited
                    matrix[a][b] += weight
                    matrix[b][a] += weight

        for p in present:
            for x in absent:
                matrix[p][x] += weight

    return matrix


def smith_set_from_matrix(matrix, active_candidates):
    """
    Same Copeland-score / Smith-set-boundary algorithm as the original
    Smith(), but consuming a precomputed matrix via cheap dict lookups
    instead of re-scanning ballots for every pair, every round.
    """
    cands = list(active_candidates)

    if len(cands) == 1:
        return set(cands)

    pairwise_dict = {a: {c: 0 for c in cands if c != a} for a in cands}
    for a, c in combinations(cands, 2):
        aw = matrix[a][c]
        cw = matrix[c][a]
        if aw > cw:
            pairwise_dict[a][c] = 1
        elif aw == cw:
            pairwise_dict[a][c] = 0.5
            pairwise_dict[c][a] = 0.5
        else:
            pairwise_dict[c][a] = 1

    copeland_scores = {a: sum(pairwise_dict[a].values()) for a in cands}
    copeland_order = [a for (a, _) in sorted(copeland_scores.items(), key=lambda x: x[1], reverse=True)]
    max_copeland = copeland_scores[copeland_order[0]]
    l = len(copeland_order)
    first_non_smith = 1

    while first_non_smith < l:
        if copeland_scores[copeland_order[first_non_smith]] != max_copeland:
            break
        first_non_smith += 1

    while first_non_smith < l:
        lower_rows = [
            k for k in range(first_non_smith, l)
            if sum(pairwise_dict[copeland_order[k]][copeland_order[i]] for i in range(first_non_smith)) != 0
        ]
        if lower_rows == []:
            break
        else:
            j = max(lower_rows)
            first_non_smith = max(
                [i for i in range(j, l) if copeland_scores[copeland_order[i]] == copeland_scores[copeland_order[j]]]
            ) + 1

    return set(copeland_order[:first_non_smith])


def condorcet_winner_from_matrix(matrix, active_candidates):
    elected = smith_set_from_matrix(matrix, active_candidates)
    if len(elected) > 1:
        return set()
    return elected


def get_diversity_score(ballots, candidate, threshold=0):
    total_weight = sum(weight for _, weight in ballots)
    min_weight = threshold * total_weight

    score = 0
    for ranking, weight in ballots:
        if ranking and candidate in ranking[0]:
            if weight >= min_weight:
                score += 1
    return score


def drop_candidate(ballots, candidates, threshold):
    lowest_score = {"candidates": [], "score": None}

    for c in candidates:
        score = get_diversity_score(ballots, c, threshold)
        if lowest_score["score"] is None or score < lowest_score["score"]:
            lowest_score["candidates"] = [c]
            lowest_score["score"] = score
        elif score == lowest_score["score"]:
            lowest_score["candidates"].append(c)

    return lowest_score["candidates"]


def first_place_votes_plain(ballots, tie_convention="average"):
    """
    Reimplementation of votekit's first_place_votes utility (default
    tie_convention='average': n candidates tied for first each get
    weight/n), operating on plain ballot tuples.
    """
    fpv = defaultdict(float)
    for ranking, weight in ballots:
        if not ranking:
            continue
        first_slot = ranking[0]
        n = len(first_slot)
        if n == 0:
            continue
        if tie_convention == "average":
            share = weight / n
            for c in first_slot:
                fpv[c] += share
        elif tie_convention == "high":
            for c in first_slot:
                fpv[c] += weight
        elif tie_convention == "low":
            pass
        else:
            raise ValueError(f"Unknown tie_convention: {tie_convention}")
    return fpv


def first_place_count(ballots, candidates_to_compare):
    fpv = first_place_votes_plain(ballots)
    fpv = {c: fpv.get(c, 0) for c in candidates_to_compare}

    result_cand, result_score = '', None
    for c in candidates_to_compare:
        if result_score is None or fpv[c] < result_score:
            result_cand, result_score = c, fpv[c]
    return result_cand


def main_helper(ballots, candidates, threshold, matrix, round_num=1):
    winner = condorcet_winner_from_matrix(matrix, candidates)
    if winner:
        return list(winner)[0], round_num

    cand = drop_candidate(ballots, candidates, threshold)
    if len(cand) == 1:
        cand_to_drop = cand[0]
    else:
        cand_to_drop = first_place_count(ballots, cand)

    candidates = [c for c in candidates if c != cand_to_drop]
    ballots = remove_candidate_and_condense(ballots, cand_to_drop)

    return main_helper(ballots, candidates, threshold, matrix, round_num + 1)


def prepare_context(vprofile):
    """
    Do the one-time work -- votekit conversion + pairwise matrix -- once,
    and return a context that can be reused across many threshold values
    for the SAME underlying profile (e.g. the outer 10-threshold sweep in
    the calling script). Avoids repeating the conversion+matrix build once
    per threshold.
    """
    candidates = [
        c for c in vprofile.candidates
        if c not in ('skipped', 'writein', 'Write-in')
    ]
    ballots = votekit_profile_to_plain_ballots(vprofile)
    matrix = build_pairwise_matrix(ballots, candidates)
    return {"ballots": ballots, "candidates": candidates, "matrix": matrix}


def run_diversity_from_context(context, threshold=0):
    """Same elimination loop as run_diversity(), but skips the one-time
    setup by reusing a context built once via prepare_context()."""
    return main_helper(context["ballots"], context["candidates"], threshold, context["matrix"])


def run_diversity(vprofile, threshold=0):
    """
    Drop-in replacement for the original run_diversity(vprofile, threshold).
    Same signature, same return value (winner, rounds). Internally: one
    conversion out of votekit, one pairwise-matrix precomputation, then a
    pure-Python elimination loop with no further votekit object
    construction.

    If you're calling this many times for the SAME vprofile at different
    thresholds (e.g. a threshold sweep), use prepare_context() once and
    run_diversity_from_context() per threshold instead -- this function
    redoes the one-time setup on every call.
    """
    context = prepare_context(vprofile)
    return run_diversity_from_context(context, threshold)