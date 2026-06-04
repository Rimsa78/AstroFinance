"""Dignity: exaltation / debilitation / own / moolatrikona on crafted longitudes.

Reference: BPHS exaltation degrees and own/moolatrikona signs (engine/constants).
Longitudes are absolute sidereal degrees (sign_index * 30 + deg_in_sign).
"""

from engine.chart import dignity_of


def lon(sign, deg):
    return sign * 30.0 + deg


def test_exaltation_by_sign():
    assert dignity_of("Sun", lon(0, 10)) == "exalted"      # Aries
    assert dignity_of("Moon", lon(1, 3)) == "exalted"      # Taurus
    assert dignity_of("Mars", lon(9, 28)) == "exalted"     # Capricorn
    assert dignity_of("Jupiter", lon(3, 5)) == "exalted"   # Cancer
    assert dignity_of("Venus", lon(11, 27)) == "exalted"   # Pisces
    assert dignity_of("Saturn", lon(6, 20)) == "exalted"   # Libra


def test_debilitation_is_seventh_from_exaltation():
    assert dignity_of("Sun", lon(6, 10)) == "debilitated"      # Libra
    assert dignity_of("Jupiter", lon(9, 5)) == "debilitated"   # Capricorn
    assert dignity_of("Saturn", lon(0, 20)) == "debilitated"   # Aries
    assert dignity_of("Mercury", lon(11, 15)) == "debilitated" # Pisces


def test_own_sign():
    assert dignity_of("Saturn", lon(9, 25)) == "own"   # Capricorn
    assert dignity_of("Mercury", lon(2, 10)) == "own"  # Gemini
    assert dignity_of("Mars", lon(7, 5)) == "own"      # Scorpio


def test_moolatrikona_vs_own_split():
    # Saturn moolatrikona = Aquarius 0-20; beyond 20 it is merely own.
    assert dignity_of("Saturn", lon(10, 10)) == "moolatrikona"  # Aquarius 10
    assert dignity_of("Saturn", lon(10, 25)) == "own"           # Aquarius 25
    # Sun moolatrikona = Leo 0-20; beyond is own.
    assert dignity_of("Sun", lon(4, 10)) == "moolatrikona"      # Leo 10
    assert dignity_of("Sun", lon(4, 25)) == "own"               # Leo 25


def test_nodes_have_no_dignity():
    assert dignity_of("Rahu", lon(0, 0)) == "n/a"
    assert dignity_of("Ketu", lon(6, 15)) == "n/a"
