"""One orchestration seam shared by the CLI (run.py) and the UI (app.py).

Pure composition of the existing layers — no I/O of its own, no Streamlit, no
network unless the caller passes a live provider. Keeps run.py and app.py from
drifting apart and stays unit-testable.
"""

from __future__ import annotations

from typing import NamedTuple, Optional

from engine.chart import compute_chart, ChartFact
from signals import compute_signals
from scoring import score_all
from reality_check import reality_for_all, NeutralProvider, LiveDataProvider
from reconcile import reconcile
from report import generate_report, generate_finance_analysis


class Analysis(NamedTuple):
    chart: ChartFact
    signals: dict
    scores: list
    advice: list
    report_md: Optional[str]        # the Jyotishi (astrology) reading
    finance_md: Optional[str]       # the Finance Analyst (economics) brief


def analyze(birth, provider: Optional[LiveDataProvider] = None,
            with_report: bool = False, report_client=None) -> Analysis:
    """Run the full pipeline. `provider` defaults to offline NeutralProvider.

    When with_report is set, BOTH agents run: the Jyotishi (astrology reading) and
    the Finance Analyst (economics brief) — two separate voices, never merged.
    """
    provider = provider or NeutralProvider()
    chart = compute_chart(birth)
    signals = compute_signals(chart)
    scores = score_all(signals)
    reality = reality_for_all(provider)
    advice = reconcile(scores, reality)
    report_md = finance_md = None
    if with_report:
        report_md = generate_report(chart, signals, advice, client=report_client)
        finance_md = generate_finance_analysis(advice, client=report_client)
    return Analysis(chart, signals, scores, advice, report_md, finance_md)
