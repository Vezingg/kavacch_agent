#!/bin/bash
# Quick deployment script for Kalash Agent
# Run this after the build completes successfully

set -e

echo "🚀 Deploying Kalash Agent to Cloud Run..."
echo ""

# Check if latest build succeeded
BUILD_STATUS=$(gcloud builds list --limit=1 --format="value(status)")
if [ "$BUILD_STATUS" != "SUCCESS" ]; then
    echo "❌ Error: Latest build status is: $BUILD_STATUS"
    echo "   Wait for build to complete or check logs"
    exit 1
fi

echo "✅ Latest build: SUCCESS"
echo ""
echo "📦 Deploying to Cloud Run..."
echo ""

gcloud run deploy kalash-agent \
    --image asia-south1-docker.pkg.dev/kavacch-agent-lite-494311/kalash-repo/kalash-agent:latest \
    --region asia-south1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --port 8080 \
    --timeout 300 \
    --cpu-boost \
    --no-cpu-throttling \
    --update-secrets="SECRET_KEY=jwt_secret_key:latest,JWT_SECRET_KEY=jwt_secret_key:latest,WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token:latest,WHATSAPP_PHONE_NUMBER_ID=whatsapp_phone_number_id:latest,WHATSAPP_ACCESS_TOKEN=whatsapp_access_token:latest"
    # --min-instances=1

echo ""
echo "✅ Deployment complete!"
echo ""

# Test health
echo "🧪 Testing service..."
HEALTH=$(curl -s https://kalash-agent-yefqdnx46q-el.a.run.app/health)
echo "   Health: $HEALTH"
echo ""

if [[ "$HEALTH" == *"healthy"* ]]; then
    echo "✅ Service is healthy!"
    echo ""
    echo "📱 WhatsApp Webhook: https://kalash-agent-yefqdnx46q-el.a.run.app/webhooks/whatsapp"
else
    echo "⚠️  Warning: Health check failed"
    echo "   Check logs: gcloud run services logs read kalash-agent --region=asia-south1 --limit=50"
fi
