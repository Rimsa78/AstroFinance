"""Private Streamlit UI for AstroFinance (backlog Phase G).

Run it:
    streamlit run app.py
then open http://localhost:8501 (or the box's LAN IP) in your browser.

Thin view over pipeline.analyze() + report.py presentation helpers; all logic
lives in the tested modules. Deterministic chart/scoring runs offline. The "live
2026 data" toggle and LLM report only activate with ANTHROPIC_API_KEY and degrade
gracefully. Two scores are always shown separately, never merged.
"""

from __future__ import annotations

import json
import os

import streamlit as st

from pipeline import analyze
from reality_check import NeutralProvider
from reconcile import DISCLAIMER
from report import (planet_rows, varga_rows, karaka_rows, house_rows, dasha_rows,
                    financial_rows, VARGA_LABEL, VARGA_ORDER)

st.set_page_config(page_title="AstroFinance", page_icon="🪐", layout="wide")

VERDICT_COLOR = {
    "AGREE_PURSUE": "🟢", "REALITY_SOUND": "🔵", "WATCH": "🟡",
    "NEUTRAL": "⚪", "ASTRO_ONLY_TIMING": "🟠", "AVOID": "🔴",
}

st.title("🪐 AstroFinance")
st.caption("Your birth chart → two separate scores per earning path: **ASTRO** "
           "(does your chart classically favour it?) and **REALITY** (do the "
           "economics make it a smart bet?). Never merged; economics govern.")

has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

# --- Birth input form -------------------------------------------------------
with st.sidebar:
    st.header("Birth details")
    with st.form("birth"):
        name = st.text_input("Name", "Me")
        date = st.text_input("Date (YYYY-MM-DD)", "1998-05-19")
        time = st.text_input("Time (24h HH:MM, local at birthplace)", "16:10")
        lat = st.number_input("Latitude (°N+)", value=27.7172, format="%.4f")
        lon = st.number_input("Longitude (°E+)", value=85.3240, format="%.4f")
        tz = st.text_input("Timezone (IANA, e.g. Asia/Kathmandu)", "Asia/Kathmandu")
        use_live = st.checkbox("Use live 2026 data (needs API key)", value=False,
                               disabled=not has_key)
        want_report = st.checkbox("Write a narrative report", value=True)
        submitted = st.form_submit_button("Generate", type="primary")
    if not has_key:
        st.info("ANTHROPIC_API_KEY not set → live data + LLM report disabled; "
                "deterministic outputs still work fully.")


def _provider(use_live: bool):
    if use_live and has_key:
        from live_data import WebSearchLiveProvider
        return WebSearchLiveProvider(), True
    return NeutralProvider(), False


if not submitted:
    st.info("Enter birth details in the sidebar and press **Generate**.")
    st.stop()

# --- Run pipeline -----------------------------------------------------------
birth = {"name": name, "date": date, "time": time, "lat": lat, "lon": lon, "tz": tz}
try:
    provider, _ = _provider(use_live)
    with st.spinner("Computing chart and reconciling…"):
        result = analyze(birth, provider=provider, with_report=want_report)
except Exception as e:
    st.error(f"Could not compute chart: {e}")
    st.stop()

chart, advice = result.chart, result.advice
a = chart.ascendant

# --- Header metrics ---------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ascendant", a.sign_name, a.nakshatra)
c2.metric("Moon nakshatra", chart.dasha.moon_nakshatra)
c3.metric("Atmakaraka", chart.karakas.get("Atmakaraka", "—"))
c4.metric("Birth mahadasha", chart.dasha.starting_lord,
          f"{chart.dasha.balance_years_at_birth:.1f}y balance")
live_used = any(e["reality"].get("live_data_used") for e in advice)
st.caption(f"Lahiri ayanamsa {chart.ayanamsa:.3f}° · Whole-Sign houses · "
           f"live 2026 data: {'yes' if live_used else 'no (base rates only)'}")

tab_channels, tab_chart, tab_report = st.tabs(
    ["📊 Earning channels", "🪐 Chart & Vedic detail", "📝 Narrative report"])

# =============================== CHANNELS ===================================
with tab_channels:
    st.subheader("ASTRO vs REALITY (never merged)")
    st.dataframe(
        [{"Channel": e["name"],
          "Verdict": f"{VERDICT_COLOR.get(e['verdict'],'')} {e['verdict']}",
          "ASTRO": e["astro"]["score"], "astro label": e["astro"]["label"],
          "REALITY": e["reality"]["score"], "reality label": e["reality"]["label"]}
         for e in advice],
        use_container_width=True, hide_index=True)

    st.subheader("Financial fundamentals (base rates)")
    st.dataframe(financial_rows(advice), use_container_width=True, hide_index=True)

    st.subheader("Why — per channel")
    for e in advice[:12]:
        with st.expander(f"{VERDICT_COLOR.get(e['verdict'],'')} {e['name']} — {e['verdict']}"):
            st.write(e["rationale"])
            col_a, col_r = st.columns(2)
            with col_a:
                st.markdown(f"**ASTRO {e['astro']['score']}** ({e['astro']['label']})")
                for d in e["astro"]["why_fits"]:
                    st.markdown(f"- ✅ `{d['signal']}` — {d['why']}")
                for d in e["astro"]["why_caution"]:
                    st.markdown(f"- ⚠️ `{d['signal']}` — {d['why']}")
            with col_r:
                st.markdown(f"**REALITY {e['reality']['score']}** ({e['reality']['label']})")
                for w in e["reality"]["why_viable"]:
                    st.markdown(f"- ✅ {w}")
                for w in e["reality"]["why_risky"]:
                    st.markdown(f"- ⚠️ {w}")

# ============================= CHART DETAIL =================================
with tab_chart:
    st.subheader("Planetary positions")
    st.dataframe(planet_rows(chart), use_container_width=True, hide_index=True)

    cc1, cc2 = st.columns(2)
    with cc1:
        st.subheader("Houses (Whole-Sign)")
        st.dataframe(house_rows(chart), use_container_width=True, hide_index=True)
    with cc2:
        st.subheader("Chara karakas (Jaimini)")
        st.dataframe(karaka_rows(chart), use_container_width=True, hide_index=True)

    st.subheader("Divisional charts (varga) — sign of each planet")
    st.dataframe(varga_rows(chart), use_container_width=True, hide_index=True)
    st.caption(" · ".join(VARGA_LABEL[v] for v in VARGA_ORDER))

    st.subheader("Vimshottari dasha timeline")
    st.dataframe(dasha_rows(chart), use_container_width=True, hide_index=True)

    with st.expander("Verify against AstroSage (CONTRACT #8) — ascendant + planets"):
        st.json({"ascendant": {"sign": a.sign_name, "nakshatra": a.nakshatra,
                               "deg": round(a.deg_in_sign, 2)},
                 "planets": {n: {"sign": p.sign_name, "nakshatra": p.nakshatra,
                                 "deg": round(p.deg_in_sign, 2)}
                             for n, p in chart.planets.items()}})

# =============================== REPORT =====================================
with tab_report:
    if not has_key:
        st.warning("**This is the structured fallback, not the full reading.** "
                   "The complete *Vedic astrologer (Jyotishi)* reading — Lagna, "
                   "graha-by-graha, bhavas, yogas, divisional charts, dasha timing, "
                   "wealth/career, remedies, with classical citations & slokas — is "
                   "written by the LLM agent and needs `ANTHROPIC_API_KEY` set. "
                   "Set the key, restart the app, and re-Generate.")
    if result.report_md:
        st.markdown(result.report_md)
    else:
        st.info("Enable 'Write a narrative report' in the sidebar to generate one.")

# --- Downloads --------------------------------------------------------------
st.divider()
d1, d2, d3 = st.columns(3)
d1.download_button("⬇ chart.json", chart.model_dump_json(indent=2), "chart.json")
d2.download_button("⬇ advice.json",
                   json.dumps({"disclaimer": DISCLAIMER, "advice": advice}, indent=2),
                   "advice.json")
if result.report_md:
    d3.download_button("⬇ report.md", result.report_md, "report.md")
st.caption(DISCLAIMER)
