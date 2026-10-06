"""Lightweight local sentiment: VADER if installed (+ finance lexicon), else built-in scorer."""
import math
import re
from typing import List, Tuple

FIN_LEXICON = {
    "surges": 2.5, "soars": 2.8, "record": 1.5, "beat": 2.0, "beats": 2.0, "strong": 2.0,
    "growth": 1.8, "upgrade": 2.2, "upgraded": 2.2, "profit": 1.8, "profits": 1.8, "rally": 2.2,
    "gains": 1.8, "bullish": 2.5, "boost": 1.8, "boosts": 1.8, "wins": 1.8, "buyback": 1.5,
    "dividend": 1.2, "outperform": 2.2, "jumps": 2.2, "breakthrough": 2.2, "demand": 1.0,
    "plunges": -3.0, "tumbles": -2.6, "falls": -1.8, "drops": -1.8, "miss": -2.0, "misses": -2.2,
    "downgrade": -2.2, "downgraded": -2.2, "lawsuit": -2.2, "probe": -2.0, "fraud": -3.0,
    "recall": -2.0, "layoffs": -2.0, "losses": -2.0, "loss": -2.0, "weak": -1.8, "bearish": -2.5,
    "fears": -2.0, "warning": -1.8, "slump": -2.4, "decline": -1.8, "crisis": -2.8,
    "bankruptcy": -3.5, "selloff": -2.4, "uncertainty": -1.5, "concerns": -1.5, "delays": -1.5,
}
POS_T, NEG_T = 0.15, -0.15

try:  # optional dependency
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    _vader.lexicon.update(FIN_LEXICON)
except Exception:  # pragma: no cover
    _vader = None

ANALYZER = "VADER" if _vader else "BUILTIN-LEXICON"


def _builtin(text: str) -> float:
    words = re.findall(r"[a-z']+", text.lower())
    total = 0.0
    for i, w in enumerate(words):
        v = FIN_LEXICON.get(w, 0.0)
        if v and i > 0 and words[i - 1] in {"not", "no", "never"}:
            v = -0.74 * v
        total += v
    return total / math.sqrt(total * total + 15.0)


def score_text(text: str) -> float:
    return _vader.polarity_scores(text)["compound"] if _vader else _builtin(text)


def analyse_headlines(headlines: List[str]) -> Tuple[List[float], float, str]:
    scores = [round(score_text(h), 3) for h in headlines]
    avg = round(sum(scores) / len(scores), 3) if scores else 0.0
    label = "POSITIVE" if avg >= POS_T else "NEGATIVE" if avg <= NEG_T else "NEUTRAL"
    return scores, avg, label
