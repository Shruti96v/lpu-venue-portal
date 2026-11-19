"""
Offline tests - no network, no API key, no openai package needed.
Run:   python tests/test_offline.py        (also works with pytest if you have it)
"""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from restaurant import RestaurantSystem                      # noqa: E402
from restaurant import config                                # noqa: E402
from restaurant.llm import GroqLLM, LLMError, LLMReply, ToolCall, BaseLLM, get_llm   # noqa: E402
from restaurant.memory import SharedMemory                   # noqa: E402
from restaurant.menu import resolve_item                     # noqa: E402
from restaurant.mock_brain import MockLLM, parse_items       # noqa: E402
from restaurant.tools import make_order_tools, make_kitchen_tools, make_billing_tools   # noqa: E402



import contextlib   # noqa: E402
import io           # noqa: E402


@contextlib.contextmanager
def no_real_key():
    """Make get_llm() behave as if there is no .env key and no USE_MOCK, even on a developer's laptop."""
    saved_env = {k: os.environ.pop(k, None) for k in ("GROQ_API_KEY", "USE_MOCK")}
    saved_fns = (config.get_api_key, config.mock_forced)
    config.get_api_key, config.mock_forced = (lambda: ""), (lambda: False)
    try:
        yield
    finally:
        config.get_api_key, config.mock_forced = saved_fns
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v


def new_system(llm=None):
    return RestaurantSystem(llm=llm or MockLLM(), quiet=True)


# ---------------------------------------------------------------- tools & rules
def test_menu_name_matching():
    assert resolve_item("paneer tikka") == "Paneer Tikka"
    assert resolve_item("PANER TIKKA") == "Paneer Tikka"          # typo
    assert resolve_item("dal makhni") == "Dal Makhani"            # alias
    assert resolve_item("a plate of paneer tikka") == "Paneer Tikka"
    assert resolve_item("green tea") is None                      # must NOT guess "tea" -> chai
    assert resolve_item("pizza") is None


def test_add_item_rules():
    mem = SharedMemory()
    add = make_order_tools(mem)["add_item"].func
    assert add(table="4", item="paneer tikka", qty="2")["ok"]     # strings from an LLM are accepted
    assert mem.stock["Paneer Tikka"] == 10                        # stock reserved
    add(table=4, item="Paneer Tikka", qty=1)                      # same dish + note merges
    assert mem.orders[4][0]["qty"] == 3 and len(mem.orders[4]) == 1
    add(table=4, item="Paneer Tikka", qty=1, note="spicy")        # different note = new line
    assert len(mem.orders[4]) == 2
    assert not add(table=4, item="Dal Makhani", qty=1)["ok"]      # out of stock refused by the tool
    r = add(table=4, item="pizza")
    assert not r["ok"] and "menu" in r                            # error includes the menu for retry
    assert not add(table=4, item="Gulab Jamun", qty=7)["ok"]      # only 6 in stock


def test_kitchen_tools():
    mem = SharedMemory()
    kt = make_kitchen_tools(mem)
    r = kt["check_stock"].func(item="dal makhani")
    assert r["in_stock"] is False and r["alternative"]["item"] == "Dal Tadka"
    assert not kt["estimate_time"].func(table=1)["ok"]             # no order yet
    make_order_tools(mem)["add_item"].func(table=1, item="Butter Naan", qty=2)
    assert kt["estimate_time"].func(table=1)["minutes"] == 6 + 1 + 0


def test_discount_only_above_threshold():
    mem = SharedMemory()
    add = make_order_tools(mem)["add_item"].func
    bt = make_billing_tools(mem)
    add(table=1, item="Paneer Tikka", qty=2)                      # 440
    assert bt["apply_discount"].func(table=1)["applied"] is False
    bill = bt["compute_bill"].func(table=1, tax_percent=5)
    assert bill["discount"] == 0 and bill["total"] == 462.0
    add(table=2, item="Butter Chicken", qty=2)                    # 640
    add(table=2, item="Veg Biryani", qty=2)                       # 480 -> 1120
    assert bt["apply_discount"].func(table=2)["applied"] is True
    bill = bt["compute_bill"].func(table=2, tax_percent=5)
    assert bill["discount"] == 112.0 and bill["tax"] == 50.4 and bill["total"] == 1058.4
    assert mem.bills[2]["status"] == "prepared"
    add(table=2, item="Butter Naan")                              # adding after billing
    assert mem.bills[2]["status"] == "outdated"
    try:
        bt["compute_bill"].func(table=2, tax_percent=99)
        assert False, "tax 99% should be rejected"
    except Exception as e:
        assert "tax_percent" in str(e)


def test_parser_notes_and_quantities():
    items = parse_items("Table 4 wants 2 paneer tikka and 1 butter naan, one without onion")
    assert items == [{"item": "Paneer Tikka", "qty": 2, "note": ""},
                     {"item": "Butter Naan", "qty": 1, "note": "without onion"}]
    assert parse_items("Table 3 wants 2 paner tikka")[0]["qty"] == 2     # regression: qty was lost


# ---------------------------------------------------------------- end-to-end (mock brain)
def test_four_example_messages_end_to_end():
    s = new_system()
    r1 = s.chat("Table 4 wants 2 paneer tikka and 1 butter naan, one without onion")
    assert "without onion" in r1.reply and "minutes" in r1.reply
    r2 = s.chat("Add a cold drink to table 4")
    assert "Cold Drink" in r2.reply
    assert [l["item"] for l in s.memory.orders[4]] == ["Paneer Tikka", "Butter Naan", "Cold Drink"]  # memory persisted
    r3 = s.chat("Is the dal makhani available?")
    assert "out of stock" in r3.reply and "Dal Tadka" in r3.reply
    r4 = s.chat("Give me the bill for table 4")
    assert "Total Rs.577.50" in r4.reply and "No discount" in r4.reply
    assert s.memory.bills[4]["total"] == 577.5


def test_out_of_stock_dish_is_not_ordered():
    s = new_system()
    r = s.chat("Table 2 wants 1 dal makhani and 2 butter naan")
    assert "Dal Tadka" in r.reply
    assert [l["item"] for l in s.memory.orders[2]] == ["Butter Naan"]


def test_big_table_gets_discount():
    s = new_system()
    s.chat("Table 5 wants 2 butter chicken, 2 garlic naan, 1 veg biryani and 2 gulab jamun")
    r = s.chat("Give me the bill for table 5")
    assert "Discount 10%" in r.reply, r.reply


def test_missing_table_asks_then_remembers():
    s = new_system()
    assert "Which table" in s.chat("I want a cold drink").reply
    s.chat("Table 7 wants a cold drink")
    assert "table 7" in s.chat("Give me the bill").reply          # table found earlier in the conversation


def test_trace_shows_handoffs_and_tools():
    s = new_system()
    r = s.chat("Table 4 wants 2 paneer tikka")
    kinds = [(e.kind, e.agent) for e in r.events]
    assert ("handoff", "manager") in kinds and ("tool_call", "kitchen") in kinds
    assert ("tool_call", "order") in kinds and ("reply", "manager") in kinds
    handoffs = [(e.data["src"], e.data["dst"]) for e in r.events if e.kind == "handoff"]
    assert handoffs == [("manager", "kitchen"), ("manager", "order"), ("manager", "kitchen")]
    assert "[HANDOFF] manager -> kitchen" in r.trace_text


def test_separate_histories_and_message_log():
    s = new_system()
    s.chat("Table 4 wants 2 paneer tikka")
    s.chat("Give me the bill for table 4")
    tools_used = {n: {c["function"]["name"] for m in a.history for c in m.get("tool_calls", []) or []}
                  for n, a in s.agents.items()}
    assert tools_used["manager"] == {"hand_off"}
    assert tools_used["order"] == {"add_item", "get_order"}
    assert tools_used["kitchen"] == {"check_stock", "estimate_time"}
    assert tools_used["billing"] == {"apply_discount", "compute_bill"}
    assert len({a.history[0]["content"] for a in s.agents.values()}) == 4      # 4 different prompts
    assert set(s.agents["order"].tools) == {"add_item", "get_order"}
    kinds = [(m.sender, m.receiver, m.kind) for m in s.memory.message_log]
    assert ("customer", "manager", "customer") in kinds
    assert ("manager", "billing", "request") in kinds and ("billing", "manager", "response") in kinds
    assert ("manager", "customer", "reply") in kinds
    # order agent kept history across tasks: two tasks -> two user messages (plus system)
    s.chat("Add a cold drink to table 4")
    assert len([m for m in s.agents["order"].history if m["role"] == "user"]) == 2


# ---------------------------------------------------------------- control: caps, failures, routing
class LoopLLM(BaseLLM):
    """A broken brain that never stops calling tools."""
    def chat(self, agent_name, messages, tools):
        return LLMReply(None, [ToolCall("x", "get_order", {"table": 1}, '{"table": 1}')])


def test_step_cap_stops_runaway_agent():
    s = new_system(LoopLLM())
    r = s.chat("hello")
    assert any(e.kind == "step_cap" for e in r.events)
    # manager has no get_order tool -> each call errors, but it must stop at its cap
    assert sum(1 for e in r.events if e.kind == "tool_call") == config.MAX_STEPS_MANAGER
    assert r.reply.startswith("[The manager agent stopped")


class FailingKitchen(MockLLM):
    def chat(self, agent_name, messages, tools):
        if agent_name == "kitchen":
            raise LLMError("kitchen brain offline")
        return super().chat(agent_name, messages, tools)


def test_one_agent_failing_does_not_crash_system():
    s = new_system(FailingKitchen())
    r = s.chat("Table 4 wants 2 paneer tikka")
    assert r.reply                                                # manager still answered
    assert any(e.kind == "error" and e.agent == "kitchen" for e in r.events)
    assert s.memory.orders[4][0]["item"] == "Paneer Tikka"        # order agent still did its job
    r2 = s.chat("Give me the bill for table 4")                   # billing is unaffected
    assert "Total" in r2.reply


class DeadManager(MockLLM):
    def chat(self, agent_name, messages, tools):
        if agent_name == "manager":
            raise LLMError("manager brain offline")
        return super().chat(agent_name, messages, tools)


def test_manager_failure_gives_polite_fallback():
    r = new_system(DeadManager()).chat("Table 4 wants tea")
    assert "trouble" in r.reply and any(e.kind == "error" for e in r.events)


class Scripted(BaseLLM):
    """Returns pre-written replies per agent. Proves the system obeys the LLM's routing choice."""
    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}
        self.seen = []
    def chat(self, agent_name, messages, tools):
        self.seen.append(agent_name)
        return self.script[agent_name].pop(0)


def hand_off(agent, request, cid="c1"):
    args = {"agent": agent, "request": request}
    return LLMReply(None, [ToolCall(cid, "hand_off", args, json.dumps(args))])


def test_routing_is_decided_only_by_llm_output():
    # The message says "bill", but our scripted LLM routes it to the KITCHEN. The system must obey.
    llm = Scripted({"manager": [hand_off("kitchen", "Check stock of Butter Naan"), LLMReply("Done.")],
                    "kitchen": [LLMReply(None, [ToolCall("k1", "check_stock", {"item": "Butter Naan"}, '{"item": "Butter Naan"}')]),
                                LLMReply("Butter Naan is available.")]})
    s = new_system(llm)
    r = s.chat("Give me the bill for table 4")
    assert [(e.data["src"], e.data["dst"]) for e in r.events if e.kind == "handoff"] == [("manager", "kitchen")]
    assert llm.seen == ["manager", "kitchen", "kitchen", "manager"]


def test_bad_agent_name_and_bad_tool_are_reported_back_to_llm():
    llm = Scripted({"manager": [hand_off("chef", "cook"), hand_off("kitchen", "x", "c2"), LLMReply("ok")],
                    "kitchen": [LLMReply(None, [ToolCall("k1", "apply_discount", {"table": 1}, '{"table": 1}')]),   # not its tool
                                LLMReply("could not")]})
    s = new_system(llm)
    r = s.chat("hi")
    results = [e.data["result"] for e in r.events if e.kind == "tool_result"]
    manager_tool_msgs = [m["content"] for m in s.manager.history if m["role"] == "tool"]
    assert "No agent called 'chef'" in manager_tool_msgs[0]
    assert any("Unknown tool 'apply_discount'" in x.get("error", "") for x in results)


def call(name, args, cid):
    return ToolCall(cid, name, args, json.dumps(args))


def test_lazy_order_agent_cannot_fake_success():
    """Real Groq failure: order agent added 2 of 4 dishes but its text claimed all were added."""
    llm = Scripted({
        "manager": [hand_off("order", "Table 5: add 2 Butter Chicken, 1 Veg Biryani, 2 Gulab Jamun"), LLMReply("ok")],
        "order": [LLMReply(None, [call("add_item", {"table": 5, "item": "Butter Chicken", "qty": 2}, "a1")]),
                  LLMReply("Added everything: 2 Butter Chicken, 1 Veg Biryani, 2 Gulab Jamun.")]})   # a lie
    s = new_system(llm)
    s.chat("anything")
    tool_msg = [m["content"] for m in s.manager.history if m["role"] == "tool"][0]
    reply_text = json.loads(tool_msg)["reply"]
    assert "[VERIFIED RECORD" in reply_text
    record = reply_text.split("[VERIFIED RECORD")[1]
    assert "Recorded this time: 2 Butter Chicken" in record
    assert "Veg Biryani" not in record and "Gulab Jamun" not in record      # the truth: they were NOT added
    assert [l["item"] for l in s.memory.orders[5]] == ["Butter Chicken"]


def test_receipt_reports_failed_adds():
    llm = Scripted({
        "manager": [hand_off("order", "Table 2: add 1 Dal Makhani"), LLMReply("ok")],
        "order": [LLMReply(None, [call("add_item", {"table": 2, "item": "Dal Makhani", "qty": 1}, "a1")]),
                  LLMReply("Done.")]})
    s = new_system(llm)
    s.chat("x")
    reply_text = json.loads([m["content"] for m in s.manager.history if m["role"] == "tool"][0])["reply"]
    assert "NOT recorded: Dal Makhani" in reply_text and "Table 2 now has: nothing." in reply_text


def test_receipt_line_never_leaks_to_customer_with_mock():
    s = new_system()
    r = s.chat("Table 4 wants 2 paneer tikka and 1 butter naan, one without onion")
    assert "VERIFIED" not in r.reply
    order_answer = [m.content for m in s.memory.message_log if m.sender == "order"][0]
    assert "[VERIFIED RECORD" in order_answer                                # but it is in the message log


# ---------------------------------------------------------------- the real-brain adapter (fake client)
def fake_response(content=None, calls=()):
    tcs = [SimpleNamespace(id=i, function=SimpleNamespace(name=n, arguments=a)) for i, n, a in calls]
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tcs or None))])


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes, self.requests = list(outcomes), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
    def _create(self, **kw):
        self.requests.append(kw)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


class HttpError(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.status_code = status


def test_groq_adapter_parses_tool_calls_and_text():
    client = FakeClient([fake_response(None, [("call_1", "check_stock", '{"item": "Butter Naan"}')]),
                         fake_response("All good.")])
    llm = GroqLLM("key", client=client, retry_delay=0)
    r = llm.chat("kitchen", [{"role": "user", "content": "hi"}], [{"type": "function"}])
    assert r.tool_calls[0].name == "check_stock" and r.tool_calls[0].arguments == {"item": "Butter Naan"}
    assert r.to_message()["tool_calls"][0]["function"]["arguments"] == '{"item": "Butter Naan"}'
    assert llm.chat("kitchen", [], []).content == "All good."
    assert client.requests[0]["model"] == "openai/gpt-oss-120b" and client.requests[0]["tool_choice"] == "auto"


def test_groq_adapter_handles_bad_json_retry_and_fatal_errors():
    client = FakeClient([fake_response(None, [("c1", "get_order", '{"table": ')])])
    r = GroqLLM("k", client=client, retry_delay=0).chat("order", [], [])
    assert "not valid JSON" in r.tool_calls[0].parse_error
    client = FakeClient([HttpError(429), HttpError(503), fake_response("fine")])        # transient -> retried
    assert GroqLLM("k", client=client, retry_delay=0).chat("order", [], []).content == "fine"
    client = FakeClient([HttpError(404)])                                              # wrong model -> fail fast
    try:
        GroqLLM("k", client=client, retry_delay=0).chat("order", [], [])
        assert False
    except LLMError as e:
        assert "404" in str(e) and len(client.requests) == 1
    client = FakeClient([HttpError(500)] * 3)                                          # gives up after 3
    try:
        GroqLLM("k", client=client, retry_delay=0).chat("order", [], [])
        assert False
    except LLMError:
        assert len(client.requests) == 3


def test_full_system_runs_through_groq_adapter_with_fake_client():
    """Whole manager->kitchen flow, but every LLM answer comes through the GroqLLM parsing code."""
    ho = json.dumps({"agent": "kitchen", "request": "Check stock for Butter Naan"})
    client = FakeClient([
        fake_response(None, [("m1", "hand_off", ho)]),                                  # manager step 1
        fake_response(None, [("k1", "check_stock", '{"item": "butter naan"}')]),        # kitchen step 1
        fake_response("Butter Naan is available."),                                     # kitchen final
        fake_response("Yes, we have butter naan today!")])                              # manager final
    s = new_system(GroqLLM("k", client=client, retry_delay=0))
    r = s.chat("Do you have butter naan?")
    assert r.reply == "Yes, we have butter naan today!" and not client.outcomes
    sent_to_kitchen = client.requests[1]["messages"][0]["content"]
    assert "KITCHEN agent" in sent_to_kitchen                                           # its own system prompt
    assert [t["function"]["name"] for t in client.requests[1]["tools"]] == ["check_stock", "estimate_time"]
    assert [t["function"]["name"] for t in client.requests[0]["tools"]] == ["hand_off"]


# ---------------------------------------------------------------- config / brain selection
def test_get_llm_falls_back_to_mock_without_key():
    with no_real_key():
        assert get_llm().is_mock
        assert "NOT the real LLM" in get_llm().label


def test_env_file_loader():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        f.write_text('# comment\nGROQ_TEST_KEY="abc123"\nexport OTHER_TEST=1\n')
        os.environ.pop("GROQ_TEST_KEY", None)
        config.load_env(f)
        assert os.environ["GROQ_TEST_KEY"] == "abc123" and os.environ["OTHER_TEST"] == "1"


# ---------------------------------------------------------------- key typed in the UI, check_groq, UI helpers
def test_get_llm_uses_key_typed_in_ui_and_model_override():
    with no_real_key():
        if _has_openai():
            llm = get_llm(api_key="gsk_dummy", model="openai/gpt-oss-20b", force_mock=False)
            assert not llm.is_mock and llm.model == "openai/gpt-oss-20b"
        assert get_llm(api_key="gsk_dummy", force_mock=True).is_mock          # checkbox wins
        assert get_llm(api_key="   ").is_mock                                  # blank key -> mock


def _has_openai():
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        return False


def test_empty_tools_list_is_not_sent_to_api():
    client = FakeClient([fake_response("OK")])
    GroqLLM("k", client=client, retry_delay=0).chat("check", [{"role": "user", "content": "hi"}], [])
    assert "tools" not in client.requests[0] and "tool_choice" not in client.requests[0]


def test_check_groq_script_messages():
    import check_groq
    saved = (check_groq.config.get_api_key, check_groq.GroqLLM)
    check_groq.config.get_api_key = lambda: "gsk_" + "x" * 30
    try:
        with contextlib.redirect_stdout(io.StringIO()):                        # keep the test output clean
            ok = FakeClient([fake_response("OK"), fake_response(None, [("t1", "say_hello", '{"name": "Asha"}')])])
            check_groq.GroqLLM = lambda **kw: GroqLLM(client=ok, retry_delay=0, **kw)
            assert check_groq.main() == 0
            bad = FakeClient([HttpError(401)])
            check_groq.GroqLLM = lambda **kw: GroqLLM(client=bad, retry_delay=0, **kw)
            assert check_groq.main() == 1
        assert "key" in check_groq.explain(LLMError("Groq rejected the request (401)")).lower()
        assert "gpt-oss-120b" in check_groq.explain(LLMError("(404)"))
    finally:
        check_groq.config.get_api_key, check_groq.GroqLLM = saved


def test_ui_helpers():
    from restaurant.ui_helpers import event_card_html, table_cards, stock_rows, activity_summary
    s = new_system()
    r = s.chat("Table 4 wants 2 paneer tikka <script>alert(1)</script>")
    cards_html = "".join(event_card_html(e) for e in r.events)
    assert "<script>" not in cards_html and "&lt;script&gt;" in cards_html      # user text is escaped
    s.chat("Give me the bill for table 4")
    card = table_cards(s.memory)[0]
    assert card["table"] == 4 and card["status"] == "prepared" and card["total"] == 462.0
    rows = stock_rows(s.memory)
    assert rows[0]["Dish"] == "Dal Makhani" and rows[0]["Status"] == "OUT"
    summary = activity_summary(s.trace)
    assert summary["hand-offs"] >= 4 and summary["errors"] == 0


# ---------------------------------------------------------------- runner
if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception:
            failed += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
