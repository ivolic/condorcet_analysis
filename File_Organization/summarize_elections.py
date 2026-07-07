import csv
import statistics

# ─── UPDATE THIS PATH ───────────────────────────────────────────────────────
METADATA_FILE = "/Users/belle/Desktop/data/elections_metadata.csv"
OUTPUT_FILE   = "/Users/belle/Desktop/data/elections_summary.txt"
# ────────────────────────────────────────────────────────────────────────────


def load_metadata(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # coerce numeric fields
            try:
                row["num_candidates"]      = int(row["num_candidates"])
                row["num_seats"]           = int(float(row["num_seats"])) if row["num_seats"] not in ("nan", "") else None
                row["total_ballots"]       = int(row["total_ballots"])
                row["unique_ballot_types"] = int(row["unique_ballot_types"])
                row["bullet_vote_count"]   = int(row["bullet_vote_count"])
                row["bullet_vote_pct"]     = float(row["bullet_vote_pct"]) if row["bullet_vote_pct"] != "" else 0.0
                row["partial_ballot_count"]= int(row["partial_ballot_count"])
                row["partial_ballot_pct"]  = float(row["partial_ballot_pct"]) if row["partial_ballot_pct"] != "" else 0.0
                row["full_ballot_count"]   = int(row["full_ballot_count"])
                row["full_ballot_pct"]     = float(row["full_ballot_pct"]) if row["full_ballot_pct"] != "" else 0.0
                rows.append(row)
            except Exception as e:
                print(f"  [SKIP] {row.get('file_path','?')} — {e}")
    return rows


def section(title):
    return f"\n{'='*60}\n  {title}\n{'='*60}\n"


def stats_block(label, values):
    if not values:
        return f"  {label}: no data\n"
    return (
        f"  {label}:\n"
        f"    count  : {len(values)}\n"
        f"    mean   : {statistics.mean(values):.2f}\n"
        f"    median : {statistics.median(values):.2f}\n"
        f"    stdev  : {statistics.stdev(values):.2f}\n" if len(values) > 1 else
        f"  {label}:\n"
        f"    count  : {len(values)}\n"
        f"    mean   : {statistics.mean(values):.2f}\n"
        f"    median : {statistics.median(values):.2f}\n"
    )


def summarize(rows, label="All elections"):
    if not rows:
        return f"  No elections found.\n"

    lines = []
    lines.append(f"  Total elections      : {len(rows)}")
    lines.append(f"  Total ballots cast   : {sum(r['total_ballots'] for r in rows):,}")
    lines.append("")

    lines.append(stats_block("Candidates per election", [r["num_candidates"] for r in rows]))
    lines.append(stats_block("Seats per election",      [r["num_seats"] for r in rows if r["num_seats"] is not None]))
    lines.append(stats_block("Ballots per election",    [r["total_ballots"] for r in rows]))
    lines.append(stats_block("Unique ballot types",     [r["unique_ballot_types"] for r in rows]))
    lines.append(stats_block("Bullet vote %",           [r["bullet_vote_pct"] for r in rows]))
    lines.append(stats_block("Partial ballot %",        [r["partial_ballot_pct"] for r in rows]))
    lines.append(stats_block("Full ballot %",           [r["full_ballot_pct"] for r in rows]))

    # Top/bottom 5 by bullet vote rate
    sorted_bullet = sorted(rows, key=lambda r: r["bullet_vote_pct"], reverse=True)
    lines.append("  Highest bullet vote rate:")
    for r in sorted_bullet[:5]:
        lines.append(f"    {r['bullet_vote_pct']:5.1f}%  {r['file_path']}")
    lines.append("  Lowest bullet vote rate:")
    for r in sorted_bullet[-5:]:
        lines.append(f"    {r['bullet_vote_pct']:5.1f}%  {r['file_path']}")

    return "\n".join(lines) + "\n"


def generate_summary():
    rows = load_metadata(METADATA_FILE)
    print(f"Loaded {len(rows)} elections.")

    single   = [r for r in rows if r["election_type"] == "single"]
    multi    = [r for r in rows if r["election_type"] == "multi"]
    unknown  = [r for r in rows if r["election_type"] == "unknown"]

    out = []
    out.append("ELECTION BALLOT SUMMARY STATISTICS")
    out.append(f"Generated from: {METADATA_FILE}\n")

    out.append(section("ALL ELECTIONS"))
    out.append(summarize(rows))

    out.append(section(f"SINGLE-WINNER ELECTIONS ({len(single)})"))
    out.append(summarize(single))

    out.append(section(f"MULTI-WINNER ELECTIONS ({len(multi)})"))
    out.append(summarize(multi))

    if unknown:
        out.append(section(f"UNKNOWN SEAT ELECTIONS ({len(unknown)})"))
        out.append(summarize(unknown))

    # Comparison table: single vs multi
    out.append(section("SINGLE vs MULTI WINNER COMPARISON"))
    metrics = [
        ("Avg candidates",   lambda r: r["num_candidates"]),
        ("Avg total ballots",lambda r: r["total_ballots"]),
        ("Avg bullet vote %",lambda r: r["bullet_vote_pct"]),
        ("Avg partial %",    lambda r: r["partial_ballot_pct"]),
        ("Avg full ballot %",lambda r: r["full_ballot_pct"]),
    ]
    out.append(f"  {'Metric':<25} {'Single':>10} {'Multi':>10}")
    out.append(f"  {'-'*25} {'-'*10} {'-'*10}")
    for label, fn in metrics:
        sv = statistics.mean([fn(r) for r in single]) if single else float("nan")
        mv = statistics.mean([fn(r) for r in multi])  if multi  else float("nan")
        out.append(f"  {label:<25} {sv:>10.2f} {mv:>10.2f}")

    result = "\n".join(out)
    print(result)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\nSummary written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_summary()
