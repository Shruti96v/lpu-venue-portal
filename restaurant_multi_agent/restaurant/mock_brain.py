"""
mock_brain.py - an OFFLINE stand-in for the LLM, for testing without an API key.

!!! THIS IS NOT THE REAL BRAIN !!!
It uses keyword rules and regular expressions. The real system's routing is decided by the
LLM (see agents/manager.py + prompts.py). The mock only imitates the SAME protocol
(text, or tool calls) so that the agents, tools, memory and trace can be tested offline.

How it behaves like a plan-act loop: every call it looks at the messages of the CURRENT task,
sees which tool results already came back, and decides the next step.
"""
import json
import re

from .llm import BaseLLM, LLMReply, ToolCall, MOCK_LABEL
from .menu import alias_pairs, money
from . import config

NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
NOTE_RE = re.compile(r"\b(without|no|extra|less|more)\s+([a-z]+(?:\s+or\s+[a-z]+)?)")


# ----------------------------------------------------------------------------
# Small text-parsing helpers (shared by all mock agents)
# ----------------------------------------------------------------------------
def find_table(text):
    m = re.search(r"table\s*(?:no\.?|number|#)?\s*(\d+)", text, re.I)
    return int(m.group(1)) if m else None


def parse_items(text):
    """'2 paneer tikka and 1 butter naan, one without onion' ->
       [{'item': 'Paneer Tikka', 'qty': 2, 'note': ''}, {'item': 'Butter Naan', 'qty': 1, 'note': 'without onion'}]"""
    t = re.sub(r"table\s*(?:no\.?|number|#)?\s*\d+", " ", text.lower())
    items = []
    for segment in re.split(r",|;|\+|\band\b", t):
        found = None
        for alias, name in alias_pairs():                     # longest names first
            # the quantity may sit up to two filler words away: "2 paner tikka", "a plate of tikka"
            m = re.search(rf"(?:\b(\d+|{'|'.join(NUMBER_WORDS)})\s*(?:x\s*)?(?:[a-z]+\s+){{0,2}}?)?\b{re.escape(alias)}s?\b", segment)
            if m:
                word = m.group(1)
                qty = int(word) if word and word.isdigit() else NUMBER_WORDS.get(word, 1)
                found = {"item": name, "qty": qty, "note": ""}
                break
        note = NOTE_RE.search(segment)
        if found:
            if note:
                found["note"] = note.group(0)
            items.append(found)
        elif note and items:                                  # "one without onion" -> previous dish
            items[-1]["note"] = note.group(0)
    return items


def format_items(items):
    return ", ".join(f"{i['qty']} {i['item']}" + (f" ({i['note']})" if i["note"] else "") for i in items)


def classify(text):
    """Very crude intent detection - only used by the MOCK."""
    t = text.lower()
    if re.search(r"\b(bill|invoice|check please|pay)\b", t):
        return "bill"
    if re.search(r"\b(available|in stock|do you have|have you got|is there)\b", t):
        return "availability"
    if re.search(r"\b(how long|wait|eta|ready|minutes)\b", t):
        return "time"
    if re.search(r"read back|so far|what.*order", t):
        return "summary"
    if parse_items(text) or re.search(r"\b(want|wants|add|order|bring|need|give me)\b", t):
        return "order"
    return "chitchat"


def _tool_pairs(this_task):
    """[(tool_name, arguments, result_dict)] for the tool calls already made in this task."""
    results = {m["tool_call_id"]: json.loads(m["content"]) for m in this_task if m["role"] == "tool"}
    pairs = []
    for m in this_task:
        for call in m.get("tool_calls", []) or []:
            pairs.append((call["function"]["name"], json.loads(call["function"]["arguments"]),
                          results.get(call["id"], {})))
    return pairs


# ----------------------------------------------------------------------------
class MockLLM(BaseLLM):
    is_mock = True
    label = MOCK_LABEL

    def __init__(self):
        self._counter = 0

    # -- plumbing ------------------------------------------------------------
    def chat(self, agent_name, messages, tools):
        last_user = max(i for i, m in enumerate(messages) if m["role"] == "user")
        task = messages[last_user]["content"]
        handler = {"manager": self._manager, "order": self._order,
                   "kitchen": self._kitchen, "billing": self._billing}[agent_name]
        return handler(task, messages[last_user + 1:], messages[:last_user])

    def _say(self, text):
        return LLMReply(content=text)

    def _call(self, *calls):
        out = []
        for name, args in calls:
            self._counter += 1
            out.append(ToolCall(id=f"mock_{self._counter}", name=name, arguments=args,
                                raw_arguments=json.dumps(args)))
        return LLMReply(content=None, tool_calls=out)

    # -- manager -------------------------------------------------------------
    def _manager(self, text, this_task, earlier):
        # the order agent appends a '[VERIFIED RECORD ...]' line for the manager; the mock does not repeat it to the customer
        done = [(a["agent"], r.get("reply", r.get("error", "")).split("\n[VERIFIED")[0]) for n, a, r in _tool_pairs(this_task)]
        table = find_table(text)
        if table is None:                                     # look back in the conversation
            for m in reversed(earlier):
                if m["role"] == "user" and find_table(m["content"]):
                    table = find_table(m["content"])
                    break
        intent = classify(text)
        if intent == "chitchat":
            return self._say("Hello! I can take your order, check if a dish is available, or prepare your bill. What would you like?")
        if table is None and intent in ("bill", "order", "time", "summary"):
            return self._say("Sure! Which table is this for?")

        if intent == "bill":
            if not done:
                return self._call(("hand_off", {"agent": "billing", "request": f"Prepare the final bill for table {table}. Customer said: {text}"}))
            return self._say(f"Of course! {done[0][1]} Anything else I can get you?")

        if intent == "availability":
            if not done:
                return self._call(("hand_off", {"agent": "kitchen", "request": f"Check stock for: {text}"}))
            return self._say(done[0][1])

        if intent == "time":
            if not done:
                return self._call(("hand_off", {"agent": "kitchen", "request": f"Estimate the preparation time for table {table}."}))
            return self._say(done[0][1])

        if intent == "summary":
            if not done:
                return self._call(("hand_off", {"agent": "order", "request": f"Read back the current order for table {table}."}))
            return self._say(done[0][1])

        # ---- order: kitchen check -> order agent -> kitchen time -------------
        items = parse_items(text)
        if not items:
            return self._say("Happy to help! Which dishes would you like?")
        if not done:
            return self._call(("hand_off", {"agent": "kitchen", "request": f"Check whether we can cook these for table {table}: {format_items(items)}"}))
        stock_reply = done[0][1]
        unavailable = re.findall(r"Sorry, (.+?) is out of stock", stock_reply)
        available = [i for i in items if i["item"] not in unavailable]
        if len(done) == 1:
            if not available:
                return self._say(stock_reply)
            return self._call(("hand_off", {"agent": "order", "request": f"Table {table}: add {format_items(available)}"}))
        if len(done) == 2:
            return self._call(("hand_off", {"agent": "kitchen", "request": f"Estimate the preparation time for table {table}."}))
        order_reply, time_reply = done[1][1], done[2][1]
        oos_note = " ".join(re.findall(r"Sorry, .+?\?", stock_reply))
        return self._say(f"Certainly! {order_reply} {oos_note} {time_reply}".replace("  ", " ").strip())

    # -- order agent ---------------------------------------------------------
    def _order(self, text, this_task, earlier):
        table = find_table(text)
        pairs = _tool_pairs(this_task)
        items = parse_items(text)
        if not pairs:
            if items:
                return self._call(*[("add_item", {"table": table, "item": i["item"], "qty": i["qty"], "note": i["note"]}) for i in items])
            return self._call(("get_order", {"table": table}))
        adds = [(a, r) for n, a, r in pairs if n == "add_item"]
        reads = [r for n, a, r in pairs if n == "get_order"]
        if adds and not reads and any(r.get("ok") for a, r in adds):
            return self._call(("get_order", {"table": table}))
        parts = []
        added = [a for a, r in adds if r.get("ok")]
        if added:
            parts.append("Added " + ", ".join(f"{a['qty']} x {a['item']}" + (f" ({a['note']})" if a.get("note") else "") for a in added) + f" to table {table}.")
        for a, r in adds:
            if not r.get("ok"):
                parts.append(f"I could not add {a['item']}: {r.get('error')}")
        if reads:
            r = reads[0]
            if r["lines"] and not adds:
                parts.append(f"Table {table} has: " + ", ".join(f"{l['qty']} x {l['item']}" + (f" ({l['note']})" if l['note'] else "") for l in r["lines"]) + ".")
            elif not r["lines"]:
                parts.append(f"Table {table} has no order yet.")
            else:
                n = r['total_portions']
                parts.append(f"Table {table} now has {n} portion{'s' if n != 1 else ''} in total.")
        return self._say(" ".join(parts))

    # -- kitchen agent -------------------------------------------------------
    def _kitchen(self, text, this_task, earlier):
        pairs = _tool_pairs(this_task)
        if re.search(r"\b(estimate|how long|preparation time|ready)\b", text.lower()):
            table = find_table(text)
            if not pairs:
                return self._call(("estimate_time", {"table": table}))
            r = pairs[0][2]
            if not r.get("ok"):
                return self._say(r.get("error", "I could not estimate the time."))
            m = r['minutes']
            return self._say(f"Table {table}'s food should be ready in about {m} minute{'s' if m != 1 else ''}.")
        items = parse_items(text)
        if not items:                                         # e.g. "is the dal makhni available?"
            guess = re.search(r"(?:is|are|have|there)\s+(?:the\s+|any\s+|a\s+)?([a-z ]+?)\s*(?:available|in stock|today|\?|$)", text.lower())
            items = [{"item": guess.group(1).strip(), "qty": 1, "note": ""}] if guess else []
        if not items:
            return self._say("Which dish should I check?")
        if not pairs:
            return self._call(*[("check_stock", {"item": i["item"]}) for i in items])
        parts = []
        for (n, a, r), wanted in zip(pairs, items):
            if not r.get("ok"):
                hint = f" Did you mean {' or '.join(r['did_you_mean'])}?" if r.get("did_you_mean") else ""
                parts.append(f"I could not find '{a['item']}' on our menu.{hint}")
            elif not r["in_stock"]:
                alt = r.get("alternative")
                parts.append(f"Sorry, {r['item']} is out of stock today." +
                             (f" May I suggest {alt['item']} instead?" if alt else " Nothing similar is available right now."))
            elif r["qty_left"] < wanted["qty"]:
                parts.append(f"Only {r['qty_left']} {r['item']} left, you asked for {wanted['qty']}.")
            else:
                parts.append(f"{r['item']} is available.")
        return self._say(" ".join(parts))

    # -- billing agent -------------------------------------------------------
    def _billing(self, text, this_task, earlier):
        table = find_table(text)
        pairs = _tool_pairs(this_task)
        if not pairs:
            return self._call(("apply_discount", {"table": table}))
        names = [n for n, a, r in pairs]
        if "compute_bill" not in names:
            if not pairs[0][2].get("ok"):
                return self._say(pairs[0][2].get("error", "Cannot bill this table."))
            pct = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
            return self._call(("compute_bill", {"table": table, "tax_percent": float(pct.group(1)) if pct else config.DEFAULT_TAX_PERCENT}))
        disc, bill = pairs[0][2], pairs[1][2]
        if not bill.get("ok"):
            return self._say(bill.get("error", "I could not prepare the bill."))
        lines = ", ".join(f"{l['qty']} x {l['item']} {money(l['line_total'])}" for l in bill["lines"])
        text_out = f"Bill for table {table}: {lines}. Subtotal {money(bill['subtotal'])}."
        if disc.get("applied"):
            text_out += f" Discount {bill['discount_percent']}%: -{money(bill['discount'])}."
        else:
            text_out += f" No discount this time (it starts at {money(disc.get('threshold', config.DISCOUNT_THRESHOLD))})."
        text_out += f" Tax {bill['tax_percent']:g}%: {money(bill['tax'])}. Total {money(bill['total'])}."
        return self._say(text_out)
