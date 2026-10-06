"""Exercise the Streamlit dashboard without requiring a running Streamlit server."""
import importlib
import sys
from unittest.mock import MagicMock


class _State(dict):
    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


def _stub_streamlit():
    st = MagicMock()
    st.session_state = _State()
    st.columns.side_effect = lambda count, *args, **kwargs: [
        MagicMock() for _ in range(count if isinstance(count, int) else len(count))
    ]
    st.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    st.sidebar.number_input.side_effect = lambda label, value=0, **kwargs: value
    st.sidebar.select_slider.side_effect = lambda label, options, value=None, **kwargs: value
    st.sidebar.selectbox.side_effect = lambda label, options, index=0, **kwargs: options[index]
    st.sidebar.slider.side_effect = lambda label, min_value, max_value, value, **kwargs: min_value
    st.sidebar.button.return_value = False
    return st


def test_dashboard_maps_market_scenario_and_explains_agents():
    st = _stub_streamlit()
    st.sidebar.selectbox.side_effect = None
    st.sidebar.selectbox.return_value = "Market crash"
    sys.modules["streamlit"] = st
    sys.modules.pop("ui.dashboard", None)

    try:
        dashboard = importlib.import_module("ui.dashboard")

        assert "sim_data" in st.session_state
        assert st.session_state["sim_data"]["capital"] == 100000
        assert st.session_state["sim_data"]["scenario"] == "crash"
        assert st.set_page_config.call_args.kwargs["page_title"] == (
            "Mukti Agents | Portfolio Intelligence"
        )
        rendered_copy = "\n".join(
            str(call.args[0]) for call in st.markdown.call_args_list if call.args
        )
        assert "Mukti" in rendered_copy
        assert all(
            agent in rendered_copy
            for agent in ("Analyst", "Optimizer", "Risk Manager", "Executor")
        )
        assert "23CSE401" not in rendered_copy
        assert "Review 2" not in rendered_copy
        assert st.sidebar.selectbox.call_args.kwargs["options"] == [
            "Normal market",
            "Market crash",
            "High volatility",
            "Bull market",
        ]
        assert st.session_state["logs"]
        assert {entry[1] for entry in st.session_state["logs"]} >= {
            "PROPOSE",
            "REBALANCE",
        }
        st.download_button.assert_called_once()
        assert st.download_button.call_args.args[0] == "📥 Download audit log (CSV)"
        assert st.download_button.call_args.kwargs["mime"] == "text/csv"
        assert st.line_chart.called
        assert st.dataframe.called
        assert dashboard.df_trades["Action"].isin(
            ["PROPOSE", "COUNTER", "VETO", "ACCEPT", "REBALANCE"]
        ).all()
    finally:
        sys.modules.pop("streamlit", None)
        sys.modules.pop("ui.dashboard", None)
