# MLS Player Benchmarking — portfolio project (Sporting KC)

**Live dashboard:** https://public.tableau.com/app/profile/bernardo.dias/viz/MLSPlayerBenchmarking/Story1
(a guided Story with 5 pages: Player Benchmark, Undervalued Players, Player Comps, Injury-Risk Monitor, Team Value)

## Setup
```bash
pip install requests pandas numpy matplotlib
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

## Phase 4 — Recruitment layer
```bash
python 04_undervalued.py
```
Generates `data/undervalued_candidates.csv`: every player ranked by
`composite_percentile` (the average of their 4 metric percentiles), flagged
with `high_profile_team` — a **manual heuristic** (not real salary/cap-hit
data, which isn't available via this free API) marking clubs with a
historically larger media/spending profile. High composite percentile +
`high_profile_team = False` = worth a scouting look, not a guaranteed
bargain. Ties in with ScoutLink/InjuryBot recruitment work.

Same idea reproduced as a Tableau leaderboard on a second dashboard tab
("Undervalued Players") in the published viz — see `TABLEAU_GUIDE.md` if
rebuilding it from scratch.

## Phase 6 — Extended data (salaries, games, team stats)
```bash
python 05_fetch_extended.py
```
Generates `data/players_salaries.csv` (real MLSPA salary release),
`data/teams_salaries.csv`, `data/teams_xgoals.csv`, `data/games.csv`, and
`data/players_xgoals_by_game.csv` (per-game player data, whole league in one
API call via `split_by_games=true`). Powers Phases 7-10.

## Phase 7 — Player comps
```bash
python 06_comps.py
```
Generates `data/player_comps.csv`: for every player, the 5 most statistically
similar players at the same position (Euclidean distance on the percentile
profile), flagged with `cheaper_alternative` using real salary data. **Known
limitation:** GK/CB comps degenerate to distance 0 for some players, since
all 4 metrics are attacking-only — see the script's docstring.

## Phase 8 — Workload / injury-risk proxy
```bash
python 07_workload.py
```
Generates `data/player_workload.csv`: ACWR (acute:chronic workload ratio,
Gabbett et al.) per player per game — a real sports-science proxy for injury
risk, not a diagnosis. **Caveat:** at full-season/league scale ~40% of rows
read "high" because return-from-a-gap events (injury, rotation, international
duty) are common across 577 players over 6+ months; meant for week-to-week
single-team monitoring, not retroactive season-wide counting.

## Phase 9 — Team spend-vs-performance
```bash
python 08_team_dashboard.py
```
Generates `data/team_value.csv`: every team's points, xpoints, and payroll,
ranked by points-per-$M. Sporting KC currently ranks 21/30 on value-for-money
and is underperforming its own xpoints — a real, unflattering-but-honest
finding worth being able to explain in an interview.

## Phase 10 — Auto-generated scouting reports (PDF)
```bash
python 09_scouting_report.py "Dejan Joveljic"
```
Generates a one-page PDF (`data/scouting_reports/<player>.pdf`) combining the
percentile profile, top comps (with cheaper-alternative callouts), and
current workload status for any player. Defaults to a demo player if no name
is given.

## Phase 11 — Publishing
- [x] Published to Tableau Public: https://public.tableau.com/app/profile/bernardo.dias/viz/MLSPlayerBenchmarking/Story1
- [x] Pushed to GitHub: https://github.com/dododdias/mls-player-benchmarking
- [x] Tableau dashboards for Phases 7-9 (comps, workload, team value) — built, bundled into the
      Story above.
- [ ] Link the Tableau Public dashboard + repo on LinkedIn and on the resume.

**Note on the published link:** as of Tableau Public 2026.2.1, `Save to Tableau
Public As...` only publishes the currently active sheet — it does not bundle
the whole workbook with tab navigation like older versions did. The fix: build
a **Story** (New Story tab) with one story point per dashboard, and publish
the Story itself. See `TABLEAU_GUIDE.md` for the full walkthrough, including
a text-overlap bug that shows up when dashboards get compressed inside a
Story frame (fixed by setting the Story's own Size to a fixed size instead of
Automatic).

## Data source
American Soccer Analysis public API: https://app.americansocceranalysis.com/api/v1/
No authentication required. Full documentation (OpenAPI):
https://app.americansocceranalysis.com/api/v1/openapi.json
