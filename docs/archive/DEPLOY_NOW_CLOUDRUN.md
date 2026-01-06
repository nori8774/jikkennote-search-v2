# 今すぐデプロイ - Google Cloud Run 版

## 準備完了状態 ✅

- ✅ Gitリポジトリが初期化されました
- ✅ 初回コミットが完了しました (コミットID: d7f30f3)
- ✅ Dockerfileが配置されています
- ✅ すべての設定ファイルが準備されています

---

## 前提条件の確認

### 必要なツール

```bash
# gcloud CLIのインストール確認
gcloud --version

# Dockerのインストール確認
docker --version

# GitHubアカウントとリポジトリ
# Vercelアカウント
```

gcloud CLI がインストールされていない場合：

```bash
# macOS
brew install google-cloud-sdk

# Windows/Linux
# https://cloud.google.com/sdk/docs/install
```

---

## ステップ 1: Google Cloud の初期設定

### 1.1 認証とプロジェクト作成

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトIDを設定（任意の名前）
export PROJECT_ID="jikkennote-search-$(date +%s)"

# プロジェクトを作成
gcloud projects create $PROJECT_ID --name="実験ノート検索システム"

# プロジェクトを設定
gcloud config set project $PROJECT_ID

# 請求アカウントをリンク（必須）
# Google Cloud Consoleで請求を有効にしてください
# https://console.cloud.google.com/billing
```

### 1.2 必要なAPIを有効化

```bash
# 必要なAPIをまとめて有効化
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    storage-api.googleapis.com
```

**所要時間**: 約2-3分

### 1.3 Artifact Registry の設定

```bash
# リージョンを設定
export REGION="asia-northeast1"

# Docker リポジトリを作成
gcloud artifacts repositories create jikkennote-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="実験ノート検索システム"

# Docker認証
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## ステップ 2: バックエンドのビルドとデプロイ

### 2.1 プロジェクトルートに移動

```bash
cd /Users/nori8774/jikkennote-search
```

### 2.2 Dockerイメージをビルド

```bash
# イメージタグを設定
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/jikkennote-repo/backend:latest"

# ビルド実行
docker build -t $IMAGE_NAME ./backend

# ビルド確認
docker images | grep backend
```

**所要時間**: 約3-5分

### 2.3 イメージをプッシュ

```bash
# Artifact Registryにプッシュ
docker push $IMAGE_NAME
```

**所要時間**: 約2-3分

### 2.4 Cloud Run にデプロイ

```bash
# デプロイ実行
gcloud run deploy jikkennote-backend \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --set-env-vars="HOST=0.0.0.0,PORT=8000,CORS_ORIGINS=http://localhost:3000"
```

デプロイ完了後、URLが表示されます：

```
Service URL: https://jikkennote-backend-xxxxx-an.a.run.app
```

**このURLをメモしてください！**

```bash
# 環境変数に保存
export BACKEND_URL="https://jikkennote-backend-xxxxx-an.a.run.app"
```

**所要時間**: 約2-3分

### 2.5 動作確認

```bash
# ヘルスチェック
curl $BACKEND_URL/health

# 成功すると以下が表示されます
# {"status":"healthy","version":"2.0.0",...}
```

---

## ステップ 3: GitHubリポジトリの準備

### 3.1 GitHubで新しいリポジトリを作成

1. https://github.com/new にアクセス
2. リポジトリ名: `jikkennote-search`
3. Private または Public を選択
4. 「Create repository」をクリック

### 3.2 GitHubにプッシュ

```bash
# リモートリポジトリを追加（YOUR_USERNAMEを置き換え）
git remote add origin https://github.com/YOUR_USERNAME/jikkennote-search.git

# プッシュ
git push -u origin main
```

---

## ステップ 4: フロントエンドのデプロイ（Vercel）

### 4.1 Vercelプロジェクトの作成

1. https://vercel.com/ にアクセス
2. 「Add New」 → 「Project」
3. GitHub から `jikkennote-search` を選択
4. 「Import」をクリック

### 4.2 プロジェクト設定

**Configure Project** 画面：

- **Framework Preset**: Next.js（自動検出）
- **Root Directory**: `frontend` を選択
- **Build Settings**: デフォルトのまま

### 4.3 環境変数の設定

「Environment Variables」で追加：

```bash
名前: NEXT_PUBLIC_API_URL
値: https://jikkennote-backend-xxxxx-an.a.run.app
```

**重要**: ステップ2.4でメモしたCloud RunのURLを使用してください。

### 4.4 デプロイ実行

「Deploy」ボタンをクリック

デプロイ完了後、URLが表示されます：
```
https://jikkennote-search.vercel.app
```

**このURLをメモしてください！**

---

## ステップ 5: CORS設定の更新

Vercelのデプロイが完了したら、バックエンドのCORS設定を更新します。

```bash
# Vercel URLを設定
export FRONTEND_URL="https://jikkennote-search.vercel.app"

# CORS設定を更新
gcloud run services update jikkennote-backend \
    --region=$REGION \
    --update-env-vars="CORS_ORIGINS=${FRONTEND_URL},http://localhost:3000"
```

**所要時間**: 約1分

---

## ステップ 6: 動作確認

### 6.1 フロントエンドにアクセス

ブラウザで以下を開く：
```
https://jikkennote-search.vercel.app
```

### 6.2 APIキーを設定

1. 「設定」ページを開く
2. 「APIキー」タブを選択
3. OpenAI API Key を入力
4. Cohere API Key を入力
5. 「設定を保存」をクリック

### 6.3 検索機能をテスト

1. 「検索」ページを開く
2. 簡単な検索クエリを入力：
   - 目的: "ポリマー合成"
   - 材料: "ポリマーA"
   - 方法: "加熱"
3. 「検索」ボタンをクリック

**注意**: 初回はノートが取り込まれていないため、結果は0件になります。

---

## ステップ 7: 実験ノートの取り込み（オプション）

### 7.1 テストノートの作成

ローカルにテストノートを作成：

```bash
# テストノートを作成
cat > test-note.md << 'EOF'
# 実験ノート TEST-001

## 目的・背景
テストノート - ポリマー合成実験

## 材料
- ポリマーA: 10g
- ポリマーB: 5g
- トルエン: 100ml

## 方法
1. フラスコに投入
2. 80℃で加熱
3. 冷却して回収

## 結果
白色固体が得られた。収率: 85%
EOF
```

### 7.2 Cloud Storage経由でアップロード（将来的な拡張）

現在のバージョンでは、ファイルアップロード機能が実装されていません。
以下の方法でノートを取り込むことができます：

**方法A**: ローカル環境でノートを取り込んでからデータをエクスポート
**方法B**: バックエンドにファイルアップロードAPIを追加（今後の拡張）

---

## 完了チェックリスト

デプロイが完了しました！以下を確認してください：

- [ ] Google Cloud プロジェクトが作成されている
- [ ] Cloud Run にバックエンドがデプロイされている
- [ ] バックエンドのヘルスチェックが成功する
  ```bash
  curl https://jikkennote-backend-xxxxx-an.a.run.app/health
  ```
- [ ] GitHub にコードがプッシュされている
- [ ] Vercel にフロントエンドがデプロイされている
- [ ] フロントエンドからバックエンドに接続できる
- [ ] CORS設定が正しい
- [ ] APIキーが設定されている

---

## トラブルシューティング

### Cloud Run のデプロイが失敗する

```bash
# ログを確認
gcloud run services logs read jikkennote-backend \
    --region=$REGION \
    --limit=50
```

### フロントエンドがバックエンドに接続できない

1. ブラウザの開発者ツールを開く（F12）
2. Console タブでエラーを確認
3. CORS エラーの場合：
   ```bash
   # CORS設定を再確認
   gcloud run services describe jikkennote-backend \
       --region=$REGION \
       --format="value(spec.template.spec.containers[0].env)"
   ```

### Docker ビルドが失敗する

```bash
# Dockerログを確認
docker build -t test-backend ./backend

# エラーがある場合は requirements.txt を確認
cat backend/requirements.txt
```

---

## 便利なコマンド集

### サービスの管理

```bash
# サービスの情報を表示
gcloud run services describe jikkennote-backend --region=$REGION

# サービスのURLを取得
gcloud run services describe jikkennote-backend \
    --region=$REGION \
    --format="value(status.url)"

# サービスを削除（課金停止）
gcloud run services delete jikkennote-backend --region=$REGION

# すべてのリビジョンを表示
gcloud run revisions list --service=jikkennote-backend --region=$REGION
```

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs read jikkennote-backend \
    --region=$REGION \
    --follow

# エラーログのみ表示
gcloud run services logs read jikkennote-backend \
    --region=$REGION \
    --log-filter="severity>=ERROR"
```

### コストの確認

Google Cloud Console で確認：
https://console.cloud.google.com/billing

---

## 次のステップ

### 1. 本番環境テスト

**PRODUCTION_TEST_CHECKLIST.md** の手順に従ってテスト：

```bash
# チェックリストを開く
open PRODUCTION_TEST_CHECKLIST.md
```

### 2. ユーザーに共有

- フロントエンドURL: `https://jikkennote-search.vercel.app`
- ユーザーマニュアル: `USER_MANUAL.md`

### 3. モニタリング設定

```bash
# Cloud Console でメトリクスを確認
echo "https://console.cloud.google.com/run/detail/${REGION}/jikkennote-backend/metrics?project=${PROJECT_ID}"
```

### 4. バックアップの設定

```bash
# Cloud Storage バケットを作成（データバックアップ用）
gsutil mb -l $REGION gs://${PROJECT_ID}-backup

# 定期バックアップスクリプトの作成（今後の拡張）
```

---

## コスト見積もり

### Cloud Run の課金

- **無料枠**: 月2百万リクエスト、36万 vCPU秒、18万 GiB秒
- **有料**: リクエスト超過分のみ課金

### 参考コスト（月間1,000リクエストの場合）

- Cloud Run: 無料枠内
- Artifact Registry: 0.5GB ストレージ（無料枠内）
- ネットワーク: 少量（無料枠内）

**推定月額**: $0 〜 $5（小規模利用の場合）

**注意**: 実際のコストは使用量により変動します。

---

## おめでとうございます！ 🎉

実験ノート検索システム v2.0 が Google Cloud Run にデプロイされました。

**デプロイ完了情報**:
- バックエンドURL: `https://jikkennote-backend-xxxxx-an.a.run.app`
- フロントエンドURL: `https://jikkennote-search.vercel.app`
- Google Cloud プロジェクト: `$PROJECT_ID`

問題が発生した場合は、**DEPLOYMENT_CLOUDRUN.md** のトラブルシューティングセクションを参照してください。
