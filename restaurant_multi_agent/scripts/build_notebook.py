"""
Builds restaurant_demo.ipynb and fills in the output of every cell by executing the code cells
in plain Python (stdout captured). Use this when Jupyter is not available.
In Jupyter you can simply 'Run All' - you will get the same cells, run by a real kernel.

Run from the project folder:   python scripts/build_notebook.py
"""
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

MD, CODE = "markdown", "code"
cells = [
(MD, """# Restaurant multi-agent system - 3 example scenarios

Four LLM-driven agents (Manager, Order, Kitchen, Billing) share one memory and pass work to each other as messages.
For each scenario we print the **full trace**: which agent acted, which tool it called, and who handed off to whom.

> The outputs saved in this notebook were produced with the **offline MOCK brain** (a rule-based stand-in, *not* the real LLM).
> If `GROQ_API_KEY` is in your `.env`, re-running the cells uses the real Groq model automatically and the traces will differ."""),
(CODE, """import os, sys
if not os.path.isdir("restaurant"):
    raise RuntimeError("Start Jupyter from the project folder (the one that contains the 'restaurant' folder).")
sys.path.insert(0, os.getcwd())

from restaurant import RestaurantSystem"""),
(CODE, """def run_scenario(title, messages):
    \"\"\"Start a fresh restaurant session and send each customer message in order.\"\"\"
    print("=" * 100)
    print(title)
    print("=" * 100)
    system = RestaurantSystem()                      # real Groq brain if a key exists, else the mock
    print("Brain:", system.llm.label, "\\n")
    for text in messages:
        result = system.chat(text)
        print(f"----- Turn {result.turn} " + "-" * 80)
        print(result.trace_text)                     # the full multi-agent trace for this turn
        print(f"\\nFINAL REPLY TO CUSTOMER: {result.reply}\\n")
    return system"""),
(MD, """## Scenario 1 - taking an order with a special note, then adding to it
Shows: Manager -> Kitchen (stock check) -> Order (add items + note) -> Kitchen (time estimate), and **memory persisting across turns** (the second message only says "table 4")."""),
(CODE, """s1 = run_scenario("SCENARIO 1: order with a note, then add a drink", [
    "Table 4 wants 2 paneer tikka and 1 butter naan, one without onion",
    "Add a cold drink to table 4",
])"""),
(MD, """## Scenario 2 - an out-of-stock dish
Shows: the Kitchen agent flags the dish and suggests an alternative; the Manager only sends the available dishes to the Order agent."""),
(CODE, """s2 = run_scenario("SCENARIO 2: out-of-stock dish and alternative", [
    "Is the dal makhani available?",
    "Table 2 wants 1 dal makhani and 2 butter naan",
])"""),
(MD, """## Scenario 3 - billing, with and without a discount
Table 4 is a small order (below the Rs.1000 threshold -> no discount). Table 5 is a big order (above it -> 10% discount). The **tool** enforces that rule, not the LLM."""),
(CODE, """s3 = run_scenario("SCENARIO 3: bills with and without discount", [
    "Table 4 wants 2 paneer tikka and 1 butter naan",
    "Table 5 wants 2 butter chicken, 2 garlic naan, 1 veg biryani and 2 gulab jamun",
    "Give me the bill for table 4",
    "Give me the bill for table 5",
])"""),
(MD, """## What the shared memory and each agent's private history look like afterwards"""),
(CODE, """import json
snap = s3.memory.snapshot()
print("ORDERS:", json.dumps(snap["orders"], indent=1)[:900], "...\\n")
print("BILL STATUS:", {t: b["status"] for t, b in snap["bills"].items()})
print("\\nMESSAGE LOG (who told whom what):")
for m in snap["message_log"][:12]:
    print(f"  #{m['id']:>2} turn {m['turn']}  {m['sender']:>8} -> {m['receiver']:<8} [{m['kind']}] {m['content'][:80]}")
print("  ...", len(snap["message_log"]), "messages in total")
print("\\nEACH AGENT'S OWN HISTORY + TOOLS:")
for name, agent in s3.agents.items():
    print(f"  {name:<8} history={len(agent.history):>2} messages   tools={list(agent.tools)}")"""),
]


def run_cells():
    ns, nb_cells, count = {"__name__": "__main__"}, [], 0
    for kind, source in cells:
        lines = source.splitlines(keepends=True)
        if kind == MD:
            nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": lines})
            continue
        count += 1
        buf, outputs = io.StringIO(), []
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(source, f"<cell {count}>", "exec"), ns)
        except Exception:
            outputs.append({"output_type": "error", "ename": "Error", "evalue": "see traceback",
                            "traceback": traceback.format_exc().splitlines()})
            raise
        finally:
            if buf.getvalue():
                outputs.insert(0, {"output_type": "stream", "name": "stdout",
                                   "text": buf.getvalue().splitlines(keepends=True)})
        nb_cells.append({"cell_type": "code", "execution_count": count, "metadata": {},
                         "outputs": outputs, "source": lines})
    return nb_cells


if __name__ == "__main__":
    nb = {"cells": run_cells(),
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 4}
    (ROOT / "restaurant_demo.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("Wrote restaurant_demo.ipynb")
