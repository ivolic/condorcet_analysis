
# import sys
# import pandas as pd
# import matplotlib.pyplot as plt
# import itertools

# def main():
#     if len(sys.argv) < 2:
#         print("Usage: python plot_clone_outcome.py <path_to_csv> [output_image_path]")
#         sys.exit(1)

#     csv_path = sys.argv[1]
#     output_path = sys.argv[2] if len(sys.argv) > 2 else "clone_outcome_chart.png"

#     # Load data
#     df = pd.read_csv(csv_path)
#     df = df[df["percent"] <= 0.4]

#     # High-contrast colors, one per method
#     colors = [
#         "#E41A1C",  # red
#         "#377EB8",  # blue
#         "#4DAF4A",  # green
#         "#FF7F00",  # orange
#         "#984EA3",  # purple
#         "#A65628",  # brown
#         "#F781BF",  # pink
#         "#999999",  # gray
#     ]

#     methods = sorted(df["method"].unique())
#     color_map = {method: colors[i % len(colors)] for i, method in enumerate(methods)}

#     markers = ["o", "s", "^", "D", "v", "P"]
#     marker_cycle = itertools.cycle(markers)
#     marker_map = {method: next(marker_cycle) for method in methods}

#     fig, ax = plt.subplots(figsize=(9, 6))

#     for method in methods:
#         group = df[df["method"] == method].sort_values("percent")
#         color = color_map[method]
#         marker = marker_map[method]

#         # Clone wins - solid line
#         ax.plot(
#             group["percent"],
#             group["pct_clone_wins"],
#             color=color,
#             linestyle="-",
#             marker=marker,
#             markersize=6,
#             linewidth=2.2,
#             alpha=0.9,
#             label=f"{method} – Clone Wins"
#         )

#         # Spoiler wins - dashed line
#         ax.plot(
#             group["percent"],
#             group["pct_spoiler_wins"],
#             color=color,
#             linestyle="--",
#             marker=marker,
#             markersize=6,
#             linewidth=2.2,
#             alpha=0.6,
#             label=f"{method} – Spoiler Wins"
#         )

#     ax.set_xlabel("Likelihood of clone being placed above the candidate")
#     ax.set_ylabel("Pct of Flips")
#     ax.set_title("For each candidate-election pair where there is a spoiler effect, who is the new winner?")
#     ax.legend(title="Method / Outcome", bbox_to_anchor=(1.02, 1), loc="upper left")
#     ax.grid(True, alpha=0.3)

#     plt.tight_layout()
#     plt.savefig(output_path, dpi=150)
#     print(f"Chart saved to {output_path}")
#     plt.show()

# if __name__ == "__main__":
#     main()

import sys
import pandas as pd
import matplotlib.pyplot as plt
import itertools

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_elections.py <path_to_csv> [output_image_path] [--jitter]")
        sys.exit(1)

    csv_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "chart.png"
    use_jitter = "--jitter" in sys.argv

    # Load data
    df = pd.read_csv(csv_path)
    df = df[df["percent"] <= 0.4]

    # High-contrast, easily distinguishable colors (avoids similar shades)
    colors = [
        "#E41A1C",  # red
        "#377EB8",  # blue
        "#4DAF4A",  # green
        "#FF7F00",  # orange
        "#984EA3",  # purple
        "#A65628",  # brown
        "#F781BF",  # pink
        "#999999",  # gray
    ]
    linestyles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "D", "v", "P"]

    color_cycle = itertools.cycle(colors)
    linestyle_cycle = itertools.cycle(linestyles)
    marker_cycle = itertools.cycle(markers)

    fig, ax = plt.subplots(figsize=(8, 6))

    methods = sorted(df["method"].unique())
    n = len(methods)

    for i, method in enumerate(methods):
        group = df[df["method"] == method].sort_values("percent")

        y = group["pct_elections"].copy()

        # Add a tiny vertical offset per method so identical lines don't fully overlap
        if use_jitter and n > 1:
            offset = (i - (n - 1) / 2) * 0.4  # small buffer, tweak as needed
            y = y + offset

        ax.plot(
            group["percent"],
            y,
            color=next(color_cycle),
            linestyle=next(linestyle_cycle),
            marker=next(marker_cycle),
            markersize=6,
            linewidth=2.2,
            alpha=0.9,
            label=method
        )

    ax.set_xlabel("Likelihood of clone being placed above the candidate")
    ax.set_ylabel("Pct of elections")
    ax.set_title("America: Elections where cloning one of the candidates changed the result")
    ax.legend(title="Method")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Chart saved to {output_path}")

if __name__ == "__main__":
    main()