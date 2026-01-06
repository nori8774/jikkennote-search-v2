#!/bin/bash

# GCS対応版 - Cloud Runデプロイスクリプト

set -e

echo "========================================="
echo "GCS対応版デプロイを開始します"
echo "========================================="

# 変数設定
PROJECT_ID="jikkennote-search"
REGION="asia-northeast1"
REPO_NAME="jikkennote-repo"
IMAGE_NAME="backend"
SERVICE_NAME="jikkennote-backend"
BUCKET_NAME="jikkennote-storage"

# フロントエンドURLを設定（既にデプロイ済みの場合）
FRONTEND_URL=${FRONTEND_URL:-"https://jikkennote-search.vercel.app"}

echo ""
echo "📦 Step 1: Dockerイメージのビルド"
echo "========================================="
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest ./backend

echo ""
echo "📤 Step 2: Artifact Registryにプッシュ"
echo "========================================="
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest

echo ""
echo "🚀 Step 3: Cloud Runにデプロイ（GCS有効化）"
echo "========================================="
gcloud run deploy ${SERVICE_NAME} \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --set-env-vars="HOST=0.0.0.0,PORT=8000,CORS_ORIGINS=${FRONTEND_URL}\,http://localhost:3000,STORAGE_TYPE=gcs,GCS_BUCKET_NAME=${BUCKET_NAME}" \
    --project=${PROJECT_ID}

echo ""
echo "✅ デプロイ完了！"
echo "========================================="

# URLを取得
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo ""
echo "🌐 バックエンドURL: ${SERVICE_URL}"
echo ""
echo "📝 次のステップ:"
echo "  1. フロントエンドの環境変数を更新:"
echo "     NEXT_PUBLIC_API_URL=${SERVICE_URL}"
echo ""
echo "  2. ヘルスチェック:"
echo "     curl ${SERVICE_URL}/health"
echo ""
echo "  3. GCSバケット確認:"
echo "     gsutil ls gs://${BUCKET_NAME}/"
echo ""
