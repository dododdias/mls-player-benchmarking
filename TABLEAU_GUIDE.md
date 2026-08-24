# Phase 3 — Tableau Public dashboard skeleton

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
