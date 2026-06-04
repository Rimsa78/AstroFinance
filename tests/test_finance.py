"""Finance knowledge base + Finance Analyst agent (offline).

Covers: economics corpus completeness/parity with channels, the deterministic
finance brief, the analyst prompt assembly, and the no-promises / independence
guardrails in the persona.
"""

from kb.channels import CHANNELS
from kb import finance_knowledge as FK
from pipeline import analyze
from reality_check import NeutralProvider, reality_for_all
from reconcile import reconcile
from scoring import score_all
from signals import compute_signals
from engine.chart import compute_chart
import report as R

BIRTH = {"name": "T", "date": "1998-05-19", "time": "16:10",
         "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"}


def _advice():
    chart = compute_chart(BIRTH)
    signals = compute_signals(chart)
    return reconcile(score_all(signals), reality_for_all(NeutralProvider()))


def test_every_channel_has_economics():
    for ch in CHANNELS:
        assert ch.id in FK.CHANNEL_ECONOMICS, f"missing economics for {ch.id}"
        eco = FK.CHANNEL_ECONOMICS[ch.id]
        for field in ("model", "main_cost", "key_risk", "good"):
            assert eco[field], f"{ch.id} economics missing {field}"


def test_principles_and_macro_are_cited():
    for d in (FK.GENERAL_PRINCIPLES, FK.MACRO_CONTEXT):
        for k, v in d.items():
            assert v["note"] and v["ref"], f"{k} not cited"


def test_finance_for_channels_selects_top():
    advice = _advice()
    fk = FK.finance_for_channels(advice, top=5)
    assert len(fk["channels"]) <= 5
    assert fk["principles"] and fk["macro_context"]
    assert "not promise returns" in fk["note"].lower() or "promise" in fk["note"].lower()


def test_deterministic_finance_brief_is_useful_and_safe():
    advice = _advice()
    brief = R.deterministic_finance_brief(advice)
    assert "Finance Analyst" in brief
    assert "not financial" in brief.lower()
    assert advice[0]["name"] in brief


class _FakeBlock:
    type = "text"
    def __init__(self, t): self.text = t


class _FakeMsg:
    def __init__(self, t): self.content = [_FakeBlock(t)]


class _FakeClient:
    def __init__(self): self.messages = self
    def create(self, **kw):
        self.kw = kw
        return _FakeMsg("# Finance brief\nBase rates govern; no promises.")


def test_finance_agent_persona_is_independent_and_no_promises():
    advice = _advice()
    fake = _FakeClient()
    out = R.generate_finance_analysis(advice, client=fake)
    assert "Finance brief" in out
    sysp = fake.kw["system"]
    assert "NOT an astrologer" in sysp
    assert "NEVER promise" in sysp
    # the chart is explicitly not the analyst's evidence
    assert "not your evidence" in sysp.lower() or "not your evidence" in fake.kw["messages"][0]["content"].lower()


def test_pipeline_runs_both_agents():
    res = analyze(BIRTH, with_report=True)
    assert res.report_md and "AstroFinance reading" in res.report_md     # Jyotishi fallback
    assert res.finance_md and "Finance Analyst" in res.finance_md         # analyst fallback
