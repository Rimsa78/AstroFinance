"""End-to-end CLI.

    python run.py                       # built-in sample birth, offline
    python run.py my_birth.json         # your birth JSON, offline
    python run.py my_birth.json --live  # fetch live 2026 conditions (needs key+net)
    python run.py my_birth.json --report# also write a written report to out/report.md

Flags can combine. The DETERMINISTIC core (chart/signals/scoring/reconcile with
base rates) always runs offline. --live and --report are the only parts that may
touch the network, both gated behind ANTHROPIC_API_KEY and degrading gracefully.

Birth JSON schema (see my_birth.example.json):
    {"name","date":"YYYY-MM-DD","time":"HH:MM","lat","lon","tz":"Area/City"}
    (use "utc_offset": <hours> instead of "tz" if you only know the offset)

Outputs: out/chart.json, out/scores.json, out/advice.json, and (with --report)
out/report.md.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pipeline import analyze
from reality_check import NeutralProvider
from reconcile import DISCLAIMER

SAMPLE_BIRTH = {
    "name": "Sample",
    "date": "1992-03-21",
    "time": "06:45",
    "lat": 27.7172,
    "lon": 85.3240,
    "tz": "Asia/Kathmandu",
}


def _make_provider(use_live: bool):
    if not use_live:
        return NeutralProvider(), "offline (base rates only)"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[run] --live requested but ANTHROPIC_API_KEY is not set; "
              "falling back to base rates only.")
        return NeutralProvider(), "offline (no API key)"
    from live_data import WebSearchLiveProvider
    return WebSearchLiveProvider(), "live web search (2026)"


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    use_live = "--live" in flags
    want_report = "--report" in flags

    if args:
        birth = json.loads(Path(args[0]).read_text())
    else:
        birth = SAMPLE_BIRTH
        print("(no birth file given; using built-in sample)")

    provider, live_label = _make_provider(use_live)
    result = analyze(birth, provider=provider, with_report=want_report)
    chart, signals, scores, advice = (result.chart, result.signals,
                                       result.scores, result.advice)

    out = Path("out")
    out.mkdir(exist_ok=True)
    (out / "chart.json").write_text(chart.model_dump_json(indent=2))
    (out / "scores.json").write_text(json.dumps(
        {"signals": signals, "channels": scores}, indent=2))
    (out / "advice.json").write_text(json.dumps(
        {"disclaimer": DISCLAIMER, "advice": advice}, indent=2))

    written = ["out/chart.json", "out/scores.json", "out/advice.json"]
    if want_report:
        (out / "report.md").write_text(result.report_md)
        (out / "finance.md").write_text(result.finance_md)
        written += ["out/report.md (Jyotishi reading)", "out/finance.md (Finance Analyst)"]

    asc = chart.ascendant
    print(f"\nChart: {chart.name or '(unnamed)'} | Asc {asc.sign_name} "
          f"{asc.deg_in_sign:.1f} {asc.nakshatra} | ayanamsa {chart.ayanamsa:.3f}")
    print(f"Moon nakshatra: {chart.dasha.moon_nakshatra} | "
          f"current MD lord at birth: {chart.dasha.starting_lord} "
          f"(balance {chart.dasha.balance_years_at_birth:.2f}y)")

    print(f"\nDual reading (ASTRO | REALITY, never merged) — data: {live_label}:")
    print(f"  {'ASTRO':>5} {'REAL':>5}  {'CHANNEL':34} VERDICT")
    for e in advice[:8]:
        print(f"  {e['astro']['score']:5.1f} {e['reality']['score']:5.1f}  "
              f"{e['name']:34} {e['verdict']}")

    print("\nWrote " + ", ".join(written))
    print("\n" + DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
