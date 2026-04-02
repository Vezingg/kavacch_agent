#!/bin/bash
# deploy-gcp.sh - Deploy both services to Google Cloud Run
# Usage: ./deploy-gcp.sh
#
# Reads configuration from:
#   - box_retail_agent/fastworkflow.env
#   - box_retail_agent/fastworkflow.passwords.env

set -e

# Configuration - CHANGE THESE
PROJECT_ID="kavacch-agent-lite-491904"
REGION="asia-south1"  # Mumbai, change if needed

# Service names
AGENT_SERVICE="kalash-agent"
CLOUDAPP_SERVICE="kalash-cloudapp"

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
            # Skip comments and empty lines
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            # Export if contains =
            if [[ "$line" == *"="* ]]; then
                export "$line"
            fi
        done < "$file"
    fi
}

echo -e "${YELLOW}Loading environment from fastworkflow env files...${NC}"
load_env "box_retail_agent/fastworkflow.env"
load_env "box_retail_agent/fastworkflow.passwords.env"

# Verify required variables
if [[ -z "$WHATSAPP_PHONE_NUMBER_ID" || "$WHATSAPP_PHONE_NUMBER_ID" == "your-phone-number-id" ]]; then
    echo -e "${RED}Error: WHATSAPP_PHONE_NUMBER_ID not set in fastworkflow.passwords.env${NC}"
    exit 1
fi

if [[ -z "$WHATSAPP_ACCESS_TOKEN" || "$WHATSAPP_ACCESS_TOKEN" == "your-access-token" ]]; then
    echo -e "${RED}Error: WHATSAPP_ACCESS_TOKEN not set in fastworkflow.passwords.env${NC}"
    exit 1
fi

# Set verify token if not set
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

# Image URLs
AGENT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/kalash-repo/${AGENT_SERVICE}:latest"
CLOUDAPP_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/kalash-repo/${CLOUDAPP_SERVICE}:latest"

# Build and push Agent image
echo -e "${YELLOW}Building and pushing Agent image...${NC}"
docker build -f Dockerfile.agent -t $AGENT_IMAGE .
docker push $AGENT_IMAGE

# Build and push CloudApp image
echo -e "${YELLOW}Building and pushing CloudApp image...${NC}"
docker build -f Dockerfile.cloudapp -t $CLOUDAPP_IMAGE .
docker push $CLOUDAPP_IMAGE

# Deploy Agent service first (CloudApp depends on it)
echo -e "${YELLOW}Deploying Agent service...${NC}"
gcloud run deploy $AGENT_SERVICE \
    --image $AGENT_IMAGE \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300

# Get Agent URL
AGENT_URL=$(gcloud run services describe $AGENT_SERVICE --format='value(status.url)')
echo -e "${GREEN}Agent deployed at: $AGENT_URL${NC}"

# Deploy CloudApp service with environment variables
echo -e "${YELLOW}Deploying CloudApp service...${NC}"
gcloud run deploy $CLOUDAPP_SERVICE \
    --image $CLOUDAPP_IMAGE \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --set-env-vars "FASTWORKFLOW_URL=$AGENT_URL,WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN,WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID,WHATSAPP_ACCESS_TOKEN=$WHATSAPP_ACCESS_TOKEN,FACTORY_WHATSAPP=$FACTORY_WHATSAPP"

# Get CloudApp URL
CLOUDAPP_URL=$(gcloud run services describe $CLOUDAPP_SERVICE --format='value(status.url)')
echo -e "${GREEN}CloudApp deployed at: $CLOUDAPP_URL${NC}"

# Update Agent with CloudApp URL
echo -e "${YELLOW}Updating Agent with CloudApp URL...${NC}"
gcloud run deploy $AGENT_SERVICE \
    --image $AGENT_IMAGE \
    --platform managed \
    --set-env-vars "CLOUD_APP_URL=$CLOUDAPP_URL"

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Webhook URL for Meta Developer Console:"
echo -e "${GREEN}${CLOUDAPP_URL}/webhooks/whatsapp${NC}"
echo ""
echo "Verify Token:"
echo -e "${GREEN}${WHATSAPP_VERIFY_TOKEN}${NC}"
echo ""
echo "Next steps:"
echo "1. Go to Meta Developer Console > WhatsApp > Configuration"
echo "2. Set Webhook URL: ${CLOUDAPP_URL}/webhooks/whatsapp"
echo "3. Set Verify Token: ${WHATSAPP_VERIFY_TOKEN}"
echo "4. Subscribe to: messages"
echo ""
echo "Test the webhook:"
echo "  curl ${CLOUDAPP_URL}/health"
