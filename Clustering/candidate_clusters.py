"""
RCV candidate-relationship analysis
------------------------------------
Implements:
  1) Pairwise average-rank-gap distance matrix -> MDS
  3) Weighted rank-correlation matrix -> MDS

Input: CSV with columns rank1..rankN, Count, (optionally) "Num Seats"
"skipped" entries are treated as "not ranked" (missing), not as tied-last.
"""

import pandas as pd
import numpy as np
from itertools import combinations
from sklearn.manifold import MDS
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# ----------------------------------------------------------------------
# 1. LOAD DATA
# ----------------------------------------------------------------------

def load_ballots(csv_path):
    df = pd.read_csv(csv_path)
    rank_cols = [c for c in df.columns if c.lower().startswith("rank")]
    df[rank_cols] = df[rank_cols].replace("skipped", np.nan)
    return df, rank_cols


def ballot_to_rank_dict(row, rank_cols):
    """Return {candidate: rank_position} for one ballot row, ignoring NaNs."""
    d = {}
    for i, col in enumerate(rank_cols, start=1):
        cand = row[col]
        if pd.notna(cand):
            d[cand] = i
    return d


def get_candidates(df, rank_cols):
    cands = set()
    for col in rank_cols:
        cands.update(df[col].dropna().unique())
    return sorted(cands)


# ----------------------------------------------------------------------
# METHOD 1: Average rank-gap distance matrix
# ----------------------------------------------------------------------
# distance(X, Y) = weighted average of |rank(X) - rank(Y)|
# over all ballots where BOTH X and Y are ranked.
# Smaller distance = candidates tend to be ranked near each other
# (similar voter support). Pairs that never co-occur get distance = NaN,
# which we fill in afterward with the max observed distance (treat as "far").

def rank_gap_distance_matrix(df, rank_cols, count_col="Count"):
    candidates = get_candidates(df, rank_cols)
    idx = {c: i for i, c in enumerate(candidates)}
    n = len(candidates)

    weighted_gap_sum = np.zeros((n, n))
    weight_sum = np.zeros((n, n))

    for _, row in df.iterrows():
        w = row[count_col] if count_col in df.columns else 1
        rd = ballot_to_rank_dict(row, rank_cols)
        for a, b in combinations(rd.keys(), 2):
            i, j = idx[a], idx[b]
            gap = abs(rd[a] - rd[b])
            weighted_gap_sum[i, j] += gap * w
            weighted_gap_sum[j, i] += gap * w
            weight_sum[i, j] += w
            weight_sum[j, i] += w

    with np.errstate(invalid="ignore", divide="ignore"):
        dist = weighted_gap_sum / weight_sum

    # Pairs that never co-occur: fill with max observed distance (treat as "far apart")
    max_dist = np.nanmax(dist) if np.any(~np.isnan(dist)) else 1.0
    dist = np.nan_to_num(dist, nan=max_dist)
    np.fill_diagonal(dist, 0.0)

    return pd.DataFrame(dist, index=candidates, columns=candidates)


# ----------------------------------------------------------------------
# METHOD 3: Weighted rank-correlation matrix
# ----------------------------------------------------------------------
# For each candidate, build a per-ballot "rank vector" (one row per ballot,
# repeated by Count). Missing = NaN (candidate not ranked on that ballot).
# Compute pairwise correlation only over ballots where both are ranked,
# weighted by Count. High positive corr -> ranked similarly (same cluster).
# Negative corr -> traded off against each other (opposing clusters).
# Convert to a *distance* via (1 - corr) / 2 so it's directly comparable to
# method 1's output and usable in MDS (range 0 = identical, 1 = opposite).

def weighted_rank_correlation_matrix(df, rank_cols, count_col="Count"):
    candidates = get_candidates(df, rank_cols)
    n = len(candidates)
    idx = {c: i for i, c in enumerate(candidates)}

    # Expand ballots into rows of [candidate_rank_vector, weight]
    n_ballots = len(df)
    rank_matrix = np.full((n_ballots, n), np.nan)
    weights = np.zeros(n_ballots)

    for r, (_, row) in enumerate(df.iterrows()):
        w = row[count_col] if count_col in df.columns else 1
        weights[r] = w
        rd = ballot_to_rank_dict(row, rank_cols)
        for cand, rank in rd.items():
            rank_matrix[r, idx[cand]] = rank

    corr = np.full((n, n), np.nan)
    for i, j in combinations(range(n), 2):
        xi = rank_matrix[:, i]
        xj = rank_matrix[:, j]
        mask = ~np.isnan(xi) & ~np.isnan(xj)
        if mask.sum() < 2:
            continue
        w = weights[mask]
        x = xi[mask]
        y = xj[mask]

        # weighted Pearson correlation (on the ranks themselves;
        # swap to scipy.stats.rankdata first if you want weighted Spearman)
        wx_mean = np.average(x, weights=w)
        wy_mean = np.average(y, weights=w)
        cov = np.average((x - wx_mean) * (y - wy_mean), weights=w)
        var_x = np.average((x - wx_mean) ** 2, weights=w)
        var_y = np.average((y - wy_mean) ** 2, weights=w)
        denom = np.sqrt(var_x * var_y)
        c = cov / denom if denom > 0 else 0.0

        corr[i, j] = corr[j, i] = c

    np.fill_diagonal(corr, 1.0)
    # pairs that never co-occur -> assume neutral (corr = 0)
    corr = np.nan_to_num(corr, nan=0.0)

    distance = (1 - corr) / 2  # 0 = perfectly together, 1 = perfectly opposed
    return pd.DataFrame(distance, index=candidates, columns=candidates), pd.DataFrame(corr, index=candidates, columns=candidates)


# ----------------------------------------------------------------------
# MDS PROJECTION + simple clustering helper
# ----------------------------------------------------------------------

def project_2d(distance_df, random_state=42):
    mds = MDS(n_components=2, dissimilarity="precomputed",
              random_state=random_state, normalized_stress="auto")
    coords = mds.fit_transform(distance_df.values)
    return pd.DataFrame(coords, index=distance_df.index, columns=["x", "y"])


def cluster_candidates(coords_df, n_clusters=2):
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(coords_df.values)
    return pd.Series(labels, index=coords_df.index, name="cluster")


# ----------------------------------------------------------------------
# PLOTTING
# ----------------------------------------------------------------------

# Colour palette — one colour per cluster, up to 6 clusters
CLUSTER_COLORS = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#9b5de5", "#f4a261"]

def shorten(name, max_len=20):
    """Truncate long candidate names for plot labels."""
    return name if len(name) <= max_len else name[:max_len - 1] + "…"


def plot_mds(coords_df, clusters, title, ax):
    """
    Scatter plot of MDS coordinates.

    coords_df : DataFrame with columns x, y, one row per candidate
    clusters  : Series of integer cluster labels, same index as coords_df
    title     : string shown at the top of the subplot
    ax        : matplotlib Axes to draw on
    """
    n_clusters = clusters.nunique()

    for i, (cand, row) in enumerate(coords_df.iterrows()):
        cluster_id = clusters[cand]
        color = CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]

        # Draw a filled circle for the candidate
        ax.scatter(row["x"], row["y"], color=color, s=120, zorder=3,
                   edgecolors="white", linewidths=0.8)

        # Label just below-right of the dot.
        # We nudge the label slightly so it doesn't sit on top of the dot.
        ax.annotate(
            cand,
            xy=(row["x"], row["y"]),
            xytext=(6, -10),           # offset in points (not data units)
            textcoords="offset points",
            fontsize=8,
            color=color,
        )

    # Legend: one coloured patch per cluster
    legend_patches = [
        mpatches.Patch(color=CLUSTER_COLORS[k % len(CLUSTER_COLORS)],
                       label=f"Cluster {k}")
        for k in range(n_clusters)
    ]
    ax.legend(handles=legend_patches, fontsize=8, loc="best")

    # Draw faint crosshairs at the origin so you can read quadrants
    ax.axhline(0, color="grey", linewidth=0.4, linestyle="--")
    ax.axvline(0, color="grey", linewidth=0.4, linestyle="--")

    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("MDS dimension 1", fontsize=9)
    ax.set_ylabel("MDS dimension 2", fontsize=9)
    ax.tick_params(labelsize=8)


def plot_silhouette(coords_df, title, ax, max_k=None):
    """
    Bar chart of silhouette scores for k = 2 … max_k.

    The silhouette score measures how well-separated the clusters are:
      +1  = candidate is deep inside its own cluster, far from others (good)
       0  = candidate is sitting right on a cluster boundary (ambiguous)
      -1  = candidate would fit better in a different cluster (bad)
    The average across all candidates is plotted for each k.

    max_k defaults to (number of candidates - 1), which is the mathematical
    ceiling for silhouette score (you can't have more clusters than candidates
    minus one and still measure inter-cluster distance meaningfully).
    """
    n = len(coords_df)
    if max_k is None:
        max_k = min(n - 1, 6)   # cap at 6 for readability

    ks = range(2, max_k + 1)
    scores = []

    for k in ks:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(coords_df.values)
        # silhouette_score needs at least 2 distinct labels and 2 samples per label;
        # for tiny datasets (< 2k candidates) some k values are invalid — skip them.
        if len(set(labels)) < 2:
            scores.append(np.nan)
            continue
        scores.append(silhouette_score(coords_df.values, labels))

    bars = ax.bar(list(ks), scores,
                  color=[CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(len(ks))],
                  edgecolor="white", linewidth=0.6)

    # Annotate the bar values
    for bar, score in zip(bars, scores):
        if not np.isnan(score):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{score:.2f}",
                    ha="center", va="bottom", fontsize=8)

    # Highlight the best k with a black border
    best_idx = int(np.nanargmax(scores))
    bars[best_idx].set_edgecolor("black")
    bars[best_idx].set_linewidth(2)

    ax.set_xticks(list(ks))
    ax.set_xlabel("Number of clusters (k)", fontsize=9)
    ax.set_ylabel("Silhouette score", fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.tick_params(labelsize=8)

    best_k = list(ks)[best_idx]
    return best_k


def make_figure(coords1, coords3, clusters1, clusters3):
    """
    Produce a 2×2 figure:
      top row    — MDS scatter plots (method 1 left, method 3 right)
      bottom row — silhouette bar charts (method 1 left, method 3 right)
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle("RCV candidate clustering analysis", fontsize=14, fontweight="bold", y=0.98)

    # Top row: MDS scatter plots
    plot_mds(coords1, clusters1, "Method 1 — rank-gap distance (MDS)", axes[0, 0])
    plot_mds(coords3, clusters3, "Method 3 — rank-correlation distance (MDS)", axes[0, 1])

    # Bottom row: silhouette scores to help choose k
    best_k1 = plot_silhouette(coords1, "Method 1 — silhouette score by k", axes[1, 0])
    best_k3 = plot_silhouette(coords3, "Method 3 — silhouette score by k", axes[1, 1])

    plt.tight_layout(rect=[0, 0, 1, 0.96])   # leave room for the suptitle
    return fig, best_k1, best_k3


# ----------------------------------------------------------------------
# MAIN / EXAMPLE USAGE
# ----------------------------------------------------------------------

if __name__ == "__main__":
    csv_path = "/Users/belle/Desktop/build/rcv/American data condensed/Minnetonka/Minnetonka_11022021_CityCouncilAtLargeSeatB.csv"
    df, rank_cols = load_ballots(csv_path)

    # --- compute distance matrices ---
    print("Method 1: Average rank-gap distance")
    dist1 = rank_gap_distance_matrix(df, rank_cols)
    print(dist1.round(2))

    print("\nMethod 3: Rank-correlation distance (and raw correlation)")
    dist3, corr3 = weighted_rank_correlation_matrix(df, rank_cols)
    print(corr3.round(2))

    # --- project to 2D ---
    coords1 = project_2d(dist1)
    coords3 = project_2d(dist3)

    # --- initial cluster guess: k=2 ---
    clusters1 = cluster_candidates(coords1, n_clusters=2)
    clusters3 = cluster_candidates(coords3, n_clusters=2)

    # --- plot everything ---
    # The silhouette bars will tell you if k=2 is really the best split
    # or if k=3 (or more) fits better — look for the tallest bar.
    fig, best_k1, best_k3 = make_figure(coords1, coords3, clusters1, clusters3)
    print(f"\nBest k (method 1): {best_k1}")
    print(f"Best k (method 3): {best_k3}")

    fig.savefig("rcv_clusters.png", dpi=150, bbox_inches="tight")
    print("\nSaved plot to rcv_clusters.png")
    plt.show()