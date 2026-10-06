# Review 2 — Demo Script (≈ 5–7 minutes)

| # | Step | Say / show | Time |
|---|---|---|---|
| 1 | Start app | `streamlit run ui/dashboard.py`; note the **SIMULATION MODE — NO REAL TRADING** banner | 0:20 |
| 2 | Architecture | Show the flow diagram: User → Orchestrator → Market/News/Risk → Portfolio → Execution; agents talk only via messages | 0:40 |
| 3 | Select stock | Symbol `AAPL`, scenario "Live / demo data" | 0:15 |
| 4 | Run analysis | Press **ANALYSE PORTFOLIO** | 0:10 |
| 5 | Market Agent | Price, change, trend, score, LIVE/DEMO badge | 0:25 |
| 6 | News Agent | Headlines, sentiment, score | 0:25 |
| 7 | Risk Agent | Volatility, risk score, level | 0:20 |
| 8 | Agent messages | Expand messages: 3 reports → Portfolio; Portfolio → Execution; show payload JSON | 0:40 |
| 9 | Search space | Explain state/actions/heuristic; open search trace | 0:40 |
| 10 | Utilities | BUY/HOLD/SELL table with contributions; highlighted best | 0:25 |
| 11 | Final decision | Big action, utility, confidence, explanation ("simulated recommendation") | 0:20 |
| 12 | Execution Agent | Simulated order card | 0:15 |
| 13 | Transaction | Updated cash, holdings, history | 0:20 |
| 14 | Bullish | Scenario **Bullish** → BUY | 0:25 |
| 15 | Bearish | Scenario **Bearish** → SELL (sells half of the simulated position) | 0:25 |
| 16 | Conflicting | Scenario **Conflicting** → HOLD; point out agent disagreement in explanation | 0:35 |
| 17 | Tests | `pytest` (or `python run_tests_offline.py`) — all green | 0:30 |

**Tips:** run Bullish before Bearish so there is a position to sell; untick "Try live data" for a fully repeatable demo; use *Reset simulated portfolio* between runs.
