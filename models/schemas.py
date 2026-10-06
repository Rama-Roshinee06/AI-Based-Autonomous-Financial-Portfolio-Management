"""Typed data models shared by all agents (stdlib dataclasses, no extra deps)."""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

SIM_BANNER = "SIMULATION — NO REAL TRADING"


class _Payload:
    def to_payload(self) -> dict:
        d = asdict(self)
        d.pop("prices", None)  # keep messages small; prices stay in the result object
        return d


@dataclass
class MarketReport(_Payload):
    symbol: str
    price: float
    pct_change: float          # last-day % change
    momentum_pct: float        # % change over the look-back window
    trend: str                 # UP / STABLE / DOWN
    market_score: float        # normalised to [-1, 1]
    source: str                # LIVE / DEMO
    prices: List[float] = field(default_factory=list)


@dataclass
class NewsReport(_Payload):
    symbol: str
    headlines: List[str]
    headline_scores: List[float]
    sentiment: str             # POSITIVE / NEUTRAL / NEGATIVE
    sentiment_score: float     # [-1, 1]
    source: str                # LIVE / DEMO
    analyzer: str              # VADER / BUILTIN-LEXICON


@dataclass
class RiskReport(_Payload):
    symbol: str
    volatility: float          # annualised, in %
    max_drawdown: float        # %, informational
    risk_score: float          # [0, 1]
    risk_level: str            # LOW / MEDIUM / HIGH
    source: str


@dataclass
class Candidate:
    action: str
    utility: float
    market_contribution: float
    sentiment_contribution: float
    risk_term: float           # negative = penalty, positive = risk avoided
    bias_term: float           # HOLD inertia / conflict bonus, SELL transaction cost


@dataclass
class SearchStep:
    step: int
    action: str
    depth: int
    h: float
    note: str


@dataclass
class SearchResult:
    best_action: str
    best_utility: float
    candidates: List[Candidate]
    trace: List[SearchStep]
    nodes_generated: int
    nodes_expanded: int
    term_evaluations: int
    exhaustive_evaluations: int
    pruned_actions: List[str]


@dataclass
class Decision:
    symbol: str
    action: str
    utility: float
    confidence: float
    explanation: str
    search: SearchResult
    degraded: bool = False
    missing_agents: List[str] = field(default_factory=list)
    inputs: Dict[str, float] = field(default_factory=dict)


@dataclass
class Order:
    symbol: str
    action: str
    quantity: int
    price: Optional[float]
    status: str                # SUCCESS / NO_ACTION / SKIPPED / REJECTED / FAILED
    message: str
    total_value: float = 0.0
    banner: str = SIM_BANNER

    def to_payload(self) -> dict:
        return asdict(self)


@dataclass
class PortfolioState:
    balance: float = 10000.0
    holdings: Dict[str, int] = field(default_factory=dict)
    history: List[dict] = field(default_factory=list)

    def snapshot(self, price_map: Optional[Dict[str, float]] = None) -> dict:
        price_map = price_map or {}
        pos = {s: q for s, q in self.holdings.items() if q > 0}
        value = sum(q * price_map.get(s, 0.0) for s, q in pos.items())
        return {"balance": round(self.balance, 2), "holdings": pos,
                "holdings_value": round(value, 2),
                "total_value": round(self.balance + value, 2),
                "transactions": len(self.history)}
