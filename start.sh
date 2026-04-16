#!/bin/bash
set -e

echo "🚀 Starting Box Support Agent..."

# Function to start FastWorkflow
start_fastworkflow() {
    echo "📦 Starting FastWorkflow on port 8000..."
    fastworkflow run_fastapi_mcp \
        /app/box_support_agent \
        /app/box_support_agent/fastworkflow.env \
        /app/box_support_agent/fastworkflow.passwords.env \
        --host 0.0.0.0 \
        --port 8000 &
    FASTWORKFLOW_PID=$!
    echo "FastWorkflow started with PID $FASTWORKFLOW_PID"
}

# Start FastWorkflow
start_fastworkflow

# Wait for FastWorkflow to be ready
echo "⏳ Waiting for FastWorkflow to be ready..."
MAX_RETRIES=60
RETRY_COUNT=0

# Check TCP connectivity on port 8000 (FastWorkflow has no /health route)
until curl -s --max-time 2 http://localhost:8000/ > /dev/null 2>&1 || \
      curl -s --max-time 2 http://localhost:8000/docs > /dev/null 2>&1 || \
      [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES - FastWorkflow not ready yet..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ FastWorkflow failed to start after $MAX_RETRIES attempts"
    exit 1
fi

echo "✅ FastWorkflow is ready!"

# Background watchdog: restart FastWorkflow if it crashes
(
    while true; do
        sleep 5
        if ! kill -0 $FASTWORKFLOW_PID 2>/dev/null; then
            echo "⚠️ FastWorkflow (PID $FASTWORKFLOW_PID) crashed! Restarting..."
            start_fastworkflow
            # Wait for it to come back up
            until curl -s --max-time 2 http://localhost:8000/ > /dev/null 2>&1 || \
                  curl -s --max-time 2 http://localhost:8000/docs > /dev/null 2>&1; do
                sleep 2
            done
            echo "✅ FastWorkflow restarted successfully (PID $FASTWORKFLOW_PID)"
        fi
    done
) &

# Start CloudApp (WhatsApp webhook) in the foreground
echo "📱 Starting CloudApp on port 8080..."
exec uvicorn box_support_agent.application.cloud_app:app --host 0.0.0.0 --port 8080
