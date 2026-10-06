"""Deterministic demo data so the whole system works offline."""
BASE_PRICES = {"AAPL": 218.50, "MSFT": 415.20, "GOOGL": 172.80, "TSLA": 245.60,
               "AMZN": 188.40, "NVDA": 128.90, "META": 520.10, "INFY": 18.60, "RELIANCE.NS": 2950.0}

# daily drift / daily sigma: returns alternate +sigma, -sigma around drift (deterministic)
SCENARIOS = {
    "Bullish":     {"drift": 0.0045, "sigma": 0.009, "news": "positive", "expected": "BUY"},
    "Neutral":     {"drift": 0.0002, "sigma": 0.019, "news": "neutral",  "expected": "HOLD"},
    "Bearish":     {"drift": -0.005, "sigma": 0.034, "news": "negative", "expected": "SELL"},
    "Conflicting": {"drift": 0.0035, "sigma": 0.034, "news": "negative", "expected": "HOLD/SELL"},
}

HEADLINES = {
    "positive": [
        "{s} surges to record high after earnings beat expectations",
        "Analysts upgrade {s} citing strong growth and rising demand",
        "{s} announces share buyback and boosts dividend",
        "Investors turn bullish on {s} as rally extends",
        "{s} wins major contract, profit outlook improves",
    ],
    "neutral": [
        "{s} to hold annual shareholder meeting next month",
        "{s} reports quarterly results in line with consensus",
        "Analysts maintain neutral rating on {s}",
        "{s} appoints new regional operations director",
        "{s} shares trade sideways ahead of economic data",
    ],
    "negative": [
        "{s} plunges after earnings miss and weak guidance",
        "Analysts downgrade {s} amid fears of slowing demand",
        "Regulators open fraud probe into {s}",
        "{s} announces layoffs as losses widen",
        "Bearish sentiment grows as {s} faces recall and lawsuit",
    ],
}
