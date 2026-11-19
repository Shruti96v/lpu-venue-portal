"""
check_groq.py - answers ONE question: "does my Groq key work?"   Run:  python check_groq.py

It makes two tiny calls to Groq:
  1. a plain chat (checks key, model name, network)
  2. a tool call (checks the model can do 'function calling', which our agents need)
and explains in plain English what to fix if something fails.
"""
import sys

from restaurant import config
from restaurant.llm import GroqLLM, LLMError


def mask(key):
    return key[:6] + "..." + key[-4:] if len(key) > 12 else "(too short)"


def explain(err):
    text = str(err)
    if "401" in text or "403" in text:
        return "Groq rejected the key. Re-copy it from console.groq.com/keys (no spaces/quotes) and make a new one if needed."
    if "404" in text:
        return f"Groq does not offer that model to your account. Set GROQ_MODEL=openai/gpt-oss-120b in .env (or try openai/gpt-oss-20b)."
    if "429" in text:
        return "Rate limit hit (free tier). Wait a minute and run again."
    return "Could not reach Groq. Check your internet / VPN / firewall, then try again."


def main():
    key, model = config.get_api_key(), config.get_model()
    if not key:
        print("No GROQ_API_KEY found.\n  1) cp .env.example .env\n  2) open .env and paste your key after GROQ_API_KEY=\n  3) save the file and run this again")
        return 1
    print(f"Key found: {mask(key)}\nModel:     {model}\nEndpoint:  {config.GROQ_BASE_URL}\n")
    llm = GroqLLM(api_key=key, model=model, max_attempts=2)
    try:
        reply = llm.chat("check", [{"role": "user", "content": "Reply with exactly the word: OK"}], [])
        print("1) Plain chat ........ PASS  (model said:", (reply.content or "").strip()[:40], ")")
        tool = {"type": "function", "function": {"name": "say_hello", "description": "Greets the user",
                "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}}
        reply = llm.chat("check", [{"role": "user", "content": "Call the say_hello tool for the name Asha."}], [tool])
        if reply.tool_calls and not reply.tool_calls[0].parse_error:
            print("2) Tool calling ...... PASS  (model called", reply.tool_calls[0].name, reply.tool_calls[0].arguments, ")")
        else:
            print("2) Tool calling ...... WARN  model answered in text instead of calling the tool. The agents may be unreliable; try again or use another model.")
            return 2
    except LLMError as err:
        print("FAIL:", err, "\n\nWhat to do:", explain(err))
        return 1
    print("\nAll good. You can now run the notebook or the UI with the REAL model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
