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
from kb import knowledge as KN
from reconcile import DISCLAIMER

VARGA_ORDER = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12"]
VARGA_LABEL = {
    "D1": "D1 Rasi (body/overall)", "D2": "D2 Hora (wealth)",
    "D3": "D3 Drekkana (siblings/effort)", "D4": "D4 Chaturthamsha (property)",
    "D7": "D7 Saptamsha (progeny)", "D9": "D9 Navamsha (dharma/spouse)",
    "D10": "D10 Dashamsha (career)", "D12": "D12 Dwadashamsha (parents)",
}

DEFAULT_MODEL = os.environ.get("ASTRO_REPORT_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("ASTRO_REPORT_MAX_TOKENS", "8000"))

YOGA_KEYS = ["gajakesari_yoga", "dhana_yoga", "raja_yoga", "budhaditya_yoga"]

# The Vedic astrologer persona. It INTERPRETS the engine's computed chart; it does
# not (and must not) compute anything. The math is the engine's job (CONTRACT #1).
SYSTEM_PROMPT = (
    "You are Jyotirvid, a learned Vedic astrologer (Jyotishi) deeply read in the "
    "classical Sanskrit texts — Brihat Parashara Hora Shastra (BPHS), Phaladeepika, "
    "Saravali, Brihat Jataka, Jataka Parijata, and the Jaimini Sutras. You read "
    "charts in the sidereal (Lahiri) Parashari tradition with Whole-Sign houses, and "
    "you explain them in warm, lucid English for a thoughtful modern reader.\n\n"
    "ABSOLUTE RULES (these protect the reader and the craft):\n"
    "1. You are given a COMPUTED chart as JSON facts (ascendant, planets with sign/"
    "house/dignity/nakshatra, houses, karakas, divisional charts, yogas, Vimshottari "
    "dasha) plus a dual-scored earning analysis. Interpret ONLY those facts. NEVER "
    "invent, alter, or 'recall from memory' any placement, degree, nakshatra, dasha, "
    "yoga, or score. The calculation is already done — your work is MEANING, not "
    "computation. If a detail is not in the JSON, do not assert it.\n"
    "2. Ground every interpretation in classical principle and NAME the source or "
    "tradition (e.g. 'per BPHS on the 2nd lord', 'Phaladeepika's reading of an "
    "exalted Venus', 'Jaimini, on the Atmakaraka'). Where the texts differ, say so "
    "rather than pretending one truth.\n"
    "3. You MAY quote a relevant Sanskrit sloka with transliteration and an English "
    "translation to illustrate a principle — but clearly mark slokas as illustrative, "
    "do NOT fabricate precise chapter/verse numbers you are unsure of, and never "
    "present a sloka as proof of a specific outcome.\n"
    "4. NO fortune-telling: no specific events, dates, sums, or guaranteed results. "
    "Speak as the classics do — in tendencies, strengths, karmic themes, and dasha "
    "TIMING WINDOWS. This is a classical reading and self-knowledge aid, NOT "
    "financial, investment, legal, or medical advice, and not a forecast of returns.\n"
    "5. Two scores stay SEPARATE: ASTRO (classical favour/timing) vs REALITY "
    "(economics). When you discuss livelihood, honour that the REALITY layer governs "
    "real-world decisions while astrology gives direction, motivation, and timing. "
    "Never merge or average the two.\n"
    "6. You MAY draw on your broader classical training BEYOND the supplied knowledge "
    "block when it genuinely deepens the reading — but attribute it to a named text "
    "or tradition, keep it consistent with the engine's computed placements, and "
    "never invent placements or precise verse numbers. The `classical_knowledge` "
    "block is your primary, verified ground; your training fills the gaps WITH "
    "attribution. Respect the `predictive_notes`: do not state transit positions, "
    "sade-sati status, or Ashtakavarga numbers as fact — they are not computed.\n"
    "Write a comprehensive, well-structured markdown report with clear headings, in "
    "the manner of a thorough professional Jyotish reading."
)

# The section outline the agent is asked to cover (AstroSage-style depth).
READING_OUTLINE = (
    "Write a COMPLETE reading using the querent's actual placements from the JSON. "
    "Cover these sections, each with a markdown heading:\n"
    "1. **How to read this** — one short paragraph framing the two layers honestly.\n"
    "2. **Lagna & Lagnesha** — the ascendant sign/nakshatra and its lord's placement; "
    "the person's core nature and constitution.\n"
    "3. **The Moon & mind** — Moon's sign, house, and nakshatra; emotional nature.\n"
    "4. **The Sun & soul; Atmakaraka** — Sun's dignity/house and the chara Atmakaraka.\n"
    "5. **Graha by graha** — each of the nine grahas: its sign, house, dignity, "
    "retrograde state, and what it signifies here (classically cited).\n"
    "6. **Bhava analysis** — the houses, with emphasis on the 2nd (wealth), 10th "
    "(career/karma), 11th (gains), and 9th (fortune/dharma).\n"
    "7. **Yogas** — each yoga present in the JSON, what the texts promise from it, "
    "and how strongly it expresses given the supporting placements.\n"
    "8. **Divisional charts** — what D9 (dharma/marriage), D10 (career), and D2 "
    "(wealth) add beyond the rasi chart.\n"
    "9. **Vimshottari dasha** — the CURRENT mahadasha's themes and the next turn, as "
    "timing windows (not events).\n"
    "10. **Wealth & livelihood** — read the dual-scored earning channels through the "
    "chart: which paths BOTH the chart and the economics support, and which the chart "
    "favours but the economics caution (name them, keep the two scores separate).\n"
    "11. **Doshas & cautions** — any doshas flagged (Manglik, Kala Sarpa, Kemadruma) "
    "with the classical meaning AND the traditional cancellations/cautions, framed "
    "soberly (never as a verdict or doom).\n"
    "12. **Remedies (upaya)** — the traditional mantra/gemstone/deity/charity for the "
    "key planets, clearly framed as classical custom (not guarantees), with the "
    "gemstone caveat.\n"
    "13. **Closing** — a grounded summary and the disclaimer.\n"
    "Include a fitting Sanskrit sloka or two (marked illustrative).\n\n"
    "The JSON includes a `classical_knowledge` block: cited significations for the "
    "grahas, bhavas, the relevant nakshatras, the active yogas, and the dasha "
    "themes for THIS chart. Ground your interpretation in it and carry its citations "
    "into your prose (e.g. 'per BPHS — graha karakatva')."
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
    asc_sign_idx = chart.ascendant.sign
    lagna_lord = C.SIGN_LORD[asc_sign_idx]
    lagna_lord_pos = chart.planets.get(lagna_lord)
    return {
        "chart": {
            "name": chart.name,
            "ascendant": {"sign": chart.ascendant.sign_name,
                          "nakshatra": chart.ascendant.nakshatra,
                          "pada": chart.ascendant.pada,
                          "degree": round(chart.ascendant.deg_in_sign, 2)},
            "lagna_lord": lagna_lord,
            "lagna_lord_placement": (
                f"{lagna_lord} in {lagna_lord_pos.sign_name}, house "
                f"{lagna_lord_pos.house}, {lagna_lord_pos.dignity}"
                if lagna_lord_pos else None),
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
        "classical_knowledge": KN.knowledge_for_chart(chart, signals),
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


def build_reading_messages(chart: ChartFact, signals: dict, advice: list[dict],
                           top: int = 8) -> list[dict]:
    """The user turn: the section outline + the full computed facts."""
    facts = build_facts(chart, signals, advice, top)
    content = (READING_OUTLINE
               + "\n\nHere is the querent's computed chart and dual-scored earning "
                 "analysis as JSON facts. Read ONLY from these:\n\n"
               + json.dumps(facts, indent=2))
    return [{"role": "user", "content": content}]


def generate_report(chart: ChartFact, signals: dict, advice: list[dict],
                    client=None, model: str = DEFAULT_MODEL, top: int = 8,
                    max_tokens: int = MAX_TOKENS) -> str:
    """Full Vedic-astrologer reading via the LLM if a key/client is available,
    else the deterministic structured fallback. Interpret-only either way."""
    if client is None and not os.environ.get("ANTHROPIC_API_KEY"):
        return deterministic_report(chart, signals, advice, top)
    try:
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=SYSTEM_PROMPT,
            messages=build_reading_messages(chart, signals, advice, top),
        )
        text = "\n".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return text or deterministic_report(chart, signals, advice, top)
    except Exception as e:
        return (deterministic_report(chart, signals, advice, top)
                + f"\n\n<!-- LLM reading unavailable ({e}); deterministic fallback used. -->")
