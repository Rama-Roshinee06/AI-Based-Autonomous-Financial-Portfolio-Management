import html

import numpy as np
import pandas as pd
import streamlit as st

from simulation import portfolio_mas as mas


st.set_page_config(
    page_title="Mukti Agents | Portfolio Intelligence",
    page_icon="✳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        background:
            radial-gradient(ellipse at 15% 0%, rgba(13, 148, 136, 0.12), transparent 34%),
            #090D16;
        color: #E2E8F0;
    }
    [data-testid="stSidebar"] {
        background: #0D1420;
        border-right: 1px solid #1E293B;
    }
    .hero {
        padding: 1.5rem 0 1rem;
    }
    .hero-kicker {
        color: #5EEAD4;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }
    .hero-title {
        color: #F8FAFC;
        font-size: clamp(2.2rem, 5vw, 3.4rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.05;
        margin: 0.4rem 0;
    }
    .hero-copy {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 760px;
    }
    .workflow {
        display: flex;
        align-items: stretch;
        gap: 0.6rem;
        margin: 1rem 0 1.5rem;
    }
    .workflow-step {
        background: linear-gradient(145deg, #141D2B, #101723);
        border: 1px solid #263449;
        border-radius: 12px;
        flex: 1;
        min-width: 0;
        padding: 0.9rem;
    }
    .workflow-step strong {
        color: #F1F5F9;
        display: block;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }
    .workflow-step span {
        color: #94A3B8;
        display: block;
        font-size: 0.78rem;
        line-height: 1.45;
    }
    .workflow-arrow {
        align-self: center;
        color: #2DD4BF;
        font-size: 1.1rem;
    }
    .section-label {
        color: #CBD5E1;
        font-size: 1.1rem;
        font-weight: 650;
        margin: 1.3rem 0 0.2rem;
    }
    .section-copy {
        color: #94A3B8;
        font-size: 0.88rem;
        margin-bottom: 0.8rem;
    }
    .agent-card {
        background: #111927;
        border: 1px solid #263449;
        border-radius: 12px;
        height: 100%;
        padding: 1rem;
    }
    .agent-card h4 {
        color: #F8FAFC;
        font-size: 0.95rem;
        margin: 0 0 0.45rem;
    }
    .agent-card p {
        color: #A7B4C6;
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }
    .agent-tag {
        color: #5EEAD4;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .notice {
        background: rgba(13, 148, 136, 0.08);
        border: 1px solid rgba(45, 212, 191, 0.2);
        border-radius: 10px;
        color: #CBD5E1;
        font-size: 0.82rem;
        margin: 1rem 0;
        padding: 0.8rem 1rem;
    }
    .metric-card {
        background: linear-gradient(145deg, #141D2B, #101723);
        border: 1px solid #263449;
        border-radius: 12px;
        padding: 16px;
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.80rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-delta-pos { color: #10B981; font-size: 0.85rem; font-weight: 600; }
    .metric-delta-neg { color: #EF4444; font-size: 0.85rem; font-weight: 600; }
    .agent-log-box {
        background-color: #080C13;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        line-height: 1.5;
        max-height: 390px;
        overflow-y: auto;
    }
    .log-analyst { color: #67E8F9; }
    .log-optimizer { color: #FCD34D; }
    .log-risk { color: #FDA4AF; }
    .log-execution { color: #86EFAC; }
    @media (max-width: 760px) {
        .workflow { flex-direction: column; }
        .workflow-arrow { transform: rotate(90deg); }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("## ✳️ Mukti Agents")
st.sidebar.caption("Portfolio intelligence, powered by cooperating agents")
st.sidebar.markdown("---")
st.sidebar.subheader("Simulation controls")
initial_capital = st.sidebar.number_input(
    "Starting portfolio value ($)", min_value=1000, value=100000, step=5000
)
risk_appetite = st.sidebar.select_slider(
    "Risk Tolerance",
    options=["Conservative", "Moderate", "Aggressive"],
    value="Moderate",
)
scenario_labels = {
    "Normal market": "normal",
    "Market crash": "crash",
    "High volatility": "volatile",
    "Bull market": "bull",
}
scenario_label = st.sidebar.selectbox(
    "Market scenario",
    options=list(scenario_labels),
)
market_scenario = scenario_labels[scenario_label]
max_iterations = st.sidebar.slider(
    "Optimizer search iterations", min_value=100, max_value=2000, value=500, step=100,
    help="Number of candidate portfolio changes the Optimizer evaluates at each rebalance.",
)
tx_cost_pct = st.sidebar.number_input(
    "Transaction cost (%)", min_value=0.0, value=0.1, step=0.05
) / 100
run_button = st.sidebar.button(
    "▶ Run simulation", use_container_width=True, type="primary"
)
st.sidebar.caption("Synthetic market data · Simulated execution · No real trades")


def execute_mas_simulation():
    """Run the backend and collect messages as the MessageBus emits them."""
    st.session_state["logs"] = []

    def capture_message(message):
        st.session_state["logs"].append(
            (message.sender, message.kind, message.t, message.text)
        )

    result = mas.run_simulation(
        capital=initial_capital,
        risk_tolerance=risk_appetite,
        iterations=max_iterations,
        tx_cost=tx_cost_pct,
        scenario=market_scenario,
        on_message=capture_message,
    )
    portfolio = result["portfolio"]
    benchmark = result["benchmark"]
    capital = result["capital"]

    dates = pd.RangeIndex(len(portfolio["equity"]), name="Trading Day")
    df_perf = pd.DataFrame(
        {
            "MAS Portfolio": capital * portfolio["equity"],
            "Equal-Weight Benchmark": capital * benchmark["equity"],
        },
        index=dates,
    )

    final_weights = portfolio["weights"][-1]
    intervention_by_asset = {}
    for intervention in portfolio["interventions"]:
        intervention_by_asset[intervention["asset"]] = intervention

    assets = mas.ASSETS + ["CASH"]
    df_alloc = pd.DataFrame(
        {
            "Ticker": assets,
            "Target Weight (%)": final_weights * 100,
            "Allocated Capital ($)": final_weights * capital * portfolio["equity"][-1],
            "Risk Manager": [
                "🟠 Modified" if asset in intervention_by_asset else ""
                for asset in assets
            ],
        }
    )

    cost_by_day = {
        transaction["day"]: (
            capital * transaction["equity_before"] * transaction["cost"]
        )
        for transaction in portfolio["transactions"]
        if transaction["executed"]
    }
    audit_messages = [
        message
        for message in portfolio["log"]
        if message.kind in {"PROPOSE", "COUNTER", "VETO", "ACCEPT", "REBALANCE"}
    ]
    df_trades = pd.DataFrame(
        [
            {
                "Day": message.t,
                "Agent": message.sender,
                "Action": message.kind,
                "Details": message.text,
                "Tx Cost ($)": cost_by_day.get(message.t, 0.0)
                if message.kind == "REBALANCE"
                else 0.0,
            }
            for message in audit_messages
        ],
        columns=["Day", "Agent", "Action", "Details", "Tx Cost ($)"],
    )
    result["performance"] = df_perf
    result["allocations"] = df_alloc
    result["trades"] = df_trades
    return result


if run_button or "sim_data" not in st.session_state:
    st.session_state["sim_data"] = execute_mas_simulation()

sim_data = st.session_state["sim_data"]
df_perf = sim_data["performance"]
df_alloc = sim_data["allocations"]
df_trades = sim_data["trades"]
logs = st.session_state.get("logs", [])
capital = sim_data["capital"]
metrics = sim_data["metrics"]
current_val = df_perf["MAS Portfolio"].iloc[-1]
pnl = current_val - capital
pnl_pct = (pnl / capital) * 100
daily_returns = np.diff(sim_data["portfolio"]["equity"]) / sim_data["portfolio"]["equity"][:-1]
var_95 = max(0.0, -float(np.quantile(daily_returns, 0.05))) * current_val

st.markdown(
    """
<header class="hero">
    <div class="hero-kicker">Mukti · Multi-agent portfolio intelligence</div>
    <div class="hero-title">Decisions, made together.</div>
    <div class="hero-copy">
        Watch four specialized agents turn market signals into a risk-checked
        portfolio, negotiate changes, and simulate execution.
    </div>
</header>
<div class="workflow">
    <div class="workflow-step"><strong>01 · Analyst</strong><span>Reads recent returns, estimates expected returns and covariance, and detects the current volatility regime.</span></div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step"><strong>02 · Optimizer</strong><span>Searches for portfolio weights that balance return, risk, and turnover cost.</span></div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step"><strong>03 · Risk Manager</strong><span>Checks concentration and volatility limits; accepts, counters, or vetoes a proposal.</span></div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step"><strong>04 · Executor</strong><span>Applies approved weights only when the rebalance is worthwhile and records simulated costs.</span></div>
</div>
<div class="notice">
    This is an educational simulation using a synthetic market path. It does not place
    real trades and is not financial advice. The risk manager enforces configured
    portfolio limits; simulated returns are not predictions of future performance.
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    pnl_class = "metric-delta-pos" if pnl >= 0 else "metric-delta-neg"
    pnl_direction = "▲" if pnl >= 0 else "▼"
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-title">Portfolio Net Worth</div>
    <div class="metric-value">${current_val:,.2f}</div>
    <div class="{pnl_class}">{pnl_direction} ${abs(pnl):,.2f} ({pnl_pct:+.2f}%)</div>
</div>
""",
        unsafe_allow_html=True,
        help="Current portfolio value after simulated transaction costs. The change is measured against the initial capital.",
    )
with c2:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-title">Sharpe Ratio</div>
    <div class="metric-value">{metrics[3]:.2f}</div>
    <div class="metric-delta-pos">Annualized, risk-adjusted return</div>
</div>
""",
        unsafe_allow_html=True,
        help="Annualized excess return over the backend's 3% risk-free rate divided by annualized volatility. Higher values indicate stronger risk-adjusted performance.",
    )
with c3:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-title">Max Drawdown</div>
    <div class="metric-value">{metrics[4]:.2%}</div>
    <div class="metric-delta-neg">Largest peak-to-trough decline</div>
</div>
""",
        unsafe_allow_html=True,
        help="The largest percentage decline from a prior portfolio peak during the simulation. A value closer to zero indicates a smaller historical loss.",
    )
with c4:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-title">1-Day VaR (95%)</div>
    <div class="metric-value">${var_95:,.2f}</div>
    <div class="metric-delta-neg">Historical daily loss estimate</div>
</div>
""",
        unsafe_allow_html=True,
        help="Historical 95% one-day Value at Risk: the estimated dollar loss threshold exceeded on approximately 5% of simulated trading days. It is not a worst-case loss bound.",
    )

st.markdown("<br>", unsafe_allow_html=True)
tab_exec, tab_analytics = st.tabs(
    ["🤝 Agent negotiation", "📊 Portfolio insights"]
)

with tab_exec:
    col_chart, col_logs = st.columns([1.8, 1.2])
    with col_chart:
        st.subheader("Portfolio value vs equal-weight benchmark")
        st.line_chart(df_perf, height=340)
    with col_logs:
        st.subheader("Agent-to-agent message stream")
        st.caption("Messages emitted by the simulation's shared MessageBus.")
        log_html_lines = []
        for agent, kind, day, text in logs:
            css_class = "log-analyst"
            if "Optimizer" in agent:
                css_class = "log-optimizer"
            elif "Risk" in agent:
                css_class = "log-risk"
            elif "Execut" in agent:
                css_class = "log-execution"
            log_html_lines.append(
                f"<span class='{css_class}'><b>[Day {day} | {html.escape(agent)} | "
                f"{html.escape(kind)}]</b> {html.escape(text)}</span>"
            )
        log_html = "<div class='agent-log-box'>" + "<br><br>".join(log_html_lines) + "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Negotiation and execution audit")
    st.dataframe(df_trades, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Download audit log (CSV)",
        data=df_trades.to_csv(index=False).encode("utf-8"),
        file_name="trade_audit_log.csv",
        mime="text/csv",
    )

with tab_analytics:
    st.markdown('<div class="section-label">How the agents collaborate</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">The sequence below reflects the roles and message types emitted by this simulation.</div>',
        unsafe_allow_html=True,
    )
    agent_columns = st.columns(4)
    agent_descriptions = [
        ("Market analyst", "INFORM", "Blends short- and long-window return estimates, measures covariance, and shares the leading asset and market regime."),
        ("Portfolio optimizer", "PROPOSE", "Uses stochastic hill-climbing to improve utility while accounting for risk aversion and transaction costs."),
        ("Risk manager", "ACCEPT · COUNTER · VETO", "Enforces asset concentration and volatility limits. During drawdown it tightens the volatility cap."),
        ("Execution agent", "REPORT · REBALANCE", "Skips small changes below the turnover threshold; otherwise applies the target and charges simulated transaction costs."),
    ]
    for column, (name, message_types, description) in zip(agent_columns, agent_descriptions):
        with column:
            st.markdown(
                f"""
<div class="agent-card">
    <div class="agent-tag">{html.escape(message_types)}</div>
    <h4>{html.escape(name)}</h4>
    <p>{html.escape(description)}</p>
</div>
""",
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1.8])
    with col_left:
        st.subheader("Final portfolio allocation")
        st.dataframe(df_alloc, use_container_width=True, hide_index=True)
        if sim_data["portfolio"]["interventions"]:
            latest_by_asset = {}
            for intervention in sim_data["portfolio"]["interventions"]:
                latest_by_asset[intervention["asset"]] = intervention
            descriptions = [
                f"{asset}: {change['proposed_weight']:.1%} proposed → "
                f"{change['adjusted_weight']:.1%} risk-adjusted "
                f"({change['reason']})"
                for asset, change in latest_by_asset.items()
            ]
            st.warning("Risk Manager adjusted proposed asset weights: " + "; ".join(descriptions))
    with col_right:
        st.subheader("Allocation by asset (%)")
        st.bar_chart(df_alloc.set_index("Ticker")["Target Weight (%)"], height=300)
