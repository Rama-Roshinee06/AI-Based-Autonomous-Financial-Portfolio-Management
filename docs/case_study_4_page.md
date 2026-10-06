# A Multi-Agent AI Framework for Collaborative Portfolio Management and Investment Decision Support

**Course:** Fundamentals of AI — Case Study  **Team:** Rama Roshinee S. V. · *[add team members / roll numbers]*  **Dept.:** CSE, Amrita Vishwa Vidyapeetham
*Educational AI decision-support prototype — simulated actions only, no real trading.*

## 1. Problem Statement
Investment decisions need price trends, news sentiment and risk — signals that can disagree. A single monolithic program mixes these concerns and hides its reasoning. We build a **multi-agent** system in which specialised agents analyse separate evidence and a Portfolio Agent resolves disagreement with an explainable utility model and Best-First Search, then a simulated order is executed. It supports decisions; it does not predict markets or give financial advice.

## 2. PEAS
| | |
|---|---|
| **Performance** | Decision consistency, risk consideration, communication success, latency, search efficiency, explainability, simulation correctness |
| **Environment** | Stock prices, news, volatility, simulated portfolio |
| **Actuators** | Recommendation, simulated order, portfolio update, agent messages |
| **Sensors** | Price, historical data, news, sentiment, volatility, portfolio state |

<div style="page-break-after: always"></div>

## 3. Environment Analysis
**Partially observable** (limited prices/headlines), **stochastic** (same action, different outcomes), **dynamic** (prices change over time), **sequential** (simulated trades alter cash/holdings), **multi-agent** (five cooperating agents), **uncertain** (noisy sentiment and volatility estimates).

## 4. Agent Analysis
| Agent | Goal | Output | Type |
|---|---|---|---|
| Market | Summarise price action | price, change, trend, score | Reactive / info-processing |
| News | Estimate sentiment | headlines, label, score | Model-based |
| Risk | Quantify risk | volatility, score, LOW/MED/HIGH | Analytical / model-based |
| Portfolio | Pick best action | BUY/HOLD/SELL, utility, confidence | Goal / utility-based |
| Execution | Simulate order | order, new portfolio | Reactive |

The Orchestrator accepts the user request, dispatches work and collects the result.

<div style="page-break-after: always"></div>

## 5. Algorithmic Modeling
**State:** candidate action with partially evaluated terms; inputs M (market, [-1,1]), S (sentiment, [-1,1]), R (risk, [0,1]). **Actions:** BUY, HOLD, SELL.

```
U(BUY)  =  0.40·M + 0.30·S − 0.30·R
U(SELL) = −0.40·M − 0.30·S + 0.30·R − 0.10
U(HOLD) =  0.12 + 0.30·|M − S|/2
```
**Search — Best-First.** Each action starts as a node with an optimistic heuristic h (evaluated terms + upper bounds of unevaluated terms). The frontier is a priority queue by h; the best node is expanded by evaluating its next term (market → sentiment → risk → bias). The first fully evaluated node popped is the goal; the others are pruned. Because h is admissible the result equals exhaustive search (tested) while typically using 4–9 of 12 term evaluations. Best-First suits a small, evidence-composed action space and yields a readable trace.

**Resolving conflict.** Market UP + News NEGATIVE + Risk HIGH → BUY −0.18, SELL +0.08, HOLD +0.36: the disagreement bonus makes HOLD the conservative choice.

<div style="page-break-after: always"></div>

## 6. Architecture & Communication
`User → Orchestrator → {Market, News, Risk} → Portfolio Agent → Best-First Search → Execution Agent → Simulated Portfolio → Dashboard (Streamlit)`.
Agents never call each other: all communication uses a common `Message` model (`message_id, sender, receiver, timestamp, message_type, payload`) over an in-memory bus whose log is shown in the UI. If an agent fails it sends `AGENT_ERROR`; the Portfolio Agent uses a neutral default, flags **degraded mode** and halves confidence. Data comes from yfinance when available, otherwise deterministic demo data (clearly labelled LIVE/DEMO); sentiment uses VADER or a built-in lexicon.

## 7. Expected Outcomes
Bullish → BUY; Neutral → HOLD; Bearish → SELL; Conflicting → HOLD/SELL (verified by automated tests, plus end-to-end and message-flow tests).

## 8. Limitations
Not a predictor or advisor; lexicon sentiment is coarse; 30-day window and fixed utility weights are heuristic; demo data is synthetic; single stock per run; simulation ignores fees and slippage beyond a fixed SELL cost.

## 9. Conclusion
A modular, explainable multi-agent decision-support prototype: separate evidence agents, structured messaging, a transparent utility model with Best-First Search, fail-soft behaviour and a fully simulated execution layer.
