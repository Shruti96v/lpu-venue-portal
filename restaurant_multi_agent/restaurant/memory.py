"""
memory.py - the SHARED memory every agent can read and write.

It holds four things:
  1. orders       - what each table has ordered
  2. stock        - portions left in the kitchen
  3. bills        - the bill (and its status) for each table
  4. message_log  - who told whom what (this is how agents "talk")

It lives for the whole session, so turn 2 can see what happened in turn 1.
(Each agent ALSO keeps its own private conversation history - see agents/base.py.)
"""
import copy
from dataclasses import dataclass

from .menu import INITIAL_STOCK


@dataclass
class Message:
    """One entry in the message log."""
    id: int
    turn: int
    sender: str      # "customer", "manager", "order", "kitchen", "billing"
    receiver: str
    kind: str        # "customer", "request", "response", "reply"
    content: str


class SharedMemory:
    def __init__(self):
        self.orders = {}                 # table number -> list of line dicts
        self.stock = dict(INITIAL_STOCK)  # dish name -> portions left
        self.bills = {}                  # table number -> bill dict
        self.message_log = []            # list of Message
        self.turn = 0                    # current customer turn

    # ---- message passing ----------------------------------------------------
    def post_message(self, sender, receiver, content, kind):
        msg = Message(len(self.message_log) + 1, self.turn, sender, receiver, kind, content)
        self.message_log.append(msg)
        return msg

    # ---- small helpers used by tools ---------------------------------------
    def bill_status(self, table):
        return self.bills.get(table, {}).get("status", "none")

    def mark_bill_outdated(self, table):
        """If items are added after a bill was made, that bill is no longer correct."""
        if table in self.bills and self.bills[table].get("status") == "prepared":
            self.bills[table]["status"] = "outdated"

    def snapshot(self):
        """A plain-dict copy of everything (handy for printing / the Streamlit UI)."""
        return {
            "orders": copy.deepcopy(self.orders),
            "stock": dict(self.stock),
            "bills": copy.deepcopy(self.bills),
            "message_log": [m.__dict__.copy() for m in self.message_log],
        }
