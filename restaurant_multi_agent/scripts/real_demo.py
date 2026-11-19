"""
real_demo.py - runs a whole demo session and prints a COMPACT summary, easy to copy and paste.
Uses the real Groq brain if your key is set (otherwise the offline mock, clearly labelled).

Run from the project folder:   python scripts/real_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from restaurant import RestaurantSystem                    # noqa: E402

MESSAGES = [
    "Table 4 wants 2 paneer tikka and 1 butter naan, one without onion",
    "Add a cold drink to table 4",
    "Is the dal makhani available?",
    "Table 2 wants 1 dal makhani and 2 butter naan",
    "Table 5 wants 2 butter chicken, 2 garlic naan, 1 veg biryani and 2 gulab jamun",
    "Give me the bill for table 4",
    "Give me the bill for table 5",
]


def main():
    system = RestaurantSystem()
    print("BRAIN:", system.llm.label)
    for text in MESSAGES:
        result = system.chat(text)
        route = [f"{e.data['src']}->{e.data['dst']}" for e in result.events if e.kind == "handoff"]
        calls = [f"{e.agent}.{e.data['tool']}" for e in result.events if e.kind == "tool_call" and e.agent != "manager"]
        bad = [f"{e.agent}.{e.data['tool']}: {e.data['result'].get('error')}" for e in result.events
               if e.kind == "tool_result" and not e.data["result"].get("ok", True)]
        problems = [e.text for e in result.events if e.kind in ("error", "step_cap")]
        print(f"\n> {text}")
        print("  route :", " , ".join(route) or "(none)")
        print("  tools :", " , ".join(calls) or "(none)")
        print("  tool errors:", bad or "none", "| agent errors/step caps:", problems or "none")
        print("  REPLY :", result.reply)
    print("\nFINAL MEMORY")
    for table, lines in sorted(system.memory.orders.items()):
        print(f"  table {table}:", "; ".join(f"{l['qty']} {l['item']}" + (f" ({l['note']})" if l['note'] else "") for l in lines))
    for table, bill in sorted(system.memory.bills.items()):
        print(f"  bill {table}: status={bill['status']} discount={bill.get('discount_percent', 0)}% total={bill.get('total')}")
    print("  LLM history sizes:", {n: len(a.history) for n, a in system.agents.items()})


if __name__ == "__main__":
    main()
