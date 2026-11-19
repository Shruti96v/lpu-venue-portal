"""
api_server.py - FastAPI backend that bridges the Stitch HTML frontend
                to the Restaurant Multi-Agent system.

Run:  uvicorn api_server:app --reload --port 8000

Then open:
  http://localhost:8000              -> Dashboard Overview
  http://localhost:8000/chat         -> Customer AI Chat
  http://localhost:8000/kitchen      -> Kitchen Display System
  http://localhost:8000/activity     -> AI Staff Multi-Agent Activity
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── import the multi-agent system ────────────────────────────────────────────
from restaurant import RestaurantSystem
from restaurant.llm import get_llm
from restaurant import config

# ── app setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Atelier Hospitality AI — Restaurant Multi-Agent API",
    description="4-agent (Manager / Order / Kitchen / Billing) restaurant AI powered by Groq.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND = Path(__file__).parent / "frontend"

# ── singleton restaurant system ───────────────────────────────────────────────
_system: Optional[RestaurantSystem] = None


def get_system() -> RestaurantSystem:
    global _system
    if _system is None:
        llm = get_llm()
        _system = RestaurantSystem(llm=llm, quiet=True)
    return _system


# ═══════════════════════════════════════════════════════════════════════════════
# HTML FRONTEND ROUTES  (serve the Stitch-generated HTML pages)
# ═══════════════════════════════════════════════════════════════════════════════

def _read_html(rel_path: str) -> str:
    full = FRONTEND / rel_path
    if not full.exists():
        raise HTTPException(status_code=404, detail=f"UI file not found: {rel_path}")
    return full.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def dashboard():
    """Dashboard Overview — main landing page."""
    return _read_html("dashboard_overview/index.html")


@app.get("/chat", response_class=HTMLResponse, tags=["UI"])
async def chat_ui():
    """Customer AI Chat Assistant UI."""
    return _read_html("customer_ai_chat_assistant/index.html")


@app.get("/kitchen", response_class=HTMLResponse, tags=["UI"])
async def kitchen_ui():
    """Kitchen Display System UI."""
    return _read_html("kitchen_display_system/index.html")


@app.get("/activity", response_class=HTMLResponse, tags=["UI"])
async def activity_ui():
    """AI Staff Multi-Agent Activity Monitor UI."""
    return _read_html("ai_staff_multi_agent_activity/index.html")


# ═══════════════════════════════════════════════════════════════════════════════
# JSON API ROUTES  (used by the frontend JS to talk to the agents)
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    table: Optional[int] = None


class ResetRequest(BaseModel):
    confirm: bool = True


@app.post("/api/chat", tags=["API"])
async def api_chat(req: ChatRequest):
    """
    Send a customer message to the Manager agent.
    The manager routes it to Order / Kitchen / Billing as needed.
    Returns the reply, trace, agent events, and current memory snapshot.
    """
    system = get_system()
    # Prepend table number if supplied separately
    text = req.message
    if req.table and f"table {req.table}" not in text.lower():
        text = f"Table {req.table}: {text}"

    result = system.chat(text)
    snap = system.memory.snapshot()

    return {
        "turn": result.turn,
        "reply": result.reply,
        "trace": result.trace_text,
        "events": [
            {
                "seq": e.seq,
                "turn": e.turn,
                "agent": e.agent,
                "kind": e.kind,
                "content": e.content,
            }
            for e in result.events
        ],
        "memory": {
            "tables": snap.get("tables", {}),
            "stock": snap.get("stock", {}),
            "message_log_count": len(snap.get("message_log", [])),
        },
        "brain": system.llm.label,
        "is_mock": system.llm.is_mock,
    }


@app.get("/api/status", tags=["API"])
async def api_status():
    """Current restaurant state: tables, bills, stock levels, agent metrics."""
    system = get_system()
    snap = system.memory.snapshot()
    from restaurant.ui_helpers import activity_summary, table_cards, stock_rows

    metrics = activity_summary(system.trace)
    return {
        "turn": system.memory.turn,
        "brain": system.llm.label,
        "is_mock": system.llm.is_mock,
        "metrics": metrics,
        "tables": table_cards(system.memory),
        "stock": stock_rows(system.memory),
        "agents": {
            name: {
                "tools": list(ag.tools.keys()),
                "history_length": len(ag.history),
            }
            for name, ag in system.agents.items()
        },
    }


@app.get("/api/trace", tags=["API"])
async def api_trace():
    """Full agent trace (all turns)."""
    system = get_system()
    return {"trace": system.trace.render()}


@app.get("/api/menu", tags=["API"])
async def api_menu():
    """Return the full menu."""
    from restaurant.menu import MENU
    return {"menu": MENU}


@app.post("/api/reset", tags=["API"])
async def api_reset(req: ResetRequest):
    """Reset the restaurant system (clear all orders, memory, trace)."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to reset.")
    system = get_system()
    system.reset()
    return {"ok": True, "message": "Restaurant reset — fresh session started."}


# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    # Warm up the system so the first chat is instant
    get_system()
    key_status = "LIVE (Groq)" if config.get_api_key() else "MOCK (offline)"
    print(f"\n{'='*60}")
    print(f"  🍽️  Atelier Hospitality AI — Restaurant Multi-Agent")
    print(f"{'='*60}")
    print(f"  Brain      : {key_status}")
    print(f"  Model      : {config.get_model()}")
    print(f"  Dashboard  : http://localhost:8000")
    print(f"  Chat UI    : http://localhost:8000/chat")
    print(f"  Kitchen    : http://localhost:8000/kitchen")
    print(f"  Activity   : http://localhost:8000/activity")
    print(f"  API docs   : http://localhost:8000/docs")
    print(f"{'='*60}\n")
