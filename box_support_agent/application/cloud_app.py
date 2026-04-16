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
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Optional

# --- FIRESTORE (optional — falls back to in-memory if unavailable) ---
try:
    from google.cloud import firestore as _gcp_firestore
    _FIRESTORE_AVAILABLE = True
except ImportError:
    _FIRESTORE_AVAILABLE = False

_firestore_db = None

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
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "kalash_verify_2024")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")

# Factory WhatsApp number (without +)
FACTORY_WHATSAPP = os.environ.get("FACTORY_WHATSAPP", "919725201616")

# FastWorkflow URL (runs locally in same container)
FASTWORKFLOW_URL = "http://localhost:8000"

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
            "updated_at": _gcp_firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        logger.error(f"Firestore persist error for {phone}: {e}")


@app.on_event("startup")
async def startup_load_conversations():
    await _load_from_firestore()



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

# Resolution counter: each agent response costs 1
RESOLUTION_LIMIT: int = int(os.environ.get("RESOLUTION_LIMIT", "500"))
REFERRAL_CREDITS: int = int(os.environ.get("REFERRAL_CREDITS", "0"))
AUTOMATION_RATE: str = os.environ.get("AUTOMATION_RATE", "0")
resolutions_used: int = 0

# Average response time tracking
total_agent_time: float = 0.0
agent_call_count: int = 0

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
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
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


async def send_typing_indicator(to: str, msg_id: str):
    """Broadcast a unified read receipt + typing indicator via Meta Graph API.

    Uses the single atomic payload with ``typing_indicator`` nested object
    as required by the WhatsApp Cloud API spec.  The old implementation
    incorrectly used ``"status": "typing"`` which is an invalid enum value
    and was silently rejected with HTTP 400.
    """
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
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

# Known LLM misspellings of "Kalash" to correct before sending to users.
# The LLM occasionally hallucinates the company name.
_COMPANY_NAME_FIXES = [
    "Kalab", "Kalash'", "Kalsh", "Kalaash", "KalAsh", "Kallash",
]

def _sanitize_agent_response(response: str) -> str:
    """Fix company name misspellings and suppress any internal term leakage."""
    # Correct LLM misspellings of the company name
    for wrong in _COMPANY_NAME_FIXES:
        if wrong.lower() in response.lower():
            response = re.sub(re.escape(wrong), "Kalash", response, flags=re.IGNORECASE)
            logger.warning(f"Corrected company name misspelling: '{wrong}' → 'Kalash'")

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


async def chat_with_agent(phone: str, message: str) -> str:
    """Send message to FastWorkflow agent and get response."""
    global total_agent_time, agent_call_count

    is_new_session = phone not in session_cache
    session = await get_or_create_session(phone)
    if not session:
        return "I'm having trouble connecting. Please try again."

    try:
        # 120s timeout: Agent processing can take time for complex queries
        async with httpx.AsyncClient(timeout=120) as client:
            # Build headers - only add Authorization if token exists
            headers = {}
            token = session.get('access_token', '')
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # For new sessions: silently initialize the session with the phone number
            # so SupportSession is created with the correct phone context.
            # We do NOT send the init response — the agent's reply to the user's
            # actual message serves as the natural welcome.
            if is_new_session:
                _t_start = time.monotonic()
                init_resp = await client.post(
                    f"{FASTWORKFLOW_URL}/invoke_agent",
                    json={
                        "user_query": f"initialize session for phone {phone}",
                        "timeout_seconds": 500
                    },
                    headers=headers
                )
                _elapsed = time.monotonic() - _t_start
                total_agent_time += _elapsed
                agent_call_count += 1

                if init_resp.status_code != 200:
                    logger.error(f"Session init error (HTTP {init_resp.status_code}): {init_resp.text}")

            _t_start = time.monotonic()
            resp = await client.post(
                f"{FASTWORKFLOW_URL}/invoke_agent",
                json={
                    "user_query": message,
                    "timeout_seconds": 500
                },
                headers=headers
            )
            _elapsed = time.monotonic() - _t_start
            total_agent_time += _elapsed
            agent_call_count += 1

            if resp.status_code == 200:
                data = resp.json()
                # FastWorkflow returns response nested in command_responses array
                command_responses = data.get("command_responses", [])
                if command_responses:
                    return _sanitize_agent_response(command_responses[0].get("response", ""))
                return _sanitize_agent_response(data.get("response", ""))
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

def log_message(phone: str, role: str, text: str):
    """Append a message to the in-memory conversation transcript."""
    if phone not in conversation_logs:
        conversation_logs[phone] = []
    conversation_logs[phone].append({
        "role": role,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    # Persist asynchronously — does not block the caller
    asyncio.create_task(_persist_conversation(phone))


def get_control_state(phone: str) -> str:
    """Return BOT_CONTROL or HUMAN_CONTROL for a customer. Default is BOT_CONTROL."""
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
    return result


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
        f"⚡ Reply with the TOTAL PRICE for this order.\n"
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

    pricing_message = (
        "💰 Pricing Update from Kalash Packaging!\n\n"
        f"{order_data['order_summary']}\n\n"
        "📋 Price Quote:\n"
        f"{price_text}\n\n"
        "Reply 'confirm' to proceed with the order or ask any questions.\n\n"
        "Thank you for choosing Kalash Packaging! 🙏"
    )

    log_message(customer_phone, "bot", pricing_message)
    await send_whatsapp(customer_phone, pricing_message)
    logger.info(f"Forwarded pricing for order {order_id} to customer {customer_phone}")

    remove_pending_order(order_id)

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

    # Order confirmation
    if stripped == "confirm":
        await send_and_log(
            phone,
            "\u2705 Thank you for confirming your order!\n\n"
            "Our team will contact you shortly to finalize the details.\n\n"
            f"\U0001f4de You can also reach us at: {FACTORY_WHATSAPP}\n\n"
            "Thank you for choosing Kalash Packaging! \U0001f64f"
        )
        return

    # Typing indicator
    if msg_id:
        await send_typing_indicator(phone, msg_id)

    # Route directly to FastWorkflow agent
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
    result = {}
    for phone, messages in conversation_logs.items():
        last_msg = messages[-1] if messages else None
        result[phone] = {
            "state": get_control_state(phone),
            "message_count": len(messages),
            "last_message": last_msg
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
    return {
        "phone": phone,
        "state": get_control_state(phone),
        "messages": conversation_logs.get(phone, [])
    }


@app.post("/api/toggle/{phone}")
async def api_toggle_control(phone: str):
    """Toggle BOT_CONTROL \u21d4 HUMAN_CONTROL for a conversation."""
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
