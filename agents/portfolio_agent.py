from agents.base_agent import BaseAgent
from algorithms.search import best_first_search
from algorithms.utility import UtilityInputs, confidence, disagreement
from communication.messages import Message
from models.schemas import Decision, MarketReport, NewsReport, RiskReport

EXPECTED = frozenset({"Market Agent", "News Agent", "Risk Agent"})


class PortfolioAgent(BaseAgent):
    name = "Portfolio Agent"
    agent_type = "Goal / Utility-based"
    goal = "Combine agent evidence and search for the best BUY/HOLD/SELL action"

    def __init__(self, bus, fail=False):
        super().__init__(bus, fail)
        self.market = self.news = self.risk = None
        self.errors, self.received, self.decision = {}, set(), None

    def handle(self, m: Message) -> None:
        p = m.payload
        if m.message_type == "MARKET_REPORT":
            self.market = MarketReport(**p)
        elif m.message_type == "NEWS_REPORT":
            self.news = NewsReport(**p)
        elif m.message_type == "RISK_REPORT":
            self.risk = RiskReport(**p)
        elif m.message_type == "AGENT_ERROR":
            self.errors[p["agent"]] = p["error"]
        else:
            return
        self.received.add(m.sender)
        if self.received >= EXPECTED and self.decision is None:
            self.decision = self.decide(self._symbol(), self.market, self.news, self.risk, self.errors)
            price = self.market.price if self.market else None
            self.send("Execution Agent", "ORDER_INSTRUCTION", {
                "symbol": self.decision.symbol, "action": self.decision.action, "price": price,
                "utility": self.decision.utility, "confidence": self.decision.confidence,
                "degraded": self.decision.degraded})

    def _symbol(self) -> str:
        for r in (self.market, self.news, self.risk):
            if r:
                return r.symbol
        return "UNKNOWN"

    def decide(self, symbol, market, news, risk, errors=None) -> Decision:
        """Fail-soft: a missing agent contributes a neutral default and lowers confidence."""
        missing = [n for n, r in (("Market Agent", market), ("News Agent", news), ("Risk Agent", risk)) if r is None]
        inp = UtilityInputs(market.market_score if market else 0.0,
                            news.sentiment_score if news else 0.0,
                            risk.risk_score if risk else 0.5).normalised()
        res = best_first_search(inp)
        conf = confidence({c.action: c.utility for c in res.candidates}, res.best_action)
        if missing:
            conf = round(conf * 0.5, 4)
        best = next(c for c in res.candidates if c.action == res.best_action)
        parts = [f"{res.best_action} selected (utility {best.utility:+.2f})."]
        if market:
            parts.append(f"Market {market.trend} (score {market.market_score:+.2f}) contributed {best.market_contribution:+.2f}.")
        if news:
            parts.append(f"News {news.sentiment} (score {news.sentiment_score:+.2f}) contributed {best.sentiment_contribution:+.2f}.")
        if risk:
            parts.append(f"Risk {risk.risk_level} (score {risk.risk_score:.2f}) added {best.risk_term:+.2f}.")
        if disagreement(inp) > 0.35:
            parts.append("Agents disagree, so the HOLD conflict bonus raised HOLD's utility.")
        if missing:
            parts.append(f"DEGRADED: {', '.join(missing)} unavailable, neutral default used, confidence halved.")
        parts.append(f"Best-First Search needed {res.term_evaluations}/{res.exhaustive_evaluations} term evaluations.")
        parts.append("AI-generated simulated recommendation - educational, not financial advice.")
        return Decision(symbol, res.best_action, best.utility, conf, " ".join(parts), res,
                        bool(missing), missing, {"market": inp.market_score, "sentiment": inp.sentiment_score,
                                                 "risk": inp.risk_score})
