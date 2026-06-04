"""Vimshottari balance-at-birth math for known Moon longitudes.

The Moon's nakshatra fixes the running mahadasha lord; the fraction of the
nakshatra already traversed fixes how much of that mahadasha has elapsed.
Each nakshatra spans 13 deg 20 min (= 13.3333... deg).

Hand-checked cases:
 - Moon at 0 deg (start of Ashwini -> Ketu): full Ketu (7y) remains.
 - Moon at the exact midpoint of Ashwini: half of Ketu (3.5y) remains.
 - Moon 1/4 into Rohini (lord Moon, 10y): 7.5y remains, 2.5y elapsed.
"""

from engine.chart import chart_from_signs
from engine import constants as C

ARC = C.NAKSHATRA_ARC  # 13.3333...


def dasha_for_moon(lon_deg):
    sign = int(lon_deg // 30)
    deg = lon_deg % 30
    chart = chart_from_signs(0, {"Moon": (sign, deg)})
    return chart.dasha


def test_start_of_ashwini_is_full_ketu():
    d = dasha_for_moon(0.0)
    assert d.starting_lord == "Ketu"
    assert d.balance_years_at_birth == 7.0
    assert d.elapsed_years_at_birth == 0.0
    assert d.moon_nakshatra == "Ashwini"


def test_midpoint_of_ashwini_is_half_ketu():
    d = dasha_for_moon(ARC * 0.5)
    assert d.starting_lord == "Ketu"
    assert d.balance_years_at_birth == 3.5
    assert d.elapsed_years_at_birth == 3.5


def test_quarter_into_rohini_is_moon_dasha():
    # Rohini is nakshatra index 3 -> lord Moon (10y).
    moon_lon = ARC * 3 + ARC * 0.25
    d = dasha_for_moon(moon_lon)
    assert d.starting_lord == "Moon"
    assert d.moon_nakshatra == "Rohini"
    assert d.balance_years_at_birth == 7.5
    assert d.elapsed_years_at_birth == 2.5


def test_mahadasha_sequence_follows_vimshottari_order():
    d = dasha_for_moon(0.0)  # starts Ketu
    lords = [md.lord for md in d.mahadashas]
    # After Ketu the order is Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
    assert lords == ["Ketu", "Venus", "Sun", "Moon", "Mars",
                     "Rahu", "Jupiter", "Saturn", "Mercury"]
    # Total span of all 9 mahadashas is the 120-year Vimshottari cycle
    # (first period here is full Ketu since balance == full).
    assert round(sum(md.years for md in d.mahadashas), 2) == float(C.VIMSHOTTARI_TOTAL)
