import sys
sys.path.append('/Users/belle/Desktop/build/rcv')

import csv
import math
import multiprocessing
import os
import re
import time
from collections import defaultdict
from fractions import Fraction

from tqdm import tqdm
import main_methods as mm
from votekit import Ballot, PreferenceProfile
from votekit.cleaning import remove_and_condense_rank_profile
from run_diversity import condense_ballots

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT_DIR        = "//Users/belle/Downloads/Australia data"
RESULTS_FILE    = "./tvr_cloning_tests.csv"
ERROR_FILE      = "./errors.txt"
CLONE_PERCENTS  = [round(p / 10, 1) for p in range(0, 6)]  # 0.0 … 0.5
TIMEOUT_SECONDS = 600  # 10 minutes per file

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
    if not candidates:
        return []
    if len(candidates) == 1:
        return [(candidates[0], tie_path)]

    scores    = _get_scores(vprofile, candidates, method)
    min_score = min(scores.values())
    to_drop   = [c for c, v in scores.items() if v == min_score]

    if len(to_drop) == 1:
        remaining = [c for c in candidates if c != to_drop[0]]
        return _eliminate(vprofile, remaining, method, tie_path, round_num + 1)

    tied_set = set(to_drop)
    results  = []
    for dropped in to_drop:
        remaining = [c for c in candidates if c != dropped]
        results.extend(_eliminate(
            vprofile, remaining, method,
            tie_path + [(tied_set, dropped)],
            round_num + 1,
        ))
    return results


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _clean(value: str) -> str:
    value = str(value)
    value = re.sub(r"[\"',;]", "", value)
    value = re.sub(r"[^\w\s\-_.\|>]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _file_key(filename: str) -> str:
    """Normalize a filename for consistent resume comparison — strip extension and clean."""
    return _clean(os.path.splitext(os.path.basename(filename))[0])


def _fmt_path(tie_path):
    parts = [
        f"tied({'|'.join(sorted(_clean(c) for c in t))}) drop({_clean(d)})"
        for t, d in tie_path
    ]
    return " | ".join(parts)


def _fmt_dropped(tie_path):
    return " | ".join(_clean(d) for _, d in tie_path)


def run_tvr(vprofile, method: str) -> list[dict]:
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
    profile    = condense_ballots(profile)

    for ballot in profile.ballots:
        ranking = list(ballot.ranking)
        weight  = ballot.weight
        idx     = next((i for i, s in enumerate(ranking) if frozenset(s) == target_candidate), None)

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
# Row building (pure computation, no I/O)
# ---------------------------------------------------------------------------

def _build_rows(profile, file_label, candidate_cloned, percent):
    base = {
        "file":             _file_key(file_label),
        "candidate_cloned": _clean(list(candidate_cloned)[0] if isinstance(candidate_cloned, (frozenset, set)) else candidate_cloned),
        "percent":          percent,
        "numCands":         len([c for c in profile.candidates if c != "skipped"]),
    }

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


def _collect_rows(profile, file_name) -> list[dict]:
    """Build all rows for one file across baseline + all percents. No I/O."""
    rows = _build_rows(profile, file_name, "none", percent=0)
    candidates = {
        frozenset(cand) if not isinstance(cand, frozenset) else cand
        for ballot in profile.ballots
        for cand in ballot.ranking
    }
    for percent in CLONE_PERCENTS:
        for candidate in candidates:
            cloned = _insert_clone(profile, candidate, percent)
            rows.extend(_build_rows(cloned, file_name, candidate, percent))
    return rows


# ---------------------------------------------------------------------------
# Worker: puts result on a queue, runs in its own Process (not a Pool slot)
# ---------------------------------------------------------------------------

def _worker(full_path: str, queue: multiprocessing.Queue) -> None:
    """
    Computes all rows for one file and puts (file_name, rows, error) on queue.
    Runs as a standalone Process so it can be hard-killed on timeout without
    affecting any other worker.
    """
    file_name = os.path.basename(full_path)
    try:
        profile = remove_and_condense_rank_profile(
            profile=mm.v_profile(full_path),
            removed=["skipped", "writein", "Write-in"],
        )
        rows = _collect_rows(profile, file_name)
        queue.put((file_name, rows, None))
    except Exception as e:
        queue.put((file_name, [], str(e)))


# ---------------------------------------------------------------------------
# CSV writer — called only from main process, lock ensures safe concurrent use
# ---------------------------------------------------------------------------

def _write_csv(rows: list[dict], results_file: str, lock) -> None:
    if not rows:
        return
    with lock:
        write_header = not os.path.exists(results_file) or os.stat(results_file).st_size == 0
        with open(results_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerows(rows)


# ---------------------------------------------------------------------------
# Resume helpers
# ---------------------------------------------------------------------------

def _already_processed(results_file: str) -> set[str]:
    if not os.path.exists(results_file) or os.stat(results_file).st_size == 0:
        return set()
    with open(results_file, newline="") as f:
        reader = csv.DictReader(f)
        if "file" not in (reader.fieldnames or []):
            return set()
        return {_file_key(row["file"]) for row in reader if row.get("file")}


def _find_csvs(root: str) -> list[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".csv"):
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    all_csvs  = _find_csvs(ROOT_DIR)
    done      = _already_processed(RESULTS_FILE)
    remaining = [p for p in all_csvs if _file_key(p) not in done]

    num_workers = max(1, multiprocessing.cpu_count() - 1)
    print(f"Found {len(all_csvs)} files — {len(done)} already done, {len(remaining)} to process.")
    print(f"Running with {num_workers} parallel workers.")

    queue   = multiprocessing.Queue()
    lock    = multiprocessing.Lock()

    jobs = list(remaining)  # paths yet to be submitted

    # active: maps path -> (Process, start_time)
    active: dict[str, tuple[multiprocessing.Process, float]] = {}

    def _spawn(path: str):
        p = multiprocessing.Process(target=_worker, args=(path, queue))
        p.start()
        active[path] = (p, time.monotonic())

    # Seed initial workers
    for _ in range(min(num_workers, len(jobs))):
        _spawn(jobs.pop(0))

    with tqdm(total=len(remaining), desc="Processing", unit="file") as bar:
        while active:
            time.sleep(0.05)

            # Drain all available results from the queue first
            while True:
                try:
                    result_name, rows, error = queue.get_nowait()
                    if error:
                        tqdm.write(f"FAILED {result_name}: {error}")
                        with open(ERROR_FILE, "a") as ef:
                            ef.write(f"{result_name}: {error}\n")
                    else:
                        tqdm.write(result_name)
                        _write_csv(rows, RESULTS_FILE, lock)
                except Exception:
                    break  # queue empty

            # Check each active process for completion or timeout
            for path, (proc, t0) in list(active.items()):
                file_name = os.path.basename(path)
                finished  = not proc.is_alive()
                timed_out = time.monotonic() - t0 > TIMEOUT_SECONDS

                if timed_out and not finished:
                    proc.terminate()
                    proc.join()
                    tqdm.write(f"TIMEOUT {file_name}")
                    with open(ERROR_FILE, "a") as ef:
                        ef.write(f"{file_name}: timeout after {TIMEOUT_SECONDS}s\n")
                    del active[path]
                    bar.update()
                    if jobs:
                        _spawn(jobs.pop(0))

                elif finished:
                    proc.join()
                    del active[path]
                    bar.update()
                    if jobs:
                        _spawn(jobs.pop(0))