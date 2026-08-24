"""
Phase 2 — Positional benchmarking.

Runs after 01_fetch_data.py. Requires: pip install pandas

Computes each player's percentile within their own position (general_position)
for a set of key metrics, normalized per 90 minutes.

IMPORTANT: after running 01_fetch_data.py, run
    python -c "import pandas as pd; print(pd.read_csv('data/players_master.csv').columns.tolist())"
and adjust the METRICS list below to match the real column names the API
returned (ASA renames things from time to time — e.g. xgoals, xassists,
key_passes, goals_added_raw, goals_added_above_avg, etc.).
"""

import pandas as pd

df = pd.read_csv("data/players_master.csv")

MINUTES_COL = "minutes_played"
POSITION_COL = "general_position"

# Adjust these names after inspecting the CSV's real columns
METRICS = [
    "shots",
    "key_passes",
    "xgoals",
    "xassists",
]

# Friendly label for each metric — used on the Tableau axis
METRIC_LABELS = {
    "shots": "Shots",
    "key_passes": "Key Passes",
    "xgoals": "xG",
    "xassists": "xA",
}

PER90_SUFFIX = "_p90"

# 1. Normalize per 90 minutes
for m in METRICS:
    if m in df.columns:
        df[m + PER90_SUFFIX] = df[m] / df[MINUTES_COL] * 90
    else:
        print(f"[warning] column '{m}' not found — skipped. Check the real name in the CSV.")

# 2. Percentile within position
percentile_cols = []
for m in METRICS:
    p90_col = m + PER90_SUFFIX
    if p90_col in df.columns:
        pct_col = m + "_percentile"
        df[pct_col] = df.groupby(POSITION_COL)[p90_col].rank(pct=True) * 100
        percentile_cols.append(pct_col)

# 3. Export a "wide" version ready for Tableau
TEAM_COLS = [c for c in ["team_id", "team_name", "team_short_name", "team_abbreviation"] if c in df.columns]
cols_to_keep = ["player_id", "player_name"] + TEAM_COLS + [POSITION_COL, MINUTES_COL] + \
    [m + PER90_SUFFIX for m in METRICS if m + PER90_SUFFIX in df.columns] + \
    percentile_cols

out = df[cols_to_keep].sort_values("player_name")
out.to_csv("data/players_benchmarked.csv", index=False)
print(f"Saved data/players_benchmarked.csv with {len(out)} players and columns: {list(out.columns)}")

# 4. Quick filter: Sporting KC only, for a visual sanity check in the terminal
# (adjust the right team_id once you've looked at teams.csv)
print("\nSample:")
print(out.head(10))
