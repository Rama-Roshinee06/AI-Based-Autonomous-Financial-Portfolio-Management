# Review 1 — Viva Questions & Answers

1. **Why multi-agent?** The task has separable sub-problems (prices, news, risk, decision, execution). Specialised agents can be built, tested and replaced independently, and the decision step can reconcile their different views.
2. **Why not a single agent?** One program would mix data handling, NLP, risk maths and execution, be hard to test, and hide why a decision was made. Agent boundaries give modularity and explainability.
3. **What is PEAS?** Performance measure, Environment, Actuators, Sensors — the standard way to specify an agent's task. Ours is in `docs/peas.md`.
4. **What is the environment?** Stock market information (prices, news, volatility) plus a simulated portfolio.
5. **Why partially observable?** Agents see only recent prices and a few headlines, not other investors' intentions or all news.
6. **Why stochastic?** Taking the same action in the same state doesn't determine the next price; markets and news are random.
7. **Which other properties apply?** Dynamic, sequential (trades change cash/holdings), multi-agent, uncertain.
8. **What are the agents?** Market, News, Risk, Portfolio Decision, Execution (plus an Orchestrator that coordinates).
9. **Agent types?** Market: reactive; News: model-based; Risk: analytical/model-based; Portfolio: goal/utility-based; Execution: reactive.
10. **How do agents communicate?** Through structured `Message` objects (id, sender, receiver, timestamp, type, payload) on a message bus; the UI shows the log. Market/News/Risk → Portfolio → Execution.
11. **What is the state?** A candidate action with the utility terms evaluated so far, given inputs M, S, R.
12. **What is the action space?** BUY, HOLD, SELL.
13. **What is the heuristic?** h = already-evaluated utility terms + optimistic upper bounds of unevaluated terms; it never underestimates the true utility (admissible).
14. **Why Best-First Search?** It evaluates the most promising action first and prunes provably worse ones; with an admissible h the result equals exhaustive search, and the trace explains the decision.
15. **What is the utility function?** `U(BUY)=0.4M+0.3S−0.3R`, `U(SELL)=−0.4M−0.3S+0.3R−0.1`, `U(HOLD)=0.12+0.3·|M−S|/2`.
16. **How is risk handled?** Risk Agent turns annualised volatility into a [0,1] score and LOW/MEDIUM/HIGH; it penalises BUY, favours SELL, and lowers appetite to act.
17. **How are conflicts resolved?** When market and news disagree, the HOLD bonus grows, so HOLD (or SELL under high risk) wins over a risky BUY.
18. **What happens if an agent fails?** It sends `AGENT_ERROR`; the Portfolio Agent substitutes a neutral value, marks the decision *degraded* and halves confidence. The system still completes.
19. **What if there's no internet?** Deterministic demo data is used and labelled DEMO DATA.
20. **Is this real trading?** No. Execution only updates a simulated cash/holdings book; it never contacts a broker. It does not predict the market or promise profit.
21. **Why Best-First Search for one stock but hill-climbing for the portfolio?** One stock has a tiny discrete action space (3 actions) where an admissible heuristic gives an exact, explainable answer. A portfolio's weight vector is continuous and high-dimensional, so we use stochastic hill-climbing over small weight shifts.
22. **How do the two layers relate?** Layer 1 gives a per-stock BUY/HOLD/SELL decision with explanation; Layer 2 allocates capital across assets under risk limits. They share the same message-oriented design and are presented as two tabs of one dashboard.
23. **What does the Risk Manager do in Layer 2?** It checks each proposal against concentration and volatility limits, tightens limits after a drawdown, and answers PROPOSE with ACCEPT or COUNTER; it has the final veto.
24. **Does the multi-agent system beat the single agent?** It reduces drawdown and volatility in all tested scenarios but earns lower average return; it does not beat buy-and-hold in normal/bull markets. Its value is risk control. Results are on synthetic data.
