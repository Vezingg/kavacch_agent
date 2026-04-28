#!/bin/bash
# Local testing script for box_support_agent
# Starts FastWorkflow (port 8000) + CloudApp dashboard/webhook (port 8080)
# No Docker build needed — runs directly in your Python environment.
#
# WhatsApp webhook testing:
#   1. Install ngrok: https://ngrok.com/download
#   2. In a separate terminal run:  ngrok http 8080
#   3. Copy the https URL ngrok gives you, e.g. https://abc123.ngrok-free.app
#   4. In Meta Developer Console → WhatsApp → Configuration → Webhook URL:
#        https://abc123.ngrok-free.app/webhooks/whatsapp
#      Verify Token: kalash_verify_2024
#   5. Subscribe to the "messages" webhook field.
#
# Local URLs once running:
#   FastWorkflow API docs : http://localhost:8000/docs
#   Dashboard             : http://localhost:8080/dashboard
#   WhatsApp webhook      : http://localhost:8080/webhooks/whatsapp
#   Health check          : http://localhost:8080/health

set -e

echo "🧪 Starting Local Test Environment"
echo "=================================="
echo ""

# ── Port checks ────────────────────────────────────────────────────────────
for PORT in 8000 8080; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $PORT is already in use."
        echo "   Kill it with:  kill \$(lsof -t -i:$PORT)"
        exit 1
    fi
done

# ── Required env vars ──────────────────────────────────────────────────────
# Copy fastworkflow.env values into the shell so uvicorn / cloudapp can read them.
# WhatsApp secrets must be set here (or exported before running this script).
: "${WHATSAPP_PHONE_NUMBER_ID:?Need to export WHATSAPP_PHONE_NUMBER_ID}"
: "${WHATSAPP_ACCESS_TOKEN:?Need to export WHATSAPP_ACCESS_TOKEN}"
# Optional — defaults are fine for local testing:
export WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-kalash_verify_2024}"
export FACTORY_WHATSAPP="${FACTORY_WHATSAPP:-919725201616}"
# Image sending is off by default; set to "true" to test image features:
export MEDIA_SEND_ENABLED="${MEDIA_SEND_ENABLED:-false}"

# ── Start FastWorkflow ─────────────────────────────────────────────────────
echo "🚀 Starting FastWorkflow on port 8000..."
fastworkflow run_fastapi_mcp \
    box_support_agent \
    box_support_agent/fastworkflow.env \
    box_support_agent/fastworkflow.passwords.env \
    --host 0.0.0.0 \
    --port 8000 \
    > /tmp/fastworkflow.log 2>&1 &

FASTWORKFLOW_PID=$!
echo "   FastWorkflow PID: $FASTWORKFLOW_PID"
echo "   Logs: /tmp/fastworkflow.log"

# Wait for FastWorkflow to respond (no /health route — poll /)
echo "⏳ Waiting for FastWorkflow to initialize (up to 120s)..."
for i in $(seq 1 60); do
    if curl -s --max-time 2 http://localhost:8000/ >/dev/null 2>&1 || \
       curl -s --max-time 2 http://localhost:8000/docs >/dev/null 2>&1; then
        echo "✅ FastWorkflow is ready!"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "❌ FastWorkflow did not start in time. Check /tmp/fastworkflow.log"
        kill "$FASTWORKFLOW_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 2
    echo "   Attempt $i/60..."
done

# ── Start CloudApp ─────────────────────────────────────────────────────────
echo ""
echo "🌐 Starting CloudApp (dashboard + webhook) on port 8080..."
echo "   Dashboard : http://localhost:8080/dashboard"
echo "   Webhook   : http://localhost:8080/webhooks/whatsapp"
echo "   Health    : http://localhost:8080/health"
echo "=================================="
echo ""

# Reload is on so code changes in cloud_app.py are picked up automatically.
uvicorn box_support_agent.application.cloud_app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload

# ── Cleanup ────────────────────────────────────────────────────────────────
trap "echo ''; echo 'Shutting down FastWorkflow...'; kill $FASTWORKFLOW_PID 2>/dev/null || true" EXIT
