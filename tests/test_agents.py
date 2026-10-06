from agents.execution_agent import ExecutionAgent
from agents.market_agent import MarketAgent
from agents.news_agent import NewsAgent
from agents.portfolio_agent import PortfolioAgent
from agents.risk_agent import RiskAgent
from communication.message_bus import MessageBus
from models.schemas import PortfolioState


def test_market_agent_trends_and_demo_label():
    a = MarketAgent(MessageBus())
    up, dn = a.analyse("AAPL", "Bullish", False), a.analyse("AAPL", "Bearish", False)
    st = a.analyse("AAPL", "Neutral", False)
    assert (up.trend, dn.trend, st.trend) == ("UP", "DOWN", "STABLE")
    assert up.source == "DEMO" and -1 <= dn.market_score < 0 < up.market_score <= 1
    assert up.price == 218.5


def test_market_agent_deterministic():
    a = MarketAgent(MessageBus())
    assert a.analyse("MSFT", None, False).prices == a.analyse("MSFT", None, False).prices


def test_news_agent_sentiment():
    a = NewsAgent(MessageBus())
    pos, neu, neg = (a.analyse("AAPL", s, False) for s in ("Bullish", "Neutral", "Bearish"))
    assert (pos.sentiment, neu.sentiment, neg.sentiment) == ("POSITIVE", "NEUTRAL", "NEGATIVE")
    assert 3 <= len(pos.headlines) <= 5 and pos.source == "DEMO"


def test_risk_agent_levels():
    a = RiskAgent(MessageBus())
    lo, mid, hi = (a.analyse("AAPL", s, False) for s in ("Bullish", "Neutral", "Bearish"))
    assert (lo.risk_level, mid.risk_level, hi.risk_level) == ("LOW", "MEDIUM", "HIGH")
    assert lo.volatility < mid.volatility < hi.volatility and 0 <= hi.risk_score <= 1


def _decide(scn):
    bus = MessageBus()
    return PortfolioAgent(bus).decide("AAPL", MarketAgent(bus).analyse("AAPL", scn, False),
                                      NewsAgent(bus).analyse("AAPL", scn, False),
                                      RiskAgent(bus).analyse("AAPL", scn, False))


def test_portfolio_agent_scenarios():
    assert _decide("Bullish").action == "BUY"
    assert _decide("Neutral").action == "HOLD"
    assert _decide("Bearish").action == "SELL"
    assert _decide("Conflicting").action in ("HOLD", "SELL")


def test_portfolio_agent_degraded_mode():
    bus = MessageBus()
    d = PortfolioAgent(bus).decide("AAPL", None, None, None)
    assert d.degraded and len(d.missing_agents) == 3 and d.confidence <= 0.5


def test_execution_agent_buy_sell_hold_reject():
    s = PortfolioState()
    ex = ExecutionAgent(MessageBus(), s)
    o = ex.execute("AAPL", "BUY", 218.5)
    assert o.status == "SUCCESS" and o.quantity == 4 and s.holdings["AAPL"] == 4
    assert s.balance == round(10000 - 4 * 218.5, 2)
    assert ex.execute("AAPL", "HOLD", 218.5).status == "NO_ACTION"
    o = ex.execute("AAPL", "SELL", 220.0)
    assert o.status == "SUCCESS" and o.quantity == 2 and s.holdings["AAPL"] == 2
    assert ex.execute("TSLA", "SELL", 200.0).status == "SKIPPED"
    assert ex.execute("AAPL", "BUY", None).status == "REJECTED"
    poor = ExecutionAgent(MessageBus(), PortfolioState(balance=10.0))
    assert poor.execute("AAPL", "BUY", 218.5).status == "REJECTED"
    assert len(s.history) == 5  # BUY, HOLD, SELL, SKIPPED, REJECTED
