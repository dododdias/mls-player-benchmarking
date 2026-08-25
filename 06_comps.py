"""
Phase 7 — Player comps: for every player, find the most statistically
similar players at the same position, using their percentile profile
(shots/key passes/xG/xA percentiles — same 4 metrics as the rest of the
project). Also surfaces the cheapest comp, using real salary data from
Phase 6, as a "similar player at lower cost" scouting angle.

Runs after 02_benchmark.py and 05_fetch_extended.py. Requires: pip install pandas numpy

Method: plain Euclidean distance on the 4-metric percentile vector, computed
within each general_position group only (comparing a CB's profile to a ST's
doesn't mean much even on a 0-100 scale — the metrics represent different
roles). No sklearn dependency needed for ~30-100 players per position group.

KNOWN LIMITATION: all 4 metrics (shots/key passes/xG/xA) are attacking
metrics. GKs — and some CBs — score near-zero on all of them, so their
percentile vectors are often identical and comps come back at distance 0.
That's degenerate, not a real "great match": this tool is only meaningful
for positions where attacking output differentiates players (FB, DM, CM, AM,
W, ST). Fixing it properly would mean pulling goals-added's shot-stopping
component for GKs and defensive actions for CB — out of scope for now, but
worth saying out loud rather than presenting fake-precise comps.

Generates:
  - data/player_comps.csv  (long format: one row per player x comp rank 1-5)
"""

import numpy as np
import pandas as pd

TOP_N = 5
PERCENTILE_COLS = [
    "shots_percentile", "key_passes_percentile", "xgoals_percentile", "xassists_percentile",
]

bench = pd.read_csv("data/players_benchmarked.csv")

missing = [c for c in PERCENTILE_COLS if c not in bench.columns]
if missing:
    raise SystemExit(f"Missing {missing} in players_benchmarked.csv — run 02_benchmark.py first.")

# Real salary data (Phase 6) — season-only rows, one per player.
try:
    salaries = pd.read_csv("data/players_salaries.csv")
    salaries = salaries[["player_id", "guaranteed_compensation"]].drop_duplicates("player_id")
    bench = bench.merge(salaries, on="player_id", how="left")
    have_salary = True
except FileNotFoundError:
    print("[warning] data/players_salaries.csv not found — run 05_fetch_extended.py "
          "for salary context. Continuing without it.")
    bench["guaranteed_compensation"] = pd.NA
    have_salary = False

rows = []
for position, group in bench.groupby("general_position"):
    if len(group) < 2:
        continue
    idx = group.index.to_numpy()
    X = group[PERCENTILE_COLS].to_numpy(dtype=float)
    # Pairwise Euclidean distance matrix within this position group.
    diffs = X[:, None, :] - X[None, :, :]
    dist = np.sqrt((diffs ** 2).sum(axis=-1))

    for i, player_row_idx in enumerate(idx):
        order = np.argsort(dist[i])
        order = order[order != i][:TOP_N]  # drop self, keep top N closest
        base = group.loc[player_row_idx]
        for rank, j in enumerate(order, start=1):
            comp = group.loc[idx[j]]
            rows.append({
                "player_id": base["player_id"],
                "player_name": base["player_name"],
                "general_position": position,
                "player_guaranteed_compensation": base.get("guaranteed_compensation"),
                "comp_rank": rank,
                "comp_player_id": comp["player_id"],
                "comp_player_name": comp["player_name"],
                "comp_team_name": comp["team_name"],
                "comp_guaranteed_compensation": comp.get("guaranteed_compensation"),
                "similarity_distance": round(float(dist[i, j]), 2),
            })

out = pd.DataFrame(rows)

# Cheaper-alternative flag: among a player's top-5 comps, is this one cheaper?
if have_salary:
    out["cheaper_alternative"] = (
        out["comp_guaranteed_compensation"] < out["player_guaranteed_compensation"]
    )
else:
    out["cheaper_alternative"] = pd.NA

out.to_csv("data/player_comps.csv", index=False)
print(f"Saved data/player_comps.csv with {len(out)} rows "
      f"({out['player_id'].nunique()} players x top {TOP_N} comps).")

degenerate = out[(out["similarity_distance"] == 0) & out["general_position"].isin(["GK", "CB"])] \
    if "general_position" in out.columns else out[out["similarity_distance"] == 0]
if len(degenerate):
    n_players = degenerate["player_id"].nunique()
    print(f"[warning] {n_players} GK/CB players have distance-0 comps — see the "
          f"KNOWN LIMITATION note at the top of this file. Their comps aren't meaningful.")

if have_salary:
    sample = out[out["cheaper_alternative"] == True].nsmallest(5, "similarity_distance")  # noqa: E712
    print("\nSample — closest comps that are also cheaper:")
    print(sample[["player_name", "comp_player_name", "comp_team_name",
                   "similarity_distance", "comp_guaranteed_compensation"]].to_string(index=False))
