"""Live-data provider tests — pure helpers only (no network).

Covers JSON extraction/parsing with clamping, daily cache round-trip and
staleness, lazy fetch via an injected fake client, and graceful degradation when
the network/client errors.
"""

import json

import live_data as LD
from reality_check import LiveCondition


VALID = {"saas", "consulting", "crypto"}


def test_parse_clamps_and_filters_unknown_ids():
    text = ('garbage before [\n'
            '  {"id":"saas","demand_trend":2.0,"saturation":-0.5,"note":"hot","source":"x"},\n'
            '  {"id":"consulting","demand_trend":-0.3,"saturation":0.4},\n'
            '  {"id":"not_a_channel","demand_trend":0.1,"saturation":0.1}\n'
            '] trailing text')
    out = LD.parse_live_response(text, VALID, asof="2026-06-04")
    assert set(out) == {"saas", "consulting"}        # unknown id dropped
    assert out["saas"].demand_trend == 1.0           # clamped from 2.0
    assert out["saas"].saturation == 0.0             # clamped from -0.5
    assert out["saas"].asof == "2026-06-04"
    assert out["consulting"].source == "web_search"  # default applied


def test_extract_json_array_raises_on_missing():
    import pytest
    with pytest.raises(ValueError):
        LD._extract_json_array("no array here")


def test_build_prompt_lists_every_channel():
    from kb.channels import CHANNELS
    prompt = LD.build_live_prompt()
    assert "JSON array" in prompt
    for c in CHANNELS:
        assert c.id in prompt


def test_cache_roundtrip_and_staleness(tmp_path):
    cache = tmp_path / "live_cache.json"
    p = LD.WebSearchLiveProvider(cache_path=cache, asof="2026-06-04")
    conds = {"saas": LiveCondition(0.5, 0.2, "2026-06-04", "n", "src")}
    p._save_cache(conds)
    # fresh load (same asof) returns the cached condition
    loaded = LD.WebSearchLiveProvider(cache_path=cache, asof="2026-06-04")._load_cache()
    assert loaded["saas"].demand_trend == 0.5
    # different day -> stale -> ignored
    stale = LD.WebSearchLiveProvider(cache_path=cache, asof="2026-06-05")._load_cache()
    assert stale is None


class _FakeBlock:
    type = "text"
    def __init__(self, text): self.text = text


class _FakeMsg:
    def __init__(self, text): self.content = [_FakeBlock(text)]


class _FakeClient:
    def __init__(self, text): self._text = text; self.messages = self
    def create(self, **kw): return _FakeMsg(self._text)


def test_lazy_fetch_with_injected_client(tmp_path):
    text = '[{"id":"saas","demand_trend":0.6,"saturation":0.3,"note":"AI tailwind","source":"q"}]'
    p = LD.WebSearchLiveProvider(client=_FakeClient(text),
                                 cache_path=tmp_path / "c.json", asof="2026-06-04")
    cond = p.get("saas")
    assert cond.has_data and cond.demand_trend == 0.6
    # a channel the model didn't return -> graceful no-data fallback
    assert p.get("crypto").has_data is False


def test_graceful_when_client_errors(tmp_path):
    class Boom:
        def __init__(self): self.messages = self
        def create(self, **kw): raise RuntimeError("network down")
    p = LD.WebSearchLiveProvider(client=Boom(), cache_path=tmp_path / "c.json",
                                 asof="2026-06-04")
    cond = p.get("saas")
    assert cond.has_data is False  # degraded to base-rates-only, no crash
