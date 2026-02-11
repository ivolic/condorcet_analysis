import pandas as pd

df = pd.read_csv('./condorcet_results2.csv')

print("Sample size: 14 (Scotland) + 2 (America) = 16\n")

winners = df.groupby('file')['winner'].nunique()
num_winners = (winners == 1).sum()

print(f"How many files have no change in winner regardless of threshold? {num_winners}\n")

for thresholds in range(1, 7):
    threshold = thresholds / 100
    filtered_winners = df[df['threshold'] > threshold].groupby('file')['winner'].nunique()
    num_filtered_winners = (filtered_winners != 1).sum()

    print(f"How many files have a change in winner for thresholds after {threshold}? {num_filtered_winners}")

print("Note: Oakland School Board District has changes up till 0.1")

