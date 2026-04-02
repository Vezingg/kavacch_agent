#!/bin/bash
# Update WhatsApp Access Token for Kalash Agent
# Usage: ./update_token.sh "YOUR_NEW_TOKEN_HERE"

set -e

if [ -z "$1" ]; then
    echo "❌ Error: No token provided"
    echo ""
    echo "Usage: ./update_token.sh \"YOUR_NEW_TOKEN\""
    echo ""
    echo "Example:"
    echo "  ./update_token.sh \"EAALxxx...\""
    exit 1
fi

NEW_TOKEN="$1"

echo "🔑 Updating WhatsApp Access Token..."
echo ""

# Step 1: Add new version to Secret Manager
echo "📝 Step 1/2: Adding new version to Secret Manager..."
echo -n "$NEW_TOKEN" | gcloud secrets versions add whatsapp_access_token --data-file=-
echo "✅ Token added to Secret Manager"
echo ""

# Step 2: Redeploy Cloud Run service
echo "🚀 Step 2/2: Redeploying Cloud Run service..."
gcloud run deploy kalash-agent \
    --image asia-south1-docker.pkg.dev/kavacch-agent-lite-491904/kalash-repo/kalash-agent:latest \
    --region asia-south1 \
    --allow-unauthenticated \
    --memory 4Gi --cpu 2 --port 8080 \
    --set-env-vars "FACTORY_WHATSAPP=919725201616" \
    --update-secrets="SECRET_KEY=jwt_secret_key:latest,JWT_SECRET_KEY=jwt_secret_key:latest,WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token:latest,WHATSAPP_PHONE_NUMBER_ID=whatsapp_phone_number_id:latest,WHATSAPP_ACCESS_TOKEN=whatsapp_access_token:latest"

echo ""
echo "✅ Deployment complete!"
echo ""

# Step 3: Test the service
echo "🧪 Testing service health..."
HEALTH=$(curl -s https://kalash-agent-uf5uwjlxjq-el.a.run.app/health)
echo "Health check: $HEALTH"
echo ""

if [[ "$HEALTH" == *"healthy"* ]]; then
    echo "✅ Service is healthy and ready!"
    echo ""
    echo "📱 Your WhatsApp agent is now using the new token."
    echo "   Service URL: https://kalash-agent-uf5uwjlxjq-el.a.run.app"
else
    echo "⚠️  Warning: Health check returned unexpected response"
    echo "   Check logs: gcloud run services logs read kalash-agent --region=asia-south1 --limit=50"
fi
