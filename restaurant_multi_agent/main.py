"""
Command-line chat with the restaurant.   python main.py          (real brain if GROQ_API_KEY is set)
                                         python main.py --mock   (force the offline mock)
Commands while chatting:  /trace  /memory  /reset  /quit
"""
import json
import sys

from restaurant import RestaurantSystem


def main():
    system = RestaurantSystem(use_mock=True if "--mock" in sys.argv else None, live_trace=True)
    print(f"Brain: {system.llm.label}")
    print("Type a customer message (e.g. 'Table 4 wants 2 paneer tikka'). /quit to exit.\n")
    while True:
        try:
            text = input("Customer> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/reset":
            system.reset()
            print("Session reset.")
        elif text == "/memory":
            snap = system.memory.snapshot()
            print(json.dumps({k: snap[k] for k in ("orders", "bills")}, indent=2))
        elif text == "/trace":
            print(system.trace.render())
        else:
            print()
            result = system.chat(text)          # trace lines print live while it works
            print(f"\nStaff> {result.reply}\n")


if __name__ == "__main__":
    main()
