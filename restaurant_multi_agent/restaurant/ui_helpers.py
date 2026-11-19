"""
ui_helpers.py - small pure-Python helpers the Streamlit UI uses (kept separate so they can be tested
without Streamlit). Nothing here talks to the LLM.
"""
import html

AGENT_STYLE = {   # name -> (colour, label)
    "customer": ("#6b7280", "Customer"),
    "manager": ("#2563eb", "Manager"),
    "order": ("#16a34a", "Order"),
    "kitchen": ("#ea580c", "Kitchen"),
    "billing": ("#7c3aed", "Billing"),
}

KIND_LABEL = {
    "customer": "customer says", "handoff": "hands off", "handoff_back": "answers back",
    "tool_call": "calls tool", "tool_result": "tool returned", "answer": "final answer",
    "reply": "replies to customer", "error": "ERROR", "step_cap": "STEP CAP reached",
}

LOW_STOCK = 3


def event_card_html(event):
    """One trace event -> a small coloured HTML card (all text is HTML-escaped)."""
    colour, name = AGENT_STYLE.get(event.agent, ("#6b7280", event.agent))
    if event.kind in ("error", "step_cap"):
        colour = "#dc2626"
    if event.kind in ("handoff", "handoff_back", "customer", "reply"):
        src, dst = event.data["src"], event.data["dst"]
        who = f"{AGENT_STYLE.get(src, ('', src))[1]} &rarr; {AGENT_STYLE.get(dst, ('', dst))[1]}"
    else:
        who = html.escape(name)
    body = html.escape(event.text)
    if event.kind == "tool_call":
        body = f"<code>{body}</code>"
    elif event.kind == "tool_result":
        body = f"<code style='font-size:0.8em'>{body[:400]}</code>"
    return (f"<div style='border-left:5px solid {colour};background:{colour}12;padding:6px 10px;"
            f"margin:4px 0;border-radius:4px;font-size:0.9em'>"
            f"<b style='color:{colour}'>{who}</b> "
            f"<span style='color:#6b7280'>{KIND_LABEL.get(event.kind, event.kind)}</span><br>{body}</div>")


def table_cards(memory):
    """[{table, lines:[str], status, total}] for every table that has an order."""
    cards = []
    for table in sorted(memory.orders):
        lines = [f"{l['qty']} x {l['item']}" + (f"  ({l['note']})" if l["note"] else "")
                 for l in memory.orders[table]]
        bill = memory.bills.get(table, {})
        cards.append({"table": table, "lines": lines, "status": memory.bill_status(table),
                      "total": bill.get("total") if bill.get("status") == "prepared" else None})
    return cards


def stock_rows(memory):
    """Stock as table rows, lowest first, with a status word."""
    rows = []
    for item, qty in sorted(memory.stock.items(), key=lambda kv: (kv[1], kv[0])):
        state = "OUT" if qty <= 0 else ("low" if qty <= LOW_STOCK else "ok")
        rows.append({"Dish": item, "Left": qty, "Status": state})
    return rows


def activity_summary(trace):
    """How many tool calls / hand-offs / errors so far (for the metrics strip)."""
    kinds = [e.kind for e in trace.events]
    return {"hand-offs": kinds.count("handoff"), "tool calls": kinds.count("tool_call"),
            "errors": kinds.count("error") + kinds.count("step_cap")}


EXAMPLES = [
    "Table 4 wants 2 paneer tikka and 1 butter naan, one without onion",
    "Add a cold drink to table 4",
    "Is the dal makhani available?",
    "Table 5 wants 2 butter chicken, 2 garlic naan, 1 veg biryani and 2 gulab jamun",
    "Give me the bill for table 4",
    "Give me the bill for table 5",
]
