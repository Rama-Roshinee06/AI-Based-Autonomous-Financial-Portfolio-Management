"""Orchestrator: USER -> request fan-out -> message-driven agent loop -> result."""
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional
from agents.execution_agent import ExecutionAgent
from agents.market_agent import MarketAgent
from agents.news_agent import NewsAgent
from agents.portfolio_agent import PortfolioAgent
from agents.risk_agent import RiskAgent
from communication.message_bus import MessageBus
from communication.messages import Message
from data.fallback_data import SCENARIOS
from models.schemas import Decision, MarketReport, NewsReport, Order, PortfolioState, RiskReport

SYMBOL_RE = re.compile(r"^[A-Z0-9.\-^]{1,12}$")


@dataclass
class AnalysisResult:
    symbol: str
    scenario: Optional[str]
    market: Optional[MarketReport]
    news: Optional[NewsReport]
    risk: Optional[RiskReport]
    decision: Decision
    order: Order
    messages: List[dict]
    portfolio: dict
    latency_ms: float
    errors: dict = field(default_factory=dict)


class Orchestrator:
    def __init__(self, portfolio: Optional[PortfolioState] = None, use_live: bool = True):
        self.portfolio = portfolio or PortfolioState()
        self.use_live = use_live

    def analyse(self, symbol: str, scenario: Optional[str] = None, fail_agents=()) -> AnalysisResult:
        t0 = time.perf_counter()
        symbol = (symbol or "").strip().upper()
        if not SYMBOL_RE.match(symbol):
            raise ValueError(f"Invalid stock symbol: {symbol!r}")
        if scenario in (None, "", "None"):
            scenario = None
        elif scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")

        bus = MessageBus()
        bus.register("User")
        bus.register("Orchestrator")
        f = set(fail_agents)
        market, news = MarketAgent(bus, "Market Agent" in f), NewsAgent(bus, "News Agent" in f)
        risk, portfolio = RiskAgent(bus, "Risk Agent" in f), PortfolioAgent(bus)
        execution = ExecutionAgent(bus, self.portfolio, "Execution Agent" in f)
        agents = [market, news, risk, portfolio, execution]

        payload = {"symbol": symbol, "scenario": scenario, "use_live": self.use_live}
        bus.send(Message.create("User", "Orchestrator", "USER_REQUEST", payload))
        for m in bus.receive("Orchestrator"):          # orchestrator dispatches the work
            for a in (market, news, risk):
                bus.send(Message.create("Orchestrator", a.name, "ANALYSIS_REQUEST", m.payload))

        names = [a.name for a in agents]
        for _ in range(20):                            # run until the bus is quiet
            if not bus.pending(names):
                break
            for a in agents:
                a.step()

        conf = bus.receive("Orchestrator")
        order = Order(**conf[-1].payload) if conf else Order(symbol, "?", 0, None, "FAILED", "No confirmation")
        price_map = {symbol: market_price} if (market_price := (portfolio.market.price if portfolio.market else None)) else {}
        return AnalysisResult(symbol, scenario, portfolio.market, portfolio.news, portfolio.risk,
                              portfolio.decision, order, bus.log(), self.portfolio.snapshot(price_map),
                              round((time.perf_counter() - t0) * 1000, 2), dict(portfolio.errors))
