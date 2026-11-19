"""
config.py - every setting lives here so you can change behaviour in one place.

We read the .env file ourselves (about 10 lines) instead of using the
python-dotenv package, so the only third-party package the agents need is `openai`.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- LLM settings (Groq exposes an OpenAI-compatible API) -------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"   # llama-3.3-70b-versatile is Enterprise-only (404)

# ---- Plan-act loop limits (a safety net against endless tool calling) -------
MAX_STEPS_MANAGER = 8
MAX_STEPS_SPECIALIST = 6

# ---- Billing rules -----------------------------------------------------------
DEFAULT_TAX_PERCENT = 5        # GST on restaurant food
DISCOUNT_THRESHOLD = 1000      # discount only if subtotal is at least this (Rs.)
DISCOUNT_PERCENT = 10


def load_env(path=None):
    """Read KEY=VALUE lines from a .env file into os.environ (real env vars win)."""
    candidates = [Path(path)] if path else [PROJECT_ROOT / ".env", Path.cwd() / ".env"]
    for file in candidates:
        if not file.is_file():
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key():
    load_env()
    key = os.environ.get("GROQ_API_KEY", "").strip()
    # Ignore the placeholder from .env.example
    return "" if key in ("", "your_groq_key_here") else key


def get_model():
    load_env()
    return os.environ.get("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def mock_forced():
    load_env()
    return os.environ.get("USE_MOCK", "").strip().lower() in ("1", "true", "yes")
