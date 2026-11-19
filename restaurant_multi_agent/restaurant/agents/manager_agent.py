"""
Manager agent: the coordinator.

Its ONLY tool is hand_off(agent, request). Which specialist to call is decided by the LLM
(from the manager prompt) - there is no if/else on keywords anywhere in this file.
A hand-off is a real message: it is written to the shared message log, the specialist
receives it, runs its own loop, and its answer comes back as another message.
"""
from .base import BaseAgent
from ..llm import LLMError
from ..prompts import MANAGER_PROMPT
from ..tools import Tool
from .. import config

APOLOGY = "I'm sorry, I'm having trouble right now. Could you please ask a staff member to help you?"


class ManagerAgent(BaseAgent):
    def __init__(self, llm, memory, trace, specialists):
        self.specialists = specialists                       # {"order": OrderAgent, ...}
        hand_off = Tool(
            "hand_off",
            "Send a self-contained request to a specialist agent and wait for its reply.",
            {"type": "object", "properties": {
                "agent": {"type": "string", "enum": list(specialists), "description": "Which specialist"},
                "request": {"type": "string", "description": "Self-contained instruction with table number, dishes, quantities, notes"}},
             "required": ["agent", "request"]},
            self._hand_off)
        super().__init__("manager", MANAGER_PROMPT, {"hand_off": hand_off}, llm, memory, trace,
                         config.MAX_STEPS_MANAGER)
        self.quiet_tools = {"hand_off"}                      # the HANDOFF BACK line already shows the result

    def _hand_off(self, agent, request):
        key = str(agent).lower().strip()
        if key not in self.specialists:
            return {"ok": False, "error": f"No agent called '{agent}'. Choose from {list(self.specialists)}."}
        message = self.memory.post_message("manager", key, request, kind="request")   # send
        self.trace.handoff("manager", key, request)
        self.trace.depth += 1
        try:
            reply = self.specialists[key].receive(message)                              # specialist works
        finally:
            self.trace.depth -= 1
        self.trace.handoff_back(key, "manager", reply.content)
        return {"ok": True, "from": key, "reply": reply.content}

    def handle_customer(self, text):
        """One customer turn: log the message, run the loop, log and return the final reply."""
        self.memory.post_message("customer", "manager", text, kind="customer")
        try:
            answer = self.run(text) or APOLOGY
        except LLMError as err:
            self.trace.error("manager", str(err))
            answer = APOLOGY
        self.memory.post_message("manager", "customer", answer, kind="reply")
        self.trace.reply(answer)
        return answer
