import math
from agents.base_agent import BaseAgent
from models.schemas import Order, PortfolioState

ALLOCATION = 0.10  # BUY spends up to 10% of cash; SELL exits half the position


class ExecutionAgent(BaseAgent):
    name = "Execution Agent"
    agent_type = "Reactive (simulation only)"
    goal = "Apply the instructed action to the SIMULATED portfolio"

    def __init__(self, bus, portfolio: PortfolioState, fail=False):
        super().__init__(bus, fail)
        self.portfolio = portfolio

    def handle(self, m):
        if m.message_type != "ORDER_INSTRUCTION":
            return
        p = m.payload
        try:
            if self.fail:
                raise RuntimeError("Execution Agent simulated failure")
            order = self.execute(p["symbol"], p["action"], p.get("price"))
        except Exception as exc:
            order = Order(p.get("symbol", "?"), p.get("action", "?"), 0, p.get("price"), "FAILED", str(exc))
        self.send("Orchestrator", "EXECUTION_CONFIRMATION", order.to_payload())

    def execute(self, symbol, action, price) -> Order:
        s = self.portfolio
        if action == "HOLD":
            order = Order(symbol, action, 0, price, "NO_ACTION", "Hold - no transaction")
        elif price is None or price <= 0:
            order = Order(symbol, action, 0, price, "REJECTED", "No valid price available")
        elif action == "BUY":
            qty = int((s.balance * ALLOCATION) // price)
            if qty == 0 and s.balance >= price:
                qty = 1
            if qty < 1:
                order = Order(symbol, action, 0, price, "REJECTED", "Insufficient simulated balance")
            else:
                cost = round(qty * price, 2)
                s.balance = round(s.balance - cost, 2)
                s.holdings[symbol] = s.holdings.get(symbol, 0) + qty
                order = Order(symbol, action, qty, price, "SUCCESS", "Simulated buy filled", cost)
        elif action == "SELL":
            held = s.holdings.get(symbol, 0)
            if held <= 0:
                order = Order(symbol, action, 0, price, "SKIPPED", "No simulated holdings to sell")
            else:
                qty = math.ceil(held / 2)
                proceeds = round(qty * price, 2)
                s.balance = round(s.balance + proceeds, 2)
                s.holdings[symbol] = held - qty
                order = Order(symbol, action, qty, price, "SUCCESS", "Simulated sell filled", proceeds)
        else:
            order = Order(symbol, action, 0, price, "REJECTED", f"Unknown action {action}")
        s.history.append({"symbol": symbol, "action": action, "quantity": order.quantity,
                          "price": price, "status": order.status, "value": order.total_value})
        return order
