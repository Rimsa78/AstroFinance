"""Divisional charts (vargas), exact Parashari rules.

Every function takes a sidereal longitude in [0, 360) and returns the resulting
**sign index** (0=Aries .. 11=Pisces). Pure, deterministic, no I/O.

Reference: Brihat Parashara Hora Shastra, "Vargas" chapter. school: "Parashara".

CONTRACT #4: D30 (Trimshamsha) and D60 (Shashtiamsha) are NOT implemented here
because their classical schemes are non-uniform/ambiguous across texts; shipping
one silently would be subtly-wrong astrology. They are marked not-implemented in
DESIGN.md.
"""

from __future__ import annotations


def _sign(lon: float) -> int:
    return int(lon // 30) % 12


def _deg_in_sign(lon: float) -> float:
    return lon % 30.0


def d1_rasi(lon: float) -> int:
    """D1: the rasi (birth) sign itself."""
    return _sign(lon)


def d2_hora(lon: float) -> int:
    """D2 Hora (15 deg each).

    Odd signs (Aries, Gemini, ... index even since 0-based Aries):
        0-15 deg  -> Leo  (Sun's hora)
        15-30 deg -> Cancer (Moon's hora)
    Even signs reverse this.

    Returns Leo (4) or Cancer (3) only, per classical Hora.
    """
    sign = _sign(lon)
    first_half = _deg_in_sign(lon) < 15.0
    is_odd_sign = (sign % 2 == 0)  # Aries(0) is the 1st = odd sign
    if is_odd_sign:
        return 4 if first_half else 3      # Leo then Cancer
    else:
        return 3 if first_half else 4      # Cancer then Leo


def d3_drekkana(lon: float) -> int:
    """D3 Drekkana (10 deg each): 1st part same sign, 2nd part 5th, 3rd part 9th."""
    sign = _sign(lon)
    part = int(_deg_in_sign(lon) // 10)  # 0,1,2
    offset = [0, 4, 8][part]             # same, 5th (+4), 9th (+8)
    return (sign + offset) % 12


def d4_chaturthamsha(lon: float) -> int:
    """D4 (7.5 deg each): parts map to 1st, 4th, 7th, 10th from the sign."""
    sign = _sign(lon)
    part = int(_deg_in_sign(lon) // 7.5)  # 0..3
    offset = [0, 3, 6, 9][part]
    return (sign + offset) % 12


# Tiny epsilon to keep float part-indices off exact division boundaries
# (e.g. 30 / (10/3) should be 9, not 8.999... -> 8).
_EPS = 1e-9

# Navamsa starting sign by element (Parashari): Fire->Aries, Earth->Capricorn,
# Air->Libra, Water->Cancer.
_NAVAMSA_START = {"Fire": 0, "Earth": 9, "Air": 6, "Water": 3}


def d7_saptamsha(lon: float) -> int:
    """D7 (30/7 deg each). Odd signs count from the sign itself; even signs
    count from the 7th sign from it."""
    sign = _sign(lon)
    part = int(_deg_in_sign(lon) * 7.0 / 30.0 + _EPS)  # 0..6
    is_odd_sign = (sign % 2 == 0)
    start = sign if is_odd_sign else (sign + 6) % 12
    return (start + part) % 12


def d9_navamsha(lon: float) -> int:
    """D9 Navamsha (3 deg 20 min each).

    Element start: Fire->Aries, Earth->Capricorn, Air->Libra, Water->Cancer;
    then advance by the navamsa index (0..8) within the sign.
    """
    from engine.constants import SIGN_ELEMENT
    sign = _sign(lon)
    idx = int(_deg_in_sign(lon) * 9.0 / 30.0 + _EPS)  # 0..8
    start = _NAVAMSA_START[SIGN_ELEMENT[sign]]
    return (start + idx) % 12


def d10_dashamsha(lon: float) -> int:
    """D10 Dashamsha (3 deg each). Odd signs count from the sign itself; even
    signs count from the 9th sign from it."""
    sign = _sign(lon)
    part = int(_deg_in_sign(lon) // 3.0)  # 0..9
    is_odd_sign = (sign % 2 == 0)
    start = sign if is_odd_sign else (sign + 8) % 12
    return (start + part) % 12


def d12_dwadashamsha(lon: float) -> int:
    """D12 (2.5 deg each): count from the sign itself."""
    sign = _sign(lon)
    part = int(_deg_in_sign(lon) // 2.5)  # 0..11
    return (sign + part) % 12


# Registry consumed by chart.py. Keys are the canonical varga names.
VARGA_FUNCS = {
    "D1": d1_rasi,
    "D2": d2_hora,
    "D3": d3_drekkana,
    "D4": d4_chaturthamsha,
    "D7": d7_saptamsha,
    "D9": d9_navamsha,
    "D10": d10_dashamsha,
    "D12": d12_dwadashamsha,
}


def all_vargas(lon: float) -> dict[str, int]:
    """Compute every implemented varga sign for a longitude."""
    return {name: fn(lon) for name, fn in VARGA_FUNCS.items()}
