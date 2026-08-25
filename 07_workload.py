"""
Phase 8 — Workload / injury-risk proxy, using ACWR (Acute:Chronic Workload
Ratio) — a real sports-science metric (Gabbett et al.), not something made up
for this project. No actual injury data exists in the free ASA API, so this
is a *proxy*: it flags players whose recent minutes load has spiked relative
to their own baseline, which the sports-science literature associates with
elevated soft-tissue injury risk. It does NOT predict injuries.

Runs after 05_fetch_extended.py. Requires: pip install pandas numpy

Method, per player:
  1. Build a daily time series of minutes played (0 on non-match days).
  2. acute_load_7d   = rolling 7-day sum of minutes (this week's load)
  3. chronic_load_28d_avg_weekly = rolling 28-day sum / 4 (average weekly
     load over the last month — the player's recent baseline)
  4. acwr = acute_load_7d / chronic_load_28d_avg_weekly

Standard interpretation bands (literature, not a hard clinical rule):
  - ACWR > 1.5              → spike risk ("danger zone")
  - 0.8 <= ACWR <= 1.3      → sweet spot
  - ACWR < 0.8 (with load)  → undertraining / returning from a dip
  - chronic load too thin (< 28 days of history) → insufficient data, not scored

CAVEAT on the numbers: run retroactively across a full season for the whole
league, a large share of rows (~40% here) land in "high". That's not a bug —
it's what you get when you score every "player returns from a multi-week gap
(injury, rotation, international duty) and plays close to a full match"
event across 577 players over 6+ months; those gap-then-return moments are
exactly what ACWR is built to catch, and they're common at league scale. In
a real deployment this tool is meant to run prospectively, week-to-week, on
one team's active roster — flagging a spike as it happens — not retroactively
counting every return-from-absence across an entire season as a single
"~40% high" statistic.

Generates:
  - data/player_workload.csv  (one row per player x game-day, with ACWR + risk_flag)
"""

import numpy as np
import pandas as pd

games = pd.read_csv("data/games.csv", parse_dates=["date_time_utc"])
by_game = pd.read_csv("data/players_xgoals_by_game.csv")
players = pd.read_csv("data/players.csv")[["player_id", "player_name"]].drop_duplicates("player_id")
teams = pd.read_csv("data/teams.csv")[["team_id", "team_name"]]

# Restrict to the same 300+ minute season population used everywhere else in
# the project. The raw per-game pull (05_fetch_extended.py) used
# minimum_minutes=1 to not miss substitute cameos when building each game's
# rolling history — but fringe players with only 1-2 appearances all season
# have no real "baseline" load, so their ACWR spikes are noise, not signal.
# A workload tool is only meaningful for players who are actually in rotation.
season_pop = pd.read_csv("data/players_benchmarked.csv")["player_id"].unique()
by_game = by_game[by_game["player_id"].isin(season_pop)]

df = by_game.merge(games[["game_id", "date_time_utc"]], on="game_id", how="left")
df = df.merge(players, on="player_id", how="left")
df = df.merge(teams, on="team_id", how="left")
df["date"] = df["date_time_utc"].dt.normalize()

MIN_HISTORY_DAYS = 28
rows = []

for player_id, g in df.groupby("player_id"):
    g = g.sort_values("date")
    if g["date"].isna().all():
        continue
    daily = g.groupby("date")["minutes_played"].sum()
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_range, fill_value=0)

    acute = daily.rolling(7, min_periods=1).sum()
    chronic = daily.rolling(28, min_periods=1).sum() / 4
    acwr = acute / chronic.replace(0, np.nan)
    days_of_history = pd.Series(range(1, len(daily) + 1), index=daily.index)

    meta = g.iloc[0]
    for game_date in g["date"].unique():
        idx = pd.Timestamp(game_date)
        has_enough_history = days_of_history.loc[idx] >= MIN_HISTORY_DAYS
        ratio = acwr.loc[idx] if has_enough_history else np.nan

        if pd.isna(ratio):
            risk_flag = "insufficient_data"
        elif ratio > 1.5:
            risk_flag = "high"
        elif ratio < 0.8:
            risk_flag = "low"
        else:
            risk_flag = "normal"

        game_rows = g[g["date"] == game_date]
        for _, r in game_rows.iterrows():
            rows.append({
                "player_id": player_id,
                "player_name": meta["player_name"],
                "team_name": meta["team_name"],
                "general_position": r["general_position"],
                "game_id": r["game_id"],
                "date": idx.date().isoformat(),
                "minutes_played": r["minutes_played"],
                "acute_load_7d": round(float(acute.loc[idx]), 1),
                "chronic_load_28d_avg_weekly": round(float(chronic.loc[idx]), 1),
                "acwr": round(float(ratio), 2) if not pd.isna(ratio) else None,
                "risk_flag": risk_flag,
            })

out = pd.DataFrame(rows)
out.to_csv("data/player_workload.csv", index=False)
print(f"Saved data/player_workload.csv with {len(out)} player-game rows.")
print(out["risk_flag"].value_counts().to_string())

high_risk = out[out["risk_flag"] == "high"].sort_values("acwr", ascending=False).head(10)
print("\nSample — most recent high-risk (spike) rows:")
print(high_risk[["player_name", "team_name", "date", "acwr", "acute_load_7d",
                  "chronic_load_28d_avg_weekly"]].to_string(index=False))
