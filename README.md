# MLS Player Benchmarking — portfolio project (Sporting KC)

**Live dashboard:** https://public.tableau.com/app/profile/bernardo.dias/viz/MLSPlayerBenchmarking/Dashboard1

## Setup
```bash
pip install requests pandas
```

## Phase 1 — Collect data
```bash
python 01_fetch_data.py
```
This creates `data/teams.csv`, `data/players.csv`, `data/players_xgoals.csv`,
`data/players_xpass.csv`, `data/players_goals_added.csv`, and
`data/players_master.csv` (the join of all of them).

**After running, check the real column names:**
```bash
python -c "import pandas as pd; print(pd.read_csv('data/players_master.csv').columns.tolist())"
```
The ASA API changes its naming from time to time — adjust the `METRICS` list
at the top of `02_benchmark.py` to match whatever real names show up.

## Phase 2 — Benchmarking / percentiles
```bash
python 02_benchmark.py
```
Generates `data/players_benchmarked.csv`: every player with their per-90
metrics and their percentile within their own position (`general_position`:
GK, CB, FB, DM, CM, AM, W, ST).

## Phase 3 — Tableau Public dashboard
```bash
python 03_prep_tableau.py
```
Generates `data/players_benchmarked_long.csv` (one row per player x metric —
the right shape for the bar/lollipop chart in Tableau).

The full dashboard skeleton (parameters, calculated fields, worksheets,
parameter actions, and publishing) is in **[TABLEAU_GUIDE.md](TABLEAU_GUIDE.md)**.
Main visual: percentile bars per player, with team/position filters and a
comparison against the position average or another player. Radar chart is
documented there as a stretch goal.

## Phase 4 (optional) — Recruitment layer
Using the same `players_benchmarked.csv`, filter players with high percentiles
in offensive/defensive metrics but outside the league's "big" teams — that
becomes an "undervalued players" list, which ties in with ScoutLink/InjuryBot
recruitment work.

## Phase 5 — Publishing
- [x] Published to Tableau Public: https://public.tableau.com/app/profile/bernardo.dias/viz/MLSPlayerBenchmarking/Dashboard1
- [x] Pushed to GitHub: https://github.com/dododdias/mls-player-benchmarking
- [ ] Link the Tableau Public dashboard + repo on LinkedIn and on the resume.

## Data source
American Soccer Analysis public API: https://app.americansocceranalysis.com/api/v1/
No authentication required. Full documentation (OpenAPI):
https://app.americansocceranalysis.com/api/v1/openapi.json
