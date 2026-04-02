"""
WhatsApp Cloud App for Box Retail Agent.
Handles WhatsApp webhook, routes to FastWorkflow, and manages pricing flow.
"""

import os
import logging
import httpx
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Optional

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
# In-memory state
# NOTE: For production, use Redis or a database for persistence
# ---------------------------------------------------------------------------

# Session cache: phone → FastWorkflow session data
session_cache: Dict[str, dict] = {}

# Message deduplication: track processed WhatsApp message IDs
# Prevents duplicate processing when WhatsApp retries webhooks
processed_message_ids: Dict[str, datetime] = {}

# Pending orders awaiting pricing from factory
# Format: {customer_phone: {"order_summary": str, "products": list, "timestamp": datetime}}
pending_orders: Dict[str, dict] = {}

# Track which customer the factory is currently replying to
# When factory sends a message, we check if there's a pending order
# Format: customer_phone (most recent pending order)
current_pricing_request: Optional[str] = None

# Conversation transcripts: phone → [{role, text, timestamp}]
conversation_logs: Dict[str, list] = {}

# Per-customer control state: phone → "BOT_CONTROL" | "HUMAN_CONTROL"
control_state: Dict[str, str] = {}

# ---------------------------------------------------------------------------
# Welcome message
# ---------------------------------------------------------------------------

WELCOME_MESSAGE = """
Welcome to Kalash Packaging! 📦

We specialize in:
• Bakery Boxes (Window Boxes)
• MDF Boards
• Drum Boards
• Cutlery Kits

Ask me about our products, sizes, colors, or customization options!

Type "help" to see what I can do.
"""

HELP_MESSAGE = """
Here's what I can help you with:

📦 Product Info - Ask about boxes, boards, or kits
📏 Sizes - "What sizes are available?"
🎨 Colors - "What colors do you have?"
✨ Customization - "Do you offer branding?"
🛒 Checkout - Say "checkout" to place an order

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


# ---------------------------------------------------------------------------
# FastWorkflow Integration
# ---------------------------------------------------------------------------

async def get_or_create_session(phone: str) -> dict:
    """Get or create a FastWorkflow session."""
    if phone in session_cache:
        return session_cache[phone]
    
    try:
        # 120s timeout: FastWorkflow initialization can be slow on first request
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{FASTWORKFLOW_URL}/initialize", json={
                "channel_id": f"whatsapp_{phone}",
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


async def chat_with_agent(phone: str, message: str) -> str:
    """Send message to FastWorkflow agent and get response."""
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
            
            resp = await client.post(
                f"{FASTWORKFLOW_URL}/invoke_agent",
                json={
                    "user_query": message,
                    "timeout_seconds": 500
                },
                headers=headers
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # FastWorkflow returns response nested in command_responses array
                command_responses = data.get("command_responses", [])
                if command_responses:
                    return command_responses[0].get("response", "")
                return data.get("response", "")
            else:
                logger.error(f"Chat error (HTTP {resp.status_code}): {resp.text}")
                return "I'm having trouble processing that. Please try again."
    except Exception as e:
        logger.error(f"Chat error: {type(e).__name__}: {str(e)}")
        return "I'm having trouble connecting. Please try again."


# ---------------------------------------------------------------------------
# Pending Order Management (for pricing flow)
# ---------------------------------------------------------------------------

def add_pending_order(customer_phone: str, order_summary: str, products: list):
    """Add a pending order awaiting pricing from factory."""
    global current_pricing_request
    
    pending_orders[customer_phone] = {
        "order_summary": order_summary,
        "products": products,
        "timestamp": datetime.now(),
        "customer_name": "Customer"  # Can be enhanced to store actual name
    }
    current_pricing_request = customer_phone
    logger.info(f"Added pending order for {customer_phone}")


def get_pending_order(customer_phone: str) -> Optional[dict]:
    """Get pending order for a customer."""
    return pending_orders.get(customer_phone)


def remove_pending_order(customer_phone: str):
    """Remove a pending order after pricing is sent."""
    global current_pricing_request
    
    if customer_phone in pending_orders:
        del pending_orders[customer_phone]
        if current_pricing_request == customer_phone:
            current_pricing_request = None
        logger.info(f"Removed pending order for {customer_phone}")


def get_oldest_pending_order() -> Optional[tuple]:
    """Get the oldest pending order (customer_phone, order_data)."""
    if not pending_orders:
        return None
    
    # Sort by timestamp and get oldest
    oldest = min(pending_orders.items(), key=lambda x: x[1]["timestamp"])
    return oldest


def cleanup_old_orders(max_age_hours: int = 24):
    """Remove orders older than max_age_hours."""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    to_remove = [
        phone for phone, data in pending_orders.items()
        if data["timestamp"] < cutoff
    ]
    for phone in to_remove:
        remove_pending_order(phone)


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
        "timestamp": datetime.now().isoformat()
    })


def get_control_state(phone: str) -> str:
    """Return BOT_CONTROL or HUMAN_CONTROL for a customer. Default is BOT_CONTROL."""
    return control_state.get(phone, "BOT_CONTROL")


def set_control_state(phone: str, state: str):
    """Set the control state for a customer conversation."""
    control_state[phone] = state
    logger.info(f"Control state for {phone} → {state}")


async def send_and_log(phone: str, message: str) -> bool:
    """Send a WhatsApp message to a customer and log it to the transcript."""
    log_message(phone, "bot", message)
    return await send_whatsapp(phone, message)


# ---------------------------------------------------------------------------
# Message Handling
# ---------------------------------------------------------------------------

async def handle_factory_reply(text: str):
    """
    Handle a reply from the factory with pricing.
    Forward the pricing to the customer who's waiting.
    """
    global current_pricing_request
    
    # Get the customer waiting for pricing
    if current_pricing_request and current_pricing_request in pending_orders:
        customer_phone = current_pricing_request
        order_data = pending_orders[customer_phone]
        
        # Format pricing message for customer
        pricing_message = f"""
💰 Pricing Update from Kalash Packaging!

{order_data['order_summary']}

📋 Price Quote:
{text}

Reply 'confirm' to proceed with the order or ask any questions.

Thank you for choosing Kalash Packaging! 🙏
"""
        
        # Log and send to customer
        log_message(customer_phone, "bot", pricing_message)
        await send_whatsapp(customer_phone, pricing_message)
        logger.info(f"Forwarded pricing to customer {customer_phone}")
        
        # Remove from pending (or keep for order confirmation)
        remove_pending_order(customer_phone)
        
        # Notify factory
        await send_whatsapp(
            FACTORY_WHATSAPP,
            f"✅ Pricing sent to customer {customer_phone}"
        )
    else:
        # No pending order - maybe factory sent unsolicited message
        logger.warning(f"Factory replied but no pending order: {text}")


async def handle_customer_message(phone: str, text: str):
    """Handle a message from a customer."""
    stripped = text.strip().lower()
    
    # Check for greetings
    if stripped in {"hi", "hello", "hey", "hii"}:
        await send_and_log(phone, WELCOME_MESSAGE)
        return
    
    # Check for help
    if stripped in {"help", "?", "menu"}:
        await send_and_log(phone, HELP_MESSAGE)
        return
    
    # Check for order confirmation (after receiving pricing)
    if stripped == "confirm":
        await send_and_log(
            phone,
            "✅ Thank you for confirming your order!\n\n"
            "Our team will contact you shortly to finalize the details.\n\n"
            f"📞 You can also reach us at: {FACTORY_WHATSAPP}\n\n"
            "Thank you for choosing Kalash Packaging! 🙏"
        )
        return
    
    # Route to FastWorkflow agent
    response = await chat_with_agent(phone, text)
    
    if response:
        await send_and_log(phone, response)


async def handle_message(phone: str, text: str):
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

            await handle_customer_message(phone, text)
            
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
                        await handle_message(phone, text)
                        
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
            return {"error": "Missing customer_phone or order_summary"}, 400
        
        add_pending_order(customer_phone, order_summary, products)
        
        return {"status": "success", "message": f"Pending order added for {customer_phone}"}
        
    except Exception as e:
        logger.error(f"Error adding pending order: {e}")
        return {"error": str(e)}, 500


@app.get("/api/pending_orders")
async def api_get_pending_orders():
    """Get all pending orders (for debugging/admin)."""
    return {
        "pending_orders": {
            phone: {
                "order_summary": data["order_summary"],
                "timestamp": data["timestamp"].isoformat(),
            }
            for phone, data in pending_orders.items()
        },
        "current_pricing_request": current_pricing_request
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
    """Toggle BOT_CONTROL ⇔ HUMAN_CONTROL for a conversation."""
    current = get_control_state(phone)
    new_state = "HUMAN_CONTROL" if current == "BOT_CONTROL" else "BOT_CONTROL"
    set_control_state(phone, new_state)

    if new_state == "HUMAN_CONTROL":
        msg = "Please wait, connecting you to our team... 👤"
    else:
        msg = "Our automated assistant is back. How can I help? 🤖"

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
