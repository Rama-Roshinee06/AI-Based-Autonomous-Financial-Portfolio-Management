import numpy as np
from simulation.portfolio_mas import (
    N,
    ExecutionAgent,
    RiskManagerAgent,
    generate_market,
    metrics,
    run,
    run_simulation,
)


def test_market_generation_deterministic_and_shaped():
    a, b = generate_market("crash", 300, 7), generate_market("crash", 300, 7)
    assert a.shape == (300, N) and np.allclose(a, b)


def test_risk_manager_enforces_concentration_and_defensive_mode():
    cov = np.cov(generate_market("normal", 200, 3)[-60:].T)
    rm = RiskManagerAgent()
    ok, adj, why = rm.review(np.array([0.9, 0.1, 0, 0, 0, 0.0]), cov, 0.0)
    assert not ok and "concentration" in why
    assert adj[:N].max() <= rm.max_w + 1e-9 and abs(adj.sum() - 1) < 1e-9
    (cap_normal, d0), (cap_def, d1) = rm.limits(0.0), rm.limits(0.2)
    assert not d0 and d1 and cap_def < cap_normal


def test_executor_skips_small_trades_and_charges_cost():
    ex, cur = ExecutionAgent(), np.array([0.2] * 5 + [0.0])
    w, cost, _, did = ex.execute(cur, cur + np.array([0.01, -0.01, 0, 0, 0, 0]))
    assert not did and cost == 0 and np.allclose(w, cur)
    tgt = np.array([0.35, 0.05, 0.2, 0.2, 0.2, 0.0])
    w, cost, _, did = ex.execute(cur, tgt)
    assert did and cost > 0 and np.allclose(w, tgt)


def test_simulation_modes_and_negotiation_messages():
    rets = generate_market("crash", 200, 7)
    res = {m: run(rets, m) for m in ("multi", "single", "equal")}
    for r in res.values():
        assert len(r["equity"]) == len(r["weights"]) == 200 - 60 + 1
        assert np.allclose(r["weights"].sum(axis=1), 1) and (r["equity"] > 0).all()
    kinds = {m.kind for m in res["multi"]["log"]}
    assert {"INFORM", "PROPOSE", "REPORT"} <= kinds and ({"ACCEPT", "COUNTER"} & kinds)
    assert not {"ACCEPT", "COUNTER"} & {m.kind for m in res["single"]["log"]}
    assert res["equal"]["log"] == [] and res["equal"]["rebalances"] == 0


def test_risk_manager_reduces_drawdown_on_fixed_crash_path():
    rets = generate_market("crash", 300, 7)   # deterministic path
    assert metrics(run(rets, "multi")["equity"])[4] > metrics(run(rets, "single")["equity"])[4]


def test_dashboard_entry_point_maps_parameters_and_captures_bus_messages():
    captured = []
    result = run_simulation(
        capital=250000,
        risk_tolerance="Conservative",
        iterations=100,
        tx_cost=0.002,
        on_message=captured.append,
    )

    assert result["capital"] == 250000
    assert result["portfolio"]["log"] == captured
    assert result["portfolio"]["equity"].shape == result["benchmark"]["equity"].shape
    assert {"PROPOSE", "REBALANCE"} <= {message.kind for message in captured}
