"""compute_chart() -> ChartFact, the single source of chart truth (CONTRACT #1).

Deterministic: Swiss Ephemeris in Moshier mode (no external ephemeris data
files, fully offline) + Lahiri sidereal + Whole-Sign houses. No network, no LLM,
no randomness (CONTRACT #2).

The LLM never computes any of this; it only interprets the emitted ChartFact.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import swisseph as swe
from pydantic import BaseModel, Field

from engine import constants as C
from engine import vargas as V

# Tropical days per year for dasha date projection (Vimshottari convention uses
# 365.25; we use the common 365.2425 Gregorian mean year — documented choice).
DAYS_PER_YEAR = 365.2425

# Swiss Ephemeris planet ids. Rahu = MEAN node (CLAUDE.md).
_SWE_ID = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}
_CALC_FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


# --- Contract models --------------------------------------------------------

class BirthInput(BaseModel):
    name: Optional[str] = None
    date: str                      # "YYYY-MM-DD"
    time: str                      # "HH:MM" or "HH:MM:SS"
    lat: float
    lon: float
    tz: Optional[str] = None       # IANA name, e.g. "Asia/Kathmandu"
    utc_offset: Optional[float] = None  # fallback if tz is not given, in hours


class PlanetPos(BaseModel):
    name: str
    lon: float
    sign: int
    sign_name: str
    deg_in_sign: float
    nakshatra: str
    nakshatra_index: int
    pada: int
    retrograde: bool
    dignity: str                   # exalted|moolatrikona|own|debilitated|neutral|n/a
    house: int                     # whole-sign house 1..12
    vargas: dict[str, int]         # varga name -> sign index


class Ascendant(BaseModel):
    lon: float
    sign: int
    sign_name: str
    deg_in_sign: float
    nakshatra: str
    nakshatra_index: int
    pada: int


class Mahadasha(BaseModel):
    lord: str
    start: str                     # ISO date
    end: str
    years: float


class DashaInfo(BaseModel):
    system: str = "Vimshottari"
    moon_nakshatra: str
    moon_nakshatra_index: int
    starting_lord: str
    elapsed_years_at_birth: float
    balance_years_at_birth: float
    mahadashas: list[Mahadasha]


class ChartFact(BaseModel):
    name: Optional[str] = None
    julian_day_ut: float
    ayanamsa: float
    ascendant: Ascendant
    planets: dict[str, PlanetPos]
    houses_whole_sign: dict[int, int]   # house 1..12 -> sign index
    chalit_cusps: list[float] = Field(default_factory=list)  # SEPARATE field (CLAUDE.md)
    dasha: DashaInfo
    karakas: dict[str, str]             # chara karaka name -> planet
    meta: dict = Field(default_factory=dict)


# --- Pure helpers (no I/O) --------------------------------------------------

def nakshatra_of(lon: float) -> tuple[int, str, int]:
    """Return (nakshatra_index, name, pada) for a sidereal longitude."""
    idx = int(lon // C.NAKSHATRA_ARC) % 27
    within = lon % C.NAKSHATRA_ARC
    pada = int(within // (C.NAKSHATRA_ARC / 4.0)) + 1
    return idx, C.NAKSHATRAS[idx], pada


def dignity_of(planet: str, lon: float) -> str:
    """Classical dignity of a graha at a longitude. Nodes -> 'n/a'."""
    if planet not in C.EXALTATION:        # Rahu/Ketu: no BPHS dignity (CONTRACT #4)
        return "n/a"
    sign = int(lon // 30) % 12
    deg = lon % 30.0
    ex_sign, _ = C.EXALTATION[planet]
    if sign == ex_sign:
        return "exalted"
    if sign == C.debilitation_sign(planet):
        return "debilitated"
    mt = C.MOOLATRIKONA.get(planet)
    if mt and sign == mt[0] and mt[1] <= deg < mt[2]:
        return "moolatrikona"
    if sign in C.OWN_SIGNS.get(planet, []):
        return "own"
    return "neutral"


def whole_sign_houses(asc_sign: int) -> dict[int, int]:
    """House number 1..12 -> sign index, with house 1 = the ascendant's sign."""
    return {h: (asc_sign + h - 1) % 12 for h in range(1, 13)}


def house_of(planet_sign: int, asc_sign: int) -> int:
    """Whole-sign house occupied by a planet."""
    return ((planet_sign - asc_sign) % 12) + 1


def chara_karakas(planet_lons: dict[str, float]) -> dict[str, str]:
    """Jaimini chara karakas using the 7-graha scheme (nodes excluded to avoid
    the text-variant 8-karaka Rahu rule). Karaka = rank by degrees-in-sign,
    highest first. school: 'Jaimini' (7-karaka variant)."""
    names = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
             "Putrakaraka", "Gnatikaraka", "Darakaraka"]
    grahas = [(p, planet_lons[p] % 30.0) for p in C.PLANETS
              if p in C.EXALTATION and p in planet_lons]
    grahas.sort(key=lambda kv: kv[1], reverse=True)
    return {names[i]: grahas[i][0] for i in range(min(len(names), len(grahas)))}


def _vimshottari_sequence(moon_lon: float, birth_dt: datetime) -> DashaInfo:
    nak_idx = int(moon_lon // C.NAKSHATRA_ARC) % 27
    fraction = (moon_lon % C.NAKSHATRA_ARC) / C.NAKSHATRA_ARC
    lord = C.nakshatra_lord(nak_idx)
    full = C.VIMSHOTTARI_YEARS[lord]
    elapsed = full * fraction
    balance = full - elapsed

    seq: list[Mahadasha] = []
    cursor = birth_dt
    start_pos = C.VIMSHOTTARI_ORDER.index(lord)
    # First (partial) mahadasha, then the rest as full periods.
    for i in range(9):
        cur_lord = C.VIMSHOTTARI_ORDER[(start_pos + i) % 9]
        years = balance if i == 0 else C.VIMSHOTTARI_YEARS[cur_lord]
        end = cursor + timedelta(days=years * DAYS_PER_YEAR)
        seq.append(Mahadasha(lord=cur_lord, start=cursor.date().isoformat(),
                             end=end.date().isoformat(), years=round(years, 4)))
        cursor = end

    return DashaInfo(
        moon_nakshatra=C.NAKSHATRAS[nak_idx],
        moon_nakshatra_index=nak_idx,
        starting_lord=lord,
        elapsed_years_at_birth=round(elapsed, 4),
        balance_years_at_birth=round(balance, 4),
        mahadashas=seq,
    )


# --- The engine -------------------------------------------------------------

def _birth_to_utc(b: BirthInput) -> datetime:
    y, mo, d = (int(x) for x in b.date.split("-"))
    parts = [int(x) for x in b.time.split(":")]
    h, mi = parts[0], parts[1]
    s = parts[2] if len(parts) > 2 else 0
    if b.tz:
        local = datetime(y, mo, d, h, mi, s, tzinfo=ZoneInfo(b.tz))
        return local.astimezone(timezone.utc)
    off = b.utc_offset or 0.0
    naive = datetime(y, mo, d, h, mi, s)
    return (naive - timedelta(hours=off)).replace(tzinfo=timezone.utc)


def compute_chart(birth: BirthInput | dict) -> ChartFact:
    """Build the canonical ChartFact from birth data."""
    b = birth if isinstance(birth, BirthInput) else BirthInput(**birth)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    utc = _birth_to_utc(b)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    jd = swe.julday(utc.year, utc.month, utc.day, hour, swe.GREG_CAL)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    # Ascendant via sidereal Placidus cusps (cusps reused as chalit/bhava field).
    cusps, ascmc = swe.houses_ex(jd, b.lat, b.lon, b"P", swe.FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360.0
    asc_sign = int(asc_lon // 30) % 12
    a_idx, a_nak, a_pada = nakshatra_of(asc_lon)
    ascendant = Ascendant(
        lon=round(asc_lon, 6), sign=asc_sign, sign_name=C.SIGNS[asc_sign],
        deg_in_sign=round(asc_lon % 30, 6), nakshatra=a_nak,
        nakshatra_index=a_idx, pada=a_pada,
    )

    planets: dict[str, PlanetPos] = {}
    planet_lons: dict[str, float] = {}

    def add_planet(name: str, lon: float, speed: float):
        lon %= 360.0
        sign = int(lon // 30) % 12
        n_idx, n_name, n_pada = nakshatra_of(lon)
        planet_lons[name] = lon
        planets[name] = PlanetPos(
            name=name, lon=round(lon, 6), sign=sign, sign_name=C.SIGNS[sign],
            deg_in_sign=round(lon % 30, 6), nakshatra=n_name,
            nakshatra_index=n_idx, pada=n_pada, retrograde=(speed < 0),
            dignity=dignity_of(name, lon), house=house_of(sign, asc_sign),
            vargas=V.all_vargas(lon),
        )

    for name, pid in _SWE_ID.items():
        xx, _ = swe.calc_ut(jd, pid, _CALC_FLAGS)
        add_planet(name, xx[0], xx[3])

    # Rahu = mean node; Ketu = Rahu + 180. Nodes are retrograde by convention.
    rahu_xx, _ = swe.calc_ut(jd, swe.MEAN_NODE, _CALC_FLAGS)
    add_planet("Rahu", rahu_xx[0], -1.0)
    add_planet("Ketu", rahu_xx[0] + 180.0, -1.0)

    dasha = _vimshottari_sequence(planet_lons["Moon"], utc)

    return ChartFact(
        name=b.name,
        julian_day_ut=jd,
        ayanamsa=round(ayanamsa, 6),
        ascendant=ascendant,
        planets=planets,
        houses_whole_sign=whole_sign_houses(asc_sign),
        chalit_cusps=[round(c % 360.0, 6) for c in cusps[:12]],
        dasha=dasha,
        karakas=chara_karakas(planet_lons),
        meta={
            "ayanamsa_name": "Lahiri",
            "house_system": "Whole-Sign (rasi); Placidus cusps in chalit_cusps",
            "ephemeris": "Moshier (offline)",
            "utc": utc.isoformat(),
        },
    )


# --- Synthetic builder (pure; for crafted test charts & demos) --------------

def chart_from_signs(asc_sign: int, placements: dict[str, tuple[int, float]],
                     name: Optional[str] = None) -> ChartFact:
    """Build a ChartFact from explicit (sign, degree-in-sign) placements without
    the ephemeris. Used to engineer charts containing a specific yoga for tests.
    Dasha is derived from the Moon placement; karakas from the given degrees.
    """
    epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)
    a_idx, a_nak, a_pada = nakshatra_of(asc_sign * 30.0)
    ascendant = Ascendant(
        lon=float(asc_sign * 30), sign=asc_sign, sign_name=C.SIGNS[asc_sign],
        deg_in_sign=0.0, nakshatra=a_nak, nakshatra_index=a_idx, pada=a_pada,
    )
    planets: dict[str, PlanetPos] = {}
    planet_lons: dict[str, float] = {}
    for pname in C.PLANETS:
        if pname not in placements:
            continue
        sign, deg = placements[pname]
        lon = (sign * 30.0 + deg) % 360.0
        n_idx, n_name, n_pada = nakshatra_of(lon)
        planet_lons[pname] = lon
        planets[pname] = PlanetPos(
            name=pname, lon=lon, sign=sign, sign_name=C.SIGNS[sign],
            deg_in_sign=deg, nakshatra=n_name, nakshatra_index=n_idx,
            pada=n_pada, retrograde=False, dignity=dignity_of(pname, lon),
            house=house_of(sign, asc_sign), vargas=V.all_vargas(lon),
        )
    dasha = (_vimshottari_sequence(planet_lons["Moon"], epoch)
             if "Moon" in planet_lons else
             DashaInfo(moon_nakshatra="?", moon_nakshatra_index=-1,
                       starting_lord="?", elapsed_years_at_birth=0.0,
                       balance_years_at_birth=0.0, mahadashas=[]))
    return ChartFact(
        name=name, julian_day_ut=0.0, ayanamsa=0.0, ascendant=ascendant,
        planets=planets, houses_whole_sign=whole_sign_houses(asc_sign),
        chalit_cusps=[], dasha=dasha,
        karakas=chara_karakas(planet_lons) if planet_lons else {},
        meta={"synthetic": True},
    )
