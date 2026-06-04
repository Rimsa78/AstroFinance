# AstroFinance 🪐

A private tool that builds your deterministic **Vedic birth chart**, scores modern
**earning channels** against classical wealth-significations, and reality-checks
each one against **hard economics** — giving you two honest, separate scores.

## The idea in one line
**Astrology proposes. Finance disposes.** For each way of earning money, you get:

- an **ASTRO score** — does your chart *classically* favour this kind of work? (ideas + timing)
- a **REALITY score** — do the *economics* make it a smart bet? (failure rates, capital, time-to-revenue, 2026 conditions)

The two are **never merged into one number**. They're shown side by side, and when
they disagree, **the economics govern** the real decision — astrology drops to
timing/flavour. This is **not** financial advice and **not** a forecast.

## Install
```bash
pip install pyswisseph pydantic pdfplumber anthropic streamlit pytest --break-system-packages
```

## Run
```bash
# CLI (offline, deterministic)
python run.py                         # built-in sample chart
cp my_birth.example.json my_birth.json   # then edit with your details
python run.py my_birth.json --report  # writes out/report.md

# with live 2026 data + an AI-written report (needs a key)
export ANTHROPIC_API_KEY=sk-...
python run.py my_birth.json --live --report

# web UI
streamlit run app.py                  # http://localhost:8501
```

## What you get
- **Full chart**: planets (sign/degree/nakshatra/pada/house/dignity/retrograde),
  Whole-Sign houses, chara karakas, divisional charts **D1–D12**, Vimshottari dasha.
- **Yogas**: Gajakesari, Dhana, Raja, Budha-Aditya (each cited + reasoned).
- **Dual-scored earning channels** (incl. SaaS, AI business, online trading,
  consulting, real estate, fintech, …) with `why_fits` / `why_caution`.
- **Financial fundamentals** per channel (base rates: failure %, time-to-revenue,
  capital intensity, margin).

## How it's built (deterministic core, all pure functions)
```
engine/constants.py   classical reference data (lords, exaltations, nakshatras, dasha)
engine/vargas.py      divisional charts D1,D2,D3,D4,D7,D9,D10,D12 (Parashari)
engine/chart.py       compute_chart() -> ChartFact (Swiss Ephemeris, Lahiri sidereal)
kb/channels.py        earning channels + astro support/warn tags
kb/base_rates.py      static financial base rates per channel (cited)
signals.py            chart -> yogas + named signals (with reasons + citations)
scoring.py            signals x channels -> ranked ASTRO score
reality_check.py      REALITY score (base rates + live-2026 via LiveDataProvider)
reconcile.py          ASTRO + REALITY -> dual-labelled advice (never merged)
live_data.py          WebSearchLiveProvider (real 2026 fetch, cached, gated)
report.py             interpret-only report (LLM or deterministic fallback)
pipeline.py           analyze() seam shared by CLI + UI
run.py                CLI    ·    app.py    Streamlit UI
validate.py           diff engine vs an AstroSage reference chart
```

## Design principles (see `CLAUDE.md` + `DESIGN.md`)
- The **engine is the only source of chart truth**; the LLM never computes a placement.
- **Determinism stays deterministic** — chart math/signals/scoring are pure & offline-testable.
- **Every score is traceable** (the exact signals + reasons ship with it).
- **Cited astrology** — each rule carries a classical reference + school.
- **No predictions, no promises.** Not financial/investment/legal/medical advice.

## Tests
```bash
pytest -q
```

## Accuracy note
The chart engine is unit-tested and internally consistent but **should be
cross-checked against an external reference (AstroSage, Lahiri) for your own birth
data** before you rely on it. The UI's "Verify against AstroSage" panel and
`validate.py` make this easy.
