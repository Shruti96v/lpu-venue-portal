"""
trace.py - a running diary of everything that happens.

Every event records WHICH agent acted and WHAT it did:
  customer     - the customer's message arrived
  handoff      - one agent passed work to another  (manager -> kitchen)
  tool_call    - an agent called one of its tools
  tool_result  - what the tool returned
  answer       - a specialist's final answer (goes back to the manager)
  handoff_back - the answer arriving back at the caller
  reply        - the manager's final reply to the customer
  error / step_cap - something went wrong
Indentation shows nesting: specialist work is indented under the manager's hand-off.
"""
import json
from dataclasses import dataclass, field


@dataclass
class Event:
    seq: int
    turn: int
    kind: str
    agent: str        # who acted
    depth: int        # 0 = manager level, 1 = inside a specialist
    text: str
    data: dict = field(default_factory=dict)


TAGS = {
    "customer": "CUSTOMER", "handoff": "HANDOFF", "tool_call": "TOOL CALL",
    "tool_result": "TOOL RESULT", "answer": "ANSWER", "handoff_back": "HANDOFF BACK",
    "reply": "REPLY", "error": "ERROR", "step_cap": "STEP CAP",
}


class Trace:
    def __init__(self, live=False):
        self.events = []
        self.turn = 0
        self.depth = 0        # the manager increases this while a specialist is working
        self.live = live      # True -> also print each event immediately

    def _add(self, kind, agent, text, **data):
        event = Event(len(self.events) + 1, self.turn, kind, agent, self.depth, text, data)
        self.events.append(event)
        if self.live:
            print(self.format_event(event))
        return event

    # ---- one method per kind of event --------------------------------------
    def customer(self, text):
        return self._add("customer", "customer", text, src="customer", dst="manager")

    def handoff(self, src, dst, text):
        return self._add("handoff", src, text, src=src, dst=dst)

    def handoff_back(self, src, dst, text):
        return self._add("handoff_back", src, text, src=src, dst=dst)

    def tool_call(self, agent, step, tool, args):
        return self._add("tool_call", agent, f"{tool}({_short_args(args)})", step=step, tool=tool, args=args)

    def tool_result(self, agent, tool, result):
        return self._add("tool_result", agent, json.dumps(result, ensure_ascii=False), tool=tool, result=result)

    def answer(self, agent, text):
        return self._add("answer", agent, text)

    def reply(self, text):
        return self._add("reply", "manager", text, src="manager", dst="customer")

    def error(self, agent, text):
        return self._add("error", agent, text)

    def step_cap(self, agent, cap):
        return self._add("step_cap", agent, f"stopped after {cap} steps (step cap reached)")

    # ---- printing ------------------------------------------------------------
    def format_event(self, e, width=230):
        pad = "    " * e.depth
        text = e.text if len(e.text) <= width else e.text[: width - 3] + "..."
        if e.kind in ("customer", "handoff", "handoff_back", "reply"):
            who = f"{e.data['src']} -> {e.data['dst']}"
        else:
            who = e.agent
        step = f" (step {e.data['step']})" if e.kind == "tool_call" else ""
        return f"{pad}[{TAGS[e.kind]}] {who}{step}: {text}"

    def render(self, turn=None):
        events = [e for e in self.events if turn is None or e.turn == turn]
        return "\n".join(self.format_event(e) for e in events)

    def events_for_agent(self, agent):
        """Everything one agent did, plus hand-offs sent to / returned by it."""
        return [e for e in self.events
                if e.agent == agent or e.data.get("dst") == agent]


def _short_args(args):
    return ", ".join(f"{k}={v!r}" for k, v in args.items())
