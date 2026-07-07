import sys
sys.path.append('/Users/belle/Desktop/build/rcv')

import csv
import logging
import math
import os
import re
from collections import defaultdict
from fractions import Fraction

from tqdm import tqdm
import main_methods as mm
from votekit import Ballot, PreferenceProfile
from votekit.cleaning import remove_and_condense_rank_profile
from run_diversity import condense_ballots

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), "tvr.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_FOLDER = "/Users/belle/Desktop/build/condorcet_analysis/Cloning/Res"
RESULTS_FILE = "./tvr_cloning_tests.csv"

# ---------------------------------------------------------------------------
# TVR elimination with tie-forking
# ---------------------------------------------------------------------------

def _get_scores(vprofile, candidates: list[str], method: str) -> dict[str, float]:
    if method == "PM":
        return mm.Borda_PM_Return_Full(vprofile, candidates, tiebreak="random")
    elif method == "OM":
        return mm.Borda_OM_Return_Full(vprofile, candidates, tiebreak="random")
    elif method == "AVG":
        return mm.Borda_AVG_Return_Full(vprofile, candidates, tiebreak="random")
    else:
        raise ValueError(f"Unknown method: {method!r}")


def _eliminate(vprofile, candidates, method, tie_path, round_num=1):
    """
    Recursively eliminate candidates. On a bottom tie, fork one branch per
    tied candidate. Returns list of (winner, tie_path) pairs.
    """
    logger.info(f"Round {round_num} [{method}]: candidates={candidates}")

    if len(candidates) == 1:
        return [(candidates[0], tie_path)]

    scores = _get_scores(vprofile, candidates, method)
    logger.info(f"Round {round_num} [{method}]: scores={scores}")

    min_score = min(scores.values())
    to_drop = [c for c, v in scores.items() if v == min_score]

    if len(to_drop) == 1:
        remaining = [c for c in candidates if c != to_drop[0]]
        logger.info(f"Round {round_num} [{method}]: dropping {to_drop[0]}")
        return _eliminate(vprofile, remaining, method, tie_path, round_num + 1)

    # Tie: fork
    tied_set = set(to_drop)
    logger.info(f"Round {round_num} [{method}]: tie {tied_set} — forking {len(to_drop)} branches")

    results = []
    for dropped in to_drop:
        remaining = [c for c in candidates if c != dropped]
        results.extend(_eliminate(
            vprofile, remaining, method,
            tie_path + [(tied_set, dropped)],
            round_num + 1,
        ))
    return results


def _clean(value: str) -> str:
    """
    Sanitize a string for safe CSV storage.
    Removes commas, quotes, and any other non-alphanumeric characters
    except spaces, hyphens, underscores, dots, and the pipe we use as
    our own separator in tie_path / tie_dropped.
    """
    value = str(value)
    value = re.sub(r"[\"',;]", "", value)          # strip CSV-breaking chars
    value = re.sub(r"[^\w\s\-_.\|>]", "", value)   # keep only safe chars
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _fmt_path(tie_path):
    # e.g.  tied(B|C) drop(B) | tied(D|E) drop(D)
    # pipes used as separators so commas are never needed
    parts = [
        f"tied({'|'.join(sorted(_clean(c) for c in t))}) drop({_clean(d)})"
        for t, d in tie_path
    ]
    return " | ".join(parts)


def _fmt_dropped(tie_path):
    # e.g.  B | D
    return " | ".join(_clean(d) for _, d in tie_path)


def run_tvr(vprofile, method: str) -> list[dict]:
    """
    Returns list of {winner, tie_path, tie_dropped} dicts —
    one per fork branch (usually just one when no ties occur).
    """
    candidates = [
        c for c in vprofile.candidates
        if c not in ("skipped", "writein", "Write-in")
    ]
    return [
        {"winner": winner, "tie_path": _fmt_path(path), "tie_dropped": _fmt_dropped(path)}
        for winner, path in _eliminate(vprofile, candidates, method, tie_path=[])
    ]


# ---------------------------------------------------------------------------
# Cloning
# ---------------------------------------------------------------------------

def _insert_clone(profile, target_candidate, percent):
    weight_map = defaultdict(Fraction)
    profile = condense_ballots(profile)

    for ballot in profile.ballots:
        ranking = list(ballot.ranking)
        weight = ballot.weight
        idx = next((i for i, s in enumerate(ranking) if frozenset(s) == target_candidate), None)

        if idx is None:
            weight_map[tuple(frozenset(s) for s in ranking)] += weight
            continue

        before_weight = math.ceil(weight * percent)
        after_weight  = weight - before_weight

        before = tuple(frozenset(s) for s in ranking[:idx] + [{"Clone"}] + ranking[idx:])
        after  = tuple(frozenset(s) for s in ranking[:idx + 1] + [{"Clone"}] + ranking[idx + 1:])

        if before_weight > 0:
            weight_map[before] += before_weight
        if after_weight > 0:
            weight_map[after] += after_weight

    return PreferenceProfile(ballots=tuple(
        Ballot(ranking=list(r), weight=w) for r, w in weight_map.items()
    ))


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def _build_rows(profile, file_label, candidate_cloned, percent):
    base = {
        "file":             _clean(re.sub(r"/0\.[0-5]/", "/", file_label.replace(OUTPUT_FOLDER, ""))),
        "candidate_cloned": _clean(list(candidate_cloned)[0] if isinstance(candidate_cloned, (frozenset, set)) else candidate_cloned),
        "percent":          percent,
        "numCands":         len([c for c in profile.candidates if c != "skipped"]),
    }
    logger.info(f"cloned={base['candidate_cloned']}  percent={percent}")

    om_res  = run_tvr(profile, "OM")
    avg_res = run_tvr(profile, "AVG")
    pm_res  = run_tvr(profile, "PM")

    rows = []
    for om in om_res:
        for avg in avg_res:
            for pm in pm_res:
                rows.append({
                    **base,
                    "om":              _clean(om["winner"]),
                    "om_tie_path":     om["tie_path"],
                    "om_tie_dropped":  om["tie_dropped"],
                    "avg":             _clean(avg["winner"]),
                    "avg_tie_path":    avg["tie_path"],
                    "avg_tie_dropped": avg["tie_dropped"],
                    "pm":              _clean(pm["winner"]),
                    "pm_tie_path":     pm["tie_path"],
                    "pm_tie_dropped":  pm["tie_dropped"],
                })
    return rows


def _append_csv(rows, results_file):
    if not rows:
        return
    write_header = not os.path.exists(results_file) or os.stat(results_file).st_size == 0
    with open(results_file, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def process_data(profile, file_name, results_file, percent):
    candidates = {
        frozenset(cand) if not isinstance(cand, frozenset) else cand
        for ballot in profile.ballots
        for cand in ballot.ranking
    }
    logger.info(f"RUNNING {file_name} — {len(candidates)} candidates, percent={percent}")

    for candidate in candidates:
        cloned = _insert_clone(profile, candidate, percent)
        _append_csv(_build_rows(cloned, file_name, candidate, percent), results_file)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

ROOT_DIR = "/Users/belle/Downloads/Scotland data processed"
ERROR_FILE = "./errors.txt"
CLONE_PERCENTS = [round(p / 10, 1) for p in range(0, 6)]  # 0.0, 0.1, 0.2, 0.3, 0.4, 0.5


def _find_csvs(root: str) -> list[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".csv"):
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


import multiprocessing

TIMEOUT_SECONDS = 600  # 10 minutes


def _process_file(full_path: str) -> None:
    file_name = os.path.basename(full_path)
    try:
        profile = remove_and_condense_rank_profile(
            profile=mm.v_profile(full_path),
            removed=["skipped", "writein", "Write-in"],
        )
        # Baseline (no cloning)
        _append_csv(_build_rows(profile, file_name, "none", percent=0), RESULTS_FILE)
        # Cloning runs across all percents
        for percent in CLONE_PERCENTS:
            process_data(profile, file_name, RESULTS_FILE, percent=percent)

    except Exception as e:
        logger.error(f"FAILED {file_name}: {e}")
        with open(ERROR_FILE, "a") as ef:
            ef.write(f"{file_name}: {e}\n")


if __name__ == "__main__":
    all_csvs = _find_csvs(ROOT_DIR)
    logger.info(f"Found {len(all_csvs)} CSV files under {ROOT_DIR}")
    print(f"Found {len(all_csvs)} files — starting...")

    for path in tqdm(all_csvs, desc="Processing", unit="file"):
        file_name = os.path.basename(path)
        tqdm.write(file_name)
        p = multiprocessing.Process(target=_process_file, args=(path,))
        p.start()
        p.join(TIMEOUT_SECONDS)
        if p.is_alive():
            p.terminate()
            p.join()
            logger.error(f"TIMEOUT {file_name}")
            with open(ERROR_FILE, "a") as ef:
                ef.write(f"{file_name}: timeout after {TIMEOUT_SECONDS}s\n")