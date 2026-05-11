import csv
import json
import re
from pathlib import Path

import numpy as np
import plotly.graph_objects as go


# ── Config ────────────────────────────────────────────────────────────────────

COUNTRY_FILES = {
    "Australia": "australia.csv",
    "Scotland":  "scotland.csv",
    "America":   "america.csv",
}

OUTPUT_STATS  = "ballot_summary_stats.json"
OUTPUT_CHART  = "ballot_candidates_vs_incomplete.html"

COLORS = {
    "Australia": "#1B6CA8",
    "Scotland":  "#B5121B",
    "America":   "#2E7D32",
}


# ── Data loading ──────────────────────────────────────────────────────────────

def extract_district(filename: str) -> str:
    match = re.search(r"BallotPaperDetails-(.+?)\s+with candidates", filename, re.IGNORECASE)
    return match.group(1).strip() if match else filename


def load_csv(path: Path) -> list[dict]:
    """Load a ballot CSV and return a list of normalised row dicts."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)

    if not rows:
        raise ValueError(f"No data rows in {path}")

    headers = list(rows[0].keys())
    records = []

    for row in rows:
        election   = row.get("election")    or row[headers[0]]
        num_cands  = int(  row.get("num_candidates") or row.get("") or row[headers[1]])
        complete   = float(row.get("complete")   or row[headers[2]])
        incomplete = float(row.get("incomplete") or row[headers[3]])

        records.append({
            "election":       election,
            "district":       extract_district(election),
            "num_candidates": num_cands,
            "complete":       complete,
            "incomplete":     incomplete,
        })

    return records


# ── Summary statistics ────────────────────────────────────────────────────────

def summarise(records: list[dict]) -> dict:
    def col(key):
        return [r[key] for r in records]

    incomplete = col("incomplete")
    complete   = col("complete")
    candidates = col("num_candidates")

    def stats(values: list) -> dict:
        arr = np.array(values, dtype=float)
        return {
            "min":    round(float(arr.min()),  2),
            "max":    round(float(arr.max()),  2),
            "mean":   round(float(arr.mean()), 2),
            "median": round(float(np.median(arr)), 2),
            "std":    round(float(arr.std()),  2),
        }

    return {
        "num_districts":        len(records),
        "incomplete_rate":      stats(incomplete),
        "complete_rate":        stats(complete),
        "num_candidates":       stats(candidates),
        "highest_incomplete":   max(records, key=lambda r: r["incomplete"])["district"],
        "lowest_incomplete":    min(records, key=lambda r: r["incomplete"])["district"],
    }


def generate_stats(country_files: dict[str, str]) -> dict:
    output = {}

    for country, filepath in country_files.items():
        path = Path(filepath)
        if not path.exists():
            print(f"  WARNING: {filepath} not found — skipping {country}")
            continue
        records = load_csv(path)
        output[country] = {
            "source_file": filepath,
            "summary":     summarise(records),
            "records":     records,
        }

    return output


# ── Visualisation ─────────────────────────────────────────────────────────────

def plot(country_data: dict, output_path: str) -> None:
    fig = go.Figure()

    for country, data in country_data.items():
        records   = data["records"]
        x         = [r["num_candidates"] for r in records]
        y         = [r["incomplete"]     for r in records]
        districts = [r["district"]       for r in records]
        elections = [r["election"]       for r in records]
        color     = COLORS.get(country, "#555555")

        hover_text = [
            f"<b>{d}</b><br>"
            f"Election: {e}<br>"
            f"Candidates: {xi}<br>"
            f"Incomplete: {yi:.1f}%"
            for d, e, xi, yi in zip(districts, elections, x, y)
        ]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name=country,
            marker=dict(
                color=color,
                size=11,
                line=dict(color="white", width=1.5),
                opacity=0.88,
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text="Incomplete ballot rate vs. number of candidates",
            font=dict(size=15, color="#222222"),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title="Number of candidates",
            tickmode="linear",
            dtick=1,
            gridcolor="#E5E5E5",
            linecolor="#CCCCCC",
            zeroline=False,
        ),
        yaxis=dict(
            title="Incomplete ballot rate (%)",
            gridcolor="#E5E5E5",
            linecolor="#CCCCCC",
            zeroline=False,
            ticksuffix="%",
        ),
        legend=dict(
            title="Country",
            bgcolor="rgba(250,250,250,0.9)",
            bordercolor="#CCCCCC",
            borderwidth=1,
        ),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FAFAFA",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#CCCCCC",
            font_size=12,
        ),
        margin=dict(l=60, r=30, t=60, b=60),
    )

    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"  Chart saved → {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    country_data = generate_stats(COUNTRY_FILES)

    if not country_data:
        print("No data loaded — check your file paths.")
        return

    # Save summary stats
    stats_out = {c: d["summary"] for c, d in country_data.items()}
    with open(OUTPUT_STATS, "w", encoding="utf-8") as f:
        json.dump(stats_out, f, indent=2)
    print(f"  Stats saved  → {OUTPUT_STATS}")

    # Print to console
    for country, summary in stats_out.items():
        print(f"\n── {country} ──")
        for key, val in summary.items():
            if isinstance(val, dict):
                print(f"  {key}:")
                for k, v in val.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {val}")

    # Plot
    print("\nGenerating chart...")
    plot(country_data, OUTPUT_CHART)


if __name__ == "__main__":
    main()