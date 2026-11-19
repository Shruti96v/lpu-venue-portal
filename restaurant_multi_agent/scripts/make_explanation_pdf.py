"""
Builds docs/explanation.pdf (roles of files, data flow, why multi-agent, failures, viva Q&A).
Needs reportlab:   pip install -r requirements-docs.txt
Run from the project folder:   python scripts/make_explanation_pdf.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

OUT = Path(__file__).resolve().parent.parent / "docs" / "explanation.pdf"
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1e3a8a"))
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.6, leading=13.2, spaceAfter=4)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8.6, leading=11, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
Q = ParagraphStyle("Q", parent=BODY, fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=1, textColor=colors.HexColor("#111827"))
A = ParagraphStyle("A", parent=BODY, leftIndent=10)
BUL = ParagraphStyle("BUL", parent=BODY, leftIndent=14, bulletIndent=4)


def table(rows, widths, header=True):
    data = [[Paragraph(str(c), CELLB if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9ca3af")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")))
    t.setStyle(TableStyle(style))
    return t


def bullets(items):
    return [Paragraph(i, BUL, bulletText="-") for i in items]


story = [Paragraph("Restaurant Multi-Agent System - Explanation", ParagraphStyle("T", parent=ss["Title"], fontSize=20)),
         Paragraph("Four LLM-driven agents (Manager, Order, Kitchen, Billing) share one memory and cooperate by passing messages. "
                   "Plain Python plus the <b>openai</b> package pointed at Groq's OpenAI-compatible API. "
                   "An offline mock brain exists for testing only; it is <b>not</b> the real LLM.", BODY)]

# ---------------------------------------------------------------- 1 files
story.append(Paragraph("1. Role of each file", H1))
files = [
    ["File", "Role"],
    ["restaurant/config.py", "Settings: Groq URL, default model, step caps, tax and discount rules, tiny .env reader."],
    ["restaurant/menu.py", "Menu, prices, starting stock, and resolve_item() which turns 'paner tikka' into 'Paneer Tikka'."],
    ["restaurant/memory.py", "SharedMemory: orders, stock, bills and the message log (who told whom what)."],
    ["restaurant/trace.py", "The trace: records which agent acted, which tool it called, who handed off to whom."],
    ["restaurant/tools.py", "The Python functions agents call (add_item, check_stock, compute_bill ...), their JSON descriptions, and the business rules inside them."],
    ["restaurant/prompts.py", "One system prompt per agent. This is where each agent's job and rules are written."],
    ["restaurant/llm.py", "The brain interface. GroqLLM (real, via openai package, with retries and JSON-error handling) and get_llm() which chooses real or mock."],
    ["restaurant/mock_brain.py", "OFFLINE rule-based stand-in for the LLM. For testing only. Labelled everywhere as not the real brain."],
    ["restaurant/agents/base.py", "BaseAgent: the plan-act loop (call LLM, run tools, read results, repeat, step cap) and private history."],
    ["restaurant/agents/manager_agent.py", "Manager: its only tool is hand_off(agent, request). The LLM chooses the specialist."],
    ["restaurant/agents/order_agent.py, kitchen_agent.py, billing_agent.py", "The three specialists. Each = own prompt + own tool list + the shared loop."],
    ["restaurant/system.py", "RestaurantSystem: wires memory, trace and agents together; chat() runs one customer turn."],
    ["main.py", "Command-line chat with live trace."],
    ["app_streamlit.py", "Optional web UI: chat with one-click examples, colour-coded tab per agent, restaurant board (tables, bills, stock), full trace, key/model entry and a Test connection button."],
    ["restaurant/ui_helpers.py", "Pure-Python helpers for the UI (escaped event cards, table cards, stock rows). Tested without Streamlit."],
    ["check_groq.py", "One-command check that your Groq key, model and tool calling work, with plain-English fixes."],
    ["restaurant_demo.ipynb", "Notebook running 3 scenarios and printing the full trace."],
    ["tests/test_offline.py", "28 offline tests (tools, rules, flow, step cap, failures, routing, Groq adapter with a fake client)."],
    ["scripts/*.py", "Rebuild the notebook, the swimlane diagram and this PDF."],
    ["docs/", "swimlane_data_flow.png/.pdf and explanation.pdf."],
]
story.append(table(files, [62 * mm, 112 * mm]))

# ---------------------------------------------------------------- 2 data flow
story.append(Paragraph("2. Data flow (one customer message)", H1))
story.append(Paragraph("Example: <i>\"Table 4 wants 2 paneer tikka and 1 butter naan, one without onion\"</i>. The full picture is in swimlane_data_flow.png/.pdf.", BODY))
flow = [
    "<b>Customer to Manager.</b> RestaurantSystem.chat() starts a turn. The message is written to the message log and the trace.",
    "<b>Manager LLM call #1.</b> The manager prompt lists the specialists. The LLM answers with a tool call hand_off(agent='kitchen', request='...'). No keyword rules exist in the code: the choice is the LLM's output.",
    "<b>Hand-off is a message.</b> hand_off writes the request to the message log, then calls kitchen.receive(message). The kitchen runs its own loop with its own prompt and tools: check_stock for each dish, then a text answer.",
    "<b>Answer returns as a message.</b> The kitchen's text is logged and returned to the manager as the tool result. Manager LLM call #2 reads it and decides the next step.",
    "<b>Order agent.</b> The manager sends a self-contained request (table, dishes, quantities, notes). The order agent calls add_item per dish (the note 'without onion' goes on the naan) and get_order to confirm. add_item writes orders and reduces stock in shared memory.",
    "<b>Kitchen again.</b> estimate_time(4) reads the order and returns minutes.",
    "<b>Final reply.</b> A last manager LLM call combines all answers into one friendly reply. It is logged and returned to the customer.",
    "<b>Billing path.</b> 'Give me the bill for table 4' goes manager to billing: apply_discount (tool checks subtotal against the threshold), then compute_bill, then the manager phrases the reply.",
]
for i, step in enumerate(flow, 1):
    story.append(Paragraph(f"{i}. {step}", BUL))
story.append(Paragraph("Two kinds of memory: <b>shared</b> (orders, stock, bills, message log; all agents) and <b>private</b> (each agent's own conversation history, kept across turns).", BODY))

# ---------------------------------------------------------------- 3 why multi-agent
story.append(Paragraph("3. Why multi-agent instead of one agent?", H1))
story += bullets([
    "<b>Focus.</b> Each agent has a short prompt and 1-2 tools, so it has fewer ways to pick the wrong tool or forget a rule. One agent would carry six tools and every rule in one prompt.",
    "<b>Separation of duties.</b> The order agent cannot compute bills; the billing agent cannot edit orders. A mistake in one area cannot silently touch another.",
    "<b>Failure isolation.</b> If one agent breaks, the others still work (see section 4).",
    "<b>Testability.</b> Each agent and tool can be tested alone; the trace shows exactly which step went wrong.",
    "<b>Flexibility.</b> A different model, prompt or tool set per agent, and new agents are easy to add (one prompt, one tool list, one line in system.py).",
])
story.append(Paragraph("<b>Honest trade-off:</b> it costs more. Taking one order used 11 LLM calls in the offline test run and 14 in the first live Groq run (4 manager, 6 kitchen, 4 order, including one wasted kitchen call); a bill used 5 offline. A single agent might need 2 or 3. So this design is slower and uses more tokens. For a system this small, a single agent with six tools would also work; the multi-agent design is justified by clarity, safety and as a learning model, not by necessity.", BODY))

# ---------------------------------------------------------------- 4 failures
story.append(Paragraph("4. What happens if one agent fails?", H1))
fails = [
    ["Failure", "What the code does"],
    ["A specialist's LLM call errors (network, rate limit)", "GroqLLM retries up to 3 times (not for 401/403/404, which fail fast). If it still fails, BaseAgent.receive() catches the error and answers '[The kitchen agent is unavailable ...]'. The manager reads that as a normal message and tells the customer honestly. Other agents keep working. Tested."],
    ["The manager's LLM fails", "handle_customer() catches it and returns a polite fallback asking the customer to call a staff member. Tested."],
    ["An agent loops on tools forever", "The loop stops at the step cap (6 specialist, 8 manager), writes a STEP CAP trace event and returns partial results. Tested."],
    ["LLM sends broken JSON, an unknown tool or wrong arguments", "The agent returns an error result to the LLM (never crashes) so it can retry. Tested with a fake client."],
    ["LLM tries to break a rule (sell missing stock, wrong discount, tax 99%)", "The tool itself refuses. Rules live in code, not only in prompts. Tested."],
    ["An agent CLAIMS success but did not do the work (seen live on Groq: 2 of 4 dishes added, all 4 'confirmed')", "After every order task the code appends a [VERIFIED RECORD] line built from the tools' real results and shared memory. The manager prompt says to trust it and re-order missing dishes before replying. Regression test replays the lie. Not re-tested on the live model."],
    ["Manager names a specialist that does not exist", "hand_off returns an error listing valid names. Tested."],
]
story.append(table(fails, [58 * mm, 116 * mm]))
story.append(Paragraph("Not handled: if the Groq service is down for everyone, every agent fails and the customer only gets the fallback message. Nothing is saved to disk, so a restart loses the session.", BODY))

# ---------------------------------------------------------------- 5 viva
story.append(Paragraph("5. Likely viva questions and answers", H1))
qa = [
    ("What makes this truly multi-agent and not just four functions?",
     "Each agent makes its own LLM calls with its own system prompt, its own tool list and its own conversation history. They cooperate by sending messages, not by sharing one big prompt."),
    ("How is routing decided?",
     "By the manager LLM. Its only tool is hand_off(agent, request) and the prompt describes the specialists. The code never inspects the customer's words. A test gives the manager a scripted LLM that sends a 'bill' message to the kitchen and the system obeys, which shows the route comes only from the LLM's output. The offline mock uses keywords, which is exactly why it is labelled as not the real brain."),
    ("What is a plan-act loop?",
     "Ask the LLM what to do; if it asks for tools, run them and add the results to the history; ask again; stop when it answers in plain text. It is the same loop in every agent (agents/base.py)."),
    ("Why a maximum step count?",
     "LLMs can repeat the same tool call endlessly. The cap guarantees the program stops and returns partial results."),
    ("How do agents communicate?",
     "Through messages. hand_off writes a request into the shared message log and delivers it to the specialist; the specialist's answer is logged and returned. It is hub-and-spoke: specialists talk to the manager, not to each other."),
    ("Why hub-and-spoke rather than agents talking directly?",
     "One coordinator keeps the flow easy to follow and debug, and only one agent speaks to the customer. The cost is that every step passes through the manager (more LLM calls)."),
    ("What is shared and what is private?",
     "Shared: orders, stock, bills, message log. Private: each agent's own history (its system prompt, tasks, tool calls and results)."),
    ("Why are rules like the discount threshold inside the tool and not only in the prompt?",
     "A prompt is a request; code is a guarantee. apply_discount refuses below the threshold no matter what the LLM says, and add_item never lets stock go negative."),
    ("How do you stop an out-of-stock dish from being ordered?",
     "Two layers. The manager asks the kitchen first, and the kitchen flags it with an alternative. Even if the manager skipped that, add_item checks stock and refuses."),
    ("Why does the order agent not report prices?",
     "Pricing belongs to billing. Keeping get_order free of prices keeps the roles clean and means only one place computes money."),
    ("What if the LLM writes the dish name differently?",
     "resolve_item() matches names, aliases and small typos. Unknown dishes return an error that lists the menu so the LLM can retry. It deliberately does not guess (green tea does not become chai)."),
    ("Why the openai package with Groq?",
     "Groq exposes an OpenAI-compatible API, so the OpenAI client works by changing base_url to https://api.groq.com/openai/v1. The default model is openai/gpt-oss-120b because llama-3.3-70b-versatile is Enterprise-only and returns a 404 on other accounts."),
    ("What are the limits of this design?",
     "Session memory is in RAM only. Agent histories grow with every turn. The kitchen time estimate is a simple formula, not a real queue. Stock never refills. If the table number is missing the manager may reuse the last table in the conversation, which could be wrong. It runs one customer at a time. The live Groq behaviour was not tested in the build environment."),
    ("What went wrong when you tested with the real model, and what did you change?",
     "Four things. The kitchen agent made a pointless estimate_time call; the manager asked for a table number on a plain availability question; it asked the customer to confirm instead of ordering the available dishes; and worst, the order agent added only 2 of 4 dishes while the manager told the customer all 4 were confirmed, so the bill was wrong. The first three were prompt fixes. The last needed code: a VERIFIED RECORD line from shared memory that the manager must trust. Lesson: never let an LLM's description of what it did stand in for the actual data."),
    ("How would you add a Payment agent?",
     "Write its prompt in prompts.py, its tools in tools.py, a small class in agents/, add it to the specialists dict in system.py (the hand_off enum updates itself) and mention it in the manager prompt."),
]
for q, a in qa:
    story.append(KeepTogether([Paragraph("Q: " + q, Q), Paragraph(a, A)]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawString(18 * mm, 10 * mm, "Restaurant multi-agent system - explanation")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                      bottomMargin=18 * mm, title="Restaurant multi-agent system - explanation").build(story, onFirstPage=footer, onLaterPages=footer)
    print("Wrote", OUT)
