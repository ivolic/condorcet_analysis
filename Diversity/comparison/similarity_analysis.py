"""
Voting Method Similarity Analysis
==================================
Compares election outcome agreement across voting methods using:
  1. Heatmap of pairwise agreement rates
  2. Dendrogram (hierarchical clustering)
  3. MDS scatter (2D embedding of dissimilarity)
  4. Average agreement bar chart (ranked)

Usage: python voting_similarity.py your_data.csv
       (or just run it — uses the bundled sample data)
"""

import sys
import ast
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial import distance

# ── palette ─────────────────────────────────────────────────────────────────

BACKGROUND = "#0f0f13"
SURFACE     = "#18181f"
BORDER      = "#2a2a35"
TEXT        = "#e2e2e8"
TEXT_DIM    = "#7a7a8c"

CMAP = LinearSegmentedColormap.from_list(
    "agreement",
    ["#3b1219", "#8b2635", "#c0614a", "#e8a44a", "#6dbf8a", "#2d9e60"],
    N=256,
)

CLUSTER_COLORS = [
    "#6c8ebf", "#82b366", "#d79b00", "#ae4132",
    "#9673a6", "#5d8a8a", "#c47f4a", "#6a6a9a",
]

plt.rcParams.update({
    "figure.facecolor":  BACKGROUND,
    "axes.facecolor":    SURFACE,
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   TEXT,
    "xtick.color":       TEXT_DIM,
    "ytick.color":       TEXT_DIM,
    "text.color":        TEXT,
    "grid.color":        BORDER,
    "grid.linewidth":    0.5,
    "font.family":       "monospace",
    "font.size":         9,
    "axes.titlesize":    11,
    "axes.titleweight":  "bold",
    "axes.titlecolor":   TEXT,
})

# ── data ─────────────────────────────────────────────────────────────────────

SAMPLE_CSV = """\
election_id,plurality,IRV,top-two,borda-pm,borda-om,borda-avg,top-3-truncation,condorcet,minimax,smith-plurality,smith-irv,smith-minimax,ranked-pairs,bucklin,smith,tvr-om,tvr-avg,tvr-pm,diversity-0,diversity-1,diversity-2,diversity-3,diversity-4,diversity-5,diversity-6,diversity-7,diversity-8,diversity-9,diversity-10
250,"['C']","['C']","['C']","['C']","['C']","['C']","['C']","[]","['C']","['C']","['C']","['C']","['C']","['C']","['A', 'C', 'B']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']"
251,"['C']","['C']","['C']","['C']","['C']","['C']","['C']","[]","['C']","['C']","['C']","['C']","['C']","['C']","['A', 'C', 'B']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']","['C']"
"""

country = "Scotland"

def parse_winner(cell: str) -> frozenset:
    """Turn "['A', 'C']", "[]", or "Cam Gordon" into a frozenset of winners."""
    try:
        val = ast.literal_eval(cell)
        return frozenset(val) if isinstance(val, list) else frozenset()
    except Exception:
        # Bare string — treat as a single winner if non-empty
        stripped = cell.strip()
        return frozenset([stripped]) if stripped else frozenset()

def load_data(*paths: str | None) -> tuple[pd.DataFrame, list[str]]:
    if paths:
        raw = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    else:
        from io import StringIO
        raw = pd.read_csv(StringIO(SAMPLE_CSV))

    raw["election_name"] = raw["election_id"].str.split("__").str[0]

    counts = raw["election_name"].value_counts()
    raw = raw[raw["election_name"].isin(counts[counts >= 200].index)]
    raw = raw.drop(columns=["election_name"])

    print(len(raw))
    EXCLUDE = {"smith", "condorcet"} # "borda-avg", "borda-om", "borda-pm", "bucklin", "top-3-truncation", "tvr-pm", "tvr-avg", "tvr-om", "irv", "top-two", "smith-plurality"}
    methods = [c for c in raw.columns if c != "election_id" and c.lower() not in EXCLUDE]
    for m in methods:
        raw[m] = raw[m].astype(str).apply(parse_winner)
    return raw, methods

def agreement_matrix(df: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    n = len(methods)
    mat = np.zeros((n, n))
    total = len(df)
    for i, a in enumerate(methods):
        for j, b in enumerate(methods):
            if total == 0:
                mat[i, j] = 0.0
            else:
                agree = sum(df[a].iloc[k] == df[b].iloc[k] for k in range(total))
                mat[i, j] = agree / total
    return pd.DataFrame(mat, index=methods, columns=methods)


# ── plots ────────────────────────────────────────────────────────────────────

def plot_heatmap(ax, sim: pd.DataFrame):
    methods = list(sim.columns)
    n = len(methods)
    data = sim.values

    im = ax.imshow(data, cmap=CMAP, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(
        [textwrap.fill(m, 10) for m in methods],
        rotation=45, ha="right", fontsize=7.5,
    )
    ax.set_yticklabels(methods, fontsize=7.5)

    for i in range(n):
        for j in range(n):
            v = data[i, j]
            ax.text(j, i, f"{v:.0%}", ha="center", va="center",
                    fontsize=6.5,
                    color="white" if v < 0.6 else "#0f0f13",
                    fontweight="bold" if i == j else "normal")

    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors=TEXT_DIM, labelsize=7)
    cbar.set_label("agreement rate", color=TEXT_DIM, fontsize=8)

    ax.set_title(f"Pairwise agreement of RCV methods ({country})", pad=10)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


def plot_dendrogram(ax, sim: pd.DataFrame):
    dist_mat = 1 - sim.values
    np.fill_diagonal(dist_mat, 0)
    condensed = squareform(np.clip(dist_mat, 0, None))
    Z = linkage(condensed, method="average")

    dn = dendrogram(
        Z,
        labels=list(sim.columns),
        ax=ax,
        orientation="left",
        leaf_font_size=8,
        color_threshold=0.3,
        above_threshold_color=TEXT_DIM,
        link_color_func=lambda k: CLUSTER_COLORS[k % len(CLUSTER_COLORS)],
    )
    ax.set_xlabel("dissimilarity  (1 − agreement)", fontsize=8, color=TEXT_DIM)
    ax.set_title(f"Hierarchical clustering dendrogram of RCV methods ({country})", pad=10)
    ax.tick_params(axis="x", colors=TEXT_DIM, labelsize=7)
    ax.tick_params(axis="y", colors=TEXT, labelsize=8)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


def plot_mds(ax, sim: pd.DataFrame):
    """Classical MDS (PCoA) on the dissimilarity matrix."""
    methods = list(sim.columns)
    n = len(methods)
    D = (1 - sim.values).clip(0)

    # Double-centre
    D2 = D ** 2
    row_mean = D2.mean(axis=1, keepdims=True)
    col_mean = D2.mean(axis=0, keepdims=True)
    grand_mean = D2.mean()
    B = -0.5 * (D2 - row_mean - col_mean + grand_mean)

    eigvals, eigvecs = np.linalg.eigh(B)
    idx = np.argsort(eigvals)[::-1]
    eigvals, eigvecs = eigvals[idx], eigvecs[:, idx]

    # Take top-2
    coords = eigvecs[:, :2] * np.sqrt(np.maximum(eigvals[:2], 0))

    # Colour points by first-level dendrogram cluster
    dist_mat = squareform(D.clip(0))
    Z = linkage(dist_mat, method="average")
    from scipy.cluster.hierarchy import fcluster
    labels = fcluster(Z, t=4, criterion="maxclust")

    for i, (x, y) in enumerate(coords):
        col = CLUSTER_COLORS[(labels[i] - 1) % len(CLUSTER_COLORS)]
        ax.scatter(x, y, color=col, s=60, zorder=3, edgecolors=BACKGROUND, linewidths=0.8)
        ax.annotate(
            methods[i], (x, y),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=7.5,
            color=TEXT,
        )

    ax.axhline(0, color=BORDER, linewidth=0.6, zorder=1)
    ax.axvline(0, color=BORDER, linewidth=0.6, zorder=1)
    ax.set_xlabel("MDS dim 1", fontsize=8, color=TEXT_DIM)
    ax.set_ylabel("MDS dim 2", fontsize=8, color=TEXT_DIM)
    ax.set_title("MDS cluster map  (distance ≈ disagreement)", pad=10)
    ax.grid(linestyle=":", alpha=0.35)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


def plot_avg_agreement(ax, sim: pd.DataFrame):
    methods = list(sim.columns)
    n = len(methods)
    # Average agreement with every OTHER method
    avg = []
    for m in methods:
        others = [x for x in methods if x != m]
        avg.append(sim.loc[m, others].mean())

    order = np.argsort(avg)[::-1]
    sorted_methods = [methods[i] for i in order]
    sorted_avg = [avg[i] for i in order]

    colors = [CMAP(v) for v in sorted_avg]
    bars = ax.barh(range(n), sorted_avg, color=colors, edgecolor=BACKGROUND, linewidth=0.5)

    ax.set_yticks(range(n))
    ax.set_yticklabels(sorted_methods, fontsize=8)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("average agreement with all other methods", fontsize=8, color=TEXT_DIM)
    ax.set_title("Method consensus rank", pad=10)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.tick_params(axis="x", labelsize=7, colors=TEXT_DIM)

    for i, v in enumerate(sorted_avg):
        ax.text(v + 0.01, i, f"{v:.1%}", va="center", fontsize=7.5, color=TEXT_DIM)

    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    # path = sys.argv[1] if len(sys.argv) > 1 else None
    # df, methods = load_data(path)
    df, methods = load_data("scotland_simul.csv")#, "usa_simul.csv", "scotland_simul.csv")
    sim = agreement_matrix(df, methods)

    fig_heat, ax_heat = plt.subplots(figsize=(10, 9), facecolor=BACKGROUND)
    # fig_heat.suptitle(
    #     "Voting method similarity analysis — Heatmap",
    #     fontsize=15, fontweight="bold", color=TEXT, y=0.99,
    # )
    plot_heatmap(ax_heat, sim)
    out_heat = f"voting_similarity_heatmap_{country}.png"
    fig_heat.savefig(out_heat, dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    print(f"Saved → {out_heat}")

    fig_dend, ax_dend = plt.subplots(figsize=(10, 9), facecolor=BACKGROUND)
    # fig_dend.suptitle(
    #     "Voting method similarity analysis — Dendrogram",
    #     fontsize=15, fontweight="bold", color=TEXT, y=0.99,
    # )
    plot_dendrogram(ax_dend, sim)
    out_dend = f"voting_similarity_dendrogram_{country}.png"
    fig_dend.savefig(out_dend, dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    print(f"Saved → {out_dend}")

if __name__ == "__main__":
    main()