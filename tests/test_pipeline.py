"""Pipeline seam tests — the shared analyze() used by both CLI and UI."""

from pipeline import analyze
from reality_check import NeutralProvider, MockLiveDataProvider, LiveCondition

BIRTH = {"name": "T", "date": "1992-03-21", "time": "06:45",
         "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"}


def test_analyze_offline_produces_advice_for_all_channels():
    from kb.channels import CHANNELS
    res = analyze(BIRTH)
    assert len(res.advice) == len(res.scores) == len(CHANNELS)
    assert res.report_md is None  # not requested
    # every advice entry carries two separate scores
    for e in res.advice:
        assert "score" in e["astro"] and "score" in e["reality"]


def test_analyze_with_report_returns_markdown():
    res = analyze(BIRTH, with_report=True)
    assert res.report_md and "AstroFinance reading" in res.report_md


def test_analyze_respects_injected_live_provider():
    mock = MockLiveDataProvider({"saas": LiveCondition(
        demand_trend=0.9, saturation=0.0, asof="2026-01-01", source="mock")})
    res = analyze(BIRTH, provider=mock)
    saas = next(e for e in res.advice if e["id"] == "saas")
    assert saas["reality"]["live_data_used"] is True
