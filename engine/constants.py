"""Classical reference data for the deterministic engine.

CONTRACT #5: every astro rule carries a classical_ref + school. The data here is
the raw classical reference layer; modules that *apply* it (signals, scoring)
attach the citation to each fired rule.

Conventions (see CLAUDE.md):
  - Sign index 0 = Aries .. 11 = Pisces.
  - Longitudes are sidereal (Lahiri), degrees in [0, 360).
  - Planet keys are the canonical strings in PLANETS.

Primary reference: Brihat Parashara Hora Shastra (BPHS). Where a value is
text-variant (notably moolatrikona ranges), it is flagged inline.
"""

from __future__ import annotations

# --- Signs ------------------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Element of each sign by index: 0=Fire,1=Earth,2=Air,3=Water (repeating).
# Aries=Fire, Taurus=Earth, Gemini=Air, Cancer=Water, ...
SIGN_ELEMENT = ["Fire", "Earth", "Air", "Water"] * 3

# Quality (modality): movable/cardinal, fixed, dual/mutable (repeating from Aries).
SIGN_QUALITY = ["Movable", "Fixed", "Dual"] * 4

# --- Planets ----------------------------------------------------------------

# Canonical planet order. Rahu = MEAN north node; Ketu = Rahu + 180 (CLAUDE.md).
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# The 7 classical grahas have dignities; the nodes (Rahu/Ketu) are treated as
# shadow grahas with no universally-agreed exaltation in BPHS, so we leave their
# dignity tables out rather than ship a text-variant (CONTRACT #4).

# Sign lordship (rulership). BPHS. Index = sign index -> ruling planet.
SIGN_LORD = [
    "Mars",     # Aries
    "Venus",    # Taurus
    "Mercury",  # Gemini
    "Moon",     # Cancer
    "Sun",      # Leo
    "Mercury",  # Virgo
    "Venus",    # Libra
    "Mars",     # Scorpio
    "Jupiter",  # Sagittarius
    "Saturn",   # Capricorn
    "Saturn",   # Aquarius
    "Jupiter",  # Pisces
]

# Own signs (by sign index) for each planet. Derived from SIGN_LORD.
OWN_SIGNS = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10],
}

# Exaltation: (sign index, exact degree of deepest exaltation). BPHS.
# Debilitation is the opposite sign (sign+6) at the same degree.
EXALTATION = {
    "Sun": (0, 10.0),      # Aries 10
    "Moon": (1, 3.0),      # Taurus 3
    "Mars": (9, 28.0),     # Capricorn 28
    "Mercury": (5, 15.0),  # Virgo 15
    "Jupiter": (3, 5.0),   # Cancer 5
    "Venus": (11, 27.0),   # Pisces 27
    "Saturn": (6, 20.0),   # Libra 20
}

def debilitation_sign(planet: str) -> int:
    """Sign index of debilitation (7th from exaltation sign)."""
    ex_sign, _ = EXALTATION[planet]
    return (ex_sign + 6) % 12

# Moolatrikona ranges: (sign index, start_deg, end_deg) within the sign.
# TEXT-VARIANT WARNING: different texts give slightly different bounds. These
# follow the most commonly cited BPHS values. signals.py cites this when used.
# school: "Parashara"
MOOLATRIKONA = {
    "Sun": (4, 0.0, 20.0),       # Leo 0-20
    "Moon": (1, 4.0, 30.0),      # Taurus 4-30 (3-30 in some texts)
    "Mars": (0, 0.0, 12.0),      # Aries 0-12
    "Mercury": (5, 16.0, 20.0),  # Virgo 16-20
    "Jupiter": (8, 0.0, 10.0),   # Sagittarius 0-10
    "Venus": (6, 0.0, 15.0),     # Libra 0-15
    "Saturn": (10, 0.0, 20.0),   # Aquarius 0-20
}

# --- Nakshatras -------------------------------------------------------------

# 27 nakshatras, each spans 13 deg 20 min = 13.333... degrees.
NAKSHATRA_ARC = 360.0 / 27.0  # 13.3333...

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# --- Vimshottari dasha ------------------------------------------------------

# Dasha lords in order, with their mahadasha length in years. Total = 120.
# The nakshatra lord sequence repeats this order starting Ashwini = Ketu. BPHS.
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL = 120

def nakshatra_lord(nak_index: int) -> str:
    """Vimshottari dasha lord of a nakshatra (0=Ashwini -> Ketu)."""
    return VIMSHOTTARI_ORDER[nak_index % 9]

# Houses considered Kendras (angles) and Trikonas (trines) from any reference.
KENDRAS = [1, 4, 7, 10]
TRIKONAS = [1, 5, 9]
# Wealth-relevant houses used by signals/scoring: 2 (accumulated wealth),
# 11 (gains/income), plus the trikonas 5/9 (lakshmi sthanas).
DHANA_HOUSES = [2, 11]
LAKSHMI_HOUSES = [5, 9]
