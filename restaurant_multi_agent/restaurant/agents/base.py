"""
base.py - the plan-act loop that EVERY agent runs.

    ask the LLM  ->  does it want tools?  -- yes -> run them, add results to history, ask again
                                           -- no  -> its text is the final answer

The loop stops after max_steps so a confused LLM cannot run forever.
Each agent keeps its own `history` (its private memory of past tasks and tool results).
"""
import json

from ..llm import LLMError
from ..tools import ToolError


class BaseAgent:
    def __init__(self, name, system_prompt, tools, llm, memory, trace, max_steps):
        self.name = name
        self.tools = tools                                   # dict: tool name -> Tool
        self.llm = llm
        self.memory = memory                                 # SHARED with all agents
        self.trace = trace                                   # SHARED with all agents
        self.max_steps = max_steps
        self.quiet_tools = set()                             # tools whose result is already traced elsewhere
        self.task_results = []                               # (tool, args, result) of the CURRENT task
        self.history = [{"role": "system", "content": system_prompt}]   # PRIVATE to this agent

    # ---- called by another agent: read the message, work, answer with a message -------------
    def receive(self, message):
        try:
            answer = self.run(message.content)
            note = self.receipt()                            # facts from the system, not from the LLM
            if note:
                answer = f"{answer}\n{note}"
        except Exception as err:                             # one broken agent must not crash the others
            self.trace.error(self.name, f"{type(err).__name__}: {err}")
            answer = f"[The {self.name} agent is unavailable right now: {err}]"
        self.trace.answer(self.name, answer)
        return self.memory.post_message(self.name, message.sender, answer, kind="response")

    def receipt(self):
        """Override in a subclass to append facts taken straight from shared memory ('' = nothing)."""
        return ""

    # ---- the plan-act loop -------------------------------------------------------------------
    def run(self, task):
        self.history.append({"role": "user", "content": task})
        self.task_results = []
        schemas = [t.schema() for t in self.tools.values()]
        for step in range(1, self.max_steps + 1):
            reply = self.llm.chat(self.name, self.history, schemas)       # 1. think
            self.history.append(reply.to_message())
            if not reply.tool_calls:                                      # 2. no tools -> final answer
                return (reply.content or "").strip()
            for call in reply.tool_calls:                                 # 3. act
                self.trace.tool_call(self.name, step, call.name, call.arguments)
                result = self._execute(call)
                self.task_results.append((call.name, call.arguments, result))
                if call.name not in self.quiet_tools:
                    self.trace.tool_result(self.name, call.name, result)
                self.history.append({"role": "tool", "tool_call_id": call.id,   # 4. observe
                                     "content": json.dumps(result)})
        # step cap reached: give the caller something honest instead of looping forever
        self.trace.step_cap(self.name, self.max_steps)
        tool_msgs = [m["content"] for m in self.history if m["role"] == "tool"][-3:]
        fallback = (f"[The {self.name} agent stopped after {self.max_steps} steps without finishing. "
                    f"Partial results: {' | '.join(tool_msgs)}]")
        self.history.append({"role": "assistant", "content": fallback})
        return fallback

    def _execute(self, call):
        """Run one tool call safely. Problems become results the LLM can read and react to."""
        if call.parse_error:
            return {"ok": False, "error": call.parse_error}
        tool = self.tools.get(call.name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool '{call.name}'. Your tools: {list(self.tools)}"}
        try:
            return tool.run(call.arguments)
        except ToolError as err:
            return {"ok": False, "error": str(err)}
        except TypeError as err:                             # wrong / missing argument names
            return {"ok": False, "error": f"Bad arguments for {call.name}: {err}"}
        except Exception as err:
            return {"ok": False, "error": f"{call.name} crashed: {err}"}
