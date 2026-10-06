import math
from agents.base_agent import AnalysisAgent
from data.market_data import get_price_history
from models.schemas import MarketReport


class MarketAgent(AnalysisAgent):
    name = "Market Agent"
    agent_type = "Reactive / Information-processing"
    goal = "Turn recent prices into a normalised market score"
    report_type = "MARKET_REPORT"
    UP, DOWN, SCALE = 3.0, -3.0, 8.0   # trend thresholds (%), tanh scale

    def analyse(self, symbol, scenario=None, use_live=True) -> MarketReport:
        h = get_price_history(symbol, scenario, use_live)
        p = h.prices
        momentum = (p[-1] / p[0] - 1) * 100
        day = (p[-1] / p[-2] - 1) * 100
        trend = "UP" if momentum > self.UP else "DOWN" if momentum < self.DOWN else "STABLE"
        return MarketReport(symbol, round(p[-1], 2), round(day, 2), round(momentum, 2), trend,
                            round(math.tanh(momentum / self.SCALE), 3), h.source, p)
