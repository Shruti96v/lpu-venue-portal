# 🍽️ Atelier Hospitality AI — Restaurant Multi-Agent System

A **complete, production-ready multi-agent SaaS** that orchestrates 4 AI agents (Manager, Order, Kitchen, Billing) to run a restaurant — with a beautiful luxury UI from the Atelier design system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Stitch HTML Frontend (Atelier Design)           │
│  Dashboard | Customer Chat | Kitchen | Activity Monitor  │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTP / fetch()
┌──────────────────────▼──────────────────────────────────┐
│          FastAPI Backend  (api_server.py)                │
│          + Streamlit UI  (app_streamlit.py)              │
└──────────────────────┬──────────────────────────────────┘
                       │  Python calls
┌──────────────────────▼──────────────────────────────────┐
│         Restaurant Multi-Agent Core  (restaurant/)       │
│                                                          │
│  ManagerAgent ──routes──► OrderAgent                     │
│       │                   KitchenAgent                   │
│       └────────────────►  BillingAgent                   │
│                                                          │
│  SharedMemory | Trace | Tools | Prompts | LLM (Groq)    │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
restaurant_multi_agent/
├── api_server.py          ← NEW: FastAPI server + JSON API + serves Stitch HTML
├── app_streamlit.py       ← Original Streamlit UI (still works)
├── main.py                ← CLI chat mode
├── check_groq.py          ← Verify Groq API key
├── requirements.txt       ← All dependencies
├── .env.example           ← Copy to .env and add your GROQ_API_KEY
│
├── frontend/              ← NEW: Stitch HTML UI (Atelier design system)
│   ├── dashboard_overview/        → http://localhost:8000/
│   ├── customer_ai_chat_assistant/ → http://localhost:8000/chat  ← WIRED TO API
│   ├── kitchen_display_system/    → http://localhost:8000/kitchen
│   └── ai_staff_multi_agent_activity/ → http://localhost:8000/activity
│
├── restaurant/            ← Multi-agent Python package
│   ├── agents/
│   │   ├── base.py        ← Plan-act loop (all agents share this)
│   │   ├── manager_agent.py
│   │   ├── order_agent.py
│   │   ├── kitchen_agent.py
│   │   └── billing_agent.py
│   ├── llm.py             ← Groq via OpenAI-compatible API
│   ├── memory.py          ← Shared state (tables, bills, stock)
│   ├── trace.py           ← Full agent event log
│   ├── tools.py           ← 10+ tools agents can call
│   ├── prompts.py         ← System prompts for each agent
│   ├── menu.py            ← Full restaurant menu
│   ├── config.py          ← Settings (model, tax, discounts)
│   └── system.py          ← RestaurantSystem entry point
│
├── tests/test_offline.py  ← 28 offline tests (no Groq key needed)
├── scripts/               ← Demo, diagram, notebook builders
├── docs/                  ← PDF explanation + swimlane diagrams
└── restaurant_demo.ipynb  ← Jupyter walkthrough
```

---

## Quick Start

### 1. Get a Groq API Key
Go to [console.groq.com/keys](https://console.groq.com/keys) → Create API Key (starts with `gsk_`)

### 2. Set Up Environment

```bash
cd restaurant_multi_agent
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env → set GROQ_API_KEY=gsk_yourkeyhere
```

### 3. Run — Choose Your Interface

| Interface | Command | URL |
|-----------|---------|-----|
| **🌐 Beautiful Web UI** (Stitch + FastAPI) | `uvicorn api_server:app --reload` | http://localhost:8000 |
| **💬 Streamlit UI** | `streamlit run app_streamlit.py` | http://localhost:8501 |
| **🖥️ Terminal chat** | `python main.py` | — |
| **📓 Notebook** | `jupyter notebook restaurant_demo.ipynb` | http://localhost:8888 |

### 4. Test (no API key needed)

```bash
python tests/test_offline.py        # 28/28 should pass
python check_groq.py                # verify Groq connection
python scripts/real_demo.py         # 7-turn real demo
```

---

## API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send message → agents respond |
| `GET`  | `/api/status` | Tables, stock, metrics |
| `GET`  | `/api/trace` | Full agent trace |
| `GET`  | `/api/menu` | Full menu |
| `POST` | `/api/reset` | Fresh restaurant session |
| `GET`  | `/docs` | Interactive Swagger docs |

**Chat example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Table 4 wants 2 paneer tikka, one without onion"}'
```

---

## The 4 Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Manager** | Routes messages, coordinates all agents | send_message, get_memory |
| **Order** | Takes and updates orders per table | add_order, update_order, get_order |
| **Kitchen** | Checks stock, estimates cook time | check_stock, update_stock, get_cook_time |
| **Billing** | Calculates bills with tax + discounts | prepare_bill, get_bill |

Each agent runs an **independent plan-act loop** (up to 6–8 LLM steps) with its own conversation history, sharing a common `SharedMemory` and `Trace`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No GROQ_API_KEY found` | Edit `.env`, set `GROQ_API_KEY=gsk_...` |
| `401 / 403` | Wrong key — create a new one at console.groq.com |
| `404 model` | Set `GROQ_MODEL=openai/gpt-oss-120b` in `.env` |
| `429 rate limit` | Free tier — wait 1 min; code retries automatically |
| Orange MOCK banner | Key not found — check `.env` in project folder |
| `ModuleNotFoundError` | Run `source .venv/bin/activate` first |
