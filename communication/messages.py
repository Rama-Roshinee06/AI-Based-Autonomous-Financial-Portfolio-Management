"""Common structured message model used for ALL inter-agent communication."""
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone

MESSAGE_TYPES = {"USER_REQUEST", "ANALYSIS_REQUEST", "MARKET_REPORT", "NEWS_REPORT",
                 "RISK_REPORT", "AGENT_ERROR", "ORDER_INSTRUCTION", "EXECUTION_CONFIRMATION"}


@dataclass(frozen=True)
class Message:
    message_id: str
    sender: str
    receiver: str
    timestamp: str
    message_type: str
    payload: dict = field(default_factory=dict)

    @staticmethod
    def create(sender: str, receiver: str, message_type: str, payload: dict) -> "Message":
        if message_type not in MESSAGE_TYPES:
            raise ValueError(f"Unknown message type: {message_type}")
        return Message(f"msg-{uuid.uuid4().hex[:8]}", sender, receiver,
                       datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                       message_type, dict(payload))

    def to_dict(self) -> dict:
        return asdict(self)
