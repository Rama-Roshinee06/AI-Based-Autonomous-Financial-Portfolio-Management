from agents.base_agent import AnalysisAgent
from algorithms.sentiment import ANALYZER, analyse_headlines
from data.market_data import get_news
from models.schemas import NewsReport


class NewsAgent(AnalysisAgent):
    name = "News Agent"
    agent_type = "Model-based (sentiment lexicon model)"
    goal = "Estimate news sentiment for the stock"
    report_type = "NEWS_REPORT"

    def analyse(self, symbol, scenario=None, use_live=True) -> NewsReport:
        headlines, source = get_news(symbol, scenario, use_live)
        scores, avg, label = analyse_headlines(headlines)
        return NewsReport(symbol, headlines, scores, label, avg, source, ANALYZER)
