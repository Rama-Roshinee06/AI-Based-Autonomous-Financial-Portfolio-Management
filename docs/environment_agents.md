# Environment & Agent Analysis

## Environment classification
| Property | Value | Why |
|---|---|---|
| Observability | **Partially observable** | Agents see only recent prices and a few headlines — not other investors' intentions, private information, or the full news universe |
| Determinism | **Stochastic** | Same state + same action does not guarantee the same next price; headlines arrive randomly |
| Dynamics | **Dynamic** | Prices and news change while the system deliberates (demo mode freezes them for repeatability) |
| Episodes | **Sequential** | A simulated BUY changes cash/holdings, which affects later SELL/BUY outcomes |
| Agents | **Multi-agent (cooperative)** | Five agents with distinct sub-goals cooperate on one decision |
| Knowledge | **Uncertain** | Sentiment lexicons and volatility are noisy estimates; hence a confidence value and fail-soft design |
| Time | Discrete | One analysis per user request |

## Agents
| Agent | Goal | Input | Output | Decision process | Communicates with | Type |
|---|---|---|---|---|---|---|
| **Market** | Summarise price action | symbol, scenario | price, 1d %, trend UP/STABLE/DOWN, score∈[-1,1] | momentum % over 30 days → tanh(m/8); trend thresholds ±3% | → Portfolio (`MARKET_REPORT`) | Reactive / information-processing |
| **News** | Gauge sentiment | symbol | 3–5 headlines, label, score∈[-1,1] | VADER (+finance lexicon) or built-in lexicon; mean compound; ±0.15 thresholds | → Portfolio (`NEWS_REPORT`) | Model-based |
| **Risk** | Quantify risk | symbol | annualised volatility, drawdown, risk score∈[0,1], LOW/MEDIUM/HIGH | σ(daily returns)·√252, score = vol/60% capped; <0.35 LOW, <0.65 MEDIUM | → Portfolio (`RISK_REPORT`) | Analytical / model-based |
| **Portfolio** | Choose best action | 3 reports | BUY/HOLD/SELL, utility, confidence, explanation | Utility model + Best-First Search | ← 3 agents; → Execution (`ORDER_INSTRUCTION`) | Goal / utility-based |
| **Execution** | Apply action to simulated book | order instruction | simulated order, updated portfolio | BUY: 10% of cash; SELL: half the position; HOLD: none | → Orchestrator (`EXECUTION_CONFIRMATION`) | Reactive |

**Orchestrator** is a coordinator (not a decision-maker): it receives `USER_REQUEST`, fans out `ANALYSIS_REQUEST`s, runs the message loop, and collects the confirmation.
