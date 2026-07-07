"""
Election Cloning Impact Analyzer
=================================
X axis: percent (0-50, probability clone is placed above original)
Lines:  one per diversity threshold (0.0-0.09), with small jitter offsets
Y axis: % of unique elections where the winner changed from baseline

Data format notes:
  - `percent` column may be a fraction string like "1/10" or a plain number
    like "0" / "50". It's converted to a percent float (0-100).
  - `candidate_cloned` is "none" for baseline rows, or a plain candidate
    name (or comma-separated names) for cloned rows. Old-style
    "frozenset({'Name'})" strings are still supported for backward compat.
  - Winner cells look like "('Robin Wonsley Worlobah', 4)" -> we take the
    first element of the tuple as the winner name.
  - Elections are grouped by `election_id` (falls back to `file` if present).

Rules:
  - Ignore percent > 50
  - At percent == 50, ignore if the new winner IS the clone of the original
    winner (i.e. the clone simply replaced its original - not a true
    spoiler effect)
"""

import ast
import re
from fractions import Fraction

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

RAW_THRESH = ["0.0", "0.01", "0.02", "0.03", "0.04",
              "0.05", "0.06", "0.07", "0.08", "0.09"]


def parse_percent(cell) -> float:
    """Convert values like '1/10', '0', '50' into a percent float (0-100)."""
    s = str(cell).strip()
    if s == "" or s.lower() == "none":
        return 0.0
    if "/" in s:
        return float(Fraction(s)) * 100
    return float(s)


def parse_winner(cell: str) -> str:
    """Extract the winner name from a cell like "('Robin Wonsley Worlobah', 4)"."""
    try:
        val = ast.literal_eval(cell)
        if isinstance(val, (tuple, list)):
            return val[0]
        return val
    except Exception:
        m = re.search(r"'([^']+)'", str(cell))
        return m.group(1) if m else str(cell)


def parse_cloned_candidates(cell) -> set:
    """Parse the candidate_cloned cell into a set of candidate names.

    Supports:
      - "none"                        -> set()
      - "Cam Gordon"                  -> {"Cam Gordon"}
      - "Cam Gordon, Yusra Arab"      -> {"Cam Gordon", "Yusra Arab"}
      - "frozenset({'Alice (Lab)'})"  -> {"Alice (Lab)"}   (legacy format)
    """
    s = str(cell).strip()
    if s == "" or s.lower() == "none":
        return set()

    if s.startswith("frozenset"):
        inner = s[len("frozenset("):-1] if s.endswith(")") else s
        try:
            val = ast.literal_eval(inner)
            if isinstance(val, (set, frozenset, list, tuple)):
                return set(val)
        except Exception:
            pass
        return set(re.findall(r"'([^']+)'", s))

    return {name.strip() for name in s.split(",") if name.strip()}


def analyze(df: pd.DataFrame) -> dict:
    df.columns = [c.strip() for c in df.columns]
    df = df.copy()

    df["percent"] = df["percent"].apply(parse_percent)

    # Only keep percent <= 50
    df = df[df["percent"] < 50].copy()
    percent_values = sorted(df["percent"].unique())

    id_col = "election_id" if "election_id" in df.columns else "file"

    results = {
        t: {p: {"impacted": set(), "total": set()} for p in percent_values}
        for t in RAW_THRESH
    }

    for election_id, group in df.groupby(id_col):
        baseline_rows = group[group["candidate_cloned"] == "none"]
        cloned_rows   = group[group["candidate_cloned"] != "none"]
        if baseline_rows.empty:
            continue
        baseline = baseline_rows.iloc[0]

        for _, clone_row in cloned_rows.iterrows():
            p = clone_row["percent"]
            cloned_candidates = parse_cloned_candidates(clone_row["candidate_cloned"])

            for t in RAW_THRESH:
                results[t][p]["total"].add(election_id)
                baseline_winner = parse_winner(baseline[t])
                clone_winner    = parse_winner(clone_row[t])

                if clone_winner == baseline_winner:
                    continue  # no change

                # At percent == 50 only: skip if the original winner was cloned
                # and the new winner is that clone (clone displaced its original)
                if p == 50 and baseline_winner in cloned_candidates and "Clone" in clone_winner:
                    continue

                results[t][p]["impacted"].add(election_id)

    return {
        "percent_values": percent_values,
        "thresholds": RAW_THRESH,
        "results": {
            t: {p: {
                "impacted": len(results[t][p]["impacted"]),
                "total":    len(results[t][p]["total"]),
            } for p in percent_values}
            for t in RAW_THRESH
        },
    }


def plot(data: dict, out_path: str = "cloning_impact.png"):
    percent_values = data["percent_values"]
    thresholds     = data["thresholds"]
    results        = data["results"]

    x = np.array(percent_values, dtype=float)
    n = len(thresholds)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f7f8fc")
    ax.tick_params(colors="#333333")
    ax.xaxis.label.set_color("#333333")
    ax.yaxis.label.set_color("#333333")
    ax.title.set_color("#111111")
    for spine in ax.spines.values():
        spine.set_edgecolor("#d0d4e0")

    cmap   = plt.get_cmap("Blues")
    colors = [cmap(0.3 + 0.7 * i / max(n - 1, 1)) for i in range(n)]

    # Small x jitter so overlapping lines are all visible
    jitter_range = (x[-1] - x[0]) * 0.008 if len(x) > 1 else 0.5
    offsets = np.linspace(-jitter_range * (n - 1) / 2,
                           jitter_range * (n - 1) / 2, n)

    for i, (t, color) in enumerate(zip(thresholds, colors)):
        y = []
        for p in percent_values:
            total    = results[t][p]["total"]
            impacted = results[t][p]["impacted"]
            y.append((impacted / total * 100) if total > 0 else 0.0)

        ax.plot(x + offsets[i], y, color=color, linewidth=2, marker="o",
                markersize=5, markerfacecolor="#ffffff",
                markeredgewidth=1.5, label=f"threshold {t}")

    ax.set_title("Australia: Elections where cloning changed the winner",
                 fontsize=13, pad=12)
    ax.set_xlabel("Probability of clone placed above original")
    ax.set_ylabel("Percent of elections")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.grid(color="#d0d4e0", linewidth=0.7, linestyle="--")
    ax.legend(title="Diversity threshold", fontsize=8, title_fontsize=9,
              framealpha=0.9, edgecolor="#d0d4e0")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"Chart saved -> {out_path}")
    # plt.show()


def main(csv_path: str, out_path: str = "cloning_impact.png"):
    df   = pd.read_csv(csv_path)
    data = analyze(df)
    plot(data, out_path)


if __name__ == "__main__":
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "elections.csv"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "cloning_impact.png"
    main(csv_file, out_file)