"""
tools.py - the Python functions agents can call, plus how they are described to the LLM.

A Tool bundles three things:
  name         - what the LLM writes when it wants to call it
  description  - tells the LLM WHEN to use it
  parameters   - a JSON-schema listing the arguments (so the LLM knows what to send)
  func         - the real Python function that runs

Each agent gets its OWN list of tools. The Order agent cannot compute bills,
the Billing agent cannot change orders, and so on.

Business rules (stock can't go negative, discount only above a threshold) are enforced
INSIDE the tool code. That way a confused LLM cannot break the data.
"""
import math

from . import config
from .menu import MENU, resolve_item, suggest_items, money


class ToolError(Exception):
    """Raised for bad arguments; the agent turns it into an error result the LLM can read."""


class Tool:
    def __init__(self, name, description, parameters, func):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def schema(self):
        """The OpenAI 'function calling' description of this tool."""
        return {"type": "function",
                "function": {"name": self.name, "description": self.description,
                             "parameters": self.parameters}}

    def run(self, arguments):
        return self.func(**arguments)


def _to_int(value, field):
    try:
        return int(value)          # accepts 4 and "4"
    except (TypeError, ValueError):
        raise ToolError(f"'{field}' must be a whole number, got {value!r}")


def _unknown_dish(text):
    return {"ok": False, "error": f"'{text}' is not on the menu.",
            "did_you_mean": suggest_items(text), "menu": list(MENU)}


# =============================================================================
# ORDER agent tools
# =============================================================================
def make_order_tools(memory):

    def add_item(table, item, qty=1, note=""):
        table, qty = _to_int(table, "table"), _to_int(qty, "qty")
        if not 1 <= qty <= 20:
            raise ToolError("qty must be between 1 and 20")
        name = resolve_item(item)
        if name is None:
            return _unknown_dish(item)
        have = memory.stock.get(name, 0)
        if have < qty:                       # safety net: never sell what we do not have
            return {"ok": False, "item": name, "error": f"Only {have} {name} left, cannot add {qty}.",
                    "qty_left": have}
        memory.stock[name] = have - qty      # reserve the portions
        lines = memory.orders.setdefault(table, [])
        note = (note or "").strip()
        for line in lines:                   # same dish + same note -> just increase quantity
            if line["item"] == name and line["note"] == note:
                line["qty"] += qty
                break
        else:
            lines.append({"item": name, "qty": qty, "note": note, "unit_price": MENU[name]["price"]})
        memory.mark_bill_outdated(table)
        return {"ok": True, "table": table, "item": name, "qty": qty, "note": note}

    def get_order(table):
        table = _to_int(table, "table")
        lines = memory.orders.get(table, [])
        # prices are deliberately left out: pricing is the Billing agent's job
        shown = [{"item": l["item"], "qty": l["qty"], "note": l["note"]} for l in lines]
        return {"ok": True, "table": table, "lines": shown,
                "total_portions": sum(l["qty"] for l in lines)}

    return {t.name: t for t in [
        Tool("add_item",
             "Add a dish to a table's order. Call once per dish (use separate calls for the same dish with different notes).",
             {"type": "object", "properties": {
                 "table": {"type": "integer", "description": "Table number"},
                 "item": {"type": "string", "description": "Dish name, e.g. 'Paneer Tikka'"},
                 "qty": {"type": "integer", "description": "How many portions (default 1)"},
                 "note": {"type": "string", "description": "Special instruction, e.g. 'without onion'. Empty if none."}},
              "required": ["table", "item"]},
             add_item),
        Tool("get_order",
             "Read back everything currently ordered for a table.",
             {"type": "object", "properties": {"table": {"type": "integer"}}, "required": ["table"]},
             get_order),
    ]}


# =============================================================================
# KITCHEN agent tools
# =============================================================================
def make_kitchen_tools(memory):

    def check_stock(item):
        name = resolve_item(item)
        if name is None:
            return _unknown_dish(item)
        left = memory.stock.get(name, 0)
        alternative = None
        if left <= 0:                        # suggest an in-stock dish from the same category
            for other, data in MENU.items():
                if other != name and data["category"] == MENU[name]["category"] and memory.stock.get(other, 0) > 0:
                    alternative = {"item": other, "qty_left": memory.stock[other]}
                    break
        return {"ok": True, "item": name, "in_stock": left > 0, "qty_left": left, "alternative": alternative}

    def estimate_time(table):
        table = _to_int(table, "table")
        lines = memory.orders.get(table, [])
        if not lines:
            return {"ok": False, "error": f"Table {table} has no order yet."}
        slowest = max(MENU[l["item"]]["prep_min"] for l in lines)
        extra_portions = sum(l["qty"] for l in lines) - 1           # +1 min per extra portion
        busy_tables = len([t for t, ls in memory.orders.items() if ls and t != table])
        load = min(10, 2 * busy_tables)                              # +2 min per other busy table (max 10)
        return {"ok": True, "table": table, "minutes": slowest + extra_portions + load,
                "how": f"slowest dish {slowest} + {extra_portions} extra portions + {load} kitchen load"}

    return {t.name: t for t in [
        Tool("check_stock",
             "Check whether a dish can be cooked right now. Returns portions left and, if out of stock, an alternative.",
             {"type": "object", "properties": {"item": {"type": "string", "description": "Dish name"}},
              "required": ["item"]},
             check_stock),
        Tool("estimate_time",
             "Estimate minutes until a table's food is ready. The table must already have an order.",
             {"type": "object", "properties": {"table": {"type": "integer"}}, "required": ["table"]},
             estimate_time),
    ]}


# =============================================================================
# BILLING agent tools
# =============================================================================
def make_billing_tools(memory):

    def _subtotal(table):
        return sum(l["qty"] * l["unit_price"] for l in memory.orders.get(table, []))

    def apply_discount(table):
        table = _to_int(table, "table")
        subtotal = _subtotal(table)
        if subtotal == 0:
            return {"ok": False, "error": f"Table {table} has no order yet."}
        if subtotal < config.DISCOUNT_THRESHOLD:     # the RULE lives here, not in the LLM
            return {"ok": True, "applied": False, "subtotal": subtotal,
                    "threshold": config.DISCOUNT_THRESHOLD,
                    "reason": f"Subtotal {money(subtotal)} is below {money(config.DISCOUNT_THRESHOLD)}."}
        bill = memory.bills.setdefault(table, {"status": "open"})
        bill["discount_percent"] = config.DISCOUNT_PERCENT
        return {"ok": True, "applied": True, "subtotal": subtotal, "threshold": config.DISCOUNT_THRESHOLD,
                "discount_percent": config.DISCOUNT_PERCENT}

    def compute_bill(table, tax_percent=config.DEFAULT_TAX_PERCENT):
        table = _to_int(table, "table")
        try:
            tax_percent = float(tax_percent)
        except (TypeError, ValueError):
            raise ToolError(f"'tax_percent' must be a number, got {tax_percent!r}")
        if not 0 <= tax_percent <= 28 or math.isnan(tax_percent):
            raise ToolError("tax_percent must be between 0 and 28")
        lines = memory.orders.get(table, [])
        if not lines:
            return {"ok": False, "error": f"Table {table} has no order yet, so there is nothing to bill."}
        subtotal = _subtotal(table)
        previous = memory.bills.get(table, {})
        discount_percent = previous.get("discount_percent", 0)
        discount = round(subtotal * discount_percent / 100, 2)
        tax = round((subtotal - discount) * tax_percent / 100, 2)
        bill = {
            "status": "prepared", "table": table,
            "lines": [{"item": l["item"], "qty": l["qty"], "note": l["note"],
                       "line_total": l["qty"] * l["unit_price"]} for l in lines],
            "subtotal": subtotal, "discount_percent": discount_percent, "discount": discount,
            "tax_percent": tax_percent, "tax": tax, "total": round(subtotal - discount + tax, 2),
        }
        memory.bills[table] = bill
        return {"ok": True, **bill}

    return {t.name: t for t in [
        Tool("apply_discount",
             "Apply the house discount to a table. The tool itself checks eligibility (only when the subtotal crosses the threshold) and tells you whether it was applied. Call this BEFORE compute_bill.",
             {"type": "object", "properties": {"table": {"type": "integer"}}, "required": ["table"]},
             apply_discount),
        Tool("compute_bill",
             "Compute the final bill for a table: subtotal, discount (if applied), tax and total.",
             {"type": "object", "properties": {
                 "table": {"type": "integer"},
                 "tax_percent": {"type": "number", "description": "Tax percentage, normally 5"}},
              "required": ["table"]},
             compute_bill),
    ]}
