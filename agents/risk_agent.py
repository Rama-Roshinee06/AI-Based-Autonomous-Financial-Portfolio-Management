import math
import statistics
from agents.base_agent import AnalysisAgent
from algorithms.utility import clamp
from data.market_data import get_price_history
from models.schemas import RiskReport


class RiskAgent(AnalysisAgent):
    name = "Risk Agent"
    agent_type = "Analytical / Model-based (volatility model)"
    goal = "Quantify downside/uncertainty risk"
    report_type = "RISK_REPORT"
    VOL_CAP, LOW, HIGH = 60.0, 0.35, 0.65   # 60% annualised vol -> risk score 1.0

    def analyse(self, symbol, scenario=None, use_live=True) -> RiskReport:
        h = get_price_history(symbol, scenario, use_live)
        p = h.prices
        rets = [p[i] / p[i - 1] - 1 for i in range(1, len(p))]
        vol = statistics.stdev(rets) * math.sqrt(252) * 100
        peak, dd = p[0], 0.0
        for x in p:
            peak = max(peak, x)
            dd = max(dd, (peak - x) / peak * 100)
        score = round(clamp(vol / self.VOL_CAP, 0, 1), 3)
        level = "LOW" if score < self.LOW else "MEDIUM" if score < self.HIGH else "HIGH"
        return RiskReport(symbol, round(vol, 2), round(dd, 2), score, level, h.source)
