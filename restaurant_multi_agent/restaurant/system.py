"""
system.py - builds the whole restaurant (memory + trace + 4 agents) and runs customer turns.

    system = RestaurantSystem()           # real Groq brain if GROQ_API_KEY is set, else the mock
    result = system.chat("Table 4 wants 2 paneer tikka")
    print(result.reply)
    print(result.trace_text)
"""
from dataclasses import dataclass

from .agents import ManagerAgent, OrderAgent, KitchenAgent, BillingAgent
from .llm import get_llm
from .memory import SharedMemory
from .trace import Trace

MOCK_BANNER = ("*" * 72 + "\n  OFFLINE MOCK BRAIN IN USE - this is NOT the real LLM.\n"
               "  It is a rule-based stand-in so you can test without an API key.\n"
               "  Put GROQ_API_KEY in .env to use the real model.\n" + "*" * 72)


@dataclass
class TurnResult:
    turn: int
    reply: str
    trace_text: str
    events: list


class RestaurantSystem:
    def __init__(self, llm=None, use_mock=None, live_trace=False, quiet=False):
        self.llm = llm or get_llm(force_mock=use_mock)
        self.live_trace = live_trace
        self.reset()
        if self.llm.is_mock and not quiet:
            print(MOCK_BANNER)

    def reset(self):
        """Start a fresh session: new shared memory, new trace, new agents (empty histories)."""
        self.memory = SharedMemory()
        self.trace = Trace(live=self.live_trace)
        specialists = {
            "order": OrderAgent(self.llm, self.memory, self.trace),
            "kitchen": KitchenAgent(self.llm, self.memory, self.trace),
            "billing": BillingAgent(self.llm, self.memory, self.trace),
        }
        self.manager = ManagerAgent(self.llm, self.memory, self.trace, specialists)
        self.agents = {"manager": self.manager, **specialists}

    def chat(self, customer_message):
        self.memory.turn += 1
        self.trace.turn = self.memory.turn
        self.trace.customer(customer_message)
        reply = self.manager.handle_customer(customer_message)
        return TurnResult(self.memory.turn, reply, self.trace.render(self.memory.turn),
                          [e for e in self.trace.events if e.turn == self.memory.turn])
