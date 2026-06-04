"""Reconcile astro_score (hypothesis) with reality_score (truth governor).

THE GOVERNING PRINCIPLE (CLAUDE.md): astrology proposes, finance disposes. This
module produces DUAL-LABELLED advice and NEVER merges the two into a single
number. Each channel carries both scores, both labelled, plus a verdict that
states which layer governs the real decision.

When the layers disagree:
  - astro favours but reality is risky  -> the TRUTH layer wins; astrology drops
    to timing/flavour only.
  - reality is sound but astro is weak   -> pursue on fundamentals; astro neutral.

Ordering favours the reality layer (truth governs), with astro agreement as a
tiebreak. The sort key is NOT a displayed/blended score.
"""

from __future__ import annotations

# Thresholds on each independent 0..100 axis.
ASTRO_HIGH, ASTRO_LOW = 58.0, 45.0
REALITY_HIGH, REALITY_LOW = 58.0, 45.0


def _astro_label(score: float) -> str:
    if score >= ASTRO_HIGH:
        return "favoured"
    if score < ASTRO_LOW:
        return "weak"
    return "neutral"


def _reality_label(score: float) -> str:
    if score >= REALITY_HIGH:
        return "viable"
    if score < REALITY_LOW:
        return "risky"
    return "mixed"


def _verdict(astro: str, reality: str) -> tuple[str, str]:
    """Return (verdict_code, plain rationale). Reality governs on conflict."""
    if reality == "viable" and astro == "favoured":
        return "AGREE_PURSUE", ("Both layers agree: economically viable AND "
                                "astrologically favoured — highest-confidence idea.")
    if reality == "viable":
        return "REALITY_SOUND", ("Economically sound on fundamentals; astrology is "
                                 f"{astro}. Fine to pursue on the numbers — astrology "
                                 "is not the reason here.")
    if reality == "risky" and astro == "favoured":
        return "ASTRO_ONLY_TIMING", ("Astrology favours this but the economics look "
                                     "like a bad bet. The TRUTH layer governs the real "
                                     "decision: treat the astro pull as timing/flavour "
                                     "only, not a green light.")
    if reality == "risky":
        return "AVOID", ("Weak on the economics and no astrological tailwind — "
                         "deprioritise.")
    # reality == "mixed"
    if astro == "favoured":
        return "WATCH", ("Economics are mixed; astrology favours it. Worth watching / "
                         "a measured experiment, with the economics as the gate.")
    return "NEUTRAL", "Neither layer makes a strong case; no clear edge."


def reconcile(astro_scored: list[dict], reality_results: dict[str, dict]) -> list[dict]:
    """Join astro scores (from scoring.score_all) with reality results
    (from reality_check.reality_for_all) into dual-labelled advice.

    Returns one entry per channel that exists in BOTH inputs. There is
    deliberately NO single merged score field.
    """
    astro_by_id = {a["id"]: a for a in astro_scored}
    out: list[dict] = []

    for cid, a in astro_by_id.items():
        r = reality_results.get(cid)
        if r is None:
            continue
        a_score, r_score = a["astro_score"], r["reality_score"]
        a_lab, r_lab = _astro_label(a_score), _reality_label(r_score)
        code, rationale = _verdict(a_lab, r_lab)
        out.append({
            "id": cid,
            "name": a["name"],
            # --- two independent, labelled axes (never merged) ---
            "astro": {"score": a_score, "label": a_lab, "why_fits": a["why_fits"],
                      "why_caution": a["why_caution"]},
            "reality": {"score": r_score, "label": r_lab,
                        "live_data_used": r["live_data_used"], "live_asof": r["live_asof"],
                        "why_viable": r["why_viable"], "why_risky": r["why_risky"]},
            "verdict": code,
            "rationale": rationale,
        })

    # Truth governs ordering: reality first, astro as tiebreak.
    out.sort(key=lambda e: (e["reality"]["score"], e["astro"]["score"]), reverse=True)
    return out


DISCLAIMER = ("Dual reading: ASTRO is a classical ideation/timing signal; REALITY "
              "is an economics base-rate + 2026 conditions check. They are shown "
              "separately and never merged. This is NOT financial, investment, "
              "legal, or medical advice, and not a forecast of returns.")
