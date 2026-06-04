"""Static base rates per earning channel — the offline half of the truth governor.

These are STATIC FUNDAMENTALS + BASE RATES (CONTRACT #6): they belong in the KB,
not fetched live. The live 2026 layer (demand, saturation) is separate and comes
through reality_check.LiveDataProvider at runtime.

Each channel id MUST match kb/channels.py. Fields:
  failure_rate_5yr   : P(venture fails / fails to sustain) within ~5 years, 0..1
  time_to_revenue_mo : realistic months to first meaningful revenue
  capital_intensity  : 0 (bootstrappable) .. 1 (capital-heavy)
  margin_potential   : 0 (thin) .. 1 (high-margin) at maturity
  capital_note       : short human note on capital realism

Sources (general, well-established base rates — not channel-specific promises):
  - BLS Business Employment Dynamics: ~20% of new US establishments fail in
    year 1, ~50% by year 5, ~65% by year 10. Used as the cross-channel anchor.
  - Restaurant/hospitality survival studies: notably worse than the BLS average
    (~60% gone within 3 years, ~80% within 5) — H. G. Parsa et al.
  - Startup/SaaS attrition (CB Insights startup post-mortems): high multi-year
    failure for venture-style software bets.
  - Creator-economy monetization reports: a small minority of creators reach
    sustaining income — high "fail to monetize" rate for content/affiliate.
These are rounded, defensible estimates for RANKING realism, not forecasts.
NOT financial advice (CONTRACT #7).
"""

from __future__ import annotations

# id -> base-rate record
BASE_RATES: dict[str, dict] = {
    "saas":          dict(failure_rate_5yr=0.80, time_to_revenue_mo=9,  capital_intensity=0.40, margin_potential=0.85, capital_note="bootstrappable but long runway to PMF"),
    "consulting":    dict(failure_rate_5yr=0.40, time_to_revenue_mo=2,  capital_intensity=0.10, margin_potential=0.70, capital_note="low overhead; income = your time"),
    "content":       dict(failure_rate_5yr=0.75, time_to_revenue_mo=12, capital_intensity=0.20, margin_potential=0.60, capital_note="cheap to start, most never monetize"),
    "ecommerce":     dict(failure_rate_5yr=0.80, time_to_revenue_mo=4,  capital_intensity=0.45, margin_potential=0.45, capital_note="inventory/ads burn capital fast"),
    "realestate":    dict(failure_rate_5yr=0.35, time_to_revenue_mo=6,  capital_intensity=0.95, margin_potential=0.55, capital_note="asset-backed but very capital-heavy"),
    "equity":        dict(failure_rate_5yr=0.30, time_to_revenue_mo=60, capital_intensity=0.60, margin_potential=0.50, capital_note="long horizon; loss risk if undiversified"),
    "crypto":        dict(failure_rate_5yr=0.85, time_to_revenue_mo=1,  capital_intensity=0.40, margin_potential=0.50, capital_note="high variance; treat as speculation"),
    "teaching":      dict(failure_rate_5yr=0.60, time_to_revenue_mo=6,  capital_intensity=0.15, margin_potential=0.70, capital_note="low capital; needs audience/credibility"),
    "advisory":      dict(failure_rate_5yr=0.35, time_to_revenue_mo=3,  capital_intensity=0.15, margin_potential=0.70, capital_note="credential-gated, sticky clients"),
    "healthcare":    dict(failure_rate_5yr=0.40, time_to_revenue_mo=12, capital_intensity=0.60, margin_potential=0.60, capital_note="licensing + equipment upfront"),
    "hospitality":   dict(failure_rate_5yr=0.70, time_to_revenue_mo=6,  capital_intensity=0.80, margin_potential=0.35, capital_note="high fixed costs; thin margins"),
    "creative":      dict(failure_rate_5yr=0.55, time_to_revenue_mo=4,  capital_intensity=0.20, margin_potential=0.55, capital_note="low capital; demand is lumpy"),
    "engineering":   dict(failure_rate_5yr=0.50, time_to_revenue_mo=18, capital_intensity=0.85, margin_potential=0.50, capital_note="tooling/plant capital, long cycle"),
    "agritech":      dict(failure_rate_5yr=0.55, time_to_revenue_mo=18, capital_intensity=0.80, margin_potential=0.45, capital_note="land/inputs heavy, seasonal"),
    "trading_import":dict(failure_rate_5yr=0.60, time_to_revenue_mo=6,  capital_intensity=0.70, margin_potential=0.40, capital_note="working capital + FX/logistics risk"),
    "legal":         dict(failure_rate_5yr=0.30, time_to_revenue_mo=6,  capital_intensity=0.20, margin_potential=0.70, capital_note="credential-gated, durable demand"),
    "govcontract":   dict(failure_rate_5yr=0.40, time_to_revenue_mo=12, capital_intensity=0.40, margin_potential=0.55, capital_note="long sales cycle, compliance heavy"),
    "media":         dict(failure_rate_5yr=0.65, time_to_revenue_mo=12, capital_intensity=0.30, margin_potential=0.45, capital_note="attention-dependent, ad-cyclical"),
    "logistics":     dict(failure_rate_5yr=0.50, time_to_revenue_mo=9,  capital_intensity=0.75, margin_potential=0.35, capital_note="fleet/space capital, thin margins"),
    "research_niche":dict(failure_rate_5yr=0.60, time_to_revenue_mo=18, capital_intensity=0.40, margin_potential=0.55, capital_note="slow, grant/niche dependent"),
    "affiliate":     dict(failure_rate_5yr=0.75, time_to_revenue_mo=9,  capital_intensity=0.10, margin_potential=0.65, capital_note="cheap; most never reach scale"),

    # --- modern / digital-first channels ---
    # ai_business: huge demand but crowded + fast-moving; talent/compute costs.
    "ai_business":    dict(failure_rate_5yr=0.75, time_to_revenue_mo=9,  capital_intensity=0.40, margin_potential=0.75, capital_note="talent/compute heavy, fast-moving, crowded"),
    # online_trading: retail-trader studies (e.g. Barber & Odean; regulator
    # disclosures) consistently show the large majority lose money over time.
    "online_trading": dict(failure_rate_5yr=0.85, time_to_revenue_mo=1,  capital_intensity=0.50, margin_potential=0.50, capital_note="most retail traders lose money; treat as speculation"),
    "digital_marketing": dict(failure_rate_5yr=0.55, time_to_revenue_mo=3, capital_intensity=0.15, margin_potential=0.60, capital_note="low capital, very crowded, results-driven"),
    "app_dev":        dict(failure_rate_5yr=0.60, time_to_revenue_mo=6,  capital_intensity=0.30, margin_potential=0.60, capital_note="build cost low, discovery/retention hard"),
    "fintech":        dict(failure_rate_5yr=0.70, time_to_revenue_mo=18, capital_intensity=0.70, margin_potential=0.60, capital_note="regulation + capital heavy, long runway"),
    "data_analytics": dict(failure_rate_5yr=0.45, time_to_revenue_mo=6,  capital_intensity=0.20, margin_potential=0.65, capital_note="skills-gated, steady enterprise demand"),

    # --- more ways of making money ---
    "digital_products": dict(failure_rate_5yr=0.65, time_to_revenue_mo=4,  capital_intensity=0.10, margin_potential=0.80, capital_note="near-zero marginal cost; distribution is the hard part"),
    "paid_community":   dict(failure_rate_5yr=0.60, time_to_revenue_mo=5,  capital_intensity=0.10, margin_potential=0.70, capital_note="cheap to start; churn/retention is the battle"),
    "marketplace":      dict(failure_rate_5yr=0.80, time_to_revenue_mo=12, capital_intensity=0.50, margin_potential=0.60, capital_note="chicken-and-egg liquidity; winner-take-most"),
    # dividend income: low 'failure' but needs sizable principal; income scales with capital.
    "dividend_income":  dict(failure_rate_5yr=0.25, time_to_revenue_mo=36, capital_intensity=0.70, margin_potential=0.50, capital_note="needs real capital; yield is modest and slow"),
    "short_term_rental":dict(failure_rate_5yr=0.50, time_to_revenue_mo=4,  capital_intensity=0.60, margin_potential=0.40, capital_note="property cost + regulation + seasonality"),
    "local_services":   dict(failure_rate_5yr=0.40, time_to_revenue_mo=2,  capital_intensity=0.25, margin_potential=0.45, capital_note="steady demand; capped by your time/crew"),
    "licensing_ip":     dict(failure_rate_5yr=0.70, time_to_revenue_mo=18, capital_intensity=0.20, margin_potential=0.85, capital_note="high margin if it hits; most IP earns little (power-law)"),
    "franchise":        dict(failure_rate_5yr=0.35, time_to_revenue_mo=9,  capital_intensity=0.85, margin_potential=0.30, capital_note="proven system but heavy upfront + ongoing royalties"),
}

# Cross-channel anchor (BLS): ~50% of new ventures fail within 5 years.
ANCHOR_FAILURE_5YR = 0.50


def get(channel_id: str) -> dict:
    return BASE_RATES[channel_id]
