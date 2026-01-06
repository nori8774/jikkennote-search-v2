#!/bin/bash
# Firebase認証 クイックセットアップスクリプト
# 作成日: 2026-01-01
# プロジェクト: 実験ノート検索システム v3.0

set -e

echo "=========================================="
echo "Firebase認証 クイックセットアップ"
echo "=========================================="
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "📁 プロジェクトディレクトリ: $SCRIPT_DIR"
echo ""

# frontendディレクトリに移動
cd "$FRONTEND_DIR"

echo "ステップ1: Vercelの環境変数を更新"
echo "=========================================="
echo ""

# Firebase環境変数
FIREBASE_API_KEY="AIzaSyBLupsnpgDj9RVTY5RhJx88yhYbtY1I_k8"
FIREBASE_AUTH_DOMAIN="jikkennote-search-9e7b9.firebaseapp.com"
FIREBASE_PROJECT_ID="jikkennote-search-9e7b9"
FIREBASE_STORAGE_BUCKET="jikkennote-search-9e7b9.firebasestorage.app"
FIREBASE_MESSAGING_SENDER_ID="109366953202"
FIREBASE_APP_ID="1:109366953202:web:ccf40ca30cad14ae197c6b"

echo "🔧 NEXT_PUBLIC_FIREBASE_API_KEY を設定中..."
echo "$FIREBASE_API_KEY" | vercel env add NEXT_PUBLIC_FIREBASE_API_KEY production --force

echo "🔧 NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN を設定中..."
echo "$FIREBASE_AUTH_DOMAIN" | vercel env add NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN production --force

echo "🔧 NEXT_PUBLIC_FIREBASE_PROJECT_ID を設定中..."
echo "$FIREBASE_PROJECT_ID" | vercel env add NEXT_PUBLIC_FIREBASE_PROJECT_ID production --force

echo "🔧 NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET を設定中..."
echo "$FIREBASE_STORAGE_BUCKET" | vercel env add NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET production --force

echo "🔧 NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID を設定中..."
echo "$FIREBASE_MESSAGING_SENDER_ID" | vercel env add NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID production --force

echo "🔧 NEXT_PUBLIC_FIREBASE_APP_ID を設定中..."
echo "$FIREBASE_APP_ID" | vercel env add NEXT_PUBLIC_FIREBASE_APP_ID production --force

echo ""
echo "✅ Vercelの環境変数を更新しました"
echo ""

echo "ステップ2: 環境変数を確認"
echo "=========================================="
vercel env ls production
echo ""

echo "ステップ3: 本番環境に再デプロイ"
echo "=========================================="
echo ""
read -p "本番環境に再デプロイしますか？ (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "🚀 デプロイを開始します..."
    vercel --prod --yes
    echo ""
    echo "✅ デプロイが完了しました"
else
    echo "⏭️  デプロイをスキップしました"
    echo "後で手動でデプロイする場合は、以下のコマンドを実行してください:"
    echo "  cd $FRONTEND_DIR"
    echo "  vercel --prod --yes"
fi

echo ""
echo "=========================================="
echo "⚠️  次の手順を手動で実行してください"
echo "=========================================="
echo ""
echo "1. Firebase Console (https://console.firebase.google.com)"
echo "   - プロジェクト: jikkennote-search-9e7b9 を選択"
echo "   - Authentication → Sign-in method → Google を有効化"
echo "   - Authentication → Settings → Authorized domains に以下を追加:"
echo "     * localhost"
echo "     * jikkennote-search-v2.vercel.app"
echo "     * jikkennote-search-9e7b9.firebaseapp.com"
echo ""
echo "2. Google Cloud Console (https://console.cloud.google.com)"
echo "   - プロジェクト: jikkennote-search-9e7b9 を選択"
echo "   - APIとサービス → 認証情報 → OAuth 2.0 クライアントID"
echo "   - 承認済みのリダイレクトURIに以下を追加:"
echo "     * https://jikkennote-search-v2.vercel.app/__/auth/handler"
echo "     * https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler"
echo "     * http://localhost:3000/__/auth/handler"
echo "   - 保存ボタンをクリック"
echo ""
echo "詳しい手順は FIREBASE_AUTH_SETUP_COMPLETE.md を参照してください"
echo ""
echo "=========================================="
echo "✅ セットアップスクリプト完了"
echo "=========================================="
