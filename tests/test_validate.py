"""Tests for the validate.py diff tool.

Two unit tests prove the diff logic itself is correct (using a reference built
from the engine's own output). A third test runs the REAL AstroSage fixture if
the user has provided tests/fixtures/reference.json, and is skipped otherwise so
the suite stays green until CONTRACT #8 is closed.
"""

from pathlib import Path

import pytest

from engine.chart import compute_chart
from validate import validate

SAMPLE_BIRTH = {
    "name": "Sample", "date": "1992-03-21", "time": "06:45",
    "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu",
}
FIXTURE = Path(__file__).parent / "fixtures" / "reference.json"


def _reference_from_engine(birth):
    """Build a reference dict that mirrors the engine output (self-consistent)."""
    chart = compute_chart(birth)
    planets = {name: {"sign": p.sign_name, "nakshatra": p.nakshatra}
               for name, p in chart.planets.items()}
    return {
        "birth": birth,
        "ascendant": {"sign": chart.ascendant.sign_name,
                      "nakshatra": chart.ascendant.nakshatra},
        "planets": planets,
    }


def test_self_consistent_reference_has_no_mismatch():
    ref = _reference_from_engine(SAMPLE_BIRTH)
    assert validate(ref) == []


def test_tampered_reference_is_detected():
    ref = _reference_from_engine(SAMPLE_BIRTH)
    # Corrupt one planet's sign and one ascendant nakshatra.
    ref["planets"]["Sun"]["sign"] = "Aries"
    ref["ascendant"]["nakshatra"] = "Ashwini"
    mism = validate(ref)
    items = {(m["item"], m["field"]) for m in mism}
    assert ("Sun", "sign") in items
    assert ("Ascendant", "nakshatra") in items


@pytest.mark.skipif(not FIXTURE.exists(),
                    reason="no AstroSage fixture yet (CONTRACT #8 open) — "
                           "see tests/fixtures/reference.template.json")
def test_real_astrosage_reference_matches():
    import json
    ref = json.loads(FIXTURE.read_text())
    mism = validate(ref)
    assert mism == [], f"engine disagrees with AstroSage reference: {mism}"
