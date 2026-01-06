# デプロイ継続手順

## 現在の状態

### 完了済み ✅

1. ✅ Google Cloud 認証（nori8774@gmail.com）
2. ✅ プロジェクト設定（jikkennote-search）
3. ✅ 必要なAPIの有効化
4. ✅ Artifact Registry リポジトリ作成（jikkennote-repo）
5. ✅ Docker 認証設定
6. ✅ Dockerイメージのビルドとプッシュ
7. ✅ Cloud Runへのデプロイ完了

**バックエンドURL**: https://jikkennote-backend-285071263188.asia-northeast1.run.app

### 次に実行する作業

---

## 方法1: 自動スクリプトで実行（推奨）

### 1. Docker Desktop を起動

アプリケーションから Docker Desktop を起動してください。

### 2. デプロイスクリプトを実行

```bash
./DEPLOY_CONTINUE.sh
```

このスクリプトは以下を自動実行します：
- Docker イメージのビルド
- Artifact Registry へのプッシュ
- Cloud Run へのデプロイ
- ヘルスチェック

---

## 方法2: 手動で実行

### 1. Docker Desktop を起動

### 2. Docker が起動しているか確認

```bash
docker ps
```

エラーが出なければOK。

### 3. Dockerイメージをビルド

```bash
docker build -t asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:latest ./backend
```

**所要時間**: 約3-5分

### 4. イメージをArtifact Registryにプッシュ

```bash
docker push asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:latest
```

**所要時間**: 約2-3分

### 5. Cloud Runにデプロイ

```bash
gcloud run deploy jikkennote-backend \
    --image=asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:latest \
    --platform=managed \
    --region=asia-northeast1 \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --set-env-vars="HOST=0.0.0.0,PORT=8000,CORS_ORIGINS=http://localhost:3000" \
    --project=jikkennote-search
```

**所要時間**: 約2-3分

デプロイ完了後、URLが表示されます：
```
Service URL: https://jikkennote-backend-xxxxx-an.a.run.app
```

**このURLをメモしてください！**

### 6. 動作確認

```bash
# バックエンドURLを変数に設定（実際のURLに置き換え）
export BACKEND_URL="https://jikkennote-backend-xxxxx-an.a.run.app"

# ヘルスチェック
curl $BACKEND_URL/health
```

成功すると以下のようなレスポンスが返ります：
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "config": {...}
}
```

---

## 次のステップ: フロントエンドのデプロイ

### 1. GitHubにコードをプッシュ

```bash
# リモートリポジトリを追加（まだの場合）
git remote add origin https://github.com/YOUR_USERNAME/jikkennote-search.git

# プッシュ
git push -u origin main
```

### 2. Vercelでプロジェクトをインポート

1. https://vercel.com/ にアクセス
2. 「Add New」 → 「Project」
3. GitHub から `jikkennote-search` を選択
4. **Root Directory**: `frontend` を選択
5. **環境変数**を追加：
   ```
   名前: NEXT_PUBLIC_API_URL
   値: https://jikkennote-backend-xxxxx-an.a.run.app
   ```
   （ステップ5でメモしたCloud RunのURLを使用）
6. 「Deploy」をクリック

### 3. CORS設定を更新

Vercelのデプロイが完了したら、バックエンドのCORS設定を更新：

```bash
# VercelのURLを変数に設定
export FRONTEND_URL="https://jikkennote-search.vercel.app"

# CORS設定を更新
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --update-env-vars="CORS_ORIGINS=${FRONTEND_URL},http://localhost:3000" \
    --project=jikkennote-search
```

### 4. 動作確認

1. Vercel URL にアクセス: `https://jikkennote-search.vercel.app`
2. 「設定」ページでAPIキーを設定
3. 検索機能をテスト

---

## トラブルシューティング

### Docker のビルドが失敗する

```bash
# ログを確認
docker build -t test-backend ./backend

# エラーがある場合は backend/requirements.txt を確認
```

### Cloud Run のデプロイが失敗する

```bash
# ログを確認
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --limit=50
```

### フロントエンドがバックエンドに接続できない

1. ブラウザの開発者ツール（F12）を開く
2. Console タブでエラーを確認
3. CORS エラーの場合：
   ```bash
   # CORS設定を確認
   gcloud run services describe jikkennote-backend \
       --region=asia-northeast1 \
       --project=jikkennote-search \
       --format="value(spec.template.spec.containers[0].env)"
   ```

---

## 便利なコマンド

### サービス情報の確認

```bash
# サービスの詳細
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search

# URLを取得
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --format="value(status.url)"
```

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --follow

# エラーログのみ
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --log-filter="severity>=ERROR"
```

### サービスの更新

```bash
# 環境変数の更新
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --update-env-vars="KEY=VALUE" \
    --project=jikkennote-search

# メモリの変更
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --memory=4Gi \
    --project=jikkennote-search
```

### サービスの削除（課金停止）

```bash
gcloud run services delete jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search
```

---

## 完了チェックリスト

デプロイが完了したら：

- [x] Docker Desktop が起動している
- [x] Docker イメージがビルドされた
- [x] イメージが Artifact Registry にプッシュされた
- [x] Cloud Run にデプロイされた
- [x] バックエンドのヘルスチェックが成功する
- [x] GitHub にコードがプッシュされた (https://github.com/nori8774/jikkennote-search)
- [x] Vercel にフロントエンドがデプロイされた (https://jikkennote-search.vercel.app)
- [x] フロントエンドからバックエンドに接続できる
- [x] CORS設定が正しい
- [x] APIキーが設定されている
- [ ] 検索機能が動作する

---

## サポート

詳細なドキュメント：
- **[DEPLOYMENT_CLOUDRUN.md](DEPLOYMENT_CLOUDRUN.md)** - 詳細なデプロイ手順
- **[DEPLOY_NOW_CLOUDRUN.md](DEPLOY_NOW_CLOUDRUN.md)** - ステップバイステップガイド
- **[PRODUCTION_TEST_CHECKLIST.md](PRODUCTION_TEST_CHECKLIST.md)** - テストチェックリスト

問題が発生した場合は、上記のドキュメントを参照してください。
