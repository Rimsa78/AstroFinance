"""The human-facing report. INTERPRET-ONLY (CONTRACT #1).

The LLM never computes or recalls a placement, dasha, yoga, or score — it only
narrates the ChartFact + signals + reconciled advice it is handed. If a fact is
not in the input, the correct answer is "I don't have that," not a guess.

Two paths:
  - generate_report(): uses the Anthropic SDK if ANTHROPIC_API_KEY is set;
  - deterministic_report(): a pure, offline markdown report used as the fallback
    (and fully unit-testable). The tool is usable with or without a key.

Both keep ASTRO and REALITY scores separate and never merged (governing
principle), and both carry the no-advice disclaimer (CONTRACT #7).
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Optional

from engine.chart import ChartFact
from engine import constants as C
from kb import base_rates as BR
from reconcile import DISCLAIMER

VARGA_ORDER = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12"]
VARGA_LABEL = {
    "D1": "D1 Rasi (body/overall)", "D2": "D2 Hora (wealth)",
    "D3": "D3 Drekkana (siblings/effort)", "D4": "D4 Chaturthamsha (property)",
    "D7": "D7 Saptamsha (progeny)", "D9": "D9 Navamsha (dharma/spouse)",
    "D10": "D10 Dashamsha (career)", "D12": "D12 Dwadashamsha (parents)",
}

DEFAULT_MODEL = os.environ.get("ASTRO_REPORT_MODEL", "claude-sonnet-4-6")

YOGA_KEYS = ["gajakesari_yoga", "dhana_yoga", "raja_yoga", "budhaditya_yoga"]

SYSTEM_PROMPT = (
    "You are an interpreter for a Vedic-astrology + finance tool. You are handed a "
    "JSON bundle of FACTS: a computed chart, named signals, and dual-scored advice "
    "per earning channel. Rules you must obey:\n"
    "1. Interpret ONLY the facts provided. NEVER compute, recall, or invent any "
    "placement, dasha, yoga, degree, or score. If something is not in the JSON, say "
    "you don't have it.\n"
    "2. Keep the two scores SEPARATE. ASTRO is a classical ideation/timing signal; "
    "REALITY is an economics base-rate + 2026 check. Never merge them into one "
    "number or average them. When they conflict, the REALITY layer governs the real "
    "decision and astrology is timing/flavour only.\n"
    "3. No predictions, no promises, no figures, no timing certainty. This is not "
    "financial, investment, legal, or medical advice.\n"
    "4. Be concrete and cite the signals/reasons already present in the JSON.\n"
    "Write a clear, friendly markdown report."
)


def _current_mahadasha(chart: ChartFact, today: Optional[str] = None) -> Optional[dict]:
    today = today or date.today().isoformat()
    for md in chart.dasha.mahadashas:
        if md.start <= today < md.end:
            return {"lord": md.lord, "start": md.start, "end": md.end}
    return None


def _notable_dignities(chart: ChartFact) -> list[str]:
    out = []
    for name, p in chart.planets.items():
        if p.dignity in ("exalted", "debilitated", "moolatrikona", "own"):
            out.append(f"{name} {p.dignity} in {p.sign_name}")
    return out


def _active_yogas(signals: dict[str, dict]) -> list[tuple[str, str]]:
    out = []
    for k in YOGA_KEYS:
        s = signals.get(k)
        if s and s["value"] >= 1.0:
            out.append((k.replace("_", " ").title(), s["why"]))
    return out


def planet_rows(chart: ChartFact) -> list[dict]:
    """Full planet table: sign, degree, nakshatra+pada, house, dignity, retro."""
    return [{"Planet": n, "Sign": p.sign_name, "Deg": round(p.deg_in_sign, 2),
             "Nakshatra": p.nakshatra, "Pada": p.pada, "House": p.house,
             "Dignity": p.dignity, "Retro": "R" if p.retrograde else ""}
            for n, p in chart.planets.items()]


def varga_rows(chart: ChartFact) -> list[dict]:
    """Divisional chart positions: each planet's sign across D1..D12."""
    rows = []
    for n, p in chart.planets.items():
        row = {"Planet": n}
        for v in VARGA_ORDER:
            row[v] = C.SIGNS[p.vargas[v]]
        rows.append(row)
    return rows


def karaka_rows(chart: ChartFact) -> list[dict]:
    """All chara karakas (soul significators), highest degree first."""
    return [{"Karaka": k, "Planet": v} for k, v in chart.karakas.items()]


def house_rows(chart: ChartFact) -> list[dict]:
    """Whole-sign houses: sign, lord, and occupying planets."""
    rows = []
    for h in range(1, 13):
        sign_idx = chart.houses_whole_sign[h]
        occ = [n for n, p in chart.planets.items() if p.house == h]
        rows.append({"House": h, "Sign": C.SIGNS[sign_idx],
                     "Lord": C.SIGN_LORD[sign_idx], "Occupants": ", ".join(occ) or "—"})
    return rows


def dasha_rows(chart: ChartFact) -> list[dict]:
    return [{"Lord": md.lord, "Start": md.start, "End": md.end,
             "Years": round(md.years, 1)} for md in chart.dasha.mahadashas]


def financial_rows(advice: list[dict]) -> list[dict]:
    """Per-channel financial fundamentals (base rates) aligned to the advice order."""
    rows = []
    for e in advice:
        rec = BR.BASE_RATES.get(e["id"])
        if not rec:
            continue
        rows.append({
            "Channel": e["name"],
            "5-yr failure": f"{round(rec['failure_rate_5yr']*100)}%",
            "Time to revenue": f"{rec['time_to_revenue_mo']} mo",
            "Capital intensity": f"{round(rec['capital_intensity']*100)}%",
            "Margin potential": f"{round(rec['margin_potential']*100)}%",
            "REALITY": e["reality"]["score"],
            "Capital note": rec["capital_note"],
        })
    return rows


def _md_table(rows: list[dict], cols: list[str]) -> list[str]:
    if not rows:
        return ["_(none)_"]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return out


def build_facts(chart: ChartFact, signals: dict, advice: list[dict], top: int = 8) -> dict:
    """Compact, interpret-only fact bundle for the LLM (no raw ephemeris noise)."""
    return {
        "chart": {
            "name": chart.name,
            "ascendant": {"sign": chart.ascendant.sign_name,
                          "nakshatra": chart.ascendant.nakshatra},
            "moon_nakshatra": chart.dasha.moon_nakshatra,
            "atmakaraka": chart.karakas.get("Atmakaraka"),
            "current_mahadasha": _current_mahadasha(chart),
            "upcoming_mahadashas": [md.model_dump() for md in chart.dasha.mahadashas[:4]],
            "notable_dignities": _notable_dignities(chart),
            "active_yogas": _active_yogas(signals),
            "planets": planet_rows(chart),
            "houses": house_rows(chart),
            "karakas": karaka_rows(chart),
            "divisional_charts": varga_rows(chart),
        },
        "advice_top": advice[:top],
        "rules": {
            "two_scores_never_merged": True,
            "reality_governs_on_conflict": True,
            "not_financial_advice": True,
        },
    }


def deterministic_report(chart: ChartFact, signals: dict, advice: list[dict],
                         top: int = 8) -> str:
    a = chart.ascendant
    cur = _current_mahadasha(chart)
    lines = [
        f"# AstroFinance reading — {chart.name or 'your chart'}",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Chart snapshot",
        f"- **Ascendant:** {a.sign_name} ({a.nakshatra}), {a.deg_in_sign:.1f}°",
        f"- **Moon nakshatra:** {chart.dasha.moon_nakshatra}",
        f"- **Atmakaraka (soul significator):** {chart.karakas.get('Atmakaraka', '—')}",
        f"- **Current mahadasha:** "
        + (f"{cur['lord']} ({cur['start']} → {cur['end']})" if cur
           else f"begins with {chart.dasha.starting_lord} at birth"),
    ]

    dignities = _notable_dignities(chart)
    if dignities:
        lines += ["", "## Notable planetary dignities", *(f"- {d}" for d in dignities)]

    yogas = _active_yogas(signals)
    lines += ["", "## Active yogas"]
    lines += [f"- **{n}** — {why}" for n, why in yogas] if yogas else ["- none detected"]

    # --- Full Vedic detail ---
    lines += ["", "## Planetary positions", ""]
    lines += _md_table(planet_rows(chart),
                       ["Planet", "Sign", "Deg", "Nakshatra", "Pada", "House", "Dignity", "Retro"])

    lines += ["", "## Houses (Whole-Sign)", ""]
    lines += _md_table(house_rows(chart), ["House", "Sign", "Lord", "Occupants"])

    lines += ["", "## Chara karakas (Jaimini, 7-karaka)", ""]
    lines += _md_table(karaka_rows(chart), ["Karaka", "Planet"])

    lines += ["", "## Divisional charts (sign of each planet)", ""]
    lines += _md_table(varga_rows(chart), ["Planet"] + VARGA_ORDER)
    lines += ["", "_" + " · ".join(VARGA_LABEL[v] for v in VARGA_ORDER) + "_"]

    lines += ["", "## Earning channels — DUAL reading (ASTRO and REALITY, never merged)"]
    live_used = any(e["reality"].get("live_data_used") for e in advice)
    lines.append(f"_Live 2026 data used: {'yes' if live_used else 'no (base rates only)'}._")
    lines.append("")
    for e in advice[:top]:
        astr, real = e["astro"], e["reality"]
        lines.append(f"### {e['name']} — **{e['verdict']}**")
        lines.append(f"- ASTRO **{astr['score']}** ({astr['label']}) | "
                     f"REALITY **{real['score']}** ({real['label']})")
        lines.append(f"- {e['rationale']}")
        fits = [d["signal"] for d in astr["why_fits"]]
        if fits:
            lines.append(f"- astro supports: {', '.join(fits)}")
        if real["why_viable"]:
            lines.append(f"- reality for: {'; '.join(real['why_viable'][:3])}")
        if real["why_risky"]:
            lines.append(f"- reality against: {'; '.join(real['why_risky'][:3])}")
        lines.append("")

    lines += ["", "## Financial fundamentals (base rates, ranked by REALITY)", ""]
    lines += _md_table(financial_rows(advice[:top]),
                       ["Channel", "REALITY", "5-yr failure", "Time to revenue",
                        "Capital intensity", "Margin potential", "Capital note"])

    lines += ["", "## Dasha timeline (Vimshottari)",
              *(f"- {md.lord}: {md.start} → {md.end}" for md in chart.dasha.mahadashas[:6])]
    lines += ["", "---", f"_{DISCLAIMER}_"]
    return "\n".join(lines)


def generate_report(chart: ChartFact, signals: dict, advice: list[dict],
                    client=None, model: str = DEFAULT_MODEL, top: int = 8) -> str:
    """LLM report if a key/client is available, else the deterministic fallback."""
    if client is None and not os.environ.get("ANTHROPIC_API_KEY"):
        return deterministic_report(chart, signals, advice, top)
    try:
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        facts = build_facts(chart, signals, advice, top)
        msg = client.messages.create(
            model=model, max_tokens=2000, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content":
                       "Here are the facts. Write the report.\n\n"
                       + json.dumps(facts, indent=2)}],
        )
        text = "\n".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return text or deterministic_report(chart, signals, advice, top)
    except Exception as e:
        return (deterministic_report(chart, signals, advice, top)
                + f"\n\n<!-- LLM report unavailable ({e}); deterministic fallback used. -->")
