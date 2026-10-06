"""In-memory message bus: per-agent inboxes + a full audit log shown in the UI."""
from typing import Dict, Iterable, List
from communication.messages import Message


class UnknownReceiverError(KeyError):
    pass


class MessageBus:
    def __init__(self):
        self._inboxes: Dict[str, List[Message]] = {}
        self.history: List[Message] = []

    def register(self, name: str) -> None:
        self._inboxes.setdefault(name, [])

    def send(self, msg: Message) -> None:
        if msg.receiver not in self._inboxes:
            raise UnknownReceiverError(f"Receiver '{msg.receiver}' is not registered")
        self._inboxes[msg.receiver].append(msg)
        self.history.append(msg)

    def receive(self, name: str) -> List[Message]:
        msgs, self._inboxes[name] = self._inboxes[name], []
        return msgs

    def pending(self, names: Iterable[str]) -> int:
        return sum(len(self._inboxes.get(n, [])) for n in names)

    def log(self) -> List[dict]:
        return [m.to_dict() for m in self.history]
