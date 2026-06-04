"""Knowledge-base completeness + the per-chart RAG selector.

Ensures the cited corpus covers every graha/house/sign/nakshatra/yoga/dasha lord,
that every entry carries a citation (CONTRACT #5), and that knowledge_for_chart
selects grounded material specific to a chart.
"""

from engine import constants as C
from engine.chart import compute_chart
from signals import compute_signals, SIGNAL_NAMES
from kb import knowledge as KN

BIRTH = {"name": "T", "date": "1998-05-19", "time": "16:10",
         "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"}


def test_all_grahas_covered_and_cited():
    for p in C.PLANETS:
        assert p in KN.GRAHAS, f"missing graha knowledge: {p}"
        assert KN.GRAHAS[p]["ref"], f"graha {p} lacks a citation"


def test_all_houses_and_signs_covered():
    assert set(KN.BHAVAS) == set(range(1, 13))
    assert set(KN.SIGN_TRAITS) == set(range(12))


def test_all_nakshatras_covered():
    assert set(KN.NAKSHATRA_INFO) == set(C.NAKSHATRAS)
    assert len(KN.NAKSHATRA_INFO) == 27


def test_dasha_effects_cover_all_lords():
    for lord in C.VIMSHOTTARI_ORDER:
        assert lord in KN.DASHA_EFFECTS


def test_yoga_info_matches_yoga_signals():
    yoga_signals = {s for s in SIGNAL_NAMES if s.endswith("_yoga")}
    assert set(KN.YOGA_INFO) == yoga_signals


def test_dignity_meanings_cover_engine_dignities():
    for d in ("exalted", "moolatrikona", "own", "neutral", "debilitated", "n/a"):
        assert d in KN.DIGNITY_MEANING


def test_yoga_library_entries_are_cited():
    assert len(KN.YOGA_LIBRARY) >= 25
    for name, y in KN.YOGA_LIBRARY.items():
        assert y["condition"] and y["result"] and y["ref"], f"{name} incomplete"


def test_remedies_cover_all_grahas():
    for p in C.PLANETS:
        assert p in KN.REMEDIES and KN.REMEDIES[p]["beej_mantra"]


def test_functional_lords_for_aries_lagna():
    f = KN.functional_lords(0)  # Aries ascendant
    # Sun lords the 5th (Leo) and is a trikona lord; Mars lords 1 & 8.
    assert "Sun" in f["functional_benefics"]
    # Mars lords Aries(1) and Scorpio(8) -> not a kendra+trikona yogakaraka here.
    assert isinstance(f["yogakaraka"], list)
    assert f["ref"]


def test_manglik_detector(make_chart):
    from signals import detect_doshas
    # Mars in the 1st house (Aries asc, Mars in Aries) -> Manglik.
    d = detect_doshas(make_chart(asc_sign=0, Mars=(0, 5.0)))
    assert d["manglik"]["present"] is True
    # Mars in the 3rd (Gemini) -> not a Manglik house.
    d2 = detect_doshas(make_chart(asc_sign=0, Mars=(2, 5.0)))
    assert d2["manglik"]["present"] is False


def test_planet_aspects_include_seventh_and_specials(make_chart):
    from signals import planet_aspects
    asp = planet_aspects(make_chart(asc_sign=0, Jupiter=(0, 5.0)))  # Jupiter in house 1
    # Jupiter in house 1 aspects 7th, 5th (house 5) and 9th (house 9).
    assert set(asp["Jupiter"]) == {5, 7, 9}


def test_knowledge_for_chart_is_grounded_and_specific():
    chart = compute_chart(BIRTH)
    signals = compute_signals(chart)
    k = KN.knowledge_for_chart(chart, signals)
    # every planet present, with placement text drawn from the engine
    assert set(k["grahas"]) == set(chart.planets)
    venus = k["grahas"]["Venus"]
    assert chart.planets["Venus"].sign_name in venus["placement"]
    assert venus["karaka"] and venus["ref"]
    # lagna lord matches the engine's ascendant
    assert k["lagna"]["lord"] == C.SIGN_LORD[chart.ascendant.sign]
    # only fired yogas are included
    for key in k["active_yogas"]:
        assert signals[key]["value"] >= 1.0
    # the expanded slices are all present
    for key in ("functional_lords", "graha_aspects", "doshas", "remedies",
                "yoga_library", "divisional_meanings", "predictive_notes"):
        assert key in k, f"missing knowledge slice: {key}"
    # remedies always carry the gemstone caveat
    assert "qualified astrologer" in k["remedies"]["caveat"]
