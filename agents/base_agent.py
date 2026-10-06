"""Base classes: every agent owns an inbox on the bus and talks ONLY via Messages."""
from communication.message_bus import MessageBus
from communication.messages import Message


class BaseAgent:
    name = "Agent"
    agent_type = ""
    goal = ""

    def __init__(self, bus: MessageBus, fail: bool = False):
        self.bus, self.fail = bus, fail
        bus.register(self.name)

    def send(self, receiver: str, message_type: str, payload: dict) -> Message:
        msg = Message.create(self.name, receiver, message_type, payload)
        self.bus.send(msg)
        return msg

    def step(self) -> int:
        msgs = self.bus.receive(self.name)
        for m in msgs:
            self.handle(m)
        return len(msgs)

    def handle(self, message: Message) -> None:
        raise NotImplementedError


class AnalysisAgent(BaseAgent):
    """Market / News / Risk: ANALYSIS_REQUEST in -> *_REPORT (or AGENT_ERROR) to Portfolio Agent."""
    report_type = ""

    def analyse(self, symbol, scenario=None, use_live=True):
        raise NotImplementedError

    def handle(self, message: Message) -> None:
        if message.message_type != "ANALYSIS_REQUEST":
            return
        p = message.payload
        try:
            if self.fail:
                raise RuntimeError(f"{self.name} simulated failure")
            report = self.analyse(p["symbol"], p.get("scenario"), p.get("use_live", True))
            self.send("Portfolio Agent", self.report_type, report.to_payload())
        except Exception as exc:
            self.send("Portfolio Agent", "AGENT_ERROR", {"agent": self.name, "error": str(exc)})
