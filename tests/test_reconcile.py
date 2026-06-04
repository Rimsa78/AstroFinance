"""Reconciliation tests: the governing principle is enforced.

Critically asserts that the two layers are NEVER merged into a single number,
and that when they conflict the reality (truth) layer governs the verdict.
"""

import reconcile as RX


def astro(cid, name, score):
    return {"id": cid, "name": name, "astro_score": score,
            "why_fits": [], "why_caution": []}


def reality(cid, score, used=True):
    return {"id": cid, "reality_score": score, "base_realism": score / 100,
            "live_data_used": used, "live_asof": "2026-01-01",
            "why_viable": [], "why_risky": []}


def test_no_single_merged_score_field():
    out = RX.reconcile([astro("x", "X", 80)], {"x": reality("x", 80)})
    entry = out[0]
    # Two labelled axes must exist...
    assert "score" in entry["astro"] and "score" in entry["reality"]
    # ...and there must be NO top-level merged/blended number.
    for forbidden in ("score", "combined_score", "total", "blended", "final_score"):
        assert forbidden not in entry, f"reconcile leaked a merged field: {forbidden}"


def test_both_high_is_agree_pursue():
    out = RX.reconcile([astro("x", "X", 80)], {"x": reality("x", 80)})
    assert out[0]["verdict"] == "AGREE_PURSUE"


def test_astro_high_reality_low_is_timing_only_and_truth_governs():
    out = RX.reconcile([astro("x", "X", 85)], {"x": reality("x", 30)})
    e = out[0]
    assert e["verdict"] == "ASTRO_ONLY_TIMING"
    assert e["astro"]["label"] == "favoured"
    assert e["reality"]["label"] == "risky"
    assert "truth layer governs" in e["rationale"].lower()


def test_reality_high_astro_weak_is_reality_sound():
    out = RX.reconcile([astro("x", "X", 30)], {"x": reality("x", 80)})
    assert out[0]["verdict"] == "REALITY_SOUND"
    assert out[0]["astro"]["label"] == "weak"


def test_both_low_is_avoid():
    out = RX.reconcile([astro("x", "X", 30)], {"x": reality("x", 30)})
    assert out[0]["verdict"] == "AVOID"


def test_ordering_is_reality_first():
    astro_scored = [astro("a", "A", 90), astro("b", "B", 10)]
    reality_results = {"a": reality("a", 20), "b": reality("b", 90)}
    out = RX.reconcile(astro_scored, reality_results)
    # b has the higher reality score, so it ranks first despite weaker astro.
    assert [e["id"] for e in out] == ["b", "a"]


def test_channel_missing_from_reality_is_dropped():
    out = RX.reconcile([astro("a", "A", 50), astro("b", "B", 50)],
                       {"a": reality("a", 50)})
    assert [e["id"] for e in out] == ["a"]
