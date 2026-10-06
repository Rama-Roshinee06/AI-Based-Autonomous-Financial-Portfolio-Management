"""Price/news access: yfinance when available, deterministic synthetic data otherwise."""
import hashlib
import os
import random
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from typing import List, Tuple
from data.fallback_data import BASE_PRICES, HEADLINES, SCENARIOS


@dataclass
class PriceHistory:
    prices: List[float]
    dates: List[str]
    source: str  # LIVE / DEMO


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)


def base_price(symbol: str) -> float:
    return BASE_PRICES.get(symbol, float(40 + _seed(symbol) % 260))


def offline_forced() -> bool:
    return os.environ.get("PORTFOLIO_OFFLINE", "0") == "1"


def _dates(n: int) -> List[str]:
    end = date.today()
    return [(end - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]


def synthetic_prices(symbol: str, scenario: str = None, days: int = 31) -> List[float]:
    if scenario in SCENARIOS:
        p = SCENARIOS[scenario]
        rets = [p["drift"] + p["sigma"] * (1 if i % 2 == 0 else -1) for i in range(days - 1)]
    else:
        rng = random.Random(_seed(symbol))
        drift, sigma = rng.uniform(-0.002, 0.003), rng.uniform(0.008, 0.025)
        rets = [rng.gauss(drift, sigma) for _ in range(days - 1)]
    raw = [100.0]
    for r in rets:
        raw.append(raw[-1] * (1 + r))
    k = base_price(symbol) / raw[-1]
    return [round(x * k, 2) for x in raw]


@lru_cache(maxsize=64)
def _fetch_live(symbol: str, days: int):
    import yfinance as yf  # optional dependency
    hist = yf.Ticker(symbol).history(period="3mo", timeout=6)["Close"].dropna()
    if len(hist) < 10:
        raise ValueError("not enough live data")
    return (tuple(float(x) for x in hist.tolist()[-days:]),
            tuple(d.strftime("%Y-%m-%d") for d in hist.index[-days:]))


def get_price_history(symbol: str, scenario: str = None, use_live: bool = True, days: int = 31) -> PriceHistory:
    if use_live and not scenario and not offline_forced():
        try:
            prices, dates = _fetch_live(symbol, days)
            return PriceHistory(list(prices), list(dates), "LIVE")
        except Exception:
            pass
    return PriceHistory(synthetic_prices(symbol, scenario, days), _dates(days), "DEMO")


def _demo_headlines(symbol: str, scenario: str = None) -> List[str]:
    if scenario in SCENARIOS:
        tone = SCENARIOS[scenario]["news"]
        return [h.format(s=symbol) for h in HEADLINES[tone]]
    tones = ["positive", "neutral", "negative"]
    main = tones[_seed(symbol) % 3]
    picks = HEADLINES[main][:3] + HEADLINES["neutral"][:2]
    return [h.format(s=symbol) for h in picks]


def get_news(symbol: str, scenario: str = None, use_live: bool = True) -> Tuple[List[str], str]:
    if use_live and not scenario and not offline_forced():
        try:
            import yfinance as yf
            titles = []
            for item in yf.Ticker(symbol).news[:8]:
                t = item.get("title") or (item.get("content") or {}).get("title")
                if t:
                    titles.append(t)
            if len(titles) >= 3:
                return titles[:5], "LIVE"
        except Exception:
            pass
    return _demo_headlines(symbol, scenario), "DEMO"
