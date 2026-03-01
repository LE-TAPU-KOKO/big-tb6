#!/bin/bash

# BigTB6 - Deploy to Google Cloud Run
# Project: gemini-credits-487316

set -e

PROJECT_ID="gemini-credits-487316"
REGION="us-central1"
SERVICE_NAME="bigtb6-backend"
IMAGE_NAME="bigtb6-backend"

echo "🚀 Deploying BigTB6 to Google Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Get the server directory
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/server" && pwd)"

# Step 1: Build image
echo "📦 Step 1: Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME "$SERVER_DIR/"

# Step 2: Deploy to Cloud Run
echo ""
echo "🚀 Step 2: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars="GOOGLE_API_KEY=\$GOOGLE_API_KEY" \
  --set-env-vars="DAILY_API_KEY=\$DAILY_API_KEY"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Service URL:"
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(status.url)"
