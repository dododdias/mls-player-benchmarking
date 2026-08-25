# Tableau Public dashboard skeleton (Phases 3 & 4)

Prerequisite: run `01_fetch_data.py` → `02_benchmark.py` → `03_prep_tableau.py`.
That generates `data/players_benchmarked_long.csv`, which is the data source
for this dashboard (one row per **player x metric**, with `percentile` already
computed).

Main dashboard = **percentile bars/lollipop chart** (full skeleton below).
Radar chart is documented at the end as a stretch goal for later.

---

## 1. Connect the data source

1. Tableau Public → **Connect to Data** → Text File → `data/players_benchmarked_long.csv`.
2. Check the field types: `percentile` and `value_p90` as **Number (decimal)**,
   `minutes_played` as **Number (whole)**, everything else as **String**.
3. Tableau auto-splits the column names nicely already (`Player Name`,
   `Team Name`, `Metric Label`, etc.) — no manual renaming needed.

## 2. Parameters

Create these under **Data pane → dropdown → Create Parameter**:

| Name | Type | Detail |
|---|---|---|
| `pSelectPlayer` | String | Allowable values: **List**, populated from `Player Name` (Add from Field). Initial value: any Sporting KC player. |
| `pCompareMode` | String | Allowable values: **List**, two manual entries: `"Position Average"`, `"Another Player"`. Default: `"Position Average"`. |
| `pComparePlayer` | String | Same as `pSelectPlayer` (list of players) — only used when `pCompareMode = "Another Player"`. |

## 3. Calculated fields

```
// Is Selected Player  (bool)
[Player Name] = [pSelectPlayer]

// Is Compare Player  (bool) — used later to highlight the compare player in the list
[Player Name] = [pComparePlayer] AND [pCompareMode] = "Another Player"

// Position Avg Percentile   (LOD — position average per metric)
{ FIXED [General Position], [Metric Label] : AVG([Percentile]) }

// Reference Value  (what becomes the "background bar" for comparison)
IF [pCompareMode] = "Another Player"
THEN { FIXED [Metric Label] : MAX(IF [Player Name] = [pComparePlayer] THEN [Percentile] END) }
ELSE [Position Avg Percentile]
END
```

> Note: don't use `WINDOW_MAX` here — mixing a table calculation with the
> `Position Avg Percentile` LOD inside the same IF throws "Cannot mix
> aggregate and non-aggregate comparisons or results in 'IF' expressions".
> Keeping both branches as LOD expressions (as above) avoids that entirely.

## 4. Worksheet A — "Player List" (to drive the parameter via click)

This exists to solve a real Tableau limitation: **a parameter doesn't filter
itself**. Without this worksheet, switching players means typing the name
into the parameter by hand — it works, but it's not what you want in an
interview demo.

1. New worksheet. Rows: `Team Name`, `General Position`, `Player Name`. Marks: Text/Automatic.
2. Drag `Team Name` and `General Position` onto the **Filters** shelf → on both, "Show Filter"
   (they become quick filters on the dashboard).
3. This becomes a clickable list: filter by team/position, click a player →
   (wired to the parameter on the dashboard, step 6).

> **Gotcha:** if you drag any other numeric field onto this worksheet (e.g.
> `Minutes Played`), Tableau defaults to **SUM** aggregation. Since the data
> source is long-format (4 rows per player — one per metric), a plain SUM
> multiplies the value by the number of metrics (4x too high). Fix: change
> the pill's aggregation to **Average** or **Minimum** instead (the value is
> identical across a player's 4 rows, so either works).

## 5. Worksheet B — "Benchmark Bars" (the main chart)

1. New worksheet. **Filter the data source by `[Is Selected Player] = TRUE`**
   (drag the calculated field onto the Filters shelf, value `True`).
2. Rows: `Metric Label` (use `Metric Order` under Sort → manual/field, otherwise
   it sorts alphabetically and mixes up shots/xG/xA).
3. Columns: `Percentile`. Marks: **Bar**.
4. Fix the X axis at 0–100 (right-click the axis → Edit Axis → Fixed: 0 to 100)
   — without this Tableau auto-scales and bars aren't comparable across screens.
5. Add a second reference mark: duplicate `Percentile` on a second axis
   (Analytics pane → drag "Reference Line" onto the pane, Value = `Reference
   Value` calculated field, Scope = per cell). This draws the "position
   average" (or other-player) mark behind each bar.
6. Bar color: `Is Selected Player` (always True here, but keep the encoding
   ready — useful if you later drop the filter and want to overlay everyone).
7. Tooltip: include `Player Name`, `Metric Label`, `Value P90` formatted to 2
   decimals, `Percentile` formatted as "68th percentile", `Minutes Played`.

## 6. Build the Dashboard

1. **New Dashboard** → drag Worksheet A (list) into a narrow column on the
   left, Worksheet B (bars) taking up the rest on the right.
2. Title: something like *"MLS Player Benchmark — {selected player}"* (use a
   dynamic title field with `<Parameters.pSelectPlayer>`).
3. **Parameter Action** (Dashboard menu → Actions → Add Action → Change
   Parameter): Source sheet = Worksheet A, Target parameter = `pSelectPlayer`,
   Field = `Player Name`, Run action on = **Select**. Now clicking a name in
   the list changes the player shown in the chart.
4. Add a second `pComparePlayer` selector: a loose parameter control on the
   dashboard (Objects → add another parameter control) + `pCompareMode` as a
   dropdown, to toggle "vs position" / "vs another player" live.
5. `Team Name` and `General Position` quick filters (inherited from Worksheet A)
   already filter the clickable list — exactly what the original Phase 3 plan asked for.

## 7. Publish

Server menu → **Save to Tableau Public As...** → title something like
*"MLS Player Benchmarking — Sporting KC"*. The public link that gets
generated is what goes in the README, LinkedIn, and resume (Phase 5).

> **Gotcha (Tableau Public 2026.2.1):** the "Save to Tableau Public As..."
> dialog in this version is a simplified title-only prompt — it only
> publishes the **currently active sheet**, not the whole workbook with tab
> navigation like older Tableau versions did. If your workbook has multiple
> dashboards, this dialog will silently publish just one of them. See
> **section 11 (Story)** below for the actual fix once you've built more than
> one dashboard.

---

## 8. Phase 4 — "Undervalued Players" leaderboard (second dashboard tab)

Reuses the same `players_benchmarked_long.csv` data source already connected
— no new data source needed. Adds two calculated fields and one worksheet.

### Calculated fields

```
// Composite Percentile   (LOD — average of a player's 4 metric percentiles)
{ FIXED [Player Name] : AVG([Percentile]) }

// High Profile Team   (manual heuristic, NOT real salary/cap-hit data)
[Team Name] = "Inter Miami CF" OR
[Team Name] = "LA Galaxy" OR
[Team Name] = "LAFC" OR
[Team Name] = "Atlanta United FC" OR
[Team Name] = "Seattle Sounders FC" OR
[Team Name] = "Toronto FC"
```

### Worksheet — "Undervalued Players"

1. New worksheet. Filter: drag `Composite Percentile` onto **Filters** →
   choose aggregation **Average** (same long-format gotcha as everywhere
   else) → **At least** → `85` (top ~5% of the league; adjust to taste).
2. Rows: `Player Name`. Columns: `Composite Percentile` — again set its
   aggregation to **Average**, not the default Sum (4x bug otherwise).
3. Sort `Player Name` by field → `Composite Percentile`, Average, Descending.
4. Color: `High Profile Team`. Rename the legend items (right-click legend →
   Edit Alias): `True` → `Big-market club`, `False` → `Under the radar`.
5. Tooltip: `Team Name`, `General Position`, `Minutes Played` (Average
   aggregation again).
6. Rename the axis title (double-click it) to something like
   `Composite Percentile (avg of 4 metrics)`.

### Dashboard

New Dashboard tab ("Undervalued Players") → drag the worksheet in, enable
the title, and add a **Text** object (Objects panel) with a caveat, e.g.:
*"High-profile team" is a manual heuristic based on media/spending profile —
not real salary or cap-hit data (unavailable via this API). Treat this as a
starting point for scouting, not a definitive value ranking.*

Then **Server → Save to Tableau Public As...** with the same file name to
overwrite the published viz — both dashboard tabs go live under the same URL.

---

## 9. Phase 7 — "Player Comps" leaderboard

New data source: **Data → New Data Source... → Text File → `player_comps.csv`**
(different grain than the other CSVs — one row per player x comp rank — so it
gets its own connection, not a join).

Calculated field (in this new data source):
```
// Is Selected Player
[Player Name] = [pSelectPlayer]
```
(Workbook-level parameters like `pSelectPlayer` are visible from every data
source in the workbook, so this reuses the same parameter Dashboard 1 uses.)

Worksheet:
1. Filter by `Is Selected Player` = True.
2. Rows: `Comp Rank` — drag it on, then explicitly set it to **Discrete**
   (blue pill), not the default Continuous (green). Continuous here plots
   rank as a second numeric axis and produces a scatter/bar hybrid instead of
   one row per rank.
3. Also drag `Comp Player Name` and `Comp Team Name` onto Rows, after
   `Comp Rank` — as row headers, not as floating bar-end labels (labels
   positioned at the end of a bar collide when two bars are close in length).
4. Columns: `Similarity Distance`. Marks: Bar.
5. Color: `Cheaper Alternative`.
6. Tooltip: `Comp Player Name`, `Comp Team Name`, `Comp Guaranteed Compensation`.
7. Dashboard: drag the worksheet in, **Show Parameter** on `pSelectPlayer` so
   this tab works standalone without switching back to Dashboard 1.

## 10. Phase 8 — "Injury-Risk Monitor" (ACWR over time)

New data source: `player_workload.csv`.

1. Same `Is Selected Player` calculated field / filter pattern as above.
2. Columns: `Date` — when dragged on, Tableau defaults to `YEAR(Date)`
   (discrete, one point per year). Click the pill's dropdown → **More** →
   **Exact Date**, and confirm it's **Continuous** (green), not Discrete —
   otherwise the whole season collapses into a single aggregated point.
3. Rows: `ACWR`. Marks: Line. Color: `Risk Flag`.
4. Analytics pane → drag two **Constant Line** references onto the chart:
   `1.5` and `0.8` (the sports-science interpretation bands from
   `07_workload.py`).
5. Tooltip: `Team Name`, `General Position`, `Minutes Played`,
   `Acute Load 7d`, `Chronic Load 28d Avg Weekly`, `Risk Flag`.
6. Dashboard: Size = Automatic (not the default small responsive preset —
   same fix as Dashboard 1), Show Parameter on `pSelectPlayer`.

## 11. Phase 9 — "Team Value" leaderboard

New data source: `team_value.csv` (team-level, no `pSelectPlayer` needed).

1. Rows: `Team Name`. Columns: `Points Per Million`. Marks: Bar.
2. Sort `Team Name` by field → `Value Rank`, Minimum, Ascending.
3. Color: `Is Skc` → rename the legend items (right-click legend → Edit
   Alias) to `Sporting KC` / `Rest of league`.
4. Dashboard: drag the worksheet in, add a **Text** caveat below it
   explaining the metric is real MLSPA salary data, not a proxy.

> **Gotcha:** a Text object dropped onto a Tiled dashboard claims its whole
> grid zone, which can look like a huge empty box around a short caption.
> Fix by dragging the zone's border to shrink it — **not** by switching the
> object to Floating. Floating positions the text at fixed pixel coordinates,
> which do not scale consistently when Tableau Public renders the dashboard
> in a browser at a different aspect ratio than Desktop — the text ends up
> overlapping the chart on the published page even though it looks fine
> locally. This bit us once; Tiled + border-drag is the safe way.

## 12. Bundling multiple dashboards into one link — the Story fix

As noted in section 7, Tableau Public 2026.2.1's "Save to Tableau Public
As..." only publishes the current sheet. To ship all five dashboards
(Player Benchmark, Undervalued Players, Player Comps, Injury-Risk Monitor,
Team Value) under one shareable URL:

1. Bottom toolbar → **New Story** (third icon, after New Worksheet / New
   Dashboard).
2. Left panel → **Size** → set a **fixed size** (e.g. Generic Desktop,
   1600x1200) instead of Automatic. A Story embeds each dashboard inside its
   own frame; Automatic sizing left too little room in testing and caused
   caption text near the bottom of a few dashboards to get clipped by the
   chart's own axis labels. A fixed, generous size avoided it.
3. For each dashboard: **New story point → Blank**, drag the dashboard onto
   the point, and type a short caption in the title field at the top (e.g.
   "Player Benchmark", "Team Value").
4. Rename the Story tab to the workbook's title (e.g. `MLS Player
   Benchmarking`).
5. **Server → Save to Tableau Public As...** with the **Story tab active**.
   The published page now shows a navigable strip with all five points —
   this is what goes in the README / LinkedIn / resume, not a link to any
   single dashboard.

---

## Stretch goal — Radar chart

Not native in Tableau; the standard technique is **path-based data
densification**:

1. You need one row per (player, metric, polygon point) — i.e. the same long
   table we have today, but with each metric converted to a polar coordinate
   (`x = percentile * cos(angle)`, `y = percentile * sin(angle)`,
   `angle = metric_order / total_metrics * 2π`), and the **first metric
   duplicated at the end** to close the polygon.
2. This usually becomes a separate Python script (`04_prep_radar.py`) that
   reads `players_benchmarked_long.csv`, computes `x`/`y` per row, and
   duplicates each player's first metric with `metric_order = N` (closing the
   circle).
3. In Tableau: Columns = `x`, Rows = `y`, Marks = **Line**, Path = `Metric
   Order`, one polygon per player (Detail = `Player Name`). Overlay two
   polygons (selected player vs. position average) with dual-axis + synchronize.
4. It's more fragile to maintain (any new metric requires recalculating the
   angles) — that's why it's left out of the main skeleton. If you want, I'll
   write `04_prep_radar.py` once the rest is published and there's time left
   before the interview.
