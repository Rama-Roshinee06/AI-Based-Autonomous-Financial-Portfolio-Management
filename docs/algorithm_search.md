# Algorithmic Modeling & Search Strategy

*An educational decision-support heuristic — it does not predict the stock market.*

## Formulation
- **State:** a partially evaluated candidate `(action, {terms evaluated so far})`, with inputs M (market score ∈[-1,1]), S (sentiment ∈[-1,1]), R (risk penalty ∈[0,1]).
- **Action space:** `{BUY, HOLD, SELL}`.
- **Terms of each utility:** market, sentiment, risk, bias.

## Utility function
```
U(BUY)  =  0.40·M + 0.30·S − 0.30·R
U(SELL) = −0.40·M − 0.30·S + 0.30·R − 0.10        (0.10 = transaction cost)
U(HOLD) =  0.12 + 0.30·|M − S|/2                  (inertia + conflict bonus)
```
Selling mirrors buying: bearish evidence and high risk favour exit. HOLD wins ties and gains utility when agents disagree, so conflicting evidence is resolved conservatively.

## Search: Best-First Search
1. Root expands into three action nodes. 
2. **Heuristic h(node)** = values of terms already evaluated + *optimistic upper bounds* of the remaining terms (inputs lie in known ranges). h never underestimates the true utility (admissible).
3. **Frontier:** priority queue, highest h first; ties → HOLD < SELL < BUY (conservative).
4. **Expansion:** evaluate the next term (market → sentiment → risk → bias) of the best node; its h tightens; push back.
5. **Goal test:** a fully evaluated node popped first from the frontier ⇒ best action. Others are pruned.

**Why Best-First?** The action space is tiny but each node's utility is composed of independent evidence terms; Best-First Search focuses evaluation on the most promising action and skips provably worse ones, and its trace is directly explainable. With an admissible h the result equals the exhaustive argmax (verified over a 175-point input grid in `tests/test_search.py`).

## Example (offline demo, AAPL)
| Scenario | M | S | R | BUY | HOLD | SELL | Best | Term evals |
|---|---|---|---|---|---|---|---|---|
| Bullish | +0.95 | +0.79 | 0.24 | **+0.54** | +0.14 | −0.64 | BUY | 5/12 |
| Neutral | +0.01 | 0.00 | 0.51 | −0.15 | **+0.12** | +0.05 | HOLD | 9/12 |
| Bearish | −0.96 | −0.78 | 0.92 | −0.89 | +0.15 | **+0.79** | SELL | 4/12 |
| Conflicting | +0.82 | −0.78 | 0.92 | −0.18 | **+0.36** | +0.08 | HOLD | 7/12 |

*(Values with the built-in lexicon; VADER may shift sentiment slightly. Weights and constants are tunable in `algorithms/utility.py`.)*

---

## Layer 2 — Multi-asset rebalancing with negotiation (`simulation/portfolio_mas.py`)
Layer 1 (above) decides BUY/HOLD/SELL for one stock. Layer 2 decides **how to allocate a whole portfolio** (TECH, BANK, ENERGY, PHARMA, GOLD + CASH) over time.

| Agent | Role | Type |
|---|---|---|
| Market Analyst | Estimates returns (20d/60d momentum blend), covariance and regime (NORMAL / HIGH-VOL) | Reactive / information-processing |
| Optimizer | Searches for target weights | Utility-based search agent |
| Risk Manager | Reviews proposals; limits: max weight 35%, volatility cap 20% (12% after a >10% drawdown); can veto | Constraint-based |
| Executor | Trades only if turnover ≥ 3%; pays 0.1% proportional cost | Reactive |

**Negotiation protocol:** `INFORM` → `PROPOSE` → `ACCEPT` or `COUNTER` (up to 3 rounds; each counter raises the Optimizer's risk aversion ×1.6; the Risk Manager has the final veto) → `REPORT`.

**Search:** state = weight vector w (long-only, sums to 1); action = shift 1/2/5% of weight from asset j to asset i; goal = maximise `U(w) = E[r] − (λ/2)·wᵀΣw − tc·turnover`; stochastic hill-climbing, 800 iterations per proposal.

**Evaluation (Monte-Carlo, 8 random markets per scenario, 300 days):** the Risk Manager lowers maximum drawdown versus the single-agent (no risk manager) baseline in every scenario (e.g. crash: −13.9% vs −19.8%; volatile: −15.4% vs −28.0%) at the cost of lower average return; it does not beat equal-weight buy-and-hold in normal/bull markets. The contribution is **risk control**, not higher returns. Synthetic data; no claim about real markets.
