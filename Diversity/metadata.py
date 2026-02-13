import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('./condorcet_results2.csv')

print("Sample size: 14 (Scotland) + 2 (America) = 16\n")

winners = df.groupby('file')['winner'].nunique()
num_winners = (winners == 1).sum()
num_winners2 = (winners != 1).sum()

print(f"How many files have no change in winner regardless of threshold? {num_winners}")
print(f"How many files have some change in winner regardless of threshold? {num_winners2}\n")

for thresholds in range(0, 100):
    threshold = thresholds / 1000
    filtered_winners = df[df['threshold'] > threshold].groupby('file')['winner'].nunique()
    num_filtered_winners = (filtered_winners != 1).sum()

    print(f"How many files have a change in winner for thresholds after {threshold}? {num_filtered_winners}")

df["candsLeft"] = (df["numCands"] - df["rounds"] + 1).astype(int)

filtered = df[df["threshold"] == 0]
counts = filtered["candsLeft"].value_counts().sort_index()

plt.figure()
plt.bar(counts.index, counts.values)
plt.xticks(range(int(counts.index.min()), int(counts.index.max()) + 1))

plt.xlabel("Candidates Left Before Selection")
plt.ylabel("Elections")
plt.title("Distribution of Candidates Left (Threshold = 0)")
plt.savefig("candsLeft.png")