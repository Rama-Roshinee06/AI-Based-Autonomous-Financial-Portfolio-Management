from orchestration.orchestrator import Orchestrator
from models.schemas import PortfolioState


def _run(sc, **kw):
    return Orchestrator(use_live=False).analyse("AAPL", sc, **kw)


def test_four_scenarios_expected_decisions():
    assert _run("Bullish").decision.action == "BUY"
    assert _run("Neutral").decision.action == "HOLD"
    assert _run("Bearish").decision.action == "SELL"
    assert _run("Conflicting").decision.action in ("HOLD", "SELL")


def test_offline_mode_is_labelled_demo_and_complete():
    r = Orchestrator(use_live=False).analyse("NVDA")
    assert r.market.source == r.news.source == r.risk.source == "DEMO"
    assert r.order.banner == "SIMULATION — NO REAL TRADING"
    assert "simulated recommendation" in r.decision.explanation


def test_portfolio_persists_across_runs():
    o = Orchestrator(PortfolioState(), use_live=False)
    b = o.analyse("AAPL", "Bullish")
    assert b.order.status == "SUCCESS" and o.portfolio.holdings["AAPL"] == b.order.quantity
    s = o.analyse("AAPL", "Bearish")
    assert s.order.action == "SELL" and s.order.status == "SUCCESS"
    assert len(o.portfolio.history) == 2


def test_agent_failure_degrades_gracefully():
    r = _run("Bullish", fail_agents=["News Agent"])
    assert r.decision.degraded and "News Agent" in r.errors and r.news is None
    assert r.order.status in ("SUCCESS", "NO_ACTION", "SKIPPED")
    assert r.decision.confidence <= 0.5


def test_execution_failure_reported():
    r = _run("Bullish", fail_agents=["Execution Agent"])
    assert r.order.status == "FAILED"


def test_invalid_inputs_rejected():
    for bad, sc in [("", None), ("DROP TABLE", None), ("AAPL", "Nonexistent")]:
        try:
            Orchestrator(use_live=False).analyse(bad, sc)
        except ValueError:
            continue
        assert False, (bad, sc)


def test_conflicting_scenario_resolves_disagreement():
    r = _run("Conflicting")
    assert r.market.trend == "UP" and r.news.sentiment == "NEGATIVE" and r.risk.risk_level == "HIGH"
    assert "disagree" in r.decision.explanation
