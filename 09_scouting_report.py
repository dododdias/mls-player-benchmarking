"""
Phase 10 — Auto-generated one-page scouting report (PDF), combining
everything from Phases 2, 6, 7: percentile profile, salary context, and top
comps (with a cheaper-alternative callout if one exists).

Runs after 02_benchmark.py, 05_fetch_extended.py, and 06_comps.py.
Requires: pip install pandas matplotlib

Usage:
    python 09_scouting_report.py "Dejan Joveljic"
    python 09_scouting_report.py                      # defaults to a demo player

Generates:
    data/scouting_reports/<player_name>.pdf
"""

import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

METRICS = ["shots", "key_passes", "xgoals", "xassists"]
METRIC_LABELS = {"shots": "Shots", "key_passes": "Key Passes", "xgoals": "xG", "xassists": "xA"}


def load_data():
    bench = pd.read_csv("data/players_benchmarked.csv")
    comps = pd.read_csv("data/player_comps.csv") if os.path.exists("data/player_comps.csv") else None
    workload = pd.read_csv("data/player_workload.csv") if os.path.exists("data/player_workload.csv") else None
    return bench, comps, workload


def format_money(x):
    if pd.isna(x):
        return "n/a"
    return f"${x:,.0f}"


def build_report(player_name: str, bench: pd.DataFrame, comps: pd.DataFrame, workload: pd.DataFrame):
    row = bench[bench["player_name"] == player_name]
    if row.empty:
        matches = bench[bench["player_name"].str.contains(player_name, case=False, na=False)]
        suggestion = f" Did you mean: {', '.join(matches['player_name'].head(5))}?" if len(matches) else ""
        raise SystemExit(f"Player '{player_name}' not found in players_benchmarked.csv.{suggestion}")
    p = row.iloc[0]

    fig = plt.figure(figsize=(8.5, 8.2))
    gs = fig.add_gridspec(4, 1, height_ratios=[0.7, 1.7, 1.7, 1.1], hspace=0.35,
                           top=0.94, bottom=0.05, left=0.09, right=0.96)

    # --- Header ---
    ax_head = fig.add_subplot(gs[0])
    ax_head.axis("off")
    salary_line = ""
    if "guaranteed_compensation" in p and not pd.isna(p.get("guaranteed_compensation")):
        salary_line = f"  |  {format_money(p['guaranteed_compensation'])} guaranteed comp"
    ax_head.text(0, 1.0, p["player_name"], fontsize=22, fontweight="bold", va="top")
    ax_head.text(0, 0.55,
                 f"{p['team_name']}  |  {p['general_position']}  |  "
                 f"{p['minutes_played']:.0f} min played{salary_line}",
                 fontsize=11, va="top", color="#333333")

    # --- Percentile bars ---
    ax_bars = fig.add_subplot(gs[1])
    labels = [METRIC_LABELS[m] for m in METRICS]
    values = [p[f"{m}_percentile"] for m in METRICS]
    bars = ax_bars.barh(labels, values, color="#2b6cb0")
    ax_bars.set_xlim(0, 100)
    ax_bars.axvline(50, color="#999999", linestyle="--", linewidth=1)
    ax_bars.set_title(f"Positional percentile ({p['general_position']})", fontsize=12, loc="left")
    ax_bars.invert_yaxis()
    for bar, v in zip(bars, values):
        ax_bars.text(min(v + 2, 96), bar.get_y() + bar.get_height() / 2, f"{v:.0f}",
                     va="center", fontsize=10)

    # --- Comps ---
    ax_comps = fig.add_subplot(gs[2])
    ax_comps.axis("off")
    ax_comps.text(0, 1.0, "Statistical comps (same position)", fontsize=12, fontweight="bold", va="top")
    if comps is not None:
        player_comps = comps[comps["player_name"] == player_name].sort_values("comp_rank").head(5)
        if p["general_position"] in ("GK", "CB"):
            ax_comps.text(0, 0.82, "Note: comps for GK/CB aren't meaningful with attacking-only "
                                    "metrics (see 06_comps.py). Shown for reference only.",
                          fontsize=8.5, style="italic", color="#a33", va="top", wrap=True)
        y = 0.62
        for _, c in player_comps.iterrows():
            cheap_tag = "  (cheaper)" if c.get("cheaper_alternative") is True else ""
            line = (f"{int(c['comp_rank'])}. {c['comp_player_name']} ({c['comp_team_name']}) "
                    f"— dist {c['similarity_distance']:.1f}{cheap_tag}")
            ax_comps.text(0, y, line, fontsize=10, va="top")
            y -= 0.16
    else:
        ax_comps.text(0, 0.8, "Run 06_comps.py to populate this section.", fontsize=10, style="italic")

    # --- Workload status ---
    ax_wl = fig.add_subplot(gs[3])
    ax_wl.axis("off")
    ax_wl.text(0, 1.0, "Recent workload status", fontsize=12, fontweight="bold", va="top")
    if workload is not None:
        wl = workload[workload["player_name"] == player_name].sort_values("date")
        if len(wl):
            latest = wl.iloc[-1]
            flag_color = {"high": "#c53030", "low": "#3182ce", "normal": "#2f855a",
                          "insufficient_data": "#718096"}.get(latest["risk_flag"], "#000000")
            ax_wl.text(0, 0.78,
                       f"Last match: {latest['date']}  |  ACWR: {latest['acwr']}  |  "
                       f"status: {latest['risk_flag'].upper()}",
                       fontsize=10.5, va="top", color=flag_color, fontweight="bold")
            ax_wl.text(0, 0.55,
                       textwrap.fill("ACWR = acute (7-day) load / chronic (28-day avg weekly) load. "
                                     ">1.5 = spike risk, 0.8-1.3 = sweet spot. Proxy metric, not a "
                                     "diagnosis — see 07_workload.py.", 95),
                       fontsize=8, color="#555555", va="top")
        else:
            ax_wl.text(0, 0.78, "No workload history for this player.", fontsize=10, style="italic")
    else:
        ax_wl.text(0, 0.78, "Run 07_workload.py to populate this section.", fontsize=10, style="italic")

    fig.suptitle("MLS Scouting Report", fontsize=10, color="#888888", x=0.02, y=0.985, ha="left")
    return fig


def main():
    bench, comps, workload = load_data()
    player_name = sys.argv[1] if len(sys.argv) > 1 else "Dejan Joveljic"

    fig = build_report(player_name, bench, comps, workload)

    os.makedirs("data/scouting_reports", exist_ok=True)
    safe_name = player_name.replace(" ", "_").replace("/", "-")
    out_path = f"data/scouting_reports/{safe_name}.pdf"
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
