"""Kitchen agent: can this dish be cooked? Tools: check_stock, estimate_time."""
from .base import BaseAgent
from ..prompts import KITCHEN_PROMPT
from ..tools import make_kitchen_tools
from .. import config


class KitchenAgent(BaseAgent):
    def __init__(self, llm, memory, trace):
        super().__init__("kitchen", KITCHEN_PROMPT, make_kitchen_tools(memory), llm, memory, trace,
                         config.MAX_STEPS_SPECIALIST)
