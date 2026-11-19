"""Billing agent: prepares the bill. Tools: compute_bill, apply_discount."""
from .base import BaseAgent
from ..prompts import BILLING_PROMPT
from ..tools import make_billing_tools
from .. import config


class BillingAgent(BaseAgent):
    def __init__(self, llm, memory, trace):
        super().__init__("billing", BILLING_PROMPT, make_billing_tools(memory), llm, memory, trace,
                         config.MAX_STEPS_SPECIALIST)
