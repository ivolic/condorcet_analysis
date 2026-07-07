import os
import csv
from election_utils import parse_election

# ─── UPDATE THIS PATH ───────────────────────────────────────────────────────
SOURCE_DIR  = "/Users/belle/Desktop/data"
# ────────────────────────────────────────────────────────────────────────────

OUTPUT_FILE = os.path.join(SOURCE_DIR, "elections_metadata.csv")

FIELDNAMES = [
    "file_path", "election_type", "num_candidates", "num_seats",
    "total_ballots", "unique_ballot_types",
    "bullet_vote_count", "bullet_vote_pct",
    "partial_ballot_count", "partial_ballot_pct",
    "full_ballot_count", "full_ballot_pct",
]


def generate_metadata():
    rows   = []
    errors = []

    for root, dirs, files in os.walk(SOURCE_DIR):
        for filename in sorted(files):
            if not filename.lower().endswith(".csv"):
                continue
            filepath = os.path.join(root, filename)
            if os.path.abspath(filepath) == os.path.abspath(OUTPUT_FILE):
                continue

            try:
                d = parse_election(filepath)
            except Exception as e:
                rel = os.path.relpath(filepath, SOURCE_DIR)
                print(f"  [ERR] {rel} — {e}")
                errors.append((rel, str(e)))
                continue

            num_seats     = d["num_seats"]
            total         = d["total_ballots"]
            election_type = ("unknown" if num_seats is None else
                             "single"  if num_seats == 1    else "multi")

            def pct(n):
                return round(100 * n / total, 2) if total else ""

            rel_path = os.path.relpath(filepath, SOURCE_DIR)
            row = {
                "file_path":            rel_path,
                "election_type":        election_type,
                "num_candidates":       d["num_candidates"],
                "num_seats":            num_seats if num_seats is not None else "nan",
                "total_ballots":        total,
                "unique_ballot_types":  d["unique_ballot_types"],
                "bullet_vote_count":    d["bullet_vote_count"],
                "bullet_vote_pct":      pct(d["bullet_vote_count"]),
                "partial_ballot_count": d["partial_ballot_count"],
                "partial_ballot_pct":   pct(d["partial_ballot_count"]),
                "full_ballot_count":    d["full_ballot_count"],
                "full_ballot_pct":      pct(d["full_ballot_count"]),
            }
            rows.append(row)
            print(f"  [OK] {rel_path}")

    rows.sort(key=lambda r: r["file_path"])

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Metadata written to: {OUTPUT_FILE}")
    print(f"  Elections processed : {len(rows)}")
    print(f"  Errors              : {len(errors)}")
    if errors:
        for path, err in errors:
            print(f"    {path}: {err}")


if __name__ == "__main__":
    generate_metadata()
