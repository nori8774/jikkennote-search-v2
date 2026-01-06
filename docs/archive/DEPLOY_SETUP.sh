#!/bin/bash
# デプロイ前のセットアップスクリプト（マルチテナント対応）
# 初回デプロイ前に1度だけ実行してください

set -e

echo "============================================"
echo "デプロイ環境セットアップ"
echo "============================================"
echo ""

# 環境変数
export PROJECT_ID="jikkennote-search"
export REGION="asia-northeast1"
export SERVICE_ACCOUNT_NAME="jikkennote-backend"
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
export GCS_BUCKET="jikkennote-storage"

echo "プロジェクトID: $PROJECT_ID"
echo "リージョン: $REGION"
echo "サービスアカウント: $SERVICE_ACCOUNT_EMAIL"
echo "GCSバケット: $GCS_BUCKET"
echo ""

# ステップ1: サービスアカウントの作成
echo "ステップ1: サービスアカウントを確認/作成中..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "✅ サービスアカウントは既に存在します"
else
    echo "サービスアカウントを作成中..."
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Jikkennote Backend Service Account" \
        --description="Service account for jikkennote backend on Cloud Run" \
        --project=$PROJECT_ID
    echo "✅ サービスアカウント作成完了"
fi
echo ""

# ステップ2: GCSバケットへのアクセス権限を付与
echo "ステップ2: GCSバケットへのアクセス権限を付与中..."
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT_EMAIL}:objectAdmin gs://${GCS_BUCKET}
echo "✅ GCS権限付与完了"
echo ""

# ステップ3: Firestoreへのアクセス権限を付与
echo "ステップ3: Firestoreへのアクセス権限を付与中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/datastore.user" \
    --condition=None
echo "✅ Firestore権限付与完了"
echo ""

# ステップ4: Firebase Authenticationへのアクセス権限を付与
echo "ステップ4: Firebase Authenticationへのアクセス権限を付与中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/firebase.admin" \
    --condition=None
echo "✅ Firebase権限付与完了"
echo ""

# ステップ5: Artifact Registryリポジトリの確認
echo "ステップ5: Artifact Registryリポジトリを確認/作成中..."
if gcloud artifacts repositories describe jikkennote-repo --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Artifact Registryリポジトリは既に存在します"
else
    echo "Artifact Registryリポジトリを作成中..."
    gcloud artifacts repositories create jikkennote-repo \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Jikkennote" \
        --project=$PROJECT_ID
    echo "✅ Artifact Registryリポジトリ作成完了"
fi
echo ""

# ステップ6: Docker認証設定
echo "ステップ6: Docker認証を設定中..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
echo "✅ Docker認証設定完了"
echo ""

echo "============================================"
echo "セットアップ完了 ✅"
echo "============================================"
echo ""
echo "次のステップ:"
echo "1. ./DEPLOY_CONTINUE.sh を実行してデプロイ"
echo ""
