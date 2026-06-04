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
from report import generate_report


class Analysis(NamedTuple):
    chart: ChartFact
    signals: dict
    scores: list
    advice: list
    report_md: Optional[str]


def analyze(birth, provider: Optional[LiveDataProvider] = None,
            with_report: bool = False, report_client=None) -> Analysis:
    """Run the full pipeline. `provider` defaults to offline NeutralProvider."""
    provider = provider or NeutralProvider()
    chart = compute_chart(birth)
    signals = compute_signals(chart)
    scores = score_all(signals)
    reality = reality_for_all(provider)
    advice = reconcile(scores, reality)
    report_md = (generate_report(chart, signals, advice, client=report_client)
                 if with_report else None)
    return Analysis(chart, signals, scores, advice, report_md)
