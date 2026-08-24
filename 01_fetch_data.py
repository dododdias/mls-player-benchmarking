"""
Phase 1 — MLS data collection via the American Soccer Analysis public API.

Runs locally (outside this environment). Requires: pip install requests pandas

Saves 5 CSVs to ./data/:
  - teams.csv
  - players.csv            (player_id -> player_name, birth date, nationality, etc.)
  - players_xgoals.csv     (xG, xA, shots, key passes per player/season)
  - players_xpass.csv      (xPass / passing quality)
  - players_goals_added.csv (aggregated g+, "above replacement")

Then merges everything into a single players_master.csv keyed on player_id.

NOTE: as of the 2026 season, the API stopped returning `player_name` on the
stats endpoints (xgoals/xpass/goals-added) — only `player_id`. Names now only
come from the /players endpoint (full roster, no season_name filter — passing
season_name there returns a 500 error). That's why we fetch /players
separately and merge it in.
"""

import time
import requests
import pandas as pd

BASE = "https://app.americansocceranalysis.com/api/v1/mls"
SEASON = "2026"  # adjust to whichever season you want to analyze
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

    print("Fetching teams...")
    teams = get("teams", {})
    teams.to_csv("data/teams.csv", index=False)
    print(f"  {len(teams)} teams saved.")

    # Find Sporting KC's team_id for quick reference (doesn't filter, just prints)
    skc_row = teams[teams.apply(lambda r: "Kansas City" in str(r.get("team_name", "")), axis=1)]
    if not skc_row.empty:
        print(f"  Sporting KC team_id: {skc_row.iloc[0]['team_id']}")

    time.sleep(1)

    print("Fetching full roster (player_id -> player_name)...")
    # No season_name here: passing it makes this endpoint return a 500.
    players = get("players", {})
    players.to_csv("data/players.csv", index=False)
    print(f"  {len(players)} players saved.")

    time.sleep(1)

    print("Fetching player xG (whole league, current season)...")
    xg = get("players/xgoals", {
        "season_name": SEASON,
        "minimum_minutes": 300,  # cuts out very small samples
    })
    xg.to_csv("data/players_xgoals.csv", index=False)
    print(f"  {len(xg)} rows saved.")

    time.sleep(1)

    print("Fetching player xPass...")
    xp = get("players/xpass", {
        "season_name": SEASON,
        "minimum_minutes": 300,
    })
    xp.to_csv("data/players_xpass.csv", index=False)
    print(f"  {len(xp)} rows saved.")

    time.sleep(1)

    print("Fetching player goals-added (g+)...")
    ga = get("players/goals-added", {
        "season_name": SEASON,
        "minimum_minutes": 300,
        "above_replacement": "true",
    })
    ga.to_csv("data/players_goals_added.csv", index=False)
    print(f"  {len(ga)} rows saved.")

    # --- Merge everything into a master keyed on player_id ---
    print("Merging into players_master.csv...")

    # A player who got traded mid-season comes back with team_id as a LIST
    # (e.g. ['old_team', 'new_team']) straight from the API's JSON. For the
    # Tableau team filter we need a single value: we use the most recent team
    # (last item in the list) and keep the full history in a separate column.
    def split_team_id(v):
        if isinstance(v, list):
            return pd.Series({
                "team_id": v[-1] if v else None,
                "team_id_history": ", ".join(v),
                "traded_mid_season": len(v) > 1,
            })
        return pd.Series({
            "team_id": v,
            "team_id_history": v,
            "traded_mid_season": False,
        })

    team_split = xg["team_id"].apply(split_team_id)
    n_traded = int(team_split["traded_mid_season"].sum())
    if n_traded:
        print(f"  [info] {n_traded} players were traded mid-season — using their "
              f"most recent team for the filter (see team_id_history).")
    xg = xg.drop(columns=["team_id"]).join(team_split)

    # team_id stays in (needed for the Tableau team filter, Phase 3)
    xg_cols = xg.drop(columns=[c for c in ["season_name"] if c in xg.columns])
    xp_cols = xp.drop(columns=[c for c in ["team_id", "season_name", "player_name", "general_position", "minutes_played"] if c in xp.columns])
    ga_cols = ga.drop(columns=[c for c in ["team_id", "season_name", "player_name", "general_position", "minutes_played"] if c in ga.columns])

    master = xg_cols.merge(xp_cols, on="player_id", how="left", suffixes=("", "_xpass"))
    master = master.merge(ga_cols, on="player_id", how="left", suffixes=("", "_gplus"))

    # player_name no longer comes back on the stats endpoints — pull it from the roster (/players)
    names = players[["player_id", "player_name"]].drop_duplicates(subset="player_id")
    master = names.merge(master, on="player_id", how="right")

    # team name (team_id -> team_name), for the dashboard's team filter
    team_names = teams[["team_id", "team_name", "team_short_name", "team_abbreviation"]]
    master = master.merge(team_names, on="team_id", how="left")

    master.to_csv("data/players_master.csv", index=False)
    print(f"Done: data/players_master.csv with {len(master)} players.")
    missing_names = master["player_name"].isna().sum()
    if missing_names:
        print(f"  [warning] {missing_names} players missing player_name (not found in /players).")
    missing_teams = master["team_name"].isna().sum()
    if missing_teams:
        print(f"  [warning] {missing_teams} players missing team_name (team_id not found in teams.csv).")


if __name__ == "__main__":
    main()
