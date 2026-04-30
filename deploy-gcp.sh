#!/bin/bash
# deploy-gcp.sh - Build and deploy the unified Kalash Agent to Google Cloud Run
# Usage: ./deploy-gcp.sh
#
# Reads configuration from:
#   - box_support_agent/fastworkflow.env
#   - box_support_agent/fastworkflow.passwords.env

set -e

# Configuration
PROJECT_ID="kavacch-agent-lite-494311"
REGION="asia-south1"
SERVICE="kalash-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Kalash Packaging Deployment ===${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not installed${NC}"
    echo "Install it: curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not installed${NC}"
    exit 1
fi

# Load environment variables from fastworkflow env files
load_env() {
    local file=$1
    if [[ -f "$file" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            if [[ "$line" == *"="* ]]; then
                export "$line"
            fi
        done < "$file"
    fi
}

echo -e "${YELLOW}Loading environment from fastworkflow env files...${NC}"
load_env "box_support_agent/fastworkflow.env"
load_env "box_support_agent/fastworkflow.passwords.env"

# Verify required variables
if [[ -z "$WHATSAPP_PHONE_NUMBER_ID" || "$WHATSAPP_PHONE_NUMBER_ID" == "your-phone-number-id" ]]; then
    echo -e "${RED}Error: WHATSAPP_PHONE_NUMBER_ID not set in fastworkflow.passwords.env${NC}"
    exit 1
fi

if [[ -z "$WHATSAPP_ACCESS_TOKEN" || "$WHATSAPP_ACCESS_TOKEN" == "your-access-token" ]]; then
    echo -e "${RED}Error: WHATSAPP_ACCESS_TOKEN not set in fastworkflow.passwords.env${NC}"
    exit 1
fi

WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-kalash_verify_2024}"

echo -e "${GREEN}Environment loaded:${NC}"
echo "  FACTORY_WHATSAPP: $FACTORY_WHATSAPP"
echo "  WHATSAPP_PHONE_NUMBER_ID: ${WHATSAPP_PHONE_NUMBER_ID:0:10}..."
echo ""

# Configure gcloud
echo -e "${YELLOW}Configuring gcloud...${NC}"
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo -e "${YELLOW}Setting up Artifact Registry...${NC}"
gcloud artifacts repositories create kalash-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Kalash Packaging Docker images" \
    2>/dev/null || echo "Repository already exists"

# Configure Docker authentication
echo -e "${YELLOW}Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Image URL
AGENT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/kalash-repo/${SERVICE}:latest"

# Build and push unified agent image
echo -e "${YELLOW}Building and pushing unified agent image...${NC}"
docker build -f Dockerfile.agent -t $AGENT_IMAGE .
docker push $AGENT_IMAGE

# Deploy unified agent service (FastWorkflow + CloudApp in one container)
echo -e "${YELLOW}Deploying unified agent service...${NC}"
gcloud run deploy $SERVICE \
    --image $AGENT_IMAGE \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --port 8080 \
    --timeout 300 \
    --min-instances=1 \
    --update-secrets="SECRET_KEY=jwt_secret_key:latest,JWT_SECRET_KEY=jwt_secret_key:latest,WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token:latest,WHATSAPP_PHONE_NUMBER_ID=whatsapp_phone_number_id:latest,WHATSAPP_ACCESS_TOKEN=whatsapp_access_token:latest"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE --region=$REGION --format='value(status.url)')
echo -e "${GREEN}Agent deployed at: $SERVICE_URL${NC}"

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Webhook URL for Meta Developer Console:"
echo -e "${GREEN}${SERVICE_URL}/webhooks/whatsapp${NC}"
echo ""
echo "Verify Token:"
echo -e "${GREEN}${WHATSAPP_VERIFY_TOKEN}${NC}"
echo ""
echo "Dashboard:"
echo -e "${GREEN}${SERVICE_URL}/dashboard${NC}"
echo ""
echo "Next steps:"
echo "1. Go to Meta Developer Console > WhatsApp > Configuration"
echo "2. Set Webhook URL: ${SERVICE_URL}/webhooks/whatsapp"
echo "3. Set Verify Token: ${WHATSAPP_VERIFY_TOKEN}"
echo "4. Subscribe to: messages"
echo ""
echo "Test the service:"
echo "  curl ${SERVICE_URL}/health"
