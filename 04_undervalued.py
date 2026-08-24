"""
Phase 4 (optional) — Recruitment layer: flag high-performing players who
might be flying under the radar.

Runs after 02_benchmark.py. Requires: pip install pandas

IMPORTANT caveat: ASA's free API has no salary/cap-hit data, so this is NOT a
real "value vs. cost" analysis — it's a proxy. `high_profile_team` is a
manually curated, subjective list of MLS clubs with historically larger
media/spending presence (DP-heavy rosters, bigger markets). A player who
ranks high on `composite_percentile` AND plays for a team NOT on that list is
a reasonable "worth a scouting look" candidate — not a guaranteed bargain.
Adjust HIGH_PROFILE_TEAMS to match whatever list you actually want to defend
in an interview.

Generates:
  - data/undervalued_candidates.csv  (every player, ranked by composite_percentile)
"""

import pandas as pd

df = pd.read_csv("data/players_benchmarked.csv")

PERCENTILE_COLS = [
    "shots_percentile", "key_passes_percentile", "xgoals_percentile", "xassists_percentile",
]

# Subjective heuristic, not based on real financial data — see caveat above.
HIGH_PROFILE_TEAMS = {
    "Inter Miami CF", "LA Galaxy", "LAFC", "Atlanta United FC",
    "Seattle Sounders FC", "Toronto FC", "Lionel Messi's Inter Miami CF",
}

missing = [c for c in PERCENTILE_COLS if c not in df.columns]
if missing:
    raise SystemExit(
        f"Missing percentile columns {missing} in players_benchmarked.csv — "
        f"run 02_benchmark.py first."
    )

df["composite_percentile"] = df[PERCENTILE_COLS].mean(axis=1)
df["high_profile_team"] = df["team_name"].isin(HIGH_PROFILE_TEAMS)

cols_to_keep = [
    "player_id", "player_name", "team_name", "general_position", "minutes_played",
] + PERCENTILE_COLS + ["composite_percentile", "high_profile_team"]

out = df[cols_to_keep].sort_values("composite_percentile", ascending=False)
out.to_csv("data/undervalued_candidates.csv", index=False)

top_sleepers = out[~out["high_profile_team"]].head(10)
print(f"Saved data/undervalued_candidates.csv with {len(out)} players.")
print("\nTop 10 non-high-profile-team performers (composite percentile):")
print(top_sleepers[["player_name", "team_name", "general_position", "composite_percentile"]]
      .to_string(index=False))
