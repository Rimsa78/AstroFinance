# CLAUDE.md — AstroFinance AI

> Claude Code reads this at the start of every session. It is the source of truth
> for how to work on this project. Follow the CONTRACTS below exactly; they are
> not style preferences, they are correctness and safety requirements.

## WHY this project exists
A private tool that (1) computes a deterministic Vedic chart, (2) scores modern
earning channels against classical wealth-significations, and (3) reconciles that
"forecast" against real financial/economic "truth" to produce honest, personalized
business/wealth advice. Single-user first.

## The governing principle (read this before writing any logic)
**Astrology proposes. Finance disposes.** The two domains have different jobs and
are NEVER blended into one number:
- **Astrology layer = forecast / ideation / timing engine.** Generates directions,
  themes, motivation, "when". These are *hypotheses*.
- **Finance/economy layer = truth governor.** Reality-checks each hypothesis against
  capital, unit economics, base rates, current 2026 conditions, and risk.
When they agree → high-confidence idea. When astrology says "go" but economics say
"bad bet" → **the truth layer wins** for the real decision; astrology drops to
flavour/timing. Output always shows BOTH scores, labelled, never merged.

---

## CONTRACTS (never violate)
1. **The engine is the only source of chart truth.** `engine/chart.py` emits one
   canonical ChartFact dict. The LLM NEVER computes or "recalls" a placement, dasha,
   yoga, or score. It only interprets what it is handed. If a fact isn't in the
   input, the answer is "I don't have that," not a guess.
2. **Determinism stays deterministic.** Chart math, signals, and scoring must be
   pure functions with no network/LLM/randomness. They must be unit-testable offline.
3. **Every score is traceable.** No score ships without the exact signals + reasons
   that produced it (`why_fits` / `why_caution`). Traceability over mystique.
4. **Don't ship subtly-wrong astrology.** If a classical formula is ambiguous or
   non-uniform (e.g. D30, D60), it is better to NOT implement it than to ship a wrong
   version silently. Mark such items as not-implemented in `DESIGN.md`'s status table.
5. **Cite astrology rules.** Every astro rule carries a `classical_ref` + `school`
   tag. Texts disagree; where they conflict, surface both, don't pick a "truth".
6. **Live data is fetched at runtime, never baked into code or training.** Current
   2026 market/economy/earning-trend data comes from web search / feeds at report
   time. Static fundamentals + base rates live in the KB.
7. **No predictions, no promises.** Output is a classical reading + ideation aid, not
   a forecast of markets/returns. State this once, plainly. Never promise wealth,
   timing certainty, or figures. This is NOT financial/investment/legal/medical advice.
8. **Validate before trusting.** Any new chart feature must be checked against a
   known reference (AstroSage) for ≥2 births before downstream code relies on it.

---

## Tech stack
- Python 3.11+
- `pyswisseph` (Swiss Ephemeris, Lahiri sidereal) — chart math
- `pydantic` — validate the ChartFact contract
- `pdfplumber` — AstroSage PDF fallback parsing
- `timezonefinder` + `zoneinfo`, `geopy` (Nominatim) — place → lat/lon/historical tz
- Anthropic Python SDK (`anthropic`) — the report writer
- (later) FastAPI for endpoints, Streamlit for a private UI, SQLite for history
- Tests: `pytest`

## Commands
- Install: `pip install pyswisseph pydantic pdfplumber anthropic pytest --break-system-packages`
- Run (sample chart): `python run.py`
- Run (your chart): `python run.py my_birth.json`
- Live report: set `ANTHROPIC_API_KEY`, then `python run.py`  (report layer not built yet)
- Tests: `pytest -q`
- Validate engine vs AstroSage: `python validate.py tests/fixtures/reference.json`

## Conventions
- Sidereal Lahiri ayanamsa; **Whole-Sign** houses for rasi logic (add Chalit/bhava
  cusps as a SEPARATE field, never overwrite Whole-Sign).
- Sign index 0 = Aries. Houses 1..12. Planets include Rahu/Ketu (Rahu = mean node).
- Signals are a flat dict `{name: {"value": 0..1, "why": str}}`.
- Score formula lives in `scoring.py`; tune via `BASE`/`SUPPORT_WEIGHT`/`WARN_WEIGHT`,
  keep ordering meaningful rather than chasing absolute numbers.
- Prefer adding a new module over bloating an existing one. Keep functions small.
- When you add a rule, add a test asserting it fires on a crafted chart.

---

## Module map (current state)
```
engine/constants.py   ✅ classical reference data (lords, exaltations, nakshatras, dasha)
engine/vargas.py      ✅ D1,D2,D3,D4,D7,D9,D10,D12 (exact Parashari)
engine/chart.py       ✅ compute_chart() -> ChartFact (planets, houses, dasha, karakas)
kb/channels.py        ✅ 21 earning channels + astro support/warn tags
kb/base_rates.py      ✅ static base rates per channel (failure/ttr/capital/margin)
signals.py            ✅ chart -> yogas + named signals (with reasons)
scoring.py            ✅ signals × channels -> ranked astro_score + explanations
reality_check.py      ✅ reality_score (base rates + live-2026 via LiveDataProvider)
reconcile.py          ✅ astro_score + reality_score -> DUAL-labelled advice
live_data.py          ✅ WebSearchLiveProvider (real 2026 fetch via Claude+web_search, cached, gated)
report.py             ✅ interpret-only report; LLM if ANTHROPIC_API_KEY else deterministic fallback
pdf_parser.py         ⛔ NOT built (AstroSage fallback)
run.py                ✅ end-to-end CLI; flags --live (fetch 2026) / --report (write out/report.md)
pipeline.py           ✅ analyze() seam shared by CLI + UI
app.py                ✅ Streamlit UI (streamlit run app.py -> localhost:8501)
validate.py           ✅ diff engine vs AstroSage reference (awaiting fixture)
tests/                ✅ dignity, dasha balance, vargas, yoga detection (Phase A)
DESIGN.md             ✅ full architecture + implemented-vs-spec status table
```

## Task backlog (work top-down; do ONE phase per session, with tests)
- [x] **Phase A — Tests & validation harness.** `tests/` asserts exalted/debil
      dignity, Vimshottari balance math, varga placements, and yoga detection on
      crafted charts. `validate.py` diffs the engine vs a saved AstroSage reference
      and reports mismatches (needs `tests/fixtures/reference.json`).
- [x] **Phase B — Reality-check engine.** `reality_check.py` computes a
      `reality_score` per channel from (a) base rates in `kb/base_rates.py`
      (failure rates, time-to-revenue, capital realism, margin) and (b) a live
      2026 layer behind the `LiveDataProvider` interface (NeutralProvider offline
      default; MockLiveDataProvider for tests; web fetcher left as a documented
      seam). `reconcile.py` produces DUAL-labelled advice (two scores, never
      merged); reality governs verdicts on conflict. Wired into `run.py` ->
      out/advice.json. A real `LiveDataProvider` (web search) is still TODO.
- [ ] **Phase C — Corpus ingestion schema.** `kb/rules/` as cited YAML rules
      (`id, description, classical_ref, school, when (DSL), signals, tags`) + a ~150-
      line DSL evaluator exposing `lord_of/house_of/dignity/strength/in_kendra`.
      Migrate the Python-predicate rules in `signals.py` into cited YAML incrementally.
- [ ] **Phase D — Input robustness.** Geocoding + historical timezone resolution so
      input is "Kathmandu, 1992-03-21 06:45" not raw coordinates.
- [ ] **Phase E — Ashtakavarga (SAV/BAV) + Chalit.** Classical benefic tables
      (deterministic). Feed 2nd/11th SAV into new wealth signals.
- [ ] **Phase F — Shadbala (v2).** Replace the transparent `strength_proxy`; re-tune.
- [~] **Phase G — UI + persistence.** ✅ Streamlit form + dual-score report view
      (`app.py`, via `pipeline.analyze()`). STILL TODO: SQLite history, "what
      changes next dasha" view, chart comparison.

## When starting a session
1. Read `DESIGN.md` for full context.
2. Run `python run.py` to confirm the pipeline is green before changing anything.
3. Pick the top unchecked backlog item. Propose a short plan, then implement with tests.
4. Never break a CONTRACT to make a feature work — flag the tension instead.
