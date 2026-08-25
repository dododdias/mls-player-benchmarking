"""
Phase 6 — Extended data collection: salaries, games, team-level stats, and
per-game player data. Powers Phases 7-10 (comps, workload/injury-risk proxy,
team spend-vs-performance dashboard, auto scouting reports).

Runs after 01_fetch_data.py. Requires: pip install requests pandas

Saves to ./data/:
  - players_salaries.csv       (real MLSPA salary release — base + guaranteed comp)
  - teams_salaries.csv         (team payroll aggregates)
  - teams_xgoals.csv           (team-level attacking/defensive xG)
  - games.csv                  (fixture list with date_time_utc, matchday, teams)
  - players_xgoals_by_game.csv (same as players/xgoals but one row per player
                                 per game — needed for the workload/ACWR calc)

NOTE: salary data comes from the MLSPA's public salary release
(`mlspa_release` field marks which release each row is from) — it's real
compensation data, not a heuristic like the old `high_profile_team` flag in
04_undervalued.py.
"""

import time
import requests
import pandas as pd

BASE = "https://app.americansocceranalysis.com/api/v1/mls"
SEASON = "2026"
HEADERS = {"User-Agent": "bernardo-dias-portfolio-project/1.0"}


def get(endpoint: str, params: dict) -> pd.DataFrame:
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return pd.DataFrame(data)


def main():
    import os
    os.makedirs("data", exist_ok=True)

    print("Fetching player salaries (MLSPA public release)...")
    salaries = get("players/salaries", {"season_name": SEASON})
    salaries.to_csv("data/players_salaries.csv", index=False)
    print(f"  {len(salaries)} salary rows saved.")

    time.sleep(1)

    print("Fetching team salaries (payroll aggregates)...")
    team_salaries = get("teams/salaries", {"season_name": SEASON, "split_by_teams": "true"})
    team_salaries.to_csv("data/teams_salaries.csv", index=False)
    print(f"  {len(team_salaries)} teams saved.")

    time.sleep(1)

    print("Fetching team-level xG (attacking/defensive output)...")
    teams_xgoals = get("teams/xgoals", {"season_name": SEASON})
    teams_xgoals.to_csv("data/teams_xgoals.csv", index=False)
    print(f"  {len(teams_xgoals)} teams saved.")

    time.sleep(1)

    print("Fetching games (fixture list, for chronological ordering)...")
    games = get("games", {"season_name": SEASON})
    games.to_csv("data/games.csv", index=False)
    print(f"  {len(games)} games saved.")

    time.sleep(1)

    print("Fetching per-game player xG (whole league, one call)...")
    by_game = get("players/xgoals", {
        "season_name": SEASON,
        "split_by_games": "true",
        "minimum_minutes": 1,  # keep every appearance, even substitute cameos
    })
    by_game.to_csv("data/players_xgoals_by_game.csv", index=False)
    print(f"  {len(by_game)} player-game rows saved "
          f"({by_game['player_id'].nunique()} players, {by_game['game_id'].nunique()} games).")

    print("\nDone with Phase 6 extended fetch.")


if __name__ == "__main__":
    main()
