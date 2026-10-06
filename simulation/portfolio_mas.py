"""
AI-Based Autonomous Financial Portfolio Management using Multi-Agent Systems
23CSE401 - Fundamentals of Artificial Intelligence | Case Study (Review 2)

Four cooperating agents:
  1. MarketAnalystAgent  - senses the market, estimates returns & covariance
  2. OptimizerAgent      - searches (stochastic hill-climbing) for target weights
  3. RiskManagerAgent    - reviews proposals, enforces limits, can veto / counter
  4. ExecutionAgent      - rebalances only if worthwhile, pays transaction costs

Agents communicate through a MessageBus (negotiation: PROPOSE -> COUNTER -> ACCEPT).

Run:   python portfolio_mas.py                     (all scenarios, saves plots)
       python portfolio_mas.py --scenario crash --verbose
Needs: pip install numpy matplotlib   (matplotlib optional)
"""
import argparse
import os
from dataclasses import dataclass

import numpy as np

ASSETS = ["TECH", "BANK", "ENERGY", "PHARMA", "GOLD"]
N = len(ASSETS)
TD = 252            # trading days / year
RF = 0.03           # annual risk-free rate (cash return)


# ----------------------------------------------------------------------------
# 1. ENVIRONMENT : synthetic stochastic market (correlated, regime-switching)
# ----------------------------------------------------------------------------
def generate_market(scenario="normal", days=300, seed=7):
    """Returns daily simple returns, shape (days, N)."""
    rng = np.random.default_rng(seed)
    base_mu = np.array([0.14, 0.08, 0.07, 0.09, 0.04])
    base_sig = np.array([0.28, 0.20, 0.25, 0.18, 0.12])
    corr = np.array([[1.00, 0.50, 0.40, 0.30, -0.10],
                     [0.50, 1.00, 0.50, 0.30, -0.05],
                     [0.40, 0.50, 1.00, 0.20, 0.05],
                     [0.30, 0.30, 0.20, 1.00, 0.00],
                     [-0.10, -0.05, 0.05, 0.00, 1.00]])
    L = np.linalg.cholesky(corr)
    mu = np.tile(base_mu / TD, (days, 1))
    sig = np.tile(base_sig / np.sqrt(TD), (days, 1))

    if scenario == "crash":                       # sudden crash then recovery
        a, b, c = int(days * 0.5), int(days * 0.6), int(days * 0.85)
        mu[a:b, :4] -= 0.012
        mu[a:b, 4] += 0.001                       # gold = safe haven
        sig[a:b] *= 2.2
        mu[b:c, :4] += 0.002
    elif scenario == "volatile":                  # high-volatility sideways
        sig *= 1.8
        mu *= 0.3
    elif scenario == "bull":
        mu *= 2.0

    z = rng.standard_normal((days, N)) @ L.T
    log_r = mu - 0.5 * sig ** 2 + sig * z
    return np.exp(log_r) - 1.0


# ----------------------------------------------------------------------------
# Communication layer
# ----------------------------------------------------------------------------
@dataclass
class Message:
    t: int
    sender: str
    receiver: str
    kind: str
    text: str


class MessageBus:
    def __init__(self, verbose=False, on_message=None):
        self.log, self.verbose, self.on_message = [], verbose, on_message

    def send(self, t, sender, receiver, kind, text):
        message = Message(t, sender, receiver, kind, text)
        self.log.append(message)
        if self.on_message is not None:
            self.on_message(message)
        if self.verbose:
            print(f"   [day {t:3d}] {sender:>13} -> {receiver:<13} {kind:<8} {text}")


def fmt(w):
    return "{" + ", ".join(f"{a}:{x:.2f}" for a, x in zip(ASSETS + ["CASH"], w)) + "}"


# ----------------------------------------------------------------------------
# AGENT 1 : Market Analyst
# ----------------------------------------------------------------------------
class MarketAnalystAgent:
    name = "Analyst"

    def __init__(self, short=20, long=60):
        self.short, self.long = short, long

    def sense(self, rets_hist):
        """Percept: price/return history. Output: mu (daily), cov (daily), regime."""
        mu_s = rets_hist[-self.short:].mean(axis=0)
        mu_l = rets_hist[-self.long:].mean(axis=0)
        mu = 0.5 * mu_s + 0.5 * mu_l                       # momentum blend
        cov = np.cov(rets_hist[-self.long:].T) + 1e-8 * np.eye(N)
        vol_now = rets_hist[-self.short:].std() * np.sqrt(TD)
        vol_old = rets_hist[-self.long:].std() * np.sqrt(TD)
        regime = "HIGH-VOL" if vol_now > 1.3 * vol_old else "NORMAL"
        return mu, cov, regime


# ----------------------------------------------------------------------------
# AGENT 2 : Optimizer (search-based planner)
# ----------------------------------------------------------------------------
class OptimizerAgent:
    name = "Optimizer"

    def __init__(self, seed=1, tc=0.002):
        self.rng = np.random.default_rng(seed)
        self.tc = tc

    def propose(self, mu, cov, current, risk_aversion, max_w, iters=800):
        """Stochastic hill-climbing over weight vectors (assets + cash).
        State  : weights w (sum = 1, long-only)
        Action : shift a delta of weight from asset j to asset i
        Goal   : maximise U(w) = E[r] - (lambda/2) Var - turnover cost
        """
        mu_f = np.append(mu * TD, RF)
        cov_f = np.zeros((N + 1, N + 1))
        cov_f[:N, :N] = cov * TD

        def util(w):
            return (w @ mu_f - 0.5 * risk_aversion * (w @ cov_f @ w)
                    - self.tc * np.abs(w - current).sum())

        w = np.clip(current.copy(), 0, None)
        w[:N] = np.minimum(w[:N], max_w)
        w[N] = 1 - w[:N].sum()
        best = util(w)
        for _ in range(iters):
            i, j = self.rng.integers(0, N + 1, size=2)
            if i == j:
                continue
            d = self.rng.choice([0.01, 0.02, 0.05])
            if w[j] < d or (i < N and w[i] + d > max_w):
                continue
            cand = w.copy()
            cand[j] -= d
            cand[i] += d
            u = util(cand)
            if u > best:
                w, best = cand, u
        return w


# ----------------------------------------------------------------------------
# AGENT 3 : Risk Manager (constraint checker with veto power)
# ----------------------------------------------------------------------------
class RiskManagerAgent:
    name = "RiskManager"

    def __init__(self, max_w=0.35, vol_limit=0.20, dd_trigger=0.10):
        self.max_w, self.vol_limit, self.dd_trigger = max_w, vol_limit, dd_trigger

    def limits(self, drawdown):
        defensive = drawdown > self.dd_trigger
        return (self.vol_limit * (0.6 if defensive else 1.0)), defensive

    def review(self, w, cov, drawdown):
        """Returns (approved?, adjusted weights, reason)."""
        vol_cap, defensive = self.limits(drawdown)
        risky = np.minimum(w[:N], self.max_w)
        reasons = []
        if np.any(w[:N] > self.max_w + 1e-9):
            reasons.append("concentration>%.0f%%" % (self.max_w * 100))
        vol = np.sqrt(risky @ (cov * TD) @ risky)
        if vol > vol_cap:
            risky = risky * vol_cap / vol
            reasons.append(f"vol {vol:.1%}>{vol_cap:.1%}")
        if defensive:
            reasons.append("DEFENSIVE(drawdown)")
        adj = np.append(risky, 1 - risky.sum())
        approved = np.abs(adj - w).sum() < 1e-6
        return approved, adj, ", ".join(reasons) or "within limits"


# ----------------------------------------------------------------------------
# AGENT 4 : Execution
# ----------------------------------------------------------------------------
class ExecutionAgent:
    name = "Executor"

    def __init__(self, cost_rate=0.001, min_turnover=0.03):
        self.cost_rate, self.min_turnover = cost_rate, min_turnover

    def execute(self, current, target):
        """Skip trivial rebalances; otherwise trade and pay proportional cost."""
        turnover = np.abs(target - current).sum() / 2
        if turnover < self.min_turnover:
            return current, 0.0, turnover, False
        return target.copy(), self.cost_rate * np.abs(target - current).sum(), turnover, True


# ----------------------------------------------------------------------------
# Simulation (one run = one strategy mode on one market path)
# ----------------------------------------------------------------------------
def run(rets, mode="multi", lookback=60, rebalance_every=5, verbose=False, seed=1,
        risk_tolerance="Moderate", iterations=800, tx_cost=0.001, on_message=None):
    """mode: 'multi' (4 agents) | 'single' (no risk agent) | 'equal' (buy&hold)."""
    risk_profiles = {
        "Conservative": (0.25, 0.14),
        "Moderate": (0.35, 0.20),
        "Aggressive": (0.45, 0.28),
    }
    if risk_tolerance not in risk_profiles:
        raise ValueError(f"Unsupported risk tolerance: {risk_tolerance}")
    if iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    if tx_cost < 0:
        raise ValueError("tx_cost cannot be negative")

    analyst, optim = MarketAnalystAgent(), OptimizerAgent(seed=seed, tc=tx_cost)
    risk_max_w, risk_vol_limit = risk_profiles[risk_tolerance]
    risk, execa = RiskManagerAgent(max_w=risk_max_w, vol_limit=risk_vol_limit), ExecutionAgent(cost_rate=tx_cost)
    bus = MessageBus(verbose, on_message)

    w = np.zeros(N + 1)
    w[N] = 1.0
    if mode == "equal":
        w = np.append(np.ones(N) / N, 0.0)
    eq, peak = 1.0, 1.0
    equity, weights, nreb, costs = [1.0], [w.copy()], 0, 0.0
    transactions, interventions = [], []
    shown = 0

    for t in range(lookback, len(rets)):
        dd = 1 - eq / peak
        if mode != "equal" and (t - lookback) % rebalance_every == 0:
            mu, cov, regime = analyst.sense(rets[:t])
            show = verbose and shown < 3
            bus.verbose = show
            bus.send(t, "Analyst", "Optimizer", "INFORM", f"regime={regime}, "
                     f"best asset={ASSETS[int(np.argmax(mu))]}")
            lam, max_w, target = 3.0, (risk.max_w if mode == "multi" else 1.0), w.copy()
            approved = False
            for rnd in range(1, 4):                       # negotiation rounds
                prop = optim.propose(mu, cov, w, lam, max_w, iters=iterations)
                bus.send(t, "Optimizer", "RiskManager", "PROPOSE", f"r{rnd} {fmt(prop)}")
                if mode == "single":
                    target = prop
                    break
                ok, adj, why = risk.review(prop, cov, dd)
                if ok:
                    bus.send(t, "RiskManager", "Optimizer", "ACCEPT", why)
                    target = prop
                    approved = True
                    break
                bus.send(t, "RiskManager", "Optimizer", "COUNTER", f"{why} -> {fmt(adj)}")
                lam *= 1.6                                # optimizer becomes more risk-averse
                target = adj                              # risk manager has final veto
            if mode == "multi" and not approved:
                bus.send(t, "RiskManager", "ALL", "VETO",
                         "No proposal met risk limits; applying the final risk-adjusted weights.")
                final_prop = prop
                interventions.extend(
                    {
                        "day": t,
                        "asset": asset,
                        "proposed_weight": float(final_prop[i]),
                        "adjusted_weight": float(target[i]),
                        "reason": why,
                    }
                    for i, asset in enumerate(ASSETS)
                    if abs(final_prop[i] - target[i]) > 1e-6
                )
            new_w, cost, turn, did = execa.execute(w, target)
            bus.send(t, "Executor", "ALL", "REPORT",
                     f"{'TRADED' if did else 'SKIPPED'} turnover={turn:.1%} cost={cost:.4%}")
            transactions.append({
                "day": t,
                "turnover": float(turn),
                "cost": float(cost),
                "equity_before": float(eq),
                "executed": bool(did),
            })
            if did:
                nreb += 1
                costs += cost
                bus.send(t, "Executor", "ALL", "REBALANCE",
                         f"turnover={turn:.1%} transaction cost={cost:.4%}")
                eq *= (1 - cost)
                w = new_w
            if show:
                shown += 1
        r = np.append(rets[t], RF / TD)
        pr = w @ r
        eq *= (1 + pr)
        w = w * (1 + r) / (1 + pr)                         # weight drift
        peak = max(peak, eq)
        equity.append(eq)
        weights.append(w.copy())
    return dict(equity=np.array(equity), weights=np.array(weights),
                rebalances=nreb, costs=costs, log=bus.log,
                transactions=transactions, interventions=interventions)


def metrics(equity):
    r = np.diff(equity) / equity[:-1]
    total = equity[-1] / equity[0] - 1
    ann = (equity[-1] / equity[0]) ** (TD / len(r)) - 1
    vol = r.std() * np.sqrt(TD)
    sharpe = (ann - RF) / vol if vol > 0 else 0.0
    mdd = (equity / np.maximum.accumulate(equity) - 1).min()
    return total, ann, vol, sharpe, mdd


def run_simulation(capital=100000, risk_tolerance="Moderate", iterations=500,
                   tx_cost=0.001, scenario="normal", days=300, seed=7,
                   on_message=None):
    """Run the dashboard-ready multi-agent simulation using its sidebar parameters."""
    if capital <= 0:
        raise ValueError("capital must be positive")
    rets = generate_market(scenario=scenario, days=days, seed=seed)
    portfolio = run(
        rets,
        mode="multi",
        risk_tolerance=risk_tolerance,
        iterations=iterations,
        tx_cost=tx_cost,
        on_message=on_message,
    )
    benchmark = run(rets, mode="equal")
    return {
        "capital": capital,
        "scenario": scenario,
        "portfolio": portfolio,
        "benchmark": benchmark,
        "metrics": metrics(portfolio["equity"]),
    }


def plot(results, scenario, outdir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib not installed - skipping plots)")
        return
    fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
    for name, res in results.items():
        ax[0].plot(res["equity"], label=name)
    ax[0].set_title(f"Portfolio value - scenario: {scenario}")
    ax[0].set_xlabel("day"); ax[0].set_ylabel("growth of 1.0"); ax[0].legend(); ax[0].grid(alpha=.3)
    wts = results["Multi-Agent (4 agents)"]["weights"]
    ax[1].stackplot(range(len(wts)), wts.T, labels=ASSETS + ["CASH"])
    ax[1].set_title("Multi-agent allocation over time")
    ax[1].set_xlabel("day"); ax[1].legend(loc="upper right", fontsize=7, ncol=3)
    plt.tight_layout()
    path = os.path.join(outdir, f"result_{scenario}.png")
    plt.savefig(path, dpi=130)
    plt.close()
    print(f"  plot saved -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="all", choices=["all", "normal", "bull", "crash", "volatile"])
    ap.add_argument("--days", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--verbose", action="store_true", help="show agent negotiation messages")
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--montecarlo", type=int, default=0, metavar="K",
                    help="also average results over K random market paths")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    scenarios = ["normal", "bull", "crash", "volatile"] if a.scenario == "all" else [a.scenario]
    for sc in scenarios:
        print("=" * 78)
        print(f"SCENARIO: {sc.upper()}   (days={a.days}, seed={a.seed})")
        print("=" * 78)
        rets = generate_market(sc, a.days, a.seed)
        results = {
            "Multi-Agent (4 agents)": run(rets, "multi", verbose=a.verbose),
            "Single Agent (no risk)": run(rets, "single"),
            "Equal-Weight Buy&Hold": run(rets, "equal"),
        }
        print(f"{'Strategy':<26}{'Return':>9}{'AnnRet':>9}{'AnnVol':>9}{'Sharpe':>8}{'MaxDD':>9}{'Trades':>8}")
        for name, res in results.items():
            tot, ann, vol, sh, mdd = metrics(res["equity"])
            print(f"{name:<26}{tot:>9.1%}{ann:>9.1%}{vol:>9.1%}{sh:>8.2f}{mdd:>9.1%}{res['rebalances']:>8d}")
        msgs = results["Multi-Agent (4 agents)"]["log"]
        counters = sum(m.kind == "COUNTER" for m in msgs)
        print(f"Messages exchanged: {len(msgs)} | Risk-manager COUNTER-offers: {counters}")
        if not a.no_plot:
            plot(results, sc, a.out)
    if a.montecarlo:
        print("=" * 78)
        print(f"MONTE-CARLO TEST: mean over {a.montecarlo} random markets per scenario")
        print("=" * 78)
        print(f"{'Scenario':<10}{'Strategy':<26}{'Return':>9}{'Sharpe':>8}{'MaxDD':>9}")
        for sc in scenarios:
            acc = {"Multi-Agent (4 agents)": [], "Single Agent (no risk)": [], "Equal-Weight Buy&Hold": []}
            for k in range(a.montecarlo):
                r = generate_market(sc, a.days, 100 + k)
                for name, m in zip(acc, ["multi", "single", "equal"]):
                    acc[name].append(metrics(run(r, m, seed=k)["equity"]))
            for name, v in acc.items():
                m = np.mean(v, axis=0)
                print(f"{sc:<10}{name:<26}{m[0]:>9.1%}{m[3]:>8.2f}{m[4]:>9.1%}")
    print("\nDone.")


if __name__ == "__main__":
    main()
