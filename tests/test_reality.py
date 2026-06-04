"""Reality-check engine tests, using the mock live-data provider.

Verifies: base-rate component is pure & bounded; the live layer moves the score
in the right direction; the live_data_used flag is honest; and every channel is
covered.
"""

from kb import base_rates as BR
from kb.channels import CHANNELS
import reality_check as RC


def test_base_rates_cover_all_channels_and_are_in_range():
    for ch in CHANNELS:
        rec = BR.get(ch.id)
        assert 0.0 <= rec["failure_rate_5yr"] <= 1.0
        assert rec["time_to_revenue_mo"] >= 0
        assert 0.0 <= rec["capital_intensity"] <= 1.0
        assert 0.0 <= rec["margin_potential"] <= 1.0


def test_neutral_provider_means_no_live_data():
    res = RC.reality_for_channel("consulting", RC.NeutralProvider())
    assert res["live_data_used"] is False
    assert res["live_asof"] is None
    assert 0.0 <= res["reality_score"] <= 100.0


def test_reality_is_deterministic_offline():
    a = RC.reality_for_all(RC.NeutralProvider())
    b = RC.reality_for_all(RC.NeutralProvider())
    assert {k: v["reality_score"] for k, v in a.items()} == \
           {k: v["reality_score"] for k, v in b.items()}


def test_low_capital_service_beats_capital_heavy_on_base_rates():
    # consulting (low capital, low failure) should out-score real estate &
    # hospitality on pure base rates (no live data).
    res = RC.reality_for_all(RC.NeutralProvider())
    assert res["consulting"]["reality_score"] > res["hospitality"]["reality_score"]
    assert res["consulting"]["reality_score"] > res["realestate"]["reality_score"]


def test_live_demand_moves_score_in_the_right_direction():
    base = RC.reality_for_channel("saas", RC.NeutralProvider())["reality_score"]
    up = RC.MockLiveDataProvider({"saas": RC.LiveCondition(
        demand_trend=0.8, saturation=0.0, asof="2026-02-01", source="mock")})
    down = RC.MockLiveDataProvider({"saas": RC.LiveCondition(
        demand_trend=-0.8, saturation=0.0, asof="2026-02-01", source="mock")})
    up_score = RC.reality_for_channel("saas", up)["reality_score"]
    down_score = RC.reality_for_channel("saas", down)["reality_score"]
    assert up_score > base > down_score
    assert RC.reality_for_channel("saas", up)["live_data_used"] is True


def test_saturation_penalises_and_is_surfaced():
    crowded = RC.MockLiveDataProvider({"affiliate": RC.LiveCondition(
        demand_trend=0.0, saturation=0.9, asof="2026-02-01", source="mock")})
    res = RC.reality_for_channel("affiliate", crowded)
    base = RC.reality_for_channel("affiliate", RC.NeutralProvider())["reality_score"]
    assert res["reality_score"] < base
    assert any("saturation" in w for w in res["why_risky"])
