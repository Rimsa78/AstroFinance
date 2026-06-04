"""Modern earning channels, each tagged with the classical signals that
SUPPORT it and the signals that WARN against it.

These tags name signals emitted by signals.py. The mapping graha/house ->
earning channel is an interpretive bridge (modern channels are not in classical
texts); it is intentionally explicit and editable, never hidden in scoring.

Tag vocabulary (must match signals.SIGNAL_NAMES):
  Graha strength: strong_sun, strong_moon, strong_mars, strong_mercury,
                  strong_jupiter, strong_venus, strong_saturn, strong_rahu,
                  strong_ketu
  House strength: strong_2nd, strong_4th, strong_5th, strong_9th,
                  strong_10th, strong_11th
  Yogas:          gajakesari_yoga, dhana_yoga, raja_yoga, budhaditya_yoga
  Cautions:       heavy_dusthana, debilitated_lagna_lord, retrograde_emphasis
"""

from __future__ import annotations


class Channel:
    __slots__ = ("id", "name", "description", "astro_support", "astro_warn")

    def __init__(self, id, name, description, astro_support, astro_warn):
        self.id = id
        self.name = name
        self.description = description
        self.astro_support = astro_support
        self.astro_warn = astro_warn

    def __repr__(self):
        return f"Channel({self.id!r})"


CHANNELS: list[Channel] = [
    Channel("saas", "SaaS / software product",
            "Build and sell a recurring-revenue software product.",
            ["strong_mercury", "strong_rahu", "strong_10th", "raja_yoga"],
            ["heavy_dusthana", "retrograde_emphasis"]),
    Channel("consulting", "Freelance services / consulting",
            "Sell expertise and time directly to clients.",
            ["strong_mercury", "strong_jupiter", "strong_10th", "budhaditya_yoga"],
            ["debilitated_lagna_lord"]),
    Channel("content", "Content creation (video/social)",
            "Audience-funded media: YouTube, podcasts, social.",
            ["strong_venus", "strong_mercury", "strong_rahu", "strong_5th"],
            ["retrograde_emphasis"]),
    Channel("ecommerce", "E-commerce / online retail",
            "Sell physical or digital goods online.",
            ["strong_mercury", "strong_11th", "strong_rahu", "dhana_yoga"],
            ["heavy_dusthana"]),
    Channel("realestate", "Real estate / property",
            "Acquire, develop, or rent property.",
            ["strong_saturn", "strong_mars", "strong_4th", "dhana_yoga"],
            ["debilitated_lagna_lord"]),
    Channel("equity", "Stock / equity investing",
            "Long-term investing in listed equities.",
            ["strong_11th", "strong_jupiter", "strong_2nd", "dhana_yoga"],
            ["heavy_dusthana"]),
    Channel("crypto", "Crypto / speculative trading",
            "High-volatility speculative instruments.",
            ["strong_rahu", "strong_mars", "strong_11th"],
            ["heavy_dusthana", "debilitated_lagna_lord", "retrograde_emphasis"]),
    Channel("teaching", "Teaching / coaching / courses",
            "Package knowledge into courses, cohorts, coaching.",
            ["strong_jupiter", "strong_mercury", "strong_5th", "strong_9th"],
            []),
    Channel("advisory", "Financial advisory / accounting",
            "Advise on money, tax, accounting, planning.",
            ["strong_jupiter", "strong_mercury", "strong_2nd", "budhaditya_yoga"],
            ["debilitated_lagna_lord"]),
    Channel("healthcare", "Healthcare / wellness services",
            "Clinical, therapeutic, or wellness services.",
            ["strong_moon", "strong_jupiter", "strong_mars"],
            ["heavy_dusthana"]),
    Channel("hospitality", "Hospitality / food business",
            "Restaurants, cafes, hotels, catering.",
            ["strong_moon", "strong_venus", "strong_2nd"],
            ["heavy_dusthana"]),
    Channel("creative", "Arts / design / creative studio",
            "Design, art, music, creative production.",
            ["strong_venus", "strong_5th", "strong_mercury"],
            ["retrograde_emphasis"]),
    Channel("engineering", "Engineering / manufacturing",
            "Build physical products and systems.",
            ["strong_mars", "strong_saturn", "strong_10th"],
            ["debilitated_lagna_lord"]),
    Channel("agritech", "Agriculture / agritech",
            "Farming, food production, agritech.",
            ["strong_saturn", "strong_moon", "strong_4th"],
            ["heavy_dusthana"]),
    Channel("trading_import", "Import / export / trading",
            "Cross-border trade and distribution.",
            ["strong_mercury", "strong_rahu", "strong_11th"],
            ["retrograde_emphasis"]),
    Channel("legal", "Law / legal services",
            "Legal practice, compliance, dispute resolution.",
            ["strong_jupiter", "strong_sun", "strong_mercury"],
            ["debilitated_lagna_lord"]),
    Channel("govcontract", "Government / public-sector contracts",
            "Public tenders, regulated services, civic contracts.",
            ["strong_sun", "strong_saturn", "strong_10th", "raja_yoga"],
            ["heavy_dusthana"]),
    Channel("media", "Media / publishing",
            "Books, journalism, publishing houses.",
            ["strong_mercury", "strong_jupiter", "strong_venus"],
            ["retrograde_emphasis"]),
    Channel("logistics", "Logistics / transport",
            "Movement of goods and people.",
            ["strong_mars", "strong_saturn", "strong_rahu"],
            ["heavy_dusthana"]),
    Channel("research_niche", "Research / spiritual / niche",
            "Deep research, R&D, spiritual or contemplative niches.",
            ["strong_ketu", "strong_jupiter", "strong_saturn"],
            ["debilitated_lagna_lord"]),
    Channel("affiliate", "Affiliate / passive digital income",
            "Affiliate marketing, ad/licensing royalties.",
            ["strong_rahu", "strong_11th", "strong_venus"],
            ["heavy_dusthana", "retrograde_emphasis"]),

    # --- modern / digital-first channels ---
    Channel("ai_business", "AI / automation products & agencies",
            "Build AI products, agents, or automation services.",
            ["strong_rahu", "strong_mercury", "strong_10th", "raja_yoga"],
            ["retrograde_emphasis"]),
    Channel("online_trading", "Active online trading (stocks/forex/derivatives)",
            "Self-directed active trading of liquid markets.",
            ["strong_mercury", "strong_rahu", "strong_mars", "strong_11th"],
            ["heavy_dusthana", "debilitated_lagna_lord", "retrograde_emphasis"]),
    Channel("digital_marketing", "Digital marketing / growth agency",
            "Performance marketing, SEO, paid social, growth.",
            ["strong_mercury", "strong_venus", "strong_rahu", "strong_11th"],
            ["retrograde_emphasis"]),
    Channel("app_dev", "App / mobile software development",
            "Design and ship mobile or web apps.",
            ["strong_mercury", "strong_rahu", "strong_10th"],
            ["heavy_dusthana", "retrograde_emphasis"]),
    Channel("fintech", "Fintech / payments / lending",
            "Payments, lending, wealth, or financial infrastructure.",
            ["strong_mercury", "strong_jupiter", "strong_2nd", "strong_11th"],
            ["debilitated_lagna_lord", "heavy_dusthana"]),
    Channel("data_analytics", "Data / analytics / quant services",
            "Data science, analytics, and quantitative work.",
            ["strong_mercury", "strong_saturn", "strong_ketu"],
            ["retrograde_emphasis"]),

    # --- more ways of making money ---
    Channel("digital_products", "Digital products (templates, ebooks, presets)",
            "Sell near-zero-marginal-cost digital goods.",
            ["strong_mercury", "strong_venus", "strong_5th", "strong_11th"],
            ["retrograde_emphasis"]),
    Channel("paid_community", "Paid community / membership",
            "Recurring revenue from a members' community.",
            ["strong_venus", "strong_mercury", "strong_11th", "gajakesari_yoga"],
            ["heavy_dusthana"]),
    Channel("marketplace", "Marketplace / platform business",
            "Match buyers and sellers; take a cut.",
            ["strong_mercury", "strong_rahu", "strong_11th", "raja_yoga"],
            ["heavy_dusthana", "retrograde_emphasis"]),
    Channel("dividend_income", "Dividend / income investing",
            "Income from dividend-paying assets.",
            ["strong_jupiter", "strong_2nd", "strong_11th", "dhana_yoga"],
            ["heavy_dusthana"]),
    Channel("short_term_rental", "Short-term rentals / property hosting",
            "Host property for short stays.",
            ["strong_venus", "strong_4th", "strong_moon", "strong_2nd"],
            ["debilitated_lagna_lord", "heavy_dusthana"]),
    Channel("local_services", "Local services / trades",
            "Home, repair, care, and skilled local services.",
            ["strong_mars", "strong_saturn", "strong_moon"],
            ["debilitated_lagna_lord"]),
    Channel("licensing_ip", "Licensing / royalties / IP",
            "License intellectual property for royalties.",
            ["strong_jupiter", "strong_venus", "strong_5th", "strong_11th"],
            ["retrograde_emphasis"]),
    Channel("franchise", "Franchise ownership / operations",
            "Operate a proven franchised business system.",
            ["strong_saturn", "strong_mercury", "strong_2nd", "strong_10th"],
            ["heavy_dusthana", "debilitated_lagna_lord"]),
]

# ids must be unique (count is allowed to grow as new channels are added)
assert len(CHANNELS) == len({c.id for c in CHANNELS}), "duplicate channel id"

CHANNELS_BY_ID = {c.id: c for c in CHANNELS}
