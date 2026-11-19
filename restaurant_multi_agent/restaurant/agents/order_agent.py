"""Order agent: understands the order and notes. Tools: add_item, get_order."""
from .base import BaseAgent
from ..prompts import ORDER_PROMPT
from ..tools import make_order_tools
from .. import config


def _fmt(line):
    return f"{line['qty']} {line['item']}" + (f" ({line['note']})" if line.get("note") else "")


class OrderAgent(BaseAgent):
    def __init__(self, llm, memory, trace):
        super().__init__("order", ORDER_PROMPT, make_order_tools(memory), llm, memory, trace,
                         config.MAX_STEPS_SPECIALIST)

    def receipt(self):
        """
        An LLM can SAY it added everything while only adding some of it (this really happened on
        Groq). So after every task we append a record built from what the tools actually did and
        from shared memory. The manager is told to trust this line, not the agent's prose.
        """
        added, failed, tables = [], [], set()
        for name, args, result in self.task_results:
            try:
                tables.add(int(args.get("table")))
            except (TypeError, ValueError):
                pass
            if name == "add_item":
                if result.get("ok"):
                    added.append(_fmt(result))
                else:
                    failed.append(f"{args.get('item', '?')} ({result.get('error', 'failed')})")
        if not tables:
            return ""
        parts = ["[VERIFIED RECORD from shared memory]",
                 "Recorded this time: " + ("; ".join(added) if added else "nothing") + ".",]
        if failed:
            parts.append("NOT recorded: " + "; ".join(failed) + ".")
        for table in sorted(tables):
            lines = self.memory.orders.get(table, [])
            parts.append(f"Table {table} now has: " + ("; ".join(_fmt(l) for l in lines) if lines else "nothing") + ".")
        return " ".join(parts)
