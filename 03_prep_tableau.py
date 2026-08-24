"""
Phase 3 (prep) — Reshape players_benchmarked.csv into the format Tableau
wants for the bar/lollipop dashboard.

Runs after 02_benchmark.py. Requires: pip install pandas

Why long format? Each worksheet in Tableau becomes "one row per metric" (so
you can do Rows = metric_label, Columns = percentile and get a bar chart with
one bar per metric, like a scouting report). In wide format (one column per
metric) that requires a bunch of repeated calculated fields; in long format
it's a single Rows/Columns setup.

Generates:
  - data/players_benchmarked_long.csv  (one row per player x metric)

This is the CSV you connect to in Tableau Public for Phase 3 — see
TABLEAU_GUIDE.md.
"""

import pandas as pd

df = pd.read_csv("data/players_benchmarked.csv")

POSITION_COL = "general_position"

# Same mapping as 02_benchmark.py — keep the two in sync if you add/remove metrics.
METRICS = ["shots", "key_passes", "xgoals", "xassists"]
METRIC_LABELS = {
    "shots": "Shots",
    "key_passes": "Key Passes",
    "xgoals": "xG",
    "xassists": "xA",
}
# Display order on the Tableau axis (Rows) — without this it sorts alphabetically
METRIC_ORDER = {m: i for i, m in enumerate(METRICS)}

id_cols = [c for c in [
    "player_id", "player_name", "team_id", "team_name", "team_short_name",
    "team_abbreviation", POSITION_COL, "minutes_played",
] if c in df.columns]

rows = []
for m in METRICS:
    p90_col = f"{m}_p90"
    pct_col = f"{m}_percentile"
    if p90_col not in df.columns or pct_col not in df.columns:
        print(f"[warning] '{m}' not found in players_benchmarked.csv — skipped. "
              f"Re-run 02_benchmark.py if you changed METRICS.")
        continue
    chunk = df[id_cols + [p90_col, pct_col]].copy()
    chunk = chunk.rename(columns={p90_col: "value_p90", pct_col: "percentile"})
    chunk["metric"] = m
    chunk["metric_label"] = METRIC_LABELS.get(m, m)
    chunk["metric_order"] = METRIC_ORDER[m]
    rows.append(chunk)

long_df = pd.concat(rows, ignore_index=True)
long_df = long_df.sort_values(["player_name", "metric_order"])
long_df.to_csv("data/players_benchmarked_long.csv", index=False)
print(f"Saved data/players_benchmarked_long.csv with {len(long_df)} rows "
      f"({df['player_name'].nunique()} players x {len(rows)} metrics).")
