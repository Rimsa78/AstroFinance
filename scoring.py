"""signals x channels -> ranked astro_score with full traceability.

This is the ASTROLOGY score only -- a hypothesis/ideation signal, NOT a forecast
and NOT a reality check (see the governing principle in CLAUDE.md). The reality
governor is Phase B; this module must never reach into economics.

CONTRACT #3: no score ships without the exact signals + reasons that produced it.
Tune via BASE / SUPPORT_WEIGHT / WARN_WEIGHT; ordering is what matters, not the
absolute number.
"""

from __future__ import annotations

from kb.channels import CHANNELS, Channel

BASE = 50.0           # neutral midpoint on a 0..100 readability scale
SUPPORT_WEIGHT = 50.0  # how much fully-present supports lift the score
WARN_WEIGHT = 40.0     # how much fully-present warnings cut it
PRESENT = 0.5          # value above which a support is worth surfacing in why_fits

_clamp100 = lambda x: max(0.0, min(100.0, x))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def score_channel(channel: Channel, signals: dict[str, dict]) -> dict:
    support_detail, warn_detail = [], []
    for name in channel.astro_support:
        s = signals.get(name)
        if s is None:
            continue
        support_detail.append({"signal": name, "value": s["value"], "why": s["why"],
                               "classical_ref": s["classical_ref"], "school": s["school"]})
    for name in channel.astro_warn:
        s = signals.get(name)
        if s is None:
            continue
        warn_detail.append({"signal": name, "value": s["value"], "why": s["why"],
                            "classical_ref": s["classical_ref"], "school": s["school"]})

    support_mean = _mean([d["value"] for d in support_detail])
    warn_mean = _mean([d["value"] for d in warn_detail])
    astro_score = _clamp100(BASE + SUPPORT_WEIGHT * support_mean - WARN_WEIGHT * warn_mean)

    why_fits = sorted([d for d in support_detail if d["value"] >= PRESENT],
                      key=lambda d: d["value"], reverse=True)
    why_caution = sorted([d for d in warn_detail if d["value"] > 0.0],
                         key=lambda d: d["value"], reverse=True)

    return {
        "id": channel.id,
        "name": channel.name,
        "description": channel.description,
        "astro_score": round(astro_score, 1),
        "support_mean": round(support_mean, 4),
        "warn_mean": round(warn_mean, 4),
        "why_fits": why_fits,
        "why_caution": why_caution,
    }


def score_all(signals: dict[str, dict]) -> list[dict]:
    """Score every channel and return them ranked by astro_score, descending.

    Note (governing principle): astro_score is an IDEATION/timing signal only.
    It is reconciled against the reality governor in Phase B; never present this
    as a forecast of returns.
    """
    scored = [score_channel(c, signals) for c in CHANNELS]
    scored.sort(key=lambda r: r["astro_score"], reverse=True)
    return scored
