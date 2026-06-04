"""The truth governor: compute a reality_score per channel.

reality_score is the FINANCE/ECONOMY layer (CLAUDE.md governing principle). It is
kept entirely separate from astro_score and must never reach into astrology.

It has two parts:
  - a STATIC base-rate component (kb/base_rates.py) — pure, offline, deterministic;
  - a LIVE 2026 component fetched at runtime through a LiveDataProvider interface.

CONTRACT #6: live data is fetched at runtime, never baked in. CONTRACT #2: the
base-rate component stays pure and offline-testable. The provider seam is what
keeps both true at once — tests inject a MockLiveDataProvider; the offline default
(NeutralProvider) returns no live data so the core runs without a network.

CONTRACT #3: every reality_score ships with why_viable / why_risky reasons.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from kb import base_rates as BR
from kb.channels import CHANNELS

# --- Tunables (ranking-oriented, not absolute truth) ------------------------
# Base-rate component weights (sum need not be 1; score is normalised then scaled).
W_SURVIVAL = 0.40    # weight on (1 - failure_rate)
W_SPEED = 0.20       # weight on getting to revenue quickly
W_CAPITAL = 0.25     # weight on capital accessibility (lower intensity = better)
W_MARGIN = 0.15      # weight on margin potential
TTR_HORIZON_MO = 36  # months past which time-to-revenue stops helping

# Live component: how much 2026 conditions move the score (in 0..100 points).
LIVE_DEMAND_SWING = 18.0   # full +/-1 demand trend moves score by this much
LIVE_SATURATION_PENALTY = 12.0  # full saturation (1.0) subtracts this much

_clamp01 = lambda x: max(0.0, min(1.0, x))
_clamp100 = lambda x: max(0.0, min(100.0, x))


# --- Live data provider interface -------------------------------------------

class LiveCondition:
    """A snapshot of 2026 conditions for one channel."""
    __slots__ = ("demand_trend", "saturation", "asof", "note", "source")

    def __init__(self, demand_trend=0.0, saturation=0.0, asof=None, note="", source=None):
        self.demand_trend = demand_trend  # -1 (declining) .. +1 (surging)
        self.saturation = saturation      # 0 (open) .. 1 (crowded)
        self.asof = asof                  # ISO date string or None if no live data
        self.note = note
        self.source = source

    @property
    def has_data(self) -> bool:
        return self.asof is not None


class LiveDataProvider(ABC):
    """Runtime source of 2026 conditions. Implementations may hit the web; the
    deterministic core never assumes one does."""

    @abstractmethod
    def get(self, channel_id: str) -> LiveCondition: ...


class NeutralProvider(LiveDataProvider):
    """Offline default: no live data. Keeps the core runnable without a network.
    reality_score then reflects base rates only and flags live_data_used=False."""

    def get(self, channel_id: str) -> LiveCondition:
        return LiveCondition(asof=None, note="no live 2026 data fetched (offline)")


class MockLiveDataProvider(LiveDataProvider):
    """Test double: returns canned conditions per channel; neutral-with-data
    for any channel not in the map (asof set so has_data is True)."""

    def __init__(self, conditions: Optional[dict[str, LiveCondition]] = None,
                 default_asof: str = "2026-01-01"):
        self._c = conditions or {}
        self._default_asof = default_asof

    def get(self, channel_id: str) -> LiveCondition:
        if channel_id in self._c:
            return self._c[channel_id]
        return LiveCondition(asof=self._default_asof, note="mock neutral")


# A live provider that fetches real 2026 data (web search / feeds) would live
# here. It is intentionally NOT implemented in the deterministic core so tests
# stay offline; wire it in at the runtime/report boundary.
#
#   class WebSearchLiveProvider(LiveDataProvider):
#       def get(self, channel_id): ...  # fetch + summarise -> LiveCondition


# --- Scoring ----------------------------------------------------------------

def _base_component(rec: dict) -> tuple[float, list[str], list[str]]:
    """Return (0..1 realism, why_viable, why_risky) from static base rates."""
    survival = 1.0 - rec["failure_rate_5yr"]
    speed = _clamp01(1.0 - rec["time_to_revenue_mo"] / TTR_HORIZON_MO)
    capital_access = 1.0 - rec["capital_intensity"]
    margin = rec["margin_potential"]

    realism = (W_SURVIVAL * survival + W_SPEED * speed
               + W_CAPITAL * capital_access + W_MARGIN * margin)
    realism /= (W_SURVIVAL + W_SPEED + W_CAPITAL + W_MARGIN)

    why_viable, why_risky = [], []
    (why_viable if survival >= 0.5 else why_risky).append(
        f"~{round(rec['failure_rate_5yr']*100)}% 5-yr failure base rate")
    (why_viable if speed >= 0.5 else why_risky).append(
        f"~{rec['time_to_revenue_mo']}mo to first revenue")
    (why_viable if capital_access >= 0.5 else why_risky).append(
        f"capital: {rec['capital_note']}")
    (why_viable if margin >= 0.55 else why_risky).append(
        f"margin potential {round(margin*100)}%")
    return _clamp01(realism), why_viable, why_risky


def reality_for_channel(channel_id: str, provider: LiveDataProvider) -> dict:
    rec = BR.get(channel_id)
    realism, why_viable, why_risky = _base_component(rec)
    score = realism * 100.0

    live = provider.get(channel_id)
    live_used = live.has_data
    if live_used:
        delta = LIVE_DEMAND_SWING * live.demand_trend - LIVE_SATURATION_PENALTY * live.saturation
        score = _clamp100(score + delta)
        if live.demand_trend > 0.05:
            why_viable.append(f"2026 demand trending up (+{live.demand_trend:.2f}){_src(live)}")
        elif live.demand_trend < -0.05:
            why_risky.append(f"2026 demand trending down ({live.demand_trend:.2f}){_src(live)}")
        if live.saturation >= 0.6:
            why_risky.append(f"market crowded (saturation {live.saturation:.2f}){_src(live)}")
        if live.note:
            (why_viable if live.demand_trend >= 0 else why_risky).append(live.note)

    return {
        "id": channel_id,
        "reality_score": round(_clamp100(score), 1),
        "base_realism": round(realism, 4),
        "live_data_used": live_used,
        "live_asof": live.asof,
        "why_viable": why_viable,
        "why_risky": why_risky,
    }


def _src(live: LiveCondition) -> str:
    return f" [src: {live.source}]" if live.source else ""


def reality_for_all(provider: LiveDataProvider) -> dict[str, dict]:
    """Compute reality results for every channel, keyed by id."""
    return {c.id: reality_for_channel(c.id, provider) for c in CHANNELS}
