"""Validate the engine against a saved AstroSage reference chart (CONTRACT #8).

Usage:
    python validate.py tests/fixtures/reference.json

Diffs the engine's ascendant + 9 planets (sign & nakshatra) against the
reference and prints any mismatch with a tolerance note. Exit code 0 = match,
1 = mismatches found, 2 = no/invalid fixture.

Reference JSON schema (see tests/fixtures/reference.template.json):
    {
      "birth": {"date","time","lat","lon","tz" (or "utc_offset")},
      "ascendant": {"sign": "Pisces", "nakshatra": "Revati"},
      "planets": {"Sun": {"sign": "...", "nakshatra": "..."}, ... 9 bodies}
    }

Sign and nakshatra are compared case/space-insensitively. A mismatch at a sign
or nakshatra boundary usually means an ayanamsa-version difference (AstroSage's
Lahiri vs Swiss Lahiri can differ by a few arc-seconds) rather than a real bug —
the printed engine degree makes that visible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.chart import compute_chart

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def _boundary_note(deg_in_sign: float) -> str:
    if deg_in_sign < 1.0 or deg_in_sign > 29.0:
        return " [near sign boundary — likely ayanamsa-version diff, not a bug]"
    return ""


def validate(reference: dict) -> list[dict]:
    """Return a list of mismatch dicts (empty = full match)."""
    chart = compute_chart(reference["birth"])
    mismatches: list[dict] = []

    def check(label, expected, got_sign, got_nak, deg):
        exp_sign = expected.get("sign")
        exp_nak = expected.get("nakshatra")
        if exp_sign is not None and _norm(exp_sign) != _norm(got_sign):
            mismatches.append({"item": label, "field": "sign", "expected": exp_sign,
                               "got": got_sign, "engine_deg": round(deg, 3),
                               "note": _boundary_note(deg)})
        if exp_nak is not None and _norm(exp_nak) != _norm(got_nak):
            mismatches.append({"item": label, "field": "nakshatra", "expected": exp_nak,
                               "got": got_nak, "engine_deg": round(deg, 3),
                               "note": _boundary_note(deg)})

    if "ascendant" in reference:
        a = chart.ascendant
        check("Ascendant", reference["ascendant"], a.sign_name, a.nakshatra, a.deg_in_sign)

    for body in BODIES:
        if body not in reference.get("planets", {}):
            continue
        p = chart.planets[body]
        check(body, reference["planets"][body], p.sign_name, p.nakshatra, p.deg_in_sign)

    return mismatches


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python validate.py <reference.json>")
        print("(create one from tests/fixtures/reference.template.json)")
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"No reference fixture at {path}. CONTRACT #8 is not yet closed.")
        print("Export an AstroSage chart into the schema in "
              "tests/fixtures/reference.template.json and re-run.")
        return 2

    reference = json.loads(path.read_text())
    mismatches = validate(reference)

    name = reference.get("birth", {}).get("name", path.stem)
    if not mismatches:
        print(f"OK: engine matches reference '{name}' on ascendant + all given bodies.")
        return 0

    print(f"{len(mismatches)} mismatch(es) vs reference '{name}':")
    for m in mismatches:
        print(f"  {m['item']:11} {m['field']:9} expected={m['expected']!r:24} "
              f"got={m['got']!r:24} (engine {m['engine_deg']}°){m['note']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
