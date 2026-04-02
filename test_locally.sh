#!/bin/bash
# Quick local testing script for box_retail_agent
# Use this to test code changes WITHOUT rebuilding Docker image

set -e

echo "🧪 Starting Local Test Environment"
echo "=================================="
echo ""

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use"
    echo "Run: kill \$(lsof -t -i:8000)"
    exit 1
fi

if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8080 is already in use"
    echo "Run: kill \$(lsof -t -i:8080)"
    exit 1
fi

# Start FastWorkflow in background
echo "🚀 Starting FastWorkflow on port 8000..."
fastworkflow run_fastapi_mcp \
    box_retail_agent \
    box_retail_agent/fastworkflow.env \
    box_retail_agent/fastworkflow.passwords.env \
    --port 8000 \
    > /tmp/fastworkflow.log 2>&1 &

FASTWORKFLOW_PID=$!
echo "   FastWorkflow PID: $FASTWORKFLOW_PID"

# Wait for FastWorkflow to be ready
echo "⏳ Waiting for FastWorkflow to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ FastWorkflow is ready!"
        break
    fi
    sleep 2
    echo "   Attempt $i/30..."
done

# Start CloudApp in foreground
echo ""
echo "🌐 Starting CloudApp on port 8080..."
echo "📝 CloudApp logs will appear below"
echo "=================================="
echo ""

uvicorn box_retail_agent.appliation.cloud_app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload

# Cleanup on exit
trap "kill $FASTWORKFLOW_PID 2>/dev/null || true" EXIT
