"""Real live-2026 data provider (the only network-touching piece).

Implements reality_check.LiveDataProvider by asking Claude (with the web_search
tool) to research current 2026 demand/saturation per earning channel, returning
structured LiveCondition objects.

Design guards:
  - CONTRACT #6: live data is fetched at runtime, here, never baked in.
  - CONTRACT #2: this module is OUTSIDE the deterministic core. The core
    (engine/signals/scoring/reality base-rates/reconcile) never imports it; it is
    injected only at the runtime boundary (run.py). Tests use mocks.
  - Graceful degradation: any failure (no SDK, no key, network/parse error) makes
    a channel return a no-data LiveCondition, so reality_check simply falls back
    to base-rates-only. The tool never crashes for lack of live data.
  - Caching: one batched web call for all channels, cached to disk per day, so
    repeated runs don't re-bill or hammer the network.

The pure helpers (prompt build, JSON extraction/parse, cache I/O) are unit-tested
offline; the network call itself is not.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

from reality_check import LiveCondition, LiveDataProvider, NeutralProvider
from kb.channels import CHANNELS

DEFAULT_MODEL = os.environ.get("ASTRO_LIVE_MODEL", "claude-sonnet-4-6")
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8}
DEFAULT_CACHE = Path("out/live_cache.json")
_clamp = lambda lo, hi, x: max(lo, min(hi, x))


def build_live_prompt(channels=CHANNELS) -> str:
    lines = [
        "Research CURRENT (2026) market conditions for each earning channel below.",
        "For each, judge the present demand trajectory and how crowded the market is.",
        "Use web search for up-to-date 2026 signals; do not rely on memory alone.",
        "",
        "Return ONLY a JSON array (no prose, no markdown fence). One object per channel:",
        '  {"id": <channel id>, "demand_trend": <-1.0..1.0>, '
        '"saturation": <0.0..1.0>, "note": <≤140 chars>, "source": <one short url or outlet>}',
        "demand_trend: -1 strongly declining, 0 flat, +1 strongly surging.",
        "saturation: 0 wide open, 1 extremely crowded.",
        "",
        "Channels:",
    ]
    for c in channels:
        lines.append(f"  - {c.id}: {c.name} — {c.description}")
    return "\n".join(lines)


def _extract_json_array(text: str) -> list:
    """Pull the first top-level JSON array out of a model response."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found in response")
    return json.loads(text[start:end + 1])


def parse_live_response(text: str, valid_ids: set[str], asof: str,
                        source_default: str = "web_search") -> dict[str, LiveCondition]:
    """Parse the model's JSON into validated, clamped LiveConditions by channel id."""
    out: dict[str, LiveCondition] = {}
    for row in _extract_json_array(text):
        cid = row.get("id")
        if cid not in valid_ids:
            continue
        out[cid] = LiveCondition(
            demand_trend=_clamp(-1.0, 1.0, float(row.get("demand_trend", 0.0))),
            saturation=_clamp(0.0, 1.0, float(row.get("saturation", 0.0))),
            asof=asof,
            note=str(row.get("note", ""))[:140],
            source=row.get("source") or source_default,
        )
    return out


def _collect_text(message) -> str:
    """Concatenate text blocks from an Anthropic Messages response."""
    parts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts)


class WebSearchLiveProvider(LiveDataProvider):
    """Fetches 2026 conditions via Claude + web_search, with daily disk caching.

    Lazily fetches all channels on first .get(); falls back to no-data conditions
    on any error so reality_check keeps working on base rates alone.
    """

    def __init__(self, client=None, model: str = DEFAULT_MODEL,
                 cache_path: Path = DEFAULT_CACHE, asof: Optional[str] = None,
                 use_cache: bool = True):
        self._client = client
        self._model = model
        self._cache_path = Path(cache_path)
        self._asof = asof or date.today().isoformat()
        self._use_cache = use_cache
        self._conditions: Optional[dict[str, LiveCondition]] = None
        self._fallback = NeutralProvider()

    # --- caching ---
    def _load_cache(self) -> Optional[dict[str, LiveCondition]]:
        if not (self._use_cache and self._cache_path.exists()):
            return None
        try:
            blob = json.loads(self._cache_path.read_text())
            if blob.get("asof") != self._asof:
                return None  # stale: refetch for a new day
            return {cid: LiveCondition(**c) for cid, c in blob["conditions"].items()}
        except Exception:
            return None

    def _save_cache(self, conditions: dict[str, LiveCondition]) -> None:
        if not self._use_cache:
            return
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        blob = {"asof": self._asof, "conditions": {
            cid: {"demand_trend": c.demand_trend, "saturation": c.saturation,
                  "asof": c.asof, "note": c.note, "source": c.source}
            for cid, c in conditions.items()}}
        self._cache_path.write_text(json.dumps(blob, indent=2))

    # --- network ---
    def _make_client(self):
        if self._client is not None:
            return self._client
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        import anthropic
        self._client = anthropic.Anthropic()
        return self._client

    def _fetch(self) -> dict[str, LiveCondition]:
        client = self._make_client()
        msg = client.messages.create(
            model=self._model,
            max_tokens=2000,
            tools=[WEB_SEARCH_TOOL],
            messages=[{"role": "user", "content": build_live_prompt()}],
        )
        valid = {c.id for c in CHANNELS}
        return parse_live_response(_collect_text(msg), valid, self._asof)

    def _ensure(self) -> dict[str, LiveCondition]:
        if self._conditions is not None:
            return self._conditions
        cached = self._load_cache()
        if cached is not None:
            self._conditions = cached
            return cached
        try:
            self._conditions = self._fetch()
            self._save_cache(self._conditions)
        except Exception as e:  # graceful: degrade to no-live-data
            print(f"[live_data] live fetch unavailable ({e}); using base rates only.")
            self._conditions = {}
        return self._conditions

    def get(self, channel_id: str) -> LiveCondition:
        cond = self._ensure().get(channel_id)
        return cond if cond is not None else self._fallback.get(channel_id)
