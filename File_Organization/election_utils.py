"""
Shared utilities for parsing election file formats:

Format A (space-separated):
  First row: "num_candidates num_seats"
  Ballot rows: "count cand1 cand2 ... 0"
  Ends with a row containing just "0"

Format B (CSV, one row per voter):
  Header: voterId,rank1,...,rankN,numSeats,numCands
  Each row is one ballot; "skipped" = no ranking at that position

Format C (CSV, one row per ballot type with Count):
  Header: rank1,...,rankN,Count,Num Seats   (no voterId, no numCands)
  Each row is a ballot type with a Count; "skipped" = no ranking
  num_candidates inferred from all unique non-skipped names seen
"""

import csv


def _header_cols(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()
    return [c.strip().lower() for c in first_line.split(",")]


def detect_format(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()

    cols_lower = [c.strip().lower() for c in first_line.split(",")]

    has_rank     = any(c.startswith("rank") for c in cols_lower)
    has_numcands = any(c in ("numcands", "num cands") for c in cols_lower)
    has_count    = any(c == "count" for c in cols_lower)

    if has_rank and has_numcands:
        return "B"   # one row per voter, numCands explicit (with any leading cols)
    if has_rank and has_count:
        return "C"   # one row per ballot type, Count column, numCands inferred
    return "A"       # space-separated


# ── Format A ────────────────────────────────────────────────────────────────

def get_seats_format_a(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()
    parts = first_line.split()
    if len(parts) < 2:
        raise ValueError(f"Unexpected header: '{first_line}'")
    raw = parts[1]
    if raw.lower() == "nan":
        return None
    return int(float(raw))


def parse_format_a(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = [l.strip() for l in f if l.strip()]

    header = lines[0].split()
    num_candidates = int(float(header[0]))
    raw_seats = header[1]
    num_seats = None if raw_seats.lower() == "nan" else int(float(raw_seats))

    total_ballots = unique_ballot_types = 0
    bullet_vote_count = partial_ballot_count = full_ballot_count = 0

    for line in lines[1:]:
        parts = line.split()
        if parts == ["0"]:
            break
        try:
            count = int(parts[0])
        except ValueError:
            continue

        ranked = [p for p in parts[1:] if p != "0"]
        num_ranked = len(ranked)

        unique_ballot_types += 1
        total_ballots       += count

        if num_ranked == 1:
            bullet_vote_count += count
        elif num_ranked >= num_candidates - 1:
            full_ballot_count += count
        else:
            partial_ballot_count += count

    return {
        "num_candidates":       num_candidates,
        "num_seats":            num_seats,
        "total_ballots":        total_ballots,
        "unique_ballot_types":  unique_ballot_types,
        "bullet_vote_count":    bullet_vote_count,
        "partial_ballot_count": partial_ballot_count,
        "full_ballot_count":    full_ballot_count,
    }


# ── Format B ────────────────────────────────────────────────────────────────

def get_seats_format_b(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            col = _find_col(row.keys(), "numSeats", "num seats")
            if not col:
                return None
            raw = row[col].strip()
            if raw.lower() == "nan" or raw == "":
                return None
            return int(float(raw))
    return None


def parse_format_b(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("Empty file")

    first = rows[0]
    cands_col = _find_col(first.keys(), "numCands", "num cands")
    seats_col = _find_col(first.keys(), "numSeats", "num seats")

    if not cands_col:
        raise ValueError("No numCands column found")

    num_candidates = int(float(first[cands_col]))
    raw_seats = first[seats_col].strip() if seats_col else ""
    num_seats = None if raw_seats.lower() in ("nan", "") else int(float(raw_seats))

    rank_cols = [c for c in first.keys() if c.lower().startswith("rank")]

    ballot_counts = {}
    for row in rows:
        ranked = tuple(
            row[c].strip() for c in rank_cols
            if row[c].strip().lower() != "skipped" and row[c].strip() != ""
        )
        ballot_counts[ranked] = ballot_counts.get(ranked, 0) + 1

    total_ballots        = len(rows)
    unique_ballot_types  = len(ballot_counts)
    bullet_vote_count    = 0
    partial_ballot_count = 0
    full_ballot_count    = 0

    for ranked, count in ballot_counts.items():
        num_ranked = len(ranked)
        if num_ranked == 1:
            bullet_vote_count += count
        elif num_ranked >= num_candidates - 1:
            full_ballot_count += count
        else:
            partial_ballot_count += count

    return {
        "num_candidates":       num_candidates,
        "num_seats":            num_seats,
        "total_ballots":        total_ballots,
        "unique_ballot_types":  unique_ballot_types,
        "bullet_vote_count":    bullet_vote_count,
        "partial_ballot_count": partial_ballot_count,
        "full_ballot_count":    full_ballot_count,
    }


# ── Format C ────────────────────────────────────────────────────────────────

def _find_col(keys, *candidates):
    """Return the first key (case-insensitive) matching any candidate name."""
    lower_map = {k.strip().lower(): k for k in keys}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def get_seats_format_c(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            col = _find_col(row.keys(), "num seats", "numseats", "seats")
            if not col:
                return None
            raw = row[col].strip()
            if raw.lower() == "nan" or raw == "":
                return None
            return int(float(raw))
    return None


def parse_format_c(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("Empty file")

    first     = rows[0]
    rank_cols = [c for c in first.keys() if c.strip().lower().startswith("rank")]
    count_col = _find_col(first.keys(), "count")
    seats_col = _find_col(first.keys(), "num seats", "numseats", "seats")

    if not count_col:
        raise ValueError("No 'Count' column found")

    # Infer num_seats from first row
    if seats_col:
        raw_seats = first[seats_col].strip()
        num_seats = None if raw_seats.lower() in ("nan", "") else int(float(raw_seats))
    else:
        num_seats = None

    # Infer num_candidates from all unique non-skipped names across the file
    all_names = set()
    for row in rows:
        for c in rank_cols:
            val = row[c].strip()
            if val.lower() != "skipped" and val != "":
                all_names.add(val)
    num_candidates = len(all_names)

    total_ballots        = 0
    unique_ballot_types  = 0
    bullet_vote_count    = 0
    partial_ballot_count = 0
    full_ballot_count    = 0

    for row in rows:
        try:
            count = int(float(row[count_col].strip()))
        except (ValueError, KeyError):
            continue

        ranked = [
            row[c].strip() for c in rank_cols
            if row[c].strip().lower() != "skipped" and row[c].strip() != ""
        ]
        num_ranked = len(ranked)

        unique_ballot_types += 1
        total_ballots       += count

        if num_ranked == 1:
            bullet_vote_count += count
        elif num_ranked >= num_candidates - 1:
            full_ballot_count += count
        else:
            partial_ballot_count += count

    return {
        "num_candidates":       num_candidates,
        "num_seats":            num_seats,
        "total_ballots":        total_ballots,
        "unique_ballot_types":  unique_ballot_types,
        "bullet_vote_count":    bullet_vote_count,
        "partial_ballot_count": partial_ballot_count,
        "full_ballot_count":    full_ballot_count,
    }


# ── Unified API ─────────────────────────────────────────────────────────────

def get_seats(filepath):
    fmt = detect_format(filepath)
    if fmt == "A": return get_seats_format_a(filepath)
    if fmt == "B": return get_seats_format_b(filepath)
    if fmt == "C": return get_seats_format_c(filepath)


def parse_election(filepath):
    fmt = detect_format(filepath)
    if fmt == "A": return parse_format_a(filepath)
    if fmt == "B": return parse_format_b(filepath)
    if fmt == "C": return parse_format_c(filepath)