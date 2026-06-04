"""Cited finance/economics corpus — the grounding for the REALITY layer.

This is the finance twin of kb/knowledge.py. It holds STATIC, slow-moving
fundamentals and structural context (CONTRACT #6: static fundamentals live in the
KB; *live* 2026 specifics are fetched at runtime by live_data.py, never baked in).

Honesty rules:
  - Principles are established business/economics fundamentals, attributed to a
    source TYPE (e.g. "standard SaaS unit-economics", "BLS BDM"), not invented stats.
  - MACRO_CONTEXT is DURABLE structural themes (review periodically), explicitly
    NOT live market data. Anything time-sensitive must come from the live fetcher.
  - Nothing here promises returns (CONTRACT #7).
"""

from __future__ import annotations

# --- General fundamentals every path is judged against ----------------------
GENERAL_PRINCIPLES = {
    "unit_economics": dict(note="A durable business needs LTV comfortably above CAC (a rule of thumb is LTV ≳ 3×CAC) and a payback period it can fund.", ref="standard unit-economics (SaaS/DTC metrics)"),
    "gross_margin": dict(note="Gross margin sets the ceiling on everything; software/digital ~70–90%, services ~50–70%, retail/food often <40%.", ref="standard financial analysis"),
    "burn_and_runway": dict(note="Cash, not profit, kills businesses first; runway = cash ÷ monthly burn. Underpricing and slow collections shorten it.", ref="startup finance fundamentals"),
    "moat_defensibility": dict(note="Without a moat (brand, network effects, switching costs, IP, scale, regulation) margins erode as competitors copy you.", ref="competitive strategy (Porter; network-effects literature)"),
    "distribution": dict(note="A product without distribution dies. Owning a channel (audience, SEO, partnerships) often matters more than the product itself.", ref="go-to-market fundamentals"),
    "capital_intensity": dict(note="Capital-heavy paths (property, manufacturing, franchise) need real upfront money and tie up cash; bootstrappable paths trade capital for time.", ref="capital-budgeting basics"),
    "time_vs_scalable": dict(note="Selling time (consulting, services) is reliable but caps at your hours; products/IP scale but most never reach scale.", ref="leverage of capital/code/media (classic)"),
    "power_law": dict(note="Creator, startup, and IP income is power-law distributed — a small minority capture most of the upside; plan for the median, not the headline.", ref="creator-economy & VC return studies"),
    "survivorship_bias": dict(note="Success stories you hear are the survivors; base rates (failure %, time-to-revenue) describe the typical outcome you should plan around.", ref="base-rate / survivorship reasoning"),
    "risk_of_ruin": dict(note="Avoid bets that can wipe you out (leverage, undiversified speculation); position size so a bad outcome is survivable.", ref="risk management (Kelly/ruin theory, informal)"),
}

# --- Durable macro context (NOT live data; verify currency via the fetcher) --
MACRO_CONTEXT = {
    "cost_of_capital": dict(note="When interest rates are elevated, capital is expensive and the market rewards profitability and cash flow over growth-at-all-costs; capital-heavy and long-payback paths face a higher bar.", ref="macro structural context — verify current rates via live data"),
    "ai_leverage_vs_commoditization": dict(note="AI gives small teams huge leverage, but also commoditizes generic content/services — defensibility shifts to distribution, taste, proprietary data, and trust.", ref="structural AI-economics context — verify specifics via live data"),
    "global_talent": dict(note="Remote/global talent compresses prices for commoditized digital work; differentiation and niche expertise resist the squeeze.", ref="labor-market structural context"),
    "platform_risk": dict(note="Building solely on a platform you don't control (an app store, a social feed, an ad network) means your economics can change overnight; own your audience where you can.", ref="platform-dependency structural context"),
    "profitability_premium": dict(note="In a tighter funding climate, paths with fast time-to-revenue and positive unit economics are favored over those needing long, speculative runways.", ref="funding-climate structural context — verify via live data"),
}

# --- Per-channel economic read (model · main cost · key risk · what good looks like)
CHANNEL_ECONOMICS = {
    "saas":            dict(model="recurring subscriptions", main_cost="engineering + churn", key_risk="long road to product-market fit; churn", good="net revenue retention >100%, low churn"),
    "consulting":      dict(model="bill time/expertise", main_cost="your hours", key_risk="income capped by time; feast-or-famine pipeline", good="repeat clients, premium rates, a niche"),
    "content":         dict(model="audience → ads/sponsors/products", main_cost="time + consistency", key_risk="power-law; algorithm dependence", good="owned audience (email), repeatable format"),
    "ecommerce":       dict(model="sell goods online", main_cost="ad spend + COGS", key_risk="thin margins, rising CAC, inventory", good="repeat purchase, brand, healthy contribution margin"),
    "realestate":      dict(model="appreciation + rent", main_cost="capital + financing", key_risk="leverage, illiquidity, rates", good="positive cash flow at conservative assumptions"),
    "equity":          dict(model="long-term appreciation", main_cost="capital + patience", key_risk="volatility, behavior, concentration", good="diversification, low fees, long horizon"),
    "crypto":          dict(model="speculative price + yield", main_cost="capital at risk", key_risk="extreme volatility, fraud, total loss", good="tiny position you can fully lose; no leverage"),
    "teaching":        dict(model="sell knowledge (courses/cohorts)", main_cost="audience + content", key_risk="needs credibility & distribution", good="proof, testimonials, an audience to sell to"),
    "advisory":        dict(model="advise on money/tax", main_cost="credentials + time", key_risk="regulation, liability", good="sticky retainer clients, referrals"),
    "healthcare":      dict(model="clinical/wellness services", main_cost="licensing + equipment", key_risk="regulation, capacity", good="recurring patients, reimbursement clarity"),
    "hospitality":     dict(model="food/lodging service", main_cost="rent + labor + food", key_risk="thin margins, high failure, location", good="strong location, repeat custom, cost control"),
    "creative":        dict(model="design/art/production", main_cost="time + tools", key_risk="lumpy demand, scope creep", good="signature style, retainers, productized offers"),
    "engineering":     dict(model="build physical products/systems", main_cost="tooling/plant + R&D", key_risk="long cycle, capital, execution", good="differentiated product, real demand pre-validated"),
    "agritech":        dict(model="grow/produce food + tech", main_cost="land/inputs", key_risk="seasonality, weather, thin margins", good="off-take contracts, yield/cost edge"),
    "trading_import":  dict(model="buy low / sell high cross-border", main_cost="working capital + logistics", key_risk="FX, customs, demand timing", good="reliable supplier + buyer, financed cycle"),
    "legal":           dict(model="legal services", main_cost="credentials + time", key_risk="liability, billable cap", good="specialization, referrals, durable demand"),
    "govcontract":     dict(model="public tenders/contracts", main_cost="compliance + long sales cycle", key_risk="slow cash, bureaucracy", good="track record, compliance edge, recurring contracts"),
    "media":           dict(model="publish content/IP", main_cost="production + attention", key_risk="ad cyclicality, attention competition", good="loyal audience, owned distribution, IP"),
    "logistics":       dict(model="move goods/people", main_cost="fleet/space + fuel/labor", key_risk="thin margins, utilization", good="high utilization, density, contracts"),
    "research_niche":  dict(model="deep research/R&D/niche", main_cost="time + funding", key_risk="slow, grant/niche dependent", good="rare expertise, funded mandate"),
    "affiliate":       dict(model="commissions on referrals", main_cost="traffic/audience", key_risk="power-law, platform & program risk", good="owned traffic, high-intent niche"),
    "ai_business":     dict(model="AI products/agents/automation", main_cost="talent + compute", key_risk="fast-moving, crowded, model commoditization", good="proprietary data/distribution, real workflow ROI"),
    "online_trading":  dict(model="active market trading", main_cost="capital at risk + time", key_risk="most retail traders lose; behavior & leverage", good="tested edge, strict risk limits, treat as speculation"),
    "digital_marketing": dict(model="performance marketing/SEO", main_cost="time + ad budget", key_risk="crowded, results pressure", good="case studies, retainers, a vertical"),
    "app_dev":         dict(model="build & monetize apps", main_cost="build + user acquisition", key_risk="discovery & retention are brutal", good="retention, a wedge, low CAC channel"),
    "fintech":         dict(model="payments/lending/wealth infra", main_cost="compliance + capital", key_risk="regulation, trust, long runway", good="licensing moat, unit economics at scale"),
    "data_analytics":  dict(model="data/analytics services", main_cost="skilled time", key_risk="commoditization at the low end", good="domain depth, recurring engagements"),
    "digital_products":dict(model="sell digital goods", main_cost="creation + distribution", key_risk="discovery; easy to copy", good="audience, catalog, brand/taste"),
    "paid_community":  dict(model="membership subscriptions", main_cost="time + facilitation", key_risk="churn, founder dependence", good="strong culture, low churn, member-led value"),
    "marketplace":     dict(model="take rate on matched trades", main_cost="liquidity acquisition", key_risk="cold-start, winner-take-most", good="liquidity in a niche, network effects"),
    "dividend_income": dict(model="income from assets", main_cost="capital", key_risk="needs large principal; rate sensitivity", good="diversified, sustainable payout, growing capital"),
    "short_term_rental": dict(model="nightly property hosting", main_cost="property + operations", key_risk="regulation, seasonality, financing", good="strong occupancy at conservative ADR, light regs"),
    "local_services":  dict(model="local skilled service", main_cost="labor/crew + travel", key_risk="capped by time/crew, local demand", good="repeat customers, referrals, route density"),
    "licensing_ip":    dict(model="royalties on IP", main_cost="creation + protection", key_risk="power-law; enforcement", good="a hit asset + licensees, defensible rights"),
    "franchise":       dict(model="operate a proven system", main_cost="franchise fee + buildout + royalties", key_risk="heavy upfront, royalty drag, location", good="proven unit economics, good territory, operations"),
}
CHANNEL_ECONOMICS_REF = "business-model & unit-economics fundamentals (standard sources)"


def finance_for_channels(advice: list[dict], top: int = 8) -> dict:
    """Select the cited economic grounding for the top channels in an advice list,
    plus the general principles and durable macro context the analyst should use."""
    chans = {}
    for e in advice[:top]:
        eco = CHANNEL_ECONOMICS.get(e["id"])
        if eco:
            chans[e["id"]] = {"name": e["name"], **eco, "ref": CHANNEL_ECONOMICS_REF}
    return {
        "principles": GENERAL_PRINCIPLES,
        "macro_context": MACRO_CONTEXT,
        "channels": chans,
        "note": "Static fundamentals + durable structural context only. Live 2026 "
                "specifics (current demand/saturation) come from the runtime web "
                "fetcher, not from here. Nothing here promises returns.",
    }
