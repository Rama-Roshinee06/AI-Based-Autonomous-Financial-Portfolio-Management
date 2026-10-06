from communication.message_bus import MessageBus, UnknownReceiverError
from communication.messages import Message
from orchestration.orchestrator import Orchestrator


def test_message_creation_fields():
    m = Message.create("Market Agent", "Portfolio Agent", "MARKET_REPORT", {"x": 1})
    d = m.to_dict()
    assert set(d) == {"message_id", "sender", "receiver", "timestamp", "message_type", "payload"}
    assert d["payload"] == {"x": 1} and d["message_id"].startswith("msg-")


def test_invalid_message_type_rejected():
    try:
        Message.create("a", "b", "NOPE", {})
    except ValueError:
        return
    assert False, "expected ValueError"


def test_bus_routing_and_inbox_drain():
    bus = MessageBus()
    bus.register("A"); bus.register("B")
    bus.send(Message.create("A", "B", "USER_REQUEST", {}))
    assert bus.pending(["B"]) == 1 and bus.pending(["A"]) == 0
    assert len(bus.receive("B")) == 1 and bus.pending(["B"]) == 0
    assert len(bus.history) == 1


def test_unknown_receiver_raises():
    bus = MessageBus()
    bus.register("A")
    try:
        bus.send(Message.create("A", "Ghost", "USER_REQUEST", {}))
    except UnknownReceiverError:
        return
    assert False, "expected UnknownReceiverError"


def test_required_message_flow():
    r = Orchestrator(use_live=False).analyse("AAPL", "Bullish")
    flow = [(m["sender"], m["receiver"], m["message_type"]) for m in r.messages]
    for s, t in [("Market Agent", "MARKET_REPORT"), ("News Agent", "NEWS_REPORT"), ("Risk Agent", "RISK_REPORT")]:
        assert (s, "Portfolio Agent", t) in flow
    assert ("Portfolio Agent", "Execution Agent", "ORDER_INSTRUCTION") in flow
    assert flow[0] == ("User", "Orchestrator", "USER_REQUEST")
    assert flow[-1] == ("Execution Agent", "Orchestrator", "EXECUTION_CONFIRMATION")
    assert flow.index(("Portfolio Agent", "Execution Agent", "ORDER_INSTRUCTION")) > max(
        flow.index((s, "Portfolio Agent", t)) for s, t in
        [("Market Agent", "MARKET_REPORT"), ("News Agent", "NEWS_REPORT"), ("Risk Agent", "RISK_REPORT")])
