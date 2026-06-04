"""chart -> yogas + named signals, each with a reason and citation.

Output contract: a flat dict
    { name: {"value": float 0..1, "why": str, "classical_ref": str, "school": str} }

Every signal is traceable (CONTRACT #3) and cited (CONTRACT #5). Graha/house
"strength" here is an explicit, transparent PROXY (dignity + bhava placement),
not Shadbala; Shadbala is Phase F. The proxy nature is stated in each `why`.

Pure: takes a ChartFact, returns a dict. No I/O, no LLM, no randomness.
"""

from __future__ import annotations

from engine import constants as C
from engine.chart import ChartFact

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}

DIGNITY_STRENGTH = {
    "exalted": 1.0, "moolatrikona": 0.9, "own": 0.8,
    "neutral": 0.5, "debilitated": 0.1, "n/a": 0.5,
}

# The complete vocabulary of signal names this module can emit. Channels in
# kb/channels.py must only reference names in this set (asserted by tests).
SIGNAL_NAMES = {
    "strong_sun", "strong_moon", "strong_mars", "strong_mercury",
    "strong_jupiter", "strong_venus", "strong_saturn", "strong_rahu", "strong_ketu",
    "strong_2nd", "strong_4th", "strong_5th", "strong_9th", "strong_10th", "strong_11th",
    "gajakesari_yoga", "dhana_yoga", "raja_yoga", "budhaditya_yoga",
    "heavy_dusthana", "debilitated_lagna_lord", "retrograde_emphasis",
}

_clamp = lambda x: max(0.0, min(1.0, x))


def _ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', ..."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def lord_of_house(chart: ChartFact, house: int) -> str:
    """Sign lord of the sign occupying a whole-sign house."""
    return C.SIGN_LORD[chart.houses_whole_sign[house]]


def _graha_strength(chart: ChartFact, planet: str) -> tuple[float, str]:
    p = chart.planets[planet]
    base = DIGNITY_STRENGTH[p.dignity]
    note = f"{planet} in {p.sign_name} ({p.dignity}), house {p.house}"
    if p.house in C.KENDRAS or p.house in C.TRIKONAS:
        base += 0.15
        note += "; angular/trinal (+)"
    if p.house in (6, 8, 12):
        base -= 0.20
        note += "; in dusthana (-)"
    return _clamp(base), note + " [proxy: dignity+bhava, not Shadbala]"


def _house_strength(chart: ChartFact, house: int) -> tuple[float, str]:
    lord = lord_of_house(chart, house)
    lord_s, lord_note = _graha_strength(chart, lord)
    val = lord_s
    occupants = [name for name, p in chart.planets.items() if p.house == house]
    benefic_occ = [o for o in occupants if o in NATURAL_BENEFICS]
    if benefic_occ:
        val += 0.15
    why = (f"house {house} lord {lord}: {lord_note}"
           + (f"; benefic(s) {', '.join(benefic_occ)} occupy it (+)" if benefic_occ else ""))
    return _clamp(val), why


def _rel_house(from_sign: int, to_sign: int) -> int:
    """House number of to_sign counted from from_sign (1..12)."""
    return ((to_sign - from_sign) % 12) + 1


# --- Yogas ------------------------------------------------------------------

def _gajakesari(chart: ChartFact) -> dict:
    moon = chart.planets["Moon"].sign
    jup = chart.planets["Jupiter"].sign
    rel = _rel_house(moon, jup)
    fires = rel in C.KENDRAS
    return {
        "value": 1.0 if fires else 0.0,
        "why": (f"Jupiter is in the {_ordinal(rel)} from the Moon"
                + (" (a kendra) -> Gajakesari forms" if fires else " (not a kendra)")),
        "classical_ref": "BPHS, Gaja-Kesari Yoga",
        "school": "Parashara (measured from Moon; some texts measure from Lagna)",
    }


def _dhana(chart: ChartFact) -> dict:
    """A clearly-defined Dhana (wealth) yoga: association between the lords of
    the 2nd (accumulated wealth) and 11th (gains) houses -- by one lord sitting
    in the other's house, conjunction in one sign, or mutual exchange."""
    l2, l11 = lord_of_house(chart, 2), lord_of_house(chart, 11)
    p2, p11 = chart.planets[l2], chart.planets[l11]
    reasons = []
    if l2 == l11:
        reasons.append(f"a single lord ({l2}) rules both the 2nd and 11th")
    if p2.house == 11:
        reasons.append(f"2nd lord {l2} is placed in the 11th")
    if p11.house == 2:
        reasons.append(f"11th lord {l11} is placed in the 2nd")
    if l2 != l11 and p2.sign == p11.sign:
        reasons.append(f"2nd lord {l2} and 11th lord {l11} are conjunct in {p2.sign_name}")
    # parivartana (mutual exchange) between the 2nd and 11th lords
    if l2 != l11 and p2.house == 11 and p11.house == 2:
        reasons.append("they are in mutual exchange (parivartana)")
    fires = bool(reasons)
    return {
        "value": 1.0 if fires else 0.0,
        "why": ("Dhana yoga: " + "; ".join(reasons)) if fires
               else f"no 2nd<->11th lord association (lords: {l2}, {l11})",
        "classical_ref": "BPHS, Dhana Yogas (2nd/11th lord association)",
        "school": "Parashara",
    }


def _raja(chart: ChartFact) -> dict:
    """Raja yoga: a kendra lord associates with a trikona lord (conjunction in
    one sign or mutual exchange)."""
    kendra_lords = {lord_of_house(chart, h) for h in C.KENDRAS}
    trikona_lords = {lord_of_house(chart, h) for h in C.TRIKONAS}
    reasons = []
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue
            pk, pt = chart.planets[kl], chart.planets[tl]
            if pk.sign == pt.sign:
                reasons.append(f"kendra lord {kl} conjunct trikona lord {tl} in {pk.sign_name}")
            elif pk.house in C.TRIKONAS and pt.house in C.KENDRAS and \
                    lord_of_house(chart, pk.house) == tl and lord_of_house(chart, pt.house) == kl:
                reasons.append(f"{kl} and {tl} in mutual kendra/trikona exchange")
    fires = bool(reasons)
    return {
        "value": 1.0 if fires else 0.0,
        "why": ("Raja yoga: " + "; ".join(sorted(set(reasons)))) if fires
               else "no kendra-trikona lord association detected",
        "classical_ref": "BPHS, Raja Yogas (kendra-trikona lord union)",
        "school": "Parashara",
    }


def _budhaditya(chart: ChartFact) -> dict:
    sun, mer = chart.planets["Sun"], chart.planets["Mercury"]
    fires = sun.sign == mer.sign
    return {
        "value": 1.0 if fires else 0.0,
        "why": (f"Sun and Mercury conjunct in {sun.sign_name} -> Budha-Aditya"
                if fires else "Sun and Mercury are not conjunct"),
        "classical_ref": "Budha-Aditya Yoga (Sun-Mercury conjunction)",
        "school": "Parashara",
    }


# --- Cautions ---------------------------------------------------------------

def _heavy_dusthana(chart: ChartFact) -> dict:
    occ = [name for name, p in chart.planets.items() if p.house in (6, 8, 12)]
    val = min(1.0, len(occ) / 4.0)
    return {
        "value": val,
        "why": (f"{len(occ)} planet(s) in dusthanas 6/8/12: {', '.join(occ)}"
                if occ else "no significant dusthana load"),
        "classical_ref": "BPHS, dusthana (trik) bhavas 6/8/12",
        "school": "Parashara",
    }


def _debilitated_lagna_lord(chart: ChartFact) -> dict:
    ll = lord_of_house(chart, 1)
    deb = chart.planets[ll].dignity == "debilitated"
    return {
        "value": 1.0 if deb else 0.0,
        "why": (f"lagna lord {ll} is debilitated in {chart.planets[ll].sign_name}"
                if deb else f"lagna lord {ll} is not debilitated"),
        "classical_ref": "Lagna (lagnesha) strength",
        "school": "Parashara",
    }


def _retrograde_emphasis(chart: ChartFact) -> dict:
    retro = [name for name in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")
             if chart.planets[name].retrograde]
    val = min(1.0, len(retro) / 3.0)
    return {
        "value": val,
        "why": (f"{len(retro)} retrograde graha(s): {', '.join(retro)}"
                if retro else "no retrograde emphasis"),
        "classical_ref": "vakra (retrograde) graha",
        "school": "general",
    }


# --- Public API -------------------------------------------------------------

def compute_signals(chart: ChartFact) -> dict[str, dict]:
    sig: dict[str, dict] = {}

    for planet in C.PLANETS:
        if planet == "Ketu" and "Ketu" not in chart.planets:
            continue
        val, why = _graha_strength(chart, planet)
        sig[f"strong_{planet.lower()}"] = {
            "value": round(val, 4), "why": why,
            "classical_ref": "graha bala proxy (dignity + bhava)",
            "school": "Parashara",
        }

    for house, key in [(2, "strong_2nd"), (4, "strong_4th"), (5, "strong_5th"),
                       (9, "strong_9th"), (10, "strong_10th"), (11, "strong_11th")]:
        val, why = _house_strength(chart, house)
        sig[key] = {
            "value": round(val, 4), "why": why,
            "classical_ref": "bhava bala proxy (lord strength + benefic occupancy)",
            "school": "Parashara",
        }

    sig["gajakesari_yoga"] = _gajakesari(chart)
    sig["dhana_yoga"] = _dhana(chart)
    sig["raja_yoga"] = _raja(chart)
    sig["budhaditya_yoga"] = _budhaditya(chart)

    sig["heavy_dusthana"] = _heavy_dusthana(chart)
    sig["debilitated_lagna_lord"] = _debilitated_lagna_lord(chart)
    sig["retrograde_emphasis"] = _retrograde_emphasis(chart)

    return sig


# --- Drishti (graha aspects), combustion, doshas ----------------------------
# These are deterministic chart-pattern detectors used by the report/knowledge
# layer (NOT by channel scoring), so they stay out of SIGNAL_NAMES.

# Special full aspects (in addition to the universal 7th): house offsets.
_SPECIAL_ASPECTS = {"Mars": [4, 8], "Jupiter": [5, 9], "Saturn": [3, 10],
                    "Rahu": [5, 9], "Ketu": [5, 9]}  # nodal aspects per many schools

# Combustion orbs from the Sun in degrees (retrograde orbs in parentheses noted).
_COMBUSTION_ORB = {"Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
                   "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0}


def planet_aspects(chart) -> dict[str, list[int]]:
    """House numbers each planet aspects (drishti). All grahas aspect the 7th;
    Mars/Jupiter/Saturn (and the nodes per many schools) add special aspects.
    classical_ref: BPHS — graha drishti."""
    out = {}
    for name, p in chart.planets.items():
        offsets = [7] + _SPECIAL_ASPECTS.get(name, [])
        out[name] = sorted({((p.house - 1 + (o - 1)) % 12) + 1 for o in offsets})
    return out


def combustion(chart) -> dict[str, bool]:
    """Which planets are combust (too close to the Sun). classical_ref: asta/combustion."""
    sun = chart.planets["Sun"].lon
    out = {}
    for name, orb in _COMBUSTION_ORB.items():
        if name not in chart.planets:
            continue
        diff = abs((chart.planets[name].lon - sun + 180) % 360 - 180)
        out[name] = diff <= orb
    return out


def detect_doshas(chart) -> dict[str, dict]:
    """Deterministic detection of common doshas. Each carries why + classical_ref +
    a school/variant note. Cancellations (bhanga) are noted, not auto-applied."""
    res = {}

    # Manglik / Kuja dosha: Mars in 1,2,4,7,8,12 from Lagna (common variant).
    mars_h = chart.planets["Mars"].house
    manglik_houses = {1, 2, 4, 7, 8, 12}
    res["manglik"] = {
        "present": mars_h in manglik_houses,
        "why": (f"Mars occupies house {mars_h}"
                + (" (a Manglik house from Lagna)" if mars_h in manglik_houses
                   else " (not a Manglik house from Lagna)")),
        "classical_ref": "Kuja/Mangal dosha (variants also count from Moon & Venus)",
        "school": "Parashara (from Lagna)",
    }

    # Kala Sarpa: all 7 grahas hemmed within the Rahu–Ketu axis on one side.
    rahu = chart.planets["Rahu"].lon
    half1 = [(chart.planets[g].lon - rahu) % 360 for g in
             ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")]
    all_one_side = all(d < 180 for d in half1) or all(d >= 180 for d in half1)
    res["kala_sarpa"] = {
        "present": all_one_side,
        "why": ("all seven grahas fall on one side of the Rahu–Ketu axis"
                if all_one_side else "grahas fall on both sides of the Rahu–Ketu axis"),
        "classical_ref": "Kala Sarpa yoga/dosha (partial if axis is near a graha)",
        "school": "modern classical",
    }

    # Kemadruma: no planet (excl. Sun/nodes) in the 2nd or 12th from the Moon.
    moon_sign = chart.planets["Moon"].sign
    neighbours = {(moon_sign + 1) % 12, (moon_sign - 1) % 12}
    companions = [g for g in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                  if chart.planets[g].sign in neighbours]
    res["kemadruma"] = {
        "present": len(companions) == 0,
        "why": ("no graha in the 2nd or 12th from the Moon (isolated Moon)"
                if not companions else
                f"the Moon is supported by {', '.join(companions)} in the 2nd/12th"),
        "classical_ref": "Kemadruma yoga (cancelled by kendra support / aspects)",
        "school": "Parashara",
    }
    return res
