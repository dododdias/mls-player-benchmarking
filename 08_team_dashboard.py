"""
Phase 9 — Team spend-vs-performance: which MLS teams are getting the most
out of their payroll, and where does Sporting KC sit? Real salary data
(Phase 6) makes this a genuine value analysis, not a proxy.

Runs after 05_fetch_extended.py. Requires: pip install pandas

Generates:
  - data/team_value.csv  (one row per team: results, underlying xG process,
    payroll, and value-for-money ratios)
"""

import pandas as pd

SKC_TEAM_ID = "Z2vQ1xlqrA"  # printed by 01_fetch_data.py on first run

teams = pd.read_csv("data/teams.csv")
xgoals = pd.read_csv("data/teams_xgoals.csv")
salaries = pd.read_csv("data/teams_salaries.csv")

df = teams.merge(xgoals, on="team_id", how="inner")
df = df.merge(salaries, on="team_id", how="left")

df["payroll_millions"] = df["total_guaranteed_compensation"] / 1_000_000
df["points_per_million"] = df["points"] / df["payroll_millions"]
df["xpoints_per_million"] = df["xpoints"] / df["payroll_millions"]
# Positive = overperforming the underlying process (finishing well / good
# goalkeeping / some luck); negative = underperforming it.
df["points_minus_xpoints"] = df["points"] - df["xpoints"]
df["is_skc"] = df["team_id"] == SKC_TEAM_ID

df["value_rank"] = df["points_per_million"].rank(ascending=False, method="min").astype(int)

cols = [
    "team_id", "team_name", "is_skc", "count_games", "points", "xpoints",
    "points_minus_xpoints", "goal_difference", "xgoal_difference",
    "payroll_millions", "points_per_million", "xpoints_per_million", "value_rank",
]
out = df[cols].sort_values("value_rank")
out.to_csv("data/team_value.csv", index=False)
print(f"Saved data/team_value.csv with {len(out)} teams.")

skc = out[out["is_skc"]]
if not skc.empty:
    r = skc.iloc[0]
    print(f"\nSporting KC: value_rank {r['value_rank']}/{len(out)}, "
          f"{r['points']} pts on ${r['payroll_millions']:.1f}M "
          f"({r['points_per_million']:.2f} pts/$M), "
          f"{'over' if r['points_minus_xpoints'] > 0 else 'under'}performing "
          f"xpoints by {abs(r['points_minus_xpoints']):.1f}.")

print("\nTop 5 value-for-money teams:")
print(out.head(5)[["team_name", "points", "payroll_millions", "points_per_million"]]
      .to_string(index=False))
