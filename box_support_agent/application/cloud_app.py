"""
WhatsApp Cloud App for Box Retail Agent.
Handles WhatsApp webhook, routes to FastWorkflow, and manages pricing flow.
"""

import os
import re
import logging
import httpx
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Optional
import groq as _groq

# --- FIRESTORE (optional — falls back to in-memory if unavailable) ---
try:
    from google.cloud import firestore as _gcp_firestore
    _FIRESTORE_AVAILABLE = True
except ImportError:
    _FIRESTORE_AVAILABLE = False

_firestore_db = None
_metrics_doc_path = ("app_state", "runtime_metrics")

def _get_db():
    """Return an AsyncClient instance, or None if Firestore is unavailable."""
    global _firestore_db
    if not _FIRESTORE_AVAILABLE:
        return None
    if _firestore_db is None:
        try:
            _firestore_db = _gcp_firestore.AsyncClient()
        except Exception as e:
            logger.warning(f"Firestore init failed (in-memory fallback): {e}")
            return None
    return _firestore_db

# --- LOAD ENV FILES ---
# Load fastworkflow.env and fastworkflow.passwords.env if they exist
def load_env_files():
    """Load environment variables from fastworkflow env files."""
    # Find the env files relative to this file
    base_dir = Path(__file__).parent.parent  # box_retail_agent/
    env_files = [
        base_dir / "fastworkflow.env",
        base_dir / "fastworkflow.passwords.env"
    ]
    
    for env_file in env_files:
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value

load_env_files()

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("box_retail_cloud_app")

# --- SECRETS & CONFIG ---
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "kalash_verity_2026")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_GRAPH_API_VERSION = os.environ.get("WHATSAPP_GRAPH_API_VERSION", "v25.0")

# Factory WhatsApp number (without +)
FACTORY_WHATSAPP = os.environ.get("FACTORY_WHATSAPP", "919725201616")

# FastWorkflow URL (runs locally in same container)
FASTWORKFLOW_URL = "http://localhost:8000"

# Image messaging — feature flag for staged rollout (off by default)
MEDIA_SEND_ENABLED: bool = os.environ.get("MEDIA_SEND_ENABLED", "false").lower() == "true"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB

# PDF document sending
ALLOWED_PDF_TYPE = "application/pdf"
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB (Cloud Run hard limit is 32 MB)

app = FastAPI(title="Box Retail WhatsApp Agent")

# ---------------------------------------------------------------------------
# Firestore persistence helpers
# ---------------------------------------------------------------------------

async def _load_from_firestore():
    """On startup: load all conversations from Firestore into in-memory dicts."""
    db = _get_db()
    if not db:
        logger.info("Firestore unavailable — starting with empty in-memory state")
        return
    try:
        docs = db.collection("conversations").stream()
        count = 0
        async for doc in docs:
            data = doc.to_dict()
            phone = doc.id
            conversation_logs[phone] = data.get("messages", [])
            cs = data.get("control_state")
            if cs:
                control_state[phone] = cs
            count += 1
        logger.info(f"Loaded {count} conversations from Firestore")
    except Exception as e:
        logger.error(f"Failed to load conversations from Firestore: {e}")


async def _persist_conversation(phone: str):
    """Write this phone's conversation state to Firestore (fire-and-forget)."""
    db = _get_db()
    if not db:
        return
    try:
        doc_ref = db.collection("conversations").document(str(phone))
        await doc_ref.set({
            "messages": conversation_logs.get(phone, []),
            "control_state": control_state.get(phone, "BOT_CONTROL"),
            "human_control_activated_at": None,
            "updated_at": _gcp_firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        logger.error(f"Firestore persist error for {phone}: {e}")


async def _load_runtime_metrics_from_firestore():
    """Load runtime counters so dashboard stats survive restarts/deploys."""
    global resolutions_used, total_agent_time, agent_call_count
    db = _get_db()
    if not db:
        return
    try:
        collection, doc_id = _metrics_doc_path
        doc = await db.collection(collection).document(doc_id).get()
        if not doc.exists:
            return
        data = doc.to_dict() or {}
        resolutions_used = int(data.get("resolutions_used", resolutions_used))
        total_agent_time = float(data.get("total_agent_time", total_agent_time))
        agent_call_count = int(data.get("agent_call_count", agent_call_count))
        logger.info(
            "Loaded runtime metrics from Firestore "
            f"(used={resolutions_used}, calls={agent_call_count}, total_time={total_agent_time:.2f}s)"
        )
    except Exception as e:
        logger.error(f"Failed to load runtime metrics from Firestore: {e}")


async def _persist_runtime_metrics():
    """Persist runtime counters used by /api/resolutions."""
    db = _get_db()
    if not db:
        return
    try:
        collection, doc_id = _metrics_doc_path
        await db.collection(collection).document(doc_id).set({
            "resolutions_used": resolutions_used,
            "total_agent_time": total_agent_time,
            "agent_call_count": agent_call_count,
            "updated_at": _gcp_firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        logger.error(f"Failed to persist runtime metrics: {e}")


@app.on_event("startup")
async def startup_load_conversations():
    await _load_from_firestore()
    await _load_runtime_metrics_from_firestore()
    asyncio.create_task(_startup_upload_qr_code())




# Session cache: phone → FastWorkflow session data
session_cache: Dict[str, dict] = {}

# Session generation counter: incremented on each reset so the new session
# gets a unique channel_id, forcing FastWorkflow to start with a clean slate.
session_generation: Dict[str, int] = {}

# Message deduplication: track processed WhatsApp message IDs
# Prevents duplicate processing when WhatsApp retries webhooks
processed_message_ids: Dict[str, datetime] = {}

# Pending orders awaiting pricing from factory
# Format: {order_id: {"customer_phone": str, "order_summary": str, "products": list, "timestamp": datetime}}
pending_orders: Dict[str, dict] = {}

# current_pricing_request kept for backward compat but no longer used for routing
current_pricing_request: Optional[str] = None

# Conversation transcripts: phone → [{role, text, timestamp}]
conversation_logs: Dict[str, list] = {}

# Per-customer control state: phone → "BOT_CONTROL" | "HUMAN_CONTROL"
control_state: Dict[str, str] = {}

# Official WhatsApp blocked-users cache. The dashboard polls every 3 seconds,
# so this avoids calling the Graph API on every refresh.
blocked_users_cache: set[str] = set()
blocked_users_cache_refreshed_at: Optional[datetime] = None
BLOCKED_USERS_CACHE_TTL_SECONDS: int = int(os.environ.get("BLOCKED_USERS_CACHE_TTL_SECONDS", "30"))

# Resolution counter: each agent response costs 1
RESOLUTION_LIMIT: int = int(os.environ.get("RESOLUTION_LIMIT", "500"))
REFERRAL_CREDITS: int = int(os.environ.get("REFERRAL_CREDITS", "0"))
AUTOMATION_RATE: str = os.environ.get("AUTOMATION_RATE", "0")
resolutions_used: int = 0

# Average response time tracking
total_agent_time: float = 0.0
agent_call_count: int = 0

# Per-phone asyncio locks: serialises back-to-back messages from the same
# customer so FastWorkflow never receives concurrent requests for one session.
_phone_locks: Dict[str, asyncio.Lock] = {}


def _get_phone_lock(phone: str) -> asyncio.Lock:
    if phone not in _phone_locks:
        _phone_locks[phone] = asyncio.Lock()
    return _phone_locks[phone]


# QR code WhatsApp media ID — cached on startup to avoid re-uploading on every request
_qr_code_media_id: Optional[str] = None

# In-memory dashboard alert queue for factory operator notifications
# Format: [{"id": str, "phone": str, "message": str, "timestamp": str, "dismissed": bool}]
dashboard_alerts: list = []


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

HELP_MESSAGE = """
Here's what I can help you with:

\U0001f4e6 Product Info - Ask about boxes, boards, or kits
\U0001f4cf Sizes - "What sizes are available?"
\U0001f3a8 Colors - "What colors do you have?"
\u2728 Customization - "Do you offer branding?"
\U0001f6d2 Checkout - Say "checkout" to place an order
\U0001f504 Reset - Say "reset" to start a fresh conversation

Just type your question naturally!
"""

# ---------------------------------------------------------------------------
# WhatsApp API Functions
# ---------------------------------------------------------------------------

async def send_whatsapp(to: str, message: str) -> bool:
    """Send a WhatsApp message."""
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Message sent to {to}")
                return True
            else:
                logger.error(f"Failed to send message: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False


def _graph_api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _block_users_url() -> str:
    return f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/block_users"


def _extract_blocked_users(payload: dict) -> set[str]:
    """Best-effort extraction from block_users GET responses across API versions."""
    blocked = set()
    for item in payload.get("data", []) or payload.get("block_users", []):
        if not isinstance(item, dict):
            continue
        user_id = item.get("user") or item.get("wa_id") or item.get("input") or item.get("id")
        if user_id:
            blocked.add(str(user_id))
    return blocked


async def get_blocked_users(force_refresh: bool = False) -> set[str]:
    """Return currently blocked WhatsApp users from the official Cloud API."""
    global blocked_users_cache_refreshed_at, blocked_users_cache

    now = datetime.now(timezone.utc)
    if not force_refresh and blocked_users_cache_refreshed_at:
        age = (now - blocked_users_cache_refreshed_at).total_seconds()
        if age < BLOCKED_USERS_CACHE_TTL_SECONDS:
            return set(blocked_users_cache)

    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        logger.warning("Blocked users lookup skipped: missing PHONE_NUMBER_ID or ACCESS_TOKEN")
        return set(blocked_users_cache)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(_block_users_url(), headers=_graph_api_headers())
            resp.raise_for_status()
            blocked_users_cache = _extract_blocked_users(resp.json())
            blocked_users_cache_refreshed_at = now
            return set(blocked_users_cache)
    except Exception as exc:
        logger.error(f"Blocked users fetch error: {exc}")
        return set(blocked_users_cache)


async def set_blocked_user(phone: str, blocked: bool) -> dict:
    """Block or unblock one WhatsApp user via the official Cloud API."""
    global blocked_users_cache_refreshed_at, blocked_users_cache

    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        raise RuntimeError("Missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN")

    method = "POST" if blocked else "DELETE"
    payload = {
        "messaging_product": "whatsapp",
        "block_users": [{"user": phone}],
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.request(method, _block_users_url(), headers=_graph_api_headers(), json=payload)
        resp.raise_for_status()

    if blocked:
        blocked_users_cache.add(phone)
    else:
        blocked_users_cache.discard(phone)
    blocked_users_cache_refreshed_at = datetime.now(timezone.utc)
    return {"phone": phone, "blocked": blocked}


async def send_typing_indicator(to: str, msg_id: str):
    """Broadcast a unified read receipt + typing indicator via Meta Graph API.

    Uses the single atomic payload with ``typing_indicator`` nested object
    as required by the WhatsApp Cloud API spec.  The old implementation
    incorrectly used ``"status": "typing"`` which is an invalid enum value
    and was silently rejected with HTTP 400.
    """
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    # Unified payload: read receipt + typing indicator in one request
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": msg_id,
        "typing_indicator": {
            "type": "text"
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(f"Typing indicator sent for {to}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Meta API rejected typing indicator: {exc.response.text}")
    except Exception as e:
        logger.warning(f"Typing indicator failed (non-critical): {e}")


def _validate_image_bytes(content: bytes, claimed_type: str) -> bool:
    """Validate image magic bytes against the claimed MIME type (OWASP file-upload check)."""
    if claimed_type == "image/jpeg" and content[:3] == b'\xff\xd8\xff':
        return True
    if claimed_type == "image/png" and content[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if claimed_type == "image/webp" and content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return True
    return False


def _validate_pdf_bytes(content: bytes) -> bool:
    """Validate PDF magic bytes (%PDF header) — OWASP file-upload check."""
    return content[:4] == b'%PDF'


def _extract_image_name_from_url(image_url: str) -> Optional[str]:
    """Extract a readable filename from a URL path, if present."""
    if not image_url:
        return None
    try:
        path_part = image_url.split("?", 1)[0].rstrip("/")
        if not path_part:
            return None
        name = path_part.rsplit("/", 1)[-1].strip()
        return name or None
    except Exception:
        return None


async def _fetch_whatsapp_media_download_info(media_id: str) -> Optional[dict]:
    """Resolve a WhatsApp media_id to a temporary download URL and mime type."""
    if not media_id:
        return None
    info_url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(info_url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch media info for {media_id}: {resp.text}")
                return None
            data = resp.json()
            url = data.get("url")
            if not url:
                return None
            return {
                "url": url,
                "mime_type": data.get("mime_type", "application/octet-stream"),
                "filename": data.get("filename") or None,
            }
    except Exception as e:
        logger.error(f"Media info fetch error for {media_id}: {e}")
        return None


async def send_whatsapp_image_url(to: str, image_url: str, caption: str = "") -> bool:
    """Send a WhatsApp image message via a public URL."""
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption},
    }
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Image (URL) sent to {to}")
                return True
            logger.error(f"Image (URL) send failed: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp image URL send error: {e}")
        return False


async def send_whatsapp_image_media_id(to: str, media_id: str, caption: str = "") -> bool:
    """Send a WhatsApp image message via a pre-uploaded media ID."""
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"id": media_id, "caption": caption},
    }
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Image (media_id) sent to {to}")
                return True
            logger.error(f"Image (media_id) send failed: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp image media_id send error: {e}")
        return False


async def send_whatsapp_document_url(to: str, document_url: str, filename: str = "", caption: str = "") -> bool:
    """Send a WhatsApp document message via a public URL."""
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {"link": document_url, "caption": caption},
    }
    if filename:
        payload["document"]["filename"] = filename
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Document (URL) sent to {to}")
                return True
            logger.error(f"Document (URL) send failed: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp document URL send error: {e}")
        return False


async def send_whatsapp_document_media_id(to: str, media_id: str, filename: str = "", caption: str = "") -> bool:
    """Send a WhatsApp document message via a pre-uploaded media ID."""
    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload: dict = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {"id": media_id, "caption": caption},
    }
    if filename:
        payload["document"]["filename"] = filename
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Document (media_id) sent to {to}")
                return True
            logger.error(f"Document (media_id) send failed: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp document media_id send error: {e}")
        return False


# ---------------------------------------------------------------------------
# FastWorkflow Integration
# ---------------------------------------------------------------------------

async def get_or_create_session(phone: str) -> dict:
    """Get or create a FastWorkflow session."""
    if phone in session_cache:
        return session_cache[phone]
    
    try:
        # Build a unique channel_id based on the current session generation.
        # Incrementing the generation on reset ensures FastWorkflow creates a
        # brand-new session with no prior conversation history.
        gen = session_generation.get(phone, 0)
        channel_id = f"whatsapp_{phone}_v{gen}" if gen > 0 else f"whatsapp_{phone}"
        # 120s timeout: FastWorkflow initialization can be slow on first request
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{FASTWORKFLOW_URL}/initialize", json={
                "channel_id": channel_id,
                "user_id": phone
            })
            
            if resp.status_code == 200:
                data = resp.json()
                session_cache[phone] = data
                logger.info(f"Session created successfully for {phone}")
                return data
            else:
                logger.error(f"Failed to initialize session (HTTP {resp.status_code}): {resp.text}")
                return {}
    except Exception as e:
        logger.error(f"Session creation error: {type(e).__name__}: {str(e)}")
        return {}


# Internal FastWorkflow command/context names that must never be exposed to users.
_INTERNAL_TERMS = {
    "initialize_session", "what_can_i_do", "what_is_current_context",
    "reset_context", "go_up", "SupportSession", "command_context",
}

# Known LLM misspellings of "Kavacch" to correct before sending to users.
# The LLM occasionally hallucinates the company name.
_COMPANY_NAME_FIXES = [
    "Kavach", "Kavach'", "Kavvacch", "KavAcch", "Kavacch'", "Kavach Packaging", "Kaavacch",
]

def _sanitize_agent_response(response: str) -> str:
    """Fix company name misspellings and suppress any internal term leakage."""
    # Correct LLM misspellings of the company name
    for wrong in _COMPANY_NAME_FIXES:
        if wrong.lower() in response.lower():
            response = re.sub(re.escape(wrong), "Kavacch", response, flags=re.IGNORECASE)
            logger.warning(f"Corrected company name misspelling: '{wrong}' → 'Kavacch'")

    # Suppress responses that leak internal command/context names
    lowered = response.lower()
    if any(term.lower() in lowered for term in _INTERNAL_TERMS):
        logger.warning("Agent response contained internal terms — suppressed.")
        return (
            "Here's what I can help you with:\n\n"
            "📦 Product Info — Ask about window boxes, MDF boards, drum boards, or cutlery kits\n"
            "📏 Sizes — \"What sizes are available?\"\n"
            "🎨 Colors — \"What colors do you have?\"\n"
            "✨ Customization — \"Do you offer branding or foil stamping?\"\n"
            "🛒 Add to Cart — \"Add 500 window boxes to my cart\"\n"
            "👁 View Cart — \"Show me my cart\"\n"
            "🗑 Remove Item — \"Remove item 2 from my cart\"\n"
            "❌ Clear Cart — \"Clear my cart\"\n"
            "✅ Checkout — \"I'm ready to checkout\"\n"
            "🔄 Reset — Say \"reset\" to start a fresh conversation\n\n"
            "Just type naturally — I'll understand!"
        )
    return response


def _get_groq_api_key() -> str | None:
    """Try os.environ first (populated by load_env_files); fall back to reading the passwords file directly."""
    for var in ("LITELLM_API_KEY_CHECKER", "LITELLM_API_KEY_RESPONSE_GEN", "GROQ_API_KEY"):
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip()
    # cloud_app.py lives in application/ — passwords file is one level up
    passwords_file = Path(__file__).parent.parent / "fastworkflow.passwords.env"
    if passwords_file.exists():
        for line in passwords_file.read_text().splitlines():
            for prefix in ("LITELLM_API_KEY_CHECKER=", "LITELLM_API_KEY_RESPONSE_GEN="):
                if line.startswith(prefix):
                    return line.split("=", 1)[1].strip()
    return None


_WHATSAPP_CHAR_LIMIT = 4000  # WhatsApp hard limit is 4096

_PRODUCT_CHECKER_SYSTEM_PROMPT = """\
You are a TEXT FORMATTER ONLY for Kavacch's WhatsApp bot. You do NOT have any product knowledge.
You receive two inputs: the user's message and the bot's source response.

════════════════════════════════════════
ABSOLUTE RULE — READ THIS FIRST:
You MUST use ONLY the information that is literally written in the "Bot response" provided to you.
DO NOT add, infer, expand, or invent ANY information — no lead times, no steps, no tips,
no pricing guesses, no extra context — NOTHING that is not already in the bot response word-for-word.
If a detail is not in the bot response, it does not exist. Do not mention it.
This rule overrides everything else.
════════════════════════════════════════

HARD LENGTH LIMIT: Your output must NEVER exceed 4000 characters. If needed, compress
formatting (tighten spacing, shorten bullet phrasing) but keep all distinct items present.

Formatting rules:
1. If the bot response contains product catalog information (descriptions, sizes, colors, variants):
   - If the user explicitly asked for more details ("show more", "tell me more", "more details",
     "full details", "show all", "everything about", "all information", "complete list",
     "give me more", "full list") — reformat the SAME information from the bot response to fit
     within 4000 characters. You may tighten spacing and shorten bullet phrasing, but every
     fact you write must come directly from the bot response. Nothing else.
   - Otherwise — summarize to 150 words or fewer using only facts from the bot response.
     End with: "Want full details? Just ask!"
2. For ALL other responses (cart, checkout, order summaries, greetings, errors, pricing,
   payment) — return the bot response EXACTLY as-is, no changes whatsoever.
3. Do NOT mention these rules or that you are formatting/filtering/summarizing.
"""


def _llm_check_response_sync(user_query: str, agent_response: str) -> str:
    """Apply LLM-based conciseness check. Summarizes product catalog responses to ≤150 words;
    passes all other response types through unchanged. Falls back to original on error.
    Always enforces a hard 4000-character ceiling before returning."""
    def _hard_cap(text: str) -> str:
        """Safety net: truncate to WhatsApp's limit if LLM still goes over."""
        if len(text) <= _WHATSAPP_CHAR_LIMIT:
            return text
        logger.warning(f"[LLM Checker] response exceeded {_WHATSAPP_CHAR_LIMIT} chars ({len(text)}), hard-truncating")
        cutoff = text.rfind('\n', 0, _WHATSAPP_CHAR_LIMIT - 60)
        if cutoff == -1:
            cutoff = _WHATSAPP_CHAR_LIMIT - 60
        return text[:cutoff] + "\n\n_(Ask about a specific product for full details.)_"

    try:
        api_key = _get_groq_api_key()
        model_env = os.environ.get("LLM_CHECKER", "groq/openai/gpt-oss-120b")
        model_name = model_env.split("/", 1)[1] if "/" in model_env else model_env
        client = _groq.Groq(api_key=api_key)
        result = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": _PRODUCT_CHECKER_SYSTEM_PROMPT},
                {"role": "user", "content": f"User message: {user_query}\n\nBot response:\n{agent_response}"},
            ],
        )
        return _hard_cap(result.choices[0].message.content.strip())
    except Exception as e:
        logger.warning(f"[LLM Checker] call failed ({type(e).__name__}: {e}), using original response")
        return _hard_cap(agent_response)


async def _do_agent_call(phone: str, message: str, session: dict, is_new_session: bool) -> httpx.Response:
    """Execute the FastWorkflow /invoke_agent call(s) and return the final response."""
    global total_agent_time, agent_call_count
    async with httpx.AsyncClient(timeout=120) as client:
        headers = {}
        token = session.get('access_token', '')
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if is_new_session:
            _t_start = time.monotonic()
            init_resp = await client.post(
                f"{FASTWORKFLOW_URL}/invoke_agent",
                json={"user_query": f"initialize session for phone {phone}", "timeout_seconds": 500},
                headers=headers,
            )
            total_agent_time += time.monotonic() - _t_start
            agent_call_count += 1
            asyncio.create_task(_persist_runtime_metrics())
            if init_resp.status_code != 200:
                logger.error(f"Session init error (HTTP {init_resp.status_code}): {init_resp.text}")

        _t_start = time.monotonic()
        resp = await client.post(
            f"{FASTWORKFLOW_URL}/invoke_agent",
            json={"user_query": message, "timeout_seconds": 500},
            headers=headers,
        )
        total_agent_time += time.monotonic() - _t_start
        agent_call_count += 1
        asyncio.create_task(_persist_runtime_metrics())
        return resp


async def chat_with_agent(phone: str, message: str) -> str:
    """Send message to FastWorkflow agent and get response."""
    is_new_session = phone not in session_cache
    session = await get_or_create_session(phone)
    if not session:
        return "I'm having trouble connecting. Please try again."

    try:
        resp = await _do_agent_call(phone, message, session, is_new_session)

        # JWT expired — evict stale session and retry once with a fresh one
        if resp.status_code == 401:
            logger.warning(f"JWT expired for {phone} — refreshing session and retrying")
            session_cache.pop(phone, None)
            session = await get_or_create_session(phone)
            if not session:
                return "I'm having trouble connecting. Please try again."
            resp = await _do_agent_call(phone, message, session, is_new_session=True)

        if resp.status_code == 200:
            data = resp.json()
            command_responses = data.get("command_responses", [])
            if command_responses:
                sanitized = _sanitize_agent_response(command_responses[0].get("response", ""))
            else:
                sanitized = _sanitize_agent_response(data.get("response", ""))
            return await asyncio.to_thread(_llm_check_response_sync, message, sanitized)
        else:
            logger.error(f"Chat error (HTTP {resp.status_code}): {resp.text}")
            return "I'm having trouble processing that. Please try again."
    except Exception as e:
        logger.error(f"Chat error: {type(e).__name__}: {str(e)}")
        return "I'm having trouble connecting. Please try again."


# ---------------------------------------------------------------------------
# Pending Order Management (for pricing flow)
# ---------------------------------------------------------------------------

def add_pending_order(customer_phone: str, order_summary: str, products: list, customer_name: str = "Customer") -> str:
    """Add a pending order awaiting pricing. Returns the unique order_id (ref code)."""
    import random, string
    order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    pending_orders[order_id] = {
        "customer_phone": customer_phone,
        "customer_name": customer_name,
        "order_summary": order_summary,
        "products": products,
        "timestamp": datetime.now(),
    }
    logger.info(f"Added pending order {order_id} for {customer_phone}")
    return order_id


def get_pending_order(customer_phone: str) -> Optional[dict]:
    """Get the most recent pending order for a customer (by phone)."""
    matches = [
        (oid, data) for oid, data in pending_orders.items()
        if data["customer_phone"] == customer_phone
    ]
    if not matches:
        return None
    return max(matches, key=lambda x: x[1]["timestamp"])[1]


def remove_pending_order(order_id: str):
    """Remove a pending order by its order_id after pricing is sent."""
    if order_id in pending_orders:
        del pending_orders[order_id]
        logger.info(f"Removed pending order {order_id}")


def get_oldest_pending_order() -> Optional[tuple]:
    """Get the oldest pending order (order_id, order_data)."""
    if not pending_orders:
        return None
    oldest = min(pending_orders.items(), key=lambda x: x[1]["timestamp"])
    return oldest


def cleanup_old_orders(max_age_hours: int = 24):
    """Remove orders older than max_age_hours."""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    to_remove = [
        order_id for order_id, data in pending_orders.items()
        if data["timestamp"] < cutoff
    ]
    for order_id in to_remove:
        remove_pending_order(order_id)


def cleanup_processed_messages(max_age_minutes: int = 30):
    """Remove old message IDs to prevent memory leak."""
    cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
    to_remove = [mid for mid, ts in processed_message_ids.items() if ts < cutoff]
    for mid in to_remove:
        del processed_message_ids[mid]


# ---------------------------------------------------------------------------
# Conversation State & Logging Helpers
# ---------------------------------------------------------------------------

def log_message(phone: str, role: str, text: str, msg_type: str = "text",
                media_url: Optional[str] = None, caption: Optional[str] = None,
                media_name: Optional[str] = None):
    """Append a message to the in-memory conversation transcript."""
    if phone not in conversation_logs:
        conversation_logs[phone] = []
    entry: dict = {
        "role": role,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": msg_type,
    }
    if media_url is not None:
        entry["media_url"] = media_url
    if caption is not None:
        entry["caption"] = caption
    if media_name is not None:
        entry["media_name"] = media_name
    conversation_logs[phone].append(entry)
    # Persist asynchronously — does not block the caller
    asyncio.create_task(_persist_conversation(phone))


def get_control_state(phone: str) -> str:
    """Return BOT_CONTROL or HUMAN_CONTROL for a customer."""
    return control_state.get(phone, "BOT_CONTROL")


def set_control_state(phone: str, state: str):
    """Set the control state for a customer conversation."""
    control_state[phone] = state
    logger.info(f"Control state for {phone} \u2192 {state}")
    asyncio.create_task(_persist_conversation(phone))


# ---------------------------------------------------------------------------
# Markdown \u2192 WhatsApp Formatter
# ---------------------------------------------------------------------------

def _md_table_to_whatsapp(table_lines: list) -> str:
    """Convert a markdown table block to WhatsApp bullet-point list."""
    rows = []
    for line in table_lines:
        line = line.strip().strip('|')
        # Skip separator rows like |---|---|---|
        if re.match(r'^[\s\-\|:]+$', line):
            continue
        cells = [c.strip() for c in line.split('|')]
        if cells:
            rows.append(cells)
    if not rows:
        return ''

    headers = rows[0]
    data_rows = rows[1:]

    if not data_rows:
        # Only a header row — just bold the headers as a line
        return '*' + ' | '.join(headers) + '*'

    parts = []
    # Single-column table → plain bullet list
    if len(headers) == 1:
        for row in data_rows:
            parts.append(f'\u2022 {row[0]}')
        return '\n'.join(parts)

    # First column is the "item name", remaining columns are field:value pairs
    rest_headers = headers[1:]
    for row in data_rows:
        name = row[0] if row else ''
        parts.append(f'*{name}*')
        for i, header in enumerate(rest_headers):
            value = row[i + 1] if i + 1 < len(row) else ''
            if value:
                parts.append(f'  \u2022 {header}: {value}')
        parts.append('')  # blank line between items
    # Remove trailing blank line
    while parts and parts[-1] == '':
        parts.pop()
    return '\n'.join(parts)


def markdown_to_whatsapp(text: str) -> str:
    """Convert Markdown formatting to WhatsApp-supported formatting."""
    # Strip HTML that the agent may embed (e.g. <br>, <br/>, <strong>, etc.)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)

    # Handle markdown tables first (multi-line blocks)
    lines = text.split('\n')
    result_lines = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            table_block = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_block.append(lines[i])
                i += 1
            result_lines.append(_md_table_to_whatsapp(table_block))
        else:
            result_lines.append(lines[i])
            i += 1
    text = '\n'.join(result_lines)

    # Headings → *bold*
    text = re.sub(r'^#{1,6}\s+(.+)$', r'*\1*', text, flags=re.MULTILINE)
    # Bold **text** or __text__ → *text*  (DOTALL so multi-line bold works)
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'*\1*', text, flags=re.DOTALL)
    # Italic *text* or _text_ (single) — leave as-is, WhatsApp renders them as italic
    # Strikethrough ~~text~~ → ~text~
    text = re.sub(r'~~(.+?)~~', r'~\1~', text)
    # Inline code `text` → ```text```
    text = re.sub(r'(?<!`)`(?!`)([^`]+)(?<!`)`(?!`)', r'```\1```', text)
    # Remove markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove image markdown ![alt](url) → alt
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # Horizontal rules → unicode divider
    text = re.sub(r'^[-*_]{3,}\s*$', '\u2500' * 17, text, flags=re.MULTILINE)
    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


async def send_and_log(phone: str, message: str) -> bool:
    """Send a WhatsApp message to a customer and log it to the transcript."""
    global resolutions_used
    log_message(phone, "bot", message)  # log original markdown (dashboard renders as HTML)
    result = await send_whatsapp(phone, markdown_to_whatsapp(message))
    if result:
        resolutions_used += 1
        asyncio.create_task(_persist_runtime_metrics())
    return result


async def send_and_log_image(phone: str, image_url: str = "", media_id: str = "",
                             caption: str = "", image_name: str = "") -> bool:
    """Send a WhatsApp image from the dashboard and log it to the transcript."""
    derived_name = image_name or _extract_image_name_from_url(image_url) or (f"image_{media_id}" if media_id else "")
    display_text = caption or derived_name or "[Image]"
    log_message(
        phone, "bot",
        display_text,
        msg_type="image",
        media_url=image_url if image_url else (f"media:{media_id}" if media_id else None),
        caption=caption or None,
        media_name=derived_name or None,
    )
    if media_id:
        return await send_whatsapp_image_media_id(phone, media_id, caption)
    return await send_whatsapp_image_url(phone, image_url, caption)


async def send_and_log_document(phone: str, document_url: str = "", media_id: str = "",
                                caption: str = "", doc_name: str = "") -> bool:
    """Send a WhatsApp PDF document from the dashboard and log it to the transcript."""
    derived_name = doc_name or _extract_image_name_from_url(document_url) or (f"document_{media_id}" if media_id else "document.pdf")
    display_text = derived_name
    log_message(
        phone, "bot",
        display_text,
        msg_type="document",
        media_url=document_url if document_url else (f"media:{media_id}" if media_id else None),
        caption=caption or None,
        media_name=derived_name or None,
    )
    if media_id:
        return await send_whatsapp_document_media_id(phone, media_id, derived_name, caption)
    return await send_whatsapp_document_url(phone, document_url, derived_name, caption)


# ---------------------------------------------------------------------------
# Payment Flow Helpers
# ---------------------------------------------------------------------------

async def _upload_qr_code_to_whatsapp() -> Optional[str]:
    """Upload Factory_QR_CODE.png to WhatsApp Media API and return the media_id."""
    qr_path = Path(__file__).parent.parent / "media" / "Factory_QR_CODE.png"
    if not qr_path.exists():
        logger.warning(f"QR code file not found at {qr_path}")
        return None
    try:
        content = qr_path.read_bytes()
        upload_url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/media"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                upload_url,
                headers=headers,
                files={
                    "file": ("Factory_QR_CODE.png", content, "image/png"),
                    "type": (None, "image/png"),
                    "messaging_product": (None, "whatsapp"),
                },
            )
            if resp.status_code == 200:
                media_id = resp.json().get("id")
                logger.info(f"QR code uploaded to WhatsApp: media_id={media_id}")
                return media_id
            logger.error(f"QR code upload failed ({resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        logger.error(f"QR code upload error: {e}")
        return None


async def _startup_upload_qr_code():
    """Upload the QR code on startup and cache the media_id."""
    global _qr_code_media_id
    media_id = await _upload_qr_code_to_whatsapp()
    if media_id:
        _qr_code_media_id = media_id
        logger.info(f"QR code ready (startup): media_id={_qr_code_media_id}")
    else:
        logger.warning("QR code upload failed at startup — will retry on first use or fall back to URL")


async def _send_qr_code(phone: str) -> bool:
    """Send the factory QR code image to a customer. Returns True on success."""
    global _qr_code_media_id
    caption = "💳 Scan this QR code to make your payment"

    async def _try_send_by_id(mid: str) -> bool:
        ok = await send_whatsapp_image_media_id(phone, mid, caption)
        if ok:
            log_message(phone, "bot", caption, msg_type="image",
                        media_url=f"media:{mid}", caption=caption,
                        media_name="Factory_QR_CODE.png")
        return ok

    # Try cached media_id
    if _qr_code_media_id:
        if await _try_send_by_id(_qr_code_media_id):
            return True
        logger.warning("QR media_id send failed — re-uploading")
        _qr_code_media_id = None

    # Re-upload and retry
    new_id = await _upload_qr_code_to_whatsapp()
    if new_id:
        _qr_code_media_id = new_id
        if await _try_send_by_id(new_id):
            return True

    # Final fallback: public URL from env var
    fallback_url = os.environ.get("QR_CODE_IMAGE_URL", "")
    if fallback_url:
        ok = await send_whatsapp_image_url(phone, fallback_url, caption)
        if ok:
            log_message(phone, "bot", caption, msg_type="image",
                        media_url=fallback_url, caption=caption,
                        media_name="Factory_QR_CODE.png")
            return True

    logger.error(f"All QR code delivery methods failed for {phone}")
    return False


def _get_net_banking_link() -> str:
    """Read the net banking link from media/NET_BANKING.txt."""
    nb_path = Path(__file__).parent.parent / "media" / "NET_BANKING.txt"
    try:
        return nb_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.error(f"Failed to read NET_BANKING.txt: {e}")
        return "Please contact us for net banking details."


def _parse_payment_choice(text: str) -> Optional[int]:
    """Map free-form customer text to a payment option (1–4), or None if unclear."""
    t = text.strip().lower()
    # Exact number / "option N" matches
    if t in {"1", "1.", "option 1", "option1"}:
        return 1
    if t in {"2", "2.", "option 2", "option2"}:
        return 2
    if t in {"3", "3.", "option 3", "option3"}:
        return 3
    if t in {"4", "4.", "option 4", "option4"}:
        return 4
    # Keyword matching — option 1 (QR code)
    if any(kw in t for kw in ("qr", "scan", "qr code")):
        return 1
    # Keyword matching — option 2 (net banking)
    if any(kw in t for kw in ("net banking", "netbanking", "net bank", "bank transfer", "neft", "imps", "upi")):
        return 2
    # Keyword matching — option 3 (other way)
    if any(kw in t for kw in ("other way", "other method", "other option", "different way", "different method")):
        return 3
    if t in {"other", "others"}:
        return 3
    # Keyword matching — option 4 (talk to factory)
    if any(kw in t for kw in ("talk to factory", "connect to factory", "speak to factory",
                               "talk to team", "connect me", "speak with", "talk to someone")):
        return 4
    if t in {"talk", "factory", "connect", "speak"}:
        return 4
    return None


def _add_dashboard_alert(phone: str, message: str):
    """Append a notification alert to the dashboard alert queue."""
    import uuid
    now = datetime.now(timezone.utc)
    # Prune alerts older than 24 hours
    cutoff = now - timedelta(hours=24)
    dashboard_alerts[:] = [
        a for a in dashboard_alerts
        if datetime.fromisoformat(a["timestamp"]) > cutoff
    ]
    dashboard_alerts.append({
        "id": uuid.uuid4().hex,
        "phone": phone,
        "message": message,
        "timestamp": now.isoformat(),
        "dismissed": False,
    })
    logger.info(f"[ALERT] {phone}: {message}")


# ---------------------------------------------------------------------------
# Message Handling
# ---------------------------------------------------------------------------

async def _forward_order_to_factory(
    customer_phone: str,
    order_summary: str,
    customer_name: str = "Customer",
    products: list = None,
):
    """Forward a completed order to the factory WhatsApp for pricing."""
    if products is None:
        products = []
    order_id = add_pending_order(customer_phone, order_summary, products, customer_name)

    # Build product lines from structured data if available, else fall back to raw summary
    if products:
        lines = []
        for i, p in enumerate(products, 1):
            line = f"{i}. {p['product_type']}: {p['product_name']}"
            line += f"\n   Qty: {p['quantity']}"
            if p.get("notes"):
                line += f"\n   Notes: {p['notes']}"
            lines.append(line)
        products_text = "\n".join(lines)
    else:
        products_text = order_summary

    factory_message = (
        f"📦 *New Pricing Request*\n"
        f"🔖 Ref: #{order_id}\n\n"
        f"👤 Customer: {customer_name}\n"
        f"📞 Phone: {customer_phone}\n\n"
        f"Selected Products:\n"
        f"--------------------\n"
        f"{products_text}\n"
        f"--------------------\n\n"
        f"⚡ Reply with the TOTAL PRICE and ESTIMATED DELIVERY TIME for this order.\n"
        # f"(Start your reply with #{order_id}: to route it correctly)\n\n"
        f"Customer phone: {customer_phone}"
    )
    await send_whatsapp(FACTORY_WHATSAPP, factory_message)
    logger.info(f"Order {order_id} forwarded to factory for customer {customer_phone}")


async def handle_factory_reply(text: str):
    """
    Handle a reply from the factory with pricing.
    Factory replies must start with the ref code: #XXXXXX: <price>
    If no ref code is found, falls back to the oldest pending order.
    """
    # Parse ref code from the reply — format: #XXXXXX (6 alphanumeric chars)
    ref_match = re.match(r'#([A-Z0-9]{6})\b', text.strip(), re.IGNORECASE)
    order_id = ref_match.group(1).upper() if ref_match else None
    price_text = text[ref_match.end():].lstrip(': ').strip() if ref_match else text.strip()
    # Strip any stray markdown bold markers the factory may have typed (e.g. **60000**)
    price_text = price_text.strip('*').strip()

    # Resolve the order
    if order_id and order_id in pending_orders:
        order_data = pending_orders[order_id]
        logger.info(f"Factory reply matched order {order_id}")
    else:
        if order_id:
            logger.warning(f"Factory used ref #{order_id} but no matching order found — falling back to oldest")
        oldest = get_oldest_pending_order()
        if not oldest:
            logger.warning(f"Factory replied but no pending orders at all: {text}")
            return
        order_id, order_data = oldest
        logger.info(f"Factory reply routed to oldest pending order {order_id} (no/unknown ref)")

    customer_phone = order_data["customer_phone"]

    # Strip the "NEXT STEPS" section from the order summary — that goes in the
    # confirmation message only, not the pricing quote sent to the customer.
    raw_summary = order_data['order_summary']
    next_steps_idx = raw_summary.upper().find('NEXT STEPS')
    clean_summary = raw_summary[:next_steps_idx].rstrip() if next_steps_idx != -1 else raw_summary

    # Mark the order as awaiting the customer's payment method choice.
    pending_orders[order_id]['price_text'] = price_text
    pending_orders[order_id]['awaiting_payment_choice'] = True

    # Use **markdown bold** (not WhatsApp *bold*) so:
    #   • marked.js in the dashboard renders it as bold HTML
    #   • markdown_to_whatsapp() inside send_and_log converts ** → * before sending to WhatsApp
    pricing_message = (
        "💰 Pricing Update from Kavacch!\n\n"
        f"{clean_summary}\n\n"
        "**📋 Price Quote & Estimated Delivery:**\n"
        f"**{price_text}**\n\n"
        "Please choose your payment method:\n\n"
        "1️⃣ Pay using QR code\n"
        "2️⃣ Pay using net banking\n"
        "3️⃣ Pay using other way\n"
        "4️⃣ Talk to factory\n\n"
        "Reply *1*, *2*, *3*, or *4* to choose your option."
    )

    await send_and_log(customer_phone, pricing_message)
    logger.info(f"Forwarded pricing for order {order_id} to customer {customer_phone}")

    # Do NOT remove the pending order yet — it stays until the customer confirms or declines.

    await send_whatsapp(
        FACTORY_WHATSAPP,
        f"✅ Pricing for order #{order_id} sent to customer {customer_phone}"
    )


async def handle_customer_message(phone: str, text: str, msg_id: str = ""):
    """Handle a message from a customer."""
    stripped = text.strip().lower()

    # Help
    if stripped in {"help", "?", "menu"}:
        await send_and_log(phone, HELP_MESSAGE)
        return

    # Reset session
    if stripped == "reset":
        # Increment the generation counter so the next /initialize call uses a
        # brand-new channel_id — FastWorkflow will create a completely fresh
        # session with no prior conversation history.
        session_generation[phone] = session_generation.get(phone, 0) + 1
        session_cache.pop(phone, None)
        await send_and_log(phone, "\U0001f504 Your session has been reset! You can start a fresh conversation now.")
        return

    # --- Payment method description follow-up (option 3: "other way") ---
    _awaiting_desc = [
        (oid, data) for oid, data in pending_orders.items()
        if data.get("customer_phone") == phone and data.get("awaiting_payment_method_description")
    ]
    if _awaiting_desc:
        order_id_desc, order_data_desc = max(_awaiting_desc, key=lambda x: x[1]["timestamp"])
        payment_method = text.strip()
        await send_whatsapp(
            FACTORY_WHATSAPP,
            f"💬 Customer {phone} chose *Other Payment Method*\n"
            f"Method: {payment_method}\n"
            f"Order #{order_id_desc} — {order_data_desc.get('customer_name', 'Customer')}"
        )
        set_control_state(phone, "HUMAN_CONTROL")
        _add_dashboard_alert(
            phone,
            f"🔔 Customer chose custom payment: \"{payment_method}\" — takeover enabled for {phone} (order #{order_id_desc})"
        )
        log_message(phone, "bot", f"🔔 Customer connected to factory (payment: {payment_method})", msg_type="notification")
        pending_orders[order_id_desc]["awaiting_payment_method_description"] = False
        remove_pending_order(order_id_desc)
        await send_and_log(
            phone,
            "Thank you! We've noted your payment preference and connected you with our team. "
            "They'll assist you shortly! 🙏"
        )
        return

    # --- Payment method choice (options 1–4) ---
    _awaiting_choice = [
        (oid, data) for oid, data in pending_orders.items()
        if data.get("customer_phone") == phone and data.get("awaiting_payment_choice")
    ]
    if _awaiting_choice:
        order_id_pay, order_data_pay = max(_awaiting_choice, key=lambda x: x[1]["timestamp"])
        choice = _parse_payment_choice(stripped)

        if choice == 1:
            pending_orders[order_id_pay]["awaiting_payment_choice"] = False
            pending_orders[order_id_pay]["awaiting_payment_screenshot"] = True
            await _send_qr_code(phone)
            await send_and_log(
                phone,
                "💳 Here's the QR code above!\n\n"
                "Please complete the payment and send us a *screenshot* once done. 📸"
            )

        elif choice == 2:
            link = _get_net_banking_link()
            pending_orders[order_id_pay]["awaiting_payment_choice"] = False
            pending_orders[order_id_pay]["awaiting_payment_screenshot"] = True
            await send_and_log(
                phone,
                f"🏦 *Net Banking Payment Link:*\n{link}\n\n"
                "Please complete the payment and send us a *screenshot* once done. 📸"
            )

        elif choice == 3:
            pending_orders[order_id_pay]["awaiting_payment_choice"] = False
            pending_orders[order_id_pay]["awaiting_payment_method_description"] = True
            await send_and_log(phone, "Sure! Can you tell me which payment method you'd like to use? 💬")

        elif choice == 4:
            set_control_state(phone, "HUMAN_CONTROL")
            _add_dashboard_alert(
                phone,
                f"🔔 Customer {phone} wants to talk to factory directly (order #{order_id_pay}). Takeover enabled."
            )
            await send_whatsapp(
                FACTORY_WHATSAPP,
                f"🔔 Customer {phone} wants to talk to factory directly\n"
                f"Order #{order_id_pay} — {order_data_pay.get('customer_name', 'Customer')}\n"
                f"Price quote: {order_data_pay.get('price_text', 'N/A')}"
            )
            log_message(phone, "bot", "🔔 Customer requested factory connection. Takeover enabled.", msg_type="notification")
            remove_pending_order(order_id_pay)
            await send_and_log(
                phone,
                "Connecting you with our factory team now! They'll be with you shortly. 🙏"
            )

        elif stripped in {"cancel", "no", "nope"}:
            await send_whatsapp(
                FACTORY_WHATSAPP,
                f"❌ Order #{order_id_pay} — customer cancelled payment\n"
                f"👤 {order_data_pay.get('customer_name', 'Customer')} ({phone})"
            )
            remove_pending_order(order_id_pay)
            await send_and_log(
                phone,
                "No problem! Your order has been cancelled. Feel free to start a new order anytime. 😊\n\n"
                "Thank you for considering Kavacch!"
            )

        else:
            # Unrecognized input — repeat the menu
            await send_and_log(
                phone,
                "Please choose one of the options:\n\n"
                "1️⃣ Pay using QR code\n"
                "2️⃣ Pay using net banking\n"
                "3️⃣ Pay using other way\n"
                "4️⃣ Talk to factory\n\n"
                "Reply *1*, *2*, *3*, or *4*."
            )

        return  # always return — never fall through to agent while in payment state

    # Typing indicator — sent before acquiring the lock so the user sees
    # immediate read-receipt feedback even if a prior message is still processing.
    if msg_id:
        await send_typing_indicator(phone, msg_id)

    # Serialise agent calls per phone: prevents FastWorkflow concurrency errors
    # when the customer sends messages back-to-back.  The lock is held for the
    # full round-trip (agent call + WhatsApp send) so replies arrive in order.
    async with _get_phone_lock(phone):
        response = await chat_with_agent(phone, text)
        if response:
            await send_and_log(phone, response)


async def handle_message(phone: str, text: str, msg_id: str = ""):
    """Main message handler - routes based on sender."""
    try:
        # Clean up old pending orders
        cleanup_old_orders()
        
        # Check if message is from factory
        if phone == FACTORY_WHATSAPP or phone == FACTORY_WHATSAPP.lstrip("91"):
            logger.info(f"[FACTORY] Message received: {text}")
            await handle_factory_reply(text)
        else:
            logger.info(f"[CUSTOMER {phone}] Message: {text}")
            # Log incoming message to transcript
            log_message(phone, "user", text)

            # If factory has taken over via dashboard, skip the agent
            if get_control_state(phone) == "HUMAN_CONTROL":
                logger.info(f"[HUMAN_CONTROL] Skipping agent for {phone} — factory handles via dashboard")
                return

            await handle_customer_message(phone, text, msg_id)
            
    except Exception as e:
        logger.error(f"Error handling message from {phone}: {e}")
        await send_whatsapp(
            phone,
            "Sorry, I encountered an error. Please try again."
        )


# ---------------------------------------------------------------------------
# Webhook Endpoints
# ---------------------------------------------------------------------------

@app.get("/webhooks/whatsapp")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge)
    
    logger.warning(f"Webhook verification failed. Mode: {mode}, Token match: {token == VERIFY_TOKEN}")
    return Response(content="Forbidden", status_code=403)


@app.post("/webhooks/whatsapp")
async def webhook(request: Request):
    """Handle incoming WhatsApp messages."""
    try:
        data = await request.json()
        
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                if "messages" in value:
                    msg = value["messages"][0]
                    
                    if msg.get("type") == "text":
                        phone = msg["from"]
                        text = msg["text"]["body"]
                        msg_id = msg.get("id", "")
                        
                        # Deduplicate: skip if already processed
                        if msg_id and msg_id in processed_message_ids:
                            logger.info(f"Skipping duplicate message {msg_id}")
                            return {"status": "ok"}
                        
                        if msg_id:
                            processed_message_ids[msg_id] = datetime.now()
                            cleanup_processed_messages()
                        
                        # Await directly to keep Cloud Run request active
                        # (fire-and-forget via create_task causes Cloud Run
                        #  to kill the container when no requests are active)
                        await handle_message(phone, text, msg_id)

                    elif msg.get("type") == "image":
                        phone = msg["from"]
                        msg_id = msg.get("id", "")
                        image_info = msg.get("image", {})
                        caption = image_info.get("caption", "")
                        media_id = image_info.get("id", "")
                        media_mime = image_info.get("mime_type", "")

                        if msg_id and msg_id in processed_message_ids:
                            logger.info(f"Skipping duplicate image message {msg_id}")
                            return {"status": "ok"}
                        if msg_id:
                            processed_message_ids[msg_id] = datetime.now()
                            cleanup_processed_messages()

                        logger.info(f"[CUSTOMER {phone}] Inbound image, media_id={media_id}")
                        media_name = image_info.get("filename")
                        if not media_name and media_mime:
                            ext = media_mime.split("/")[-1] if "/" in media_mime else "img"
                            media_name = f"image_{media_id[:8]}.{ext}" if media_id else "image"

                        log_message(
                            phone, "user",
                            caption or media_name or "[Image]",
                            msg_type="image",
                            media_url=f"media:{media_id}" if media_id else None,
                            caption=caption or None,
                            media_name=media_name or None,
                        )
                        if get_control_state(phone) != "HUMAN_CONTROL":
                            # Check if customer was asked to send a payment screenshot
                            _screenshot_orders = [
                                (oid, data) for oid, data in pending_orders.items()
                                if data.get("customer_phone") == phone
                                and data.get("awaiting_payment_screenshot")
                            ]
                            if _screenshot_orders:
                                oid_ss, data_ss = max(_screenshot_orders, key=lambda x: x[1]["timestamp"])
                                await send_whatsapp(
                                    FACTORY_WHATSAPP,
                                    f"📸 Customer {phone} sent payment screenshot\n"
                                    f"Order #{oid_ss} — {data_ss.get('customer_name', 'Customer')}\n"
                                    f"Price quote: {data_ss.get('price_text', 'N/A')}"
                                )
                                pending_orders[oid_ss]["awaiting_payment_screenshot"] = False
                                remove_pending_order(oid_ss)
                                await send_and_log(
                                    phone,
                                    "✅ Thank you! We've received your payment screenshot and will confirm shortly. 🙏\n\n"
                                    "Thank you for choosing Kavacch!"
                                )
                            else:
                                await send_and_log(
                                    phone,
                                    "I received your image! For the best help, please describe your question in text and I\u2019ll assist you right away. \U0001f60a"
                                )
                        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
    
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# API Endpoints for Checkout Integration
# ---------------------------------------------------------------------------

@app.post("/api/add_pending_order")
async def api_add_pending_order(request: Request):
    """
    API endpoint to add a pending order (called by checkout command).
    This is how the checkout command notifies the cloud app about a new order.
    """
    try:
        data = await request.json()
        customer_phone = data.get("customer_phone")
        order_summary = data.get("order_summary")
        products = data.get("products", [])
        
        if not customer_phone or not order_summary:
            return JSONResponse({"error": "Missing customer_phone or order_summary"}, status_code=400)
        
        add_pending_order(customer_phone, order_summary, products)
        
        return {"status": "success", "message": f"Pending order added for {customer_phone}"}
        
    except Exception as e:
        logger.error(f"Error adding pending order: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/checkout_complete")
async def api_checkout_complete(request: Request):
    """
    Called directly by checkout.py after a successful checkout.
    Adds the order to pending_orders and forwards it to the factory WhatsApp.
    This bypasses the unreliable approach of parsing the LLM-reformatted response.
    """
    try:
        data = await request.json()
        customer_phone = data.get("customer_phone")
        order_summary = data.get("order_summary")
        customer_name = data.get("customer_name", "Customer")
        products = data.get("products", [])

        if not customer_phone or not order_summary:
            return JSONResponse({"error": "Missing customer_phone or order_summary"}, status_code=400)

        await _forward_order_to_factory(customer_phone, order_summary, customer_name, products)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"checkout_complete error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/pending_orders")
async def api_get_pending_orders():
    """Get all pending orders (for debugging/admin)."""
    return {
        "pending_orders": {
            order_id: {
                "customer_phone": data["customer_phone"],
                "order_summary": data["order_summary"],
                "timestamp": data["timestamp"].isoformat(),
            }
            for order_id, data in pending_orders.items()
        }
    }
    


# ---------------------------------------------------------------------------
# Factory Dashboard
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the factory operator dashboard."""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    with open(dashboard_path) as f:
        return HTMLResponse(content=f.read())


@app.get("/api/conversations")
async def api_get_conversations():
    """List all conversations with metadata."""
    blocked_users = await get_blocked_users()
    result = {}
    for phone, messages in conversation_logs.items():
        last_msg = messages[-1] if messages else None
        awaiting_payment_choice = any(
            d.get("customer_phone") == phone and d.get("awaiting_payment_choice")
            for d in pending_orders.values()
        )
        awaiting_method_desc = any(
            d.get("customer_phone") == phone and d.get("awaiting_payment_method_description")
            for d in pending_orders.values()
        )
        awaiting_screenshot = any(
            d.get("customer_phone") == phone and d.get("awaiting_payment_screenshot")
            for d in pending_orders.values()
        )
        result[phone] = {
            "state": get_control_state(phone),
            "blocked": phone in blocked_users,
            "message_count": len(messages),
            "last_message": last_msg,
            "awaiting_payment_choice": awaiting_payment_choice,
            "awaiting_payment_method_description": awaiting_method_desc,
            "awaiting_payment_screenshot": awaiting_screenshot,
        }
    return result


@app.get("/api/resolutions")
async def api_get_resolutions():
    """Return resolution usage, referral credits, and avg response time stats."""
    avg_time = round(total_agent_time / agent_call_count, 2) if agent_call_count > 0 else 0.0
    return {
        "used": resolutions_used,
        "limit": RESOLUTION_LIMIT,
        "remaining": max(0, RESOLUTION_LIMIT - resolutions_used),
        "referral_credits": REFERRAL_CREDITS,
        "automation_rate": AUTOMATION_RATE,
        "avg_response_time": avg_time,
        "agent_calls": agent_call_count
    }


@app.get("/api/conversations/{phone}")
async def api_get_conversation(phone: str):
    """Get full transcript for a customer."""
    blocked_users = await get_blocked_users()
    return {
        "phone": phone,
        "state": get_control_state(phone),
        "blocked": phone in blocked_users,
        "messages": conversation_logs.get(phone, [])
    }


@app.post("/api/block/{phone}")
async def api_block_number(phone: str):
    """Block a customer via the official WhatsApp Cloud API."""
    try:
        result = await set_blocked_user(phone, True)
        if get_control_state(phone) == "HUMAN_CONTROL":
            set_control_state(phone, "BOT_CONTROL")
        logger.info(f"[BLOCK] {phone} blocked via WhatsApp Cloud API")
        return result
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        logger.error(f"Block API rejected request for {phone}: {detail}")
        return JSONResponse({"error": detail or "Block request failed"}, status_code=exc.response.status_code)
    except Exception as exc:
        logger.error(f"Block request failed for {phone}: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/unblock/{phone}")
async def api_unblock_number(phone: str):
    """Unblock a customer via the official WhatsApp Cloud API."""
    try:
        result = await set_blocked_user(phone, False)
        logger.info(f"[UNBLOCK] {phone} unblocked via WhatsApp Cloud API")
        return result
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        logger.error(f"Unblock API rejected request for {phone}: {detail}")
        return JSONResponse({"error": detail or "Unblock request failed"}, status_code=exc.response.status_code)
    except Exception as exc:
        logger.error(f"Unblock request failed for {phone}: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/toggle/{phone}")
async def api_toggle_control(phone: str):
    """Toggle BOT_CONTROL \u21d4 HUMAN_CONTROL for a conversation."""
    blocked_users = await get_blocked_users()
    if phone in blocked_users:
        return JSONResponse(
            {"error": "Conversation is blocked on WhatsApp. Unblock it first."},
            status_code=400,
        )

    current = get_control_state(phone)
    new_state = "HUMAN_CONTROL" if current == "BOT_CONTROL" else "BOT_CONTROL"
    set_control_state(phone, new_state)

    if new_state == "HUMAN_CONTROL":
        msg = "Please wait, connecting you to our team... \U0001f464"
    else:
        msg = "Our automated assistant is back. How can I help? \U0001f916"

    log_message(phone, "bot", msg)
    await send_whatsapp(phone, msg)
    return {"phone": phone, "state": new_state}


@app.post("/api/agent/send")
async def api_agent_send(request: Request):
    """Factory sends a message to a customer from the dashboard."""
    data = await request.json()
    phone = data.get("phone")
    message = data.get("message", "").strip()

    if not phone or not message:
        return JSONResponse({"error": "Missing phone or message"}, status_code=400)

    if get_control_state(phone) != "HUMAN_CONTROL":
        return JSONResponse(
            {"error": "Conversation is not in HUMAN_CONTROL. Toggle takeover first."},
            status_code=400
        )

    log_message(phone, "bot", message)
    success = await send_whatsapp(phone, message)

    if success:
        return {"status": "sent"}
    return JSONResponse({"error": "Failed to send message"}, status_code=500)


# ---------------------------------------------------------------------------
# Media Upload & Image Send Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/media/upload")
async def api_media_upload(file: UploadFile = File(...)):
    """Upload an image to the WhatsApp Media API and return the media_id."""
    if not MEDIA_SEND_ENABLED:
        return JSONResponse({"error": "Image sending is disabled"}, status_code=403)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return JSONResponse(
            {"error": f"Unsupported type '{file.content_type}'. Allowed: JPEG, PNG, WebP"},
            status_code=400,
        )

    content = await file.read()

    if len(content) > MAX_IMAGE_SIZE_BYTES:
        return JSONResponse(
            {"error": f"File too large ({len(content) // (1024 * 1024)} MB). Maximum is 30 MB."},
            status_code=400,
        )

    if not _validate_image_bytes(content, file.content_type):
        return JSONResponse(
            {"error": "File content does not match the declared image type"},
            status_code=400,
        )

    upload_url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                upload_url,
                headers=headers,
                files={
                    "file": (file.filename or "image.jpg", content, file.content_type),
                    "type": (None, file.content_type),
                    "messaging_product": (None, "whatsapp"),
                },
            )
            if resp.status_code == 200:
                media_id = resp.json().get("id")
                logger.info(f"Media uploaded successfully: media_id={media_id}")
                return {"media_id": media_id}
            logger.error(f"WhatsApp media upload failed: {resp.text}")
            return JSONResponse({"error": "WhatsApp media upload failed"}, status_code=500)
    except Exception as e:
        logger.error(f"Media upload error: {e}")
        return JSONResponse({"error": "Upload error"}, status_code=500)


@app.post("/api/media/upload_pdf")
async def api_media_upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF to the WhatsApp Media API and return the media_id."""
    if not MEDIA_SEND_ENABLED:
        return JSONResponse({"error": "Document sending is disabled"}, status_code=403)

    if file.content_type != ALLOWED_PDF_TYPE:
        return JSONResponse(
            {"error": f"Unsupported type '{file.content_type}'. Only PDF is allowed."},
            status_code=400,
        )

    content = await file.read()

    if len(content) > MAX_PDF_SIZE_BYTES:
        return JSONResponse(
            {"error": f"File too large ({len(content) // (1024 * 1024)} MB). Maximum is 25 MB."},
            status_code=400,
        )

    if not _validate_pdf_bytes(content):
        return JSONResponse(
            {"error": "File content does not appear to be a valid PDF"},
            status_code=400,
        )

    upload_url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    safe_filename = file.filename or "document.pdf"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                upload_url,
                headers=headers,
                files={
                    "file": (safe_filename, content, ALLOWED_PDF_TYPE),
                    "type": (None, ALLOWED_PDF_TYPE),
                    "messaging_product": (None, "whatsapp"),
                },
            )
            if resp.status_code == 200:
                media_id = resp.json().get("id")
                logger.info(f"PDF uploaded successfully: media_id={media_id}, filename={safe_filename}")
                return {"media_id": media_id, "filename": safe_filename}
            logger.error(f"WhatsApp PDF upload failed: {resp.text}")
            return JSONResponse({"error": "WhatsApp PDF upload failed"}, status_code=500)
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        return JSONResponse({"error": "Upload error"}, status_code=500)


@app.post("/api/agent/send_image")
async def api_agent_send_image(request: Request):
    """Send an image to a customer from the dashboard during HUMAN_CONTROL takeover."""
    if not MEDIA_SEND_ENABLED:
        return JSONResponse({"error": "Image sending is disabled"}, status_code=403)

    data = await request.json()
    phone = data.get("phone", "").strip()
    caption = data.get("caption", "").strip()
    image_url = data.get("image_url", "").strip()
    media_id = data.get("media_id", "").strip()
    image_name = data.get("image_name", "").strip()

    if not phone:
        return JSONResponse({"error": "Missing phone"}, status_code=400)
    if not image_url and not media_id:
        return JSONResponse({"error": "Provide image_url or media_id"}, status_code=400)

    if get_control_state(phone) != "HUMAN_CONTROL":
        return JSONResponse(
            {"error": "Conversation is not in HUMAN_CONTROL. Toggle takeover first."},
            status_code=400,
        )

    success = await send_and_log_image(
        phone,
        image_url=image_url,
        media_id=media_id,
        caption=caption,
        image_name=image_name,
    )
    if success:
        return {"status": "sent"}
    return JSONResponse({"error": "Failed to send image"}, status_code=500)


@app.post("/api/agent/send_pdf")
async def api_agent_send_pdf(request: Request):
    """Send a PDF document to a customer from the dashboard during HUMAN_CONTROL takeover."""
    if not MEDIA_SEND_ENABLED:
        return JSONResponse({"error": "Document sending is disabled"}, status_code=403)

    data = await request.json()
    phone = data.get("phone", "").strip()
    caption = data.get("caption", "").strip()
    pdf_url = data.get("pdf_url", "").strip()
    media_id = data.get("media_id", "").strip()
    pdf_name = data.get("pdf_name", "").strip()

    if not phone:
        return JSONResponse({"error": "Missing phone"}, status_code=400)
    if not pdf_url and not media_id:
        return JSONResponse({"error": "Provide pdf_url or media_id"}, status_code=400)

    if get_control_state(phone) != "HUMAN_CONTROL":
        return JSONResponse(
            {"error": "Conversation is not in HUMAN_CONTROL. Toggle takeover first."},
            status_code=400,
        )

    success = await send_and_log_document(
        phone,
        document_url=pdf_url,
        media_id=media_id,
        caption=caption,
        doc_name=pdf_name,
    )
    if success:
        return {"status": "sent"}
    return JSONResponse({"error": "Failed to send PDF"}, status_code=500)


@app.get("/api/media/proxy/{media_id}")
async def api_media_proxy(media_id: str):
    """Proxy WhatsApp media by media_id so dashboard can render it like chat images."""
    info = await _fetch_whatsapp_media_download_info(media_id)
    if not info:
        return JSONResponse({"error": "Media not found"}, status_code=404)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(info["url"], headers=headers)
            if resp.status_code != 200:
                logger.error(f"Media proxy download failed ({media_id}): {resp.text}")
                return JSONResponse({"error": "Media download failed"}, status_code=502)

            content_type = resp.headers.get("content-type") or info.get("mime_type") or "application/octet-stream"
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Cache-Control": "private, max-age=60"},
            )
    except Exception as e:
        logger.error(f"Media proxy error for {media_id}: {e}")
        return JSONResponse({"error": "Media proxy error"}, status_code=500)


# ---------------------------------------------------------------------------
# Dashboard Alert Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/dashboard_alerts")
async def api_get_dashboard_alerts():
    """Return non-dismissed dashboard alerts (newest first, last 24h)."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    active = [
        a for a in dashboard_alerts
        if not a["dismissed"]
        and datetime.fromisoformat(a["timestamp"]) > cutoff
    ]
    active.sort(key=lambda a: a["timestamp"], reverse=True)
    return {"alerts": active}


@app.post("/api/dashboard_alerts/{alert_id}/dismiss")
async def api_dismiss_dashboard_alert(alert_id: str):
    """Mark a dashboard alert as dismissed."""
    for alert in dashboard_alerts:
        if alert["id"] == alert_id:
            alert["dismissed"] = True
            return {"status": "dismissed"}
    return JSONResponse({"error": "Alert not found"}, status_code=404)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pending_orders_count": len(pending_orders),
        "active_sessions": len(session_cache)
    }
