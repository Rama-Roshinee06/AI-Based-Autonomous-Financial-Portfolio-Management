"""Terminal demo:  python run_cli.py [SYMBOL]  - runs all four scenarios on one portfolio."""
import sys
from data.fallback_data import SCENARIOS
from orchestration.orchestrator import Orchestrator

sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
orch = Orchestrator(use_live=False)
print("SIMULATION - NO REAL TRADING\n")
for sc in SCENARIOS:
    r = orch.analyse(sym, sc)
    d = r.decision
    u = {c.action: c.utility for c in d.search.candidates}
    print(f"[{sc:<11}] market={r.market.trend:<6} news={r.news.sentiment:<8} risk={r.risk.risk_level:<6} "
          f"U={u} -> {d.action} (conf {d.confidence:.0%}) | order: {r.order.action} x{r.order.quantity} {r.order.status}")
print("\nPortfolio:", orch.portfolio.snapshot())
