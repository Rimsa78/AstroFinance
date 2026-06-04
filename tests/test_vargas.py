"""Varga placements on hand-checked degrees for D2, D9, D10 (plus a D1 sanity).

Sign indices: 0=Aries .. 11=Pisces. All inputs are absolute longitudes.
"""

import pytest

from engine import vargas as V


def lon(sign, deg):
    return sign * 30.0 + deg


# --- D2 Hora (returns only Leo=4 or Cancer=3) -------------------------------
@pytest.mark.parametrize("sign,deg,expected", [
    (0, 5, 4),    # Aries (odd) 0-15 -> Leo
    (0, 20, 3),   # Aries (odd) 15-30 -> Cancer
    (1, 5, 3),    # Taurus (even) 0-15 -> Cancer
    (1, 20, 4),   # Taurus (even) 15-30 -> Leo
])
def test_d2_hora(sign, deg, expected):
    assert V.d2_hora(lon(sign, deg)) == expected


# --- D9 Navamsha ------------------------------------------------------------
@pytest.mark.parametrize("sign,deg,expected", [
    (0, 0, 0),    # Aries 0 -> Aries
    (0, 5, 1),    # Aries 5 (2nd navamsa) -> Taurus
    (1, 0, 9),    # Taurus 0 (earth starts Capricorn) -> Capricorn
    (3, 10, 6),   # Cancer 10 (water starts Cancer, 4th navamsa) -> Libra
    (11, 29, 11), # Pisces 29 -> Pisces
])
def test_d9_navamsha(sign, deg, expected):
    assert V.d9_navamsha(lon(sign, deg)) == expected


# --- D10 Dashamsha ----------------------------------------------------------
@pytest.mark.parametrize("sign,deg,expected", [
    (0, 0, 0),    # Aries (odd) 1st -> Aries
    (0, 7, 2),    # Aries (odd) 3rd division -> Gemini
    (0, 28, 9),   # Aries (odd) 10th division -> Capricorn
    (1, 0, 9),    # Taurus (even) starts 9th from it -> Capricorn
    (1, 7, 11),   # Taurus (even) 3rd division -> Pisces
])
def test_d10_dashamsha(sign, deg, expected):
    assert V.d10_dashamsha(lon(sign, deg)) == expected


def test_d1_is_the_sign_itself():
    assert V.d1_rasi(lon(5, 12)) == 5
    assert V.d1_rasi(lon(11, 29.99)) == 11
