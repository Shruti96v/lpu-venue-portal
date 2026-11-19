"""
Streamlit UI.   Run:  streamlit run app_streamlit.py

Left : customer chat + one-click example messages.
Right: what each agent did (colour-coded tabs), the restaurant board (tables, bills, stock) and
       the full trace.
Sidebar: pick the brain (paste a Groq key here OR use .env), test the connection, reset.
"""
import streamlit as st

from restaurant import RestaurantSystem
from restaurant.llm import LLMError, get_llm
from restaurant import config
from restaurant.ui_helpers import (EXAMPLES, activity_summary, event_card_html, stock_rows, table_cards)

st.set_page_config(page_title="Restaurant AI staff", page_icon="🍽️", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.4rem;}
.badge {display:inline-block;padding:3px 10px;border-radius:12px;font-size:0.85em;font-weight:600;color:white;}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar: choose the brain
with st.sidebar:
    st.header("Brain")
    typed_key = st.text_input("Groq API key (optional)", type="password",
                              help="Paste a key from console.groq.com/keys. It stays in this browser session only. "
                                   "Leave empty to use GROQ_API_KEY from your .env file.")
    model = st.text_input("Model", value=config.get_model())
    force_mock = st.checkbox("Force offline mock brain", value=False,
                             help="Rule-based stand-in for testing. NOT the real LLM.")
    if st.button("Test connection", use_container_width=True):
        probe = get_llm(force_mock=force_mock, api_key=typed_key, model=model)
        if probe.is_mock:
            st.info("Mock brain selected - nothing to test. Add a key to use Groq.")
        else:
            try:
                with st.spinner("Calling Groq..."):
                    answer = probe.chat("check", [{"role": "user", "content": "Reply with exactly: OK"}], [])
                st.success(f"Connected. Model replied: {(answer.content or '').strip()[:30]}")
            except LLMError as err:
                st.error(str(err))
    st.divider()
    if st.button("Reset session (new empty restaurant)", use_container_width=True):
        st.session_state.pop("system", None)
        st.session_state["chat"] = []
    st.caption("Tip: the first message to a table creates its order. Later messages can say just 'table 4'.")

# The system must survive Streamlit's re-runs, so it lives in session_state.
signature = (force_mock, typed_key, model)
if "system" not in st.session_state or st.session_state.get("signature") != signature:
    st.session_state.system = RestaurantSystem(llm=get_llm(force_mock=force_mock, api_key=typed_key, model=model), quiet=True)
    st.session_state.signature = signature
    st.session_state.chat = []
system = st.session_state.system

# ------------------------------------------------------------------ header
st.title("🍽️ Restaurant AI staff")
if system.llm.is_mock:
    st.markdown("<span class='badge' style='background:#d97706'>OFFLINE MOCK BRAIN</span> "
                "&nbsp;This is a rule-based stand-in, <b>not the real LLM</b>. Paste a Groq key in the sidebar to use the real model.",
                unsafe_allow_html=True)
else:
    st.markdown(f"<span class='badge' style='background:#16a34a'>LIVE</span> &nbsp;Real brain: <code>{system.llm.label}</code>",
                unsafe_allow_html=True)

# ------------------------------------------------------------------ process a new message (before drawing)
text = st.chat_input("Type as a customer, e.g. 'Table 4 wants 2 paneer tikka, one without onion'")
text = text or st.session_state.pop("queued", None)
if text:
    with st.spinner("The team is working on it..."):
        result = system.chat(text)
    st.session_state.chat += [("user", text), ("assistant", result.reply)]

metrics = activity_summary(system.trace)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Customer turns", system.memory.turn)
c2.metric("Hand-offs", metrics["hand-offs"])
c3.metric("Tool calls", metrics["tool calls"])
c4.metric("Errors", metrics["errors"])

left, right = st.columns([1, 1.5], gap="large")

# ------------------------------------------------------------------ left: chat
with left:
    st.subheader("Customer chat")
    if not st.session_state.chat:
        st.info("Try one of the examples below, or type your own message in the box at the bottom.")
    for role, content in st.session_state.chat:
        st.chat_message(role, avatar="🧑" if role == "user" else "🍽️").write(content)
    st.caption("Quick examples (click to send):")
    for i, example in enumerate(EXAMPLES):
        if st.button(example, key=f"ex{i}", use_container_width=True):
            st.session_state.queued = example
            st.rerun()

# ------------------------------------------------------------------ right: agents, board, trace
with right:
    st.subheader("What each agent did")
    tabs = st.tabs(["Manager", "Order", "Kitchen", "Billing", "Restaurant board", "Full trace"])
    for tab, name in zip(tabs[:4], ["manager", "order", "kitchen", "billing"]):
        with tab:
            agent = system.agents[name]
            st.caption(f"Tools: {', '.join(agent.tools)}  |  own history: {len(agent.history)} messages")
            events = system.trace.events_for_agent(name)
            if name == "manager":
                events = sorted(events + [e for e in system.trace.events if e.kind == "customer"], key=lambda e: e.seq)
            if not events:
                st.caption("Nothing yet.")
            for turn in sorted({e.turn for e in events}, reverse=True):      # newest turn first
                with st.expander(f"Turn {turn}", expanded=(turn == system.memory.turn)):
                    for e in [e for e in events if e.turn == turn]:
                        st.markdown(event_card_html(e), unsafe_allow_html=True)
    with tabs[4]:
        cards = table_cards(system.memory)
        if not cards:
            st.caption("No orders yet.")
        cols = st.columns(2)
        for i, card in enumerate(cards):
            with cols[i % 2].container(border=True):
                st.markdown(f"**Table {card['table']}**")
                for line in card["lines"]:
                    st.write("- " + line)
                if card["total"] is not None:
                    st.success(f"Bill prepared: Rs.{card['total']:,.2f}")
                elif card["status"] == "outdated":
                    st.warning("Items added after the bill - bill is outdated")
                else:
                    st.caption("No bill yet")
        with st.expander("Kitchen stock"):
            st.dataframe(stock_rows(system.memory), use_container_width=True, hide_index=True)
        with st.expander("Message log (who told whom what)"):
            st.dataframe([{k: m[k] for k in ("id", "turn", "sender", "receiver", "kind", "content")}
                          for m in system.memory.snapshot()["message_log"]], use_container_width=True, hide_index=True)
    with tabs[5]:
        st.code(system.trace.render() or "(empty)", language="text")
