#!/bin/bash
# Deploy the Kalash Config Updater to Cloud Run
# Run once after: gcloud builds submit --config=cloudbuild-updater.yaml

set -e

PROJECT_ID="kavacch-agent-lite-491904"
REGION="asia-south1"
SERVICE="kalash-updater"
IMAGE="asia-south1-docker.pkg.dev/${PROJECT_ID}/kalash-repo/kalash-updater:latest"

echo "🔑 Granting IAM roles to the default compute service account..."
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Needs to read/write Secret Manager secrets
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretVersionAdder" \
    --quiet

# Needs to update the kalash-agent Cloud Run service
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA}" \
    --role="roles/run.developer" \
    --quiet

echo "✅ IAM roles granted"
echo ""
echo "🚀 Deploying ${SERVICE}..."

gcloud run deploy "${SERVICE}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --port 8080 \
    --set-env-vars "\
GCP_PROJECT_ID=${PROJECT_ID},\
GCP_REGION=${REGION},\
TARGET_SERVICE=kalash-agent,\
META_APP_SECRET_VALUE=9395ee31e52c6738e68f180a873b6ea7,\
DEFAULT_FACTORY_WHATSAPP=919925532982"

echo ""
echo "✅ Deployment complete!"
echo ""

UPDATER_URL=$(gcloud run services describe "${SERVICE}" \
    --region="${REGION}" --format="value(status.url)")
echo "🌐 Updater URL: ${UPDATER_URL}"
