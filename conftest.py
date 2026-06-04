"""Pytest root conftest: makes the project importable and provides a synthetic
full-chart builder for engineering charts that contain (or lack) a given yoga.

This dir is auto-added to sys.path by pytest, so `import engine`/`import signals`
work from the test files.
"""

import pytest

from engine.chart import chart_from_signs

# A neutral full-chart baseline (Aries ascendant) chosen so that NONE of the
# tracked yogas (Gajakesari, Dhana, Raja, Budha-Aditya) fire. Tests override
# specific planets to engineer a yoga, then assert it fires.
_BASELINE = {
    "Sun": (2, 5.0),       # Gemini
    "Moon": (4, 5.0),      # Leo
    "Mars": (6, 5.0),      # Libra
    "Mercury": (8, 5.0),   # Sagittarius
    "Jupiter": (11, 5.0),  # Pisces
    "Venus": (9, 5.0),     # Capricorn
    "Saturn": (5, 5.0),    # Virgo
    "Rahu": (3, 5.0),      # Cancer
    "Ketu": (9, 5.0),      # Capricorn (opposite Rahu)
}


@pytest.fixture
def make_chart():
    """Return builder(asc_sign=0, **overrides) -> ChartFact with all 9 planets.

    overrides map a planet name to a (sign_index, deg_in_sign) tuple.
    """
    def _build(asc_sign: int = 0, **overrides):
        placements = dict(_BASELINE)
        for planet, place in overrides.items():
            placements[planet] = place
        return chart_from_signs(asc_sign, placements)
    return _build
