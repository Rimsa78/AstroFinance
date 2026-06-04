# DESIGN.md — AstroFinance AI architecture

This is the architecture + honest implemented-vs-spec status. Read it with
CLAUDE.md (which holds the governing principle and the CONTRACTS this design
must never violate).

## The two layers (never blended)
```
   BIRTH DATA
       │
       ▼
 ┌──────────────────────────────────────────┐
 │ ASTROLOGY LAYER  (forecast / ideation)    │
 │  engine/  -> ChartFact (the only truth)   │
 │  signals  -> yogas + named signals        │
 │  scoring  -> astro_score per channel      │   ← hypotheses, timing, themes
 └──────────────────────────────────────────┘
       │  astro_score (labelled, never merged)
       ▼
 ┌──────────────────────────────────────────┐
 │ FINANCE/ECONOMY LAYER  (truth governor)   │   ← Phase B ✅ (live fetcher TODO)
 │  kb/base_rates + live-2026 (interface)    │
 │  reality_check -> reality_score           │
 │  reconcile -> DUAL-labelled advice        │
 └──────────────────────────────────────────┘
       │
       ▼
 report.py  (interpret-only LLM)  ← NOT BUILT YET (out of scope this session)
```
**Astrology proposes. Finance disposes.** Two numbers, always. See CLAUDE.md.

## Data flow (deterministic core, all pure functions)
1. `BirthInput` → `engine.chart.compute_chart()` → `ChartFact`
   (Swiss Ephemeris **Moshier mode**, Lahiri sidereal, Whole-Sign houses).
2. `ChartFact` → `signals.compute_signals()` → `{name: {value, why, classical_ref, school}}`.
3. signals → `scoring.score_all()` → ranked `astro_score` per channel with
   `why_fits` / `why_caution`.

## Key engineering choices
- **Ephemeris = Moshier** (`swe.FLG_MOSEPH`): no external ephemeris data files,
  so the core is fully offline and unit-testable (CONTRACT #2). Accuracy is
  arc-second-class for the modern era — adequate for sign/nakshatra/dignity.
- **Whole-Sign** is the house truth for rasi logic. Placidus cusps are stored
  **separately** in `ChartFact.chalit_cusps` and never overwrite Whole-Sign
  (per CLAUDE.md convention).
- **Rahu = mean node**, Ketu = Rahu+180, both flagged retrograde by convention.
- **Strength is an explicit proxy** (dignity + bhava placement), labelled as such
  in every signal `why`. True Shadbala is Phase F.
- **Dasha date projection** uses 365.2425 days/year (documented in chart.py).

## Status table (implemented vs spec)
| Area | Module | Status | Notes |
|---|---|---|---|
| Classical constants | `engine/constants.py` | ✅ | lords, exalt deg, moolatrikona (text-variant flagged), nakshatras, Vimshottari |
| Vargas D1,D2,D3,D4,D7,D9,D10,D12 | `engine/vargas.py` | ✅ | exact Parashari |
| Vargas D30, D60 | — | ⛔ not implemented | non-uniform across texts (CONTRACT #4) |
| Chart compute | `engine/chart.py` | ✅ | planets, dignity, houses, dasha, karakas, chalit cusps |
| Chara karakas | `engine/chart.py` | ✅ | 7-karaka scheme (nodes excluded to avoid text-variant) |
| Earning channels | `kb/channels.py` | ✅ | 21 channels, support/warn tags |
| Signals + yogas | `signals.py` | ✅ | Gajakesari, Dhana, Raja, Budha-Aditya + graha/bhava/caution signals |
| Astro scoring | `scoring.py` | ✅ | BASE/SUPPORT_WEIGHT/WARN_WEIGHT, fully traceable |
| CLI | `run.py` | ✅ | deterministic; writes out/chart.json, out/scores.json |
| Tests | `tests/` | ✅ | dignity, dasha balance, vargas, yoga detection |
| Engine vs AstroSage validation | `validate.py` | ⚠️ tool ready, **awaiting fixture** | needs `tests/fixtures/reference.json` (CONTRACT #8 not yet closed) |
| Shadbala (real strength) | — | ⛔ Phase F | current strength is a transparent proxy |
| Ashtakavarga / Chalit signals | — | ⛔ Phase E | Placidus cusps stored but not yet used in signals |
| Base rates (static) | `kb/base_rates.py` | ✅ | failure/ttr/capital/margin per channel, cited |
| Reality-check engine | `reality_check.py` | ✅ | base rates + live-2026 via LiveDataProvider; offline default |
| Live 2026 data fetcher | `live_data.py` | ✅ | `WebSearchLiveProvider` (Claude + web_search), daily disk cache, gated + graceful |
| Reconciliation (dual score) | `reconcile.py` | ✅ | two labelled scores, never merged; reality governs verdicts |
| LLM report | `report.py` | ✅ | interpret-only; LLM behind ANTHROPIC_API_KEY, deterministic markdown fallback |
| PDF fallback | `pdf_parser.py` | ⛔ not started | AstroSage PDF parse |
| Geocoding / historical tz | — | ⛔ Phase D | currently needs explicit lat/lon + tz/utc_offset |
| UI (Streamlit) | `app.py` + `pipeline.py` | ✅ | birth form + dual-score report at localhost:8501 |
| Persistence / history / comparison | — | ⛔ Phase G remainder | SQLite history, next-dasha view, chart compare |

## Validation status (CONTRACT #8)
The engine is **internally consistent and unit-tested**, but **not yet validated
against an external reference**. To close CONTRACT #8, drop an AstroSage export at
`tests/fixtures/reference.json` (schema in `validate.py`) for ≥2 births and run
`python validate.py tests/fixtures/reference.json`. Until then, treat placements
as engine-truth pending external confirmation.

## Text-variant decisions (surfaced, not hidden — CONTRACT #5)
- **Moolatrikona ranges**: common BPHS values used; some texts differ (e.g. Moon
  3°–30° vs 4°–30° in Taurus).
- **Gajakesari**: measured **from the Moon**; some schools measure from Lagna.
  Both noted in the signal's `school` field.
- **Chara karakas**: 7-karaka scheme (Rahu excluded). The 8-karaka scheme with a
  reversed-degree Rahu is a deliberate omission to avoid a text-variant.
