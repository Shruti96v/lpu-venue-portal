"""
llm.py - the "brain" interface. Every agent calls   llm.chat(agent_name, messages, tools).

Two brains implement it:
  GroqLLM  - the REAL brain: Groq's OpenAI-compatible API through the `openai` package.
  MockLLM  - an OFFLINE rule-based stand-in (restaurant/mock_brain.py). NOT a real LLM.

Both return an LLMReply: either some text (the agent is done) or tool calls (the agent wants
to use tools). That one shape is all the agent loop needs to understand.
"""
import json
import time
from dataclasses import dataclass, field

from . import config

MOCK_LABEL = "MOCK BRAIN (offline, rule-based) - NOT the real LLM"


class LLMError(Exception):
    """The brain could not be reached or gave an unusable answer."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict = field(default_factory=dict)
    raw_arguments: str = "{}"
    parse_error: str = ""        # filled if the LLM sent broken JSON


@dataclass
class LLMReply:
    content: str = None
    tool_calls: list = field(default_factory=list)

    def to_message(self):
        """Convert to the dict format stored in an agent's history / sent back to the API."""
        msg = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {"id": c.id, "type": "function",
                 "function": {"name": c.name, "arguments": c.raw_arguments}}
                for c in self.tool_calls]
        return msg


class BaseLLM:
    is_mock = False
    label = "LLM"

    def chat(self, agent_name, messages, tools):
        raise NotImplementedError


# =============================================================================
# The real brain
# =============================================================================
class GroqLLM(BaseLLM):
    def __init__(self, api_key, model=None, base_url=config.GROQ_BASE_URL,
                 client=None, max_attempts=3, retry_delay=1.5):
        self.model = model or config.DEFAULT_MODEL
        self.label = f"Groq / {self.model}"
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay
        if client is None:
            from openai import OpenAI          # imported here so the mock works without the package
            client = OpenAI(api_key=api_key, base_url=base_url)
        self.client = client

    def chat(self, agent_name, messages, tools):
        response = self._call_with_retries(messages, tools)
        message = response.choices[0].message
        calls = []
        for tc in (message.tool_calls or []):
            raw = tc.function.arguments or "{}"
            call = ToolCall(id=tc.id, name=tc.function.name, raw_arguments=raw)
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("arguments JSON must be an object")
                call.arguments = parsed
            except ValueError as err:          # LLMs occasionally emit broken JSON
                call.parse_error = f"Your tool arguments were not valid JSON ({err}). Send them again."
                call.raw_arguments = "{}"
            calls.append(call)
        return LLMReply(content=message.content, tool_calls=calls)

    def _call_with_retries(self, messages, tools):
        for attempt in range(1, self.max_attempts + 1):
            try:
                kwargs = dict(model=self.model, messages=messages, temperature=0.2)
                if tools:                      # some providers reject an empty tools list
                    kwargs.update(tools=tools, tool_choice="auto")
                return self.client.chat.completions.create(**kwargs)
            except Exception as err:           # network trouble, rate limit, bad request ...
                status = getattr(err, "status_code", None)
                if status in (401, 403, 404):  # wrong key / model: retrying will not help
                    raise LLMError(f"Groq rejected the request ({status}): {err}") from err
                if attempt == self.max_attempts:
                    raise LLMError(f"Groq call failed after {attempt} attempts: {err}") from err
                time.sleep(self.retry_delay * attempt)


# =============================================================================
# Picking a brain
# =============================================================================
def get_llm(force_mock=None, api_key=None, model=None):
    """
    Pick the brain.
      - force_mock=True              -> always the offline mock
      - api_key given (e.g. typed into the UI) or GROQ_API_KEY in .env -> real Groq brain
      - otherwise                    -> offline mock
    """
    from .mock_brain import MockLLM
    key = (api_key or "").strip() or config.get_api_key()
    if force_mock is None:
        force_mock = config.mock_forced()
    if force_mock or not key:
        return MockLLM()
    return GroqLLM(api_key=key, model=(model or "").strip() or config.get_model())
