"""Yoga detection on charts engineered to contain (or lack) a specific yoga.

We build full synthetic charts via the `make_chart` fixture (Aries ascendant,
baseline placements chosen so no tracked yoga fires), then override the minimum
planets needed to create one yoga and assert it fires.
"""

from signals import compute_signals, SIGNAL_NAMES
from kb.channels import CHANNELS


def test_baseline_fires_no_tracked_yoga(make_chart):
    sig = compute_signals(make_chart())
    for yoga in ("gajakesari_yoga", "dhana_yoga", "raja_yoga", "budhaditya_yoga"):
        assert sig[yoga]["value"] == 0.0, f"{yoga} unexpectedly fired on baseline"


def test_gajakesari_fires_when_jupiter_in_kendra_from_moon(make_chart):
    # Baseline Moon is in Leo (sign 4). Put Jupiter in Scorpio (sign 7):
    # that is the 4th from the Moon (a kendra) -> Gajakesari forms.
    chart = make_chart(Jupiter=(7, 5.0))
    sig = compute_signals(chart)
    assert sig["gajakesari_yoga"]["value"] == 1.0
    assert "4th from the Moon" in sig["gajakesari_yoga"]["why"]


def test_gajakesari_absent_when_jupiter_not_in_kendra(make_chart):
    # Jupiter in Gemini (sign 2) is the 11th from Moon (Leo) -> not a kendra.
    sig = compute_signals(make_chart(Jupiter=(2, 5.0)))
    assert sig["gajakesari_yoga"]["value"] == 0.0


def test_dhana_yoga_fires_when_2nd_lord_in_11th(make_chart):
    # Aries ascendant -> 2nd house is Taurus (lord Venus). Place Venus in
    # Aquarius (the 11th house) -> classic Dhana yoga (2nd lord in 11th).
    chart = make_chart(Venus=(10, 5.0))
    sig = compute_signals(chart)
    assert sig["dhana_yoga"]["value"] == 1.0
    assert "2nd lord Venus is placed in the 11th" in sig["dhana_yoga"]["why"]


def test_budhaditya_fires_on_sun_mercury_conjunction(make_chart):
    # Put Mercury in Gemini (sign 2) with the Sun (baseline Gemini) -> conjunct.
    sig = compute_signals(make_chart(Mercury=(2, 8.0)))
    assert sig["budhaditya_yoga"]["value"] == 1.0


def test_every_channel_tag_is_a_known_signal():
    for ch in CHANNELS:
        for tag in list(ch.astro_support) + list(ch.astro_warn):
            assert tag in SIGNAL_NAMES, f"{ch.id} references unknown signal {tag!r}"


def test_compute_signals_emits_full_vocabulary(make_chart):
    sig = compute_signals(make_chart())
    assert set(sig.keys()) == SIGNAL_NAMES
