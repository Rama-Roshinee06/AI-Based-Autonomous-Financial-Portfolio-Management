"""Transparent utility model for the Portfolio Agent.

Inputs (all normalised):  M = market score in [-1,1],  S = sentiment in [-1,1],
                          R = risk penalty in [0,1].

  U(BUY)  =  0.40*M + 0.30*S - 0.30*R
  U(SELL) = -0.40*M - 0.30*S + 0.30*R - SELL_COST
  U(HOLD) =  HOLD_BASE + HOLD_CONFLICT * disagreement,   disagreement = |M - S| / 2

Selling is the mirror image of buying (bearish signals and high risk favour exit),
less a transaction cost.  HOLD has an inertia baseline and gains utility when the
agents disagree - this is how conflicting evidence is resolved conservatively.
Educational decision-support heuristic - NOT a market predictor.
"""
import math
from dataclasses import dataclass
from typing import Dict
from models.schemas import Candidate

W_MARKET, W_SENT, W_RISK = 0.40, 0.30, 0.30
HOLD_BASE, HOLD_CONFLICT, SELL_COST = 0.12, 0.30, 0.10
CONF_TEMPERATURE = 0.20
ACTIONS = ("BUY", "HOLD", "SELL")
TERMS = ("market", "sentiment", "risk", "bias")


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class UtilityInputs:
    market_score: float
    sentiment_score: float
    risk_score: float

    def normalised(self) -> "UtilityInputs":
        return UtilityInputs(clamp(self.market_score, -1, 1), clamp(self.sentiment_score, -1, 1),
                             clamp(self.risk_score, 0, 1))


def disagreement(inp: UtilityInputs) -> float:
    return abs(inp.market_score - inp.sentiment_score) / 2.0


def term_value(action: str, term: str, inp: UtilityInputs) -> float:
    m, s, r = inp.market_score, inp.sentiment_score, inp.risk_score
    table = {
        "BUY":  {"market": W_MARKET * m, "sentiment": W_SENT * s, "risk": -W_RISK * r, "bias": 0.0},
        "SELL": {"market": -W_MARKET * m, "sentiment": -W_SENT * s, "risk": W_RISK * r, "bias": -SELL_COST},
        "HOLD": {"market": 0.0, "sentiment": 0.0, "risk": 0.0,
                 "bias": HOLD_BASE + HOLD_CONFLICT * disagreement(inp)},
    }
    return table[action][term]


def term_upper_bound(action: str, term: str) -> float:
    """Optimistic (admissible) bound on a not-yet-evaluated term, given inputs lie in range."""
    table = {
        "BUY":  {"market": W_MARKET, "sentiment": W_SENT, "risk": 0.0, "bias": 0.0},
        "SELL": {"market": W_MARKET, "sentiment": W_SENT, "risk": W_RISK, "bias": -SELL_COST},
        "HOLD": {"market": 0.0, "sentiment": 0.0, "risk": 0.0, "bias": HOLD_BASE + HOLD_CONFLICT},
    }
    return table[action][term]


def evaluate(action: str, inp: UtilityInputs) -> Candidate:
    v: Dict[str, float] = {t: term_value(action, t, inp) for t in TERMS}
    return Candidate(action, round(sum(v.values()), 4), round(v["market"], 4),
                     round(v["sentiment"], 4), round(v["risk"], 4), round(v["bias"], 4))


def confidence(utilities: Dict[str, float], best: str) -> float:
    exps = {a: math.exp(u / CONF_TEMPERATURE) for a, u in utilities.items()}
    return round(exps[best] / sum(exps.values()), 4)
