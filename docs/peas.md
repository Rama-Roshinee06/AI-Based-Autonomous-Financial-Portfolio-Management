# PEAS Formulation — Multi-Agent AI Portfolio Management

*Educational AI decision-support prototype. Simulation only — no real trading.*

| Component | Specification |
|---|---|
| **Performance measure** | Decision consistency (same inputs → same action); risk consideration (risk term always in utility); communication success (all 3 reports reach Portfolio Agent, order reaches Execution Agent); decision latency (ms, shown in UI); search efficiency (term evaluations vs 12 exhaustive); explainability (per-term contributions + text explanation); simulation correctness (balance/holdings/history stay consistent) |
| **Environment** | Stock market information (prices, news, volatility) plus a simulated portfolio. Partially observable, stochastic, dynamic, sequential, multi-agent, uncertain (see `environment_agents.md`) |
| **Actuators** | Recommendation (BUY/HOLD/SELL + confidence + explanation); simulated order; simulated portfolio update; structured agent messages |
| **Sensors** | Price and historical data (yfinance / demo series); news headlines; sentiment scores; volatility; simulated portfolio state (cash, holdings) |

**Why these measures?** The system does *not* claim to maximise profit or predict prices; success is judged on consistency, transparency, safe handling of conflicting evidence, and correct simulation.
