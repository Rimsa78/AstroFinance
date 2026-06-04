"""Report tests — the deterministic (offline) report and the fact bundle.

The LLM path is not exercised (no network); we test that the offline report is
useful, keeps the two scores separate, and carries the disclaimer, and that
generate_report() falls back to it with no client/key. A fake client verifies the
LLM path is wired without hitting the network.
"""

import os

from engine.chart import compute_chart
from signals import compute_signals
from scoring import score_all
from reality_check import reality_for_all, NeutralProvider
from reconcile import reconcile
import report as R

BIRTH = {"name": "T", "date": "1992-03-21", "time": "06:45",
         "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"}


def _pipeline():
    chart = compute_chart(BIRTH)
    signals = compute_signals(chart)
    advice = reconcile(score_all(signals), reality_for_all(NeutralProvider()))
    return chart, signals, advice


def test_deterministic_report_has_disclaimer_and_both_scores():
    chart, signals, advice = _pipeline()
    md = R.deterministic_report(chart, signals, advice)
    assert "not financial" in md.lower()
    assert "ASTRO" in md and "REALITY" in md
    # the top channel name appears
    assert advice[0]["name"] in md


def test_deterministic_report_never_prints_a_merged_score():
    chart, signals, advice = _pipeline()
    md = R.deterministic_report(chart, signals, advice).lower()
    for forbidden in ("combined score", "blended score", "overall score", "total score"):
        assert forbidden not in md


def test_build_facts_is_interpret_only_payload():
    chart, signals, advice = _pipeline()
    facts = R.build_facts(chart, signals, advice, top=5)
    assert facts["rules"]["two_scores_never_merged"] is True
    assert facts["chart"]["ascendant"]["sign"] == chart.ascendant.sign_name
    assert len(facts["advice_top"]) == 5
    # no raw longitudes leak into the LLM payload (interpret-only summary)
    assert "julian_day_ut" not in str(facts["chart"])


def test_generate_report_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    chart, signals, advice = _pipeline()
    out = R.generate_report(chart, signals, advice)
    assert "AstroFinance reading" in out  # deterministic header


class _FakeBlock:
    type = "text"
    def __init__(self, text): self.text = text


class _FakeMsg:
    def __init__(self, text): self.content = [_FakeBlock(text)]


class _FakeClient:
    def __init__(self): self.messages = self
    def create(self, **kw):
        self.kw = kw
        return _FakeMsg("# Fake LLM report\nASTRO and REALITY kept separate.")


def test_generate_report_uses_client_when_provided():
    chart, signals, advice = _pipeline()
    fake = _FakeClient()
    out = R.generate_report(chart, signals, advice, client=fake)
    assert "Fake LLM report" in out
    # the system prompt establishes the Jyotishi persona + interpret-only + separation
    sysp = fake.kw["system"]
    assert "Jyotishi" in sysp or "Jyotirvid" in sysp
    assert "Interpret ONLY" in sysp
    assert "NEVER invent" in sysp
    assert "Never merge" in sysp
    # the user turn carries the full computed facts and the multi-section outline
    user_msg = fake.kw["messages"][0]["content"]
    assert "Graha by graha" in user_msg
    assert chart.ascendant.sign_name in user_msg
