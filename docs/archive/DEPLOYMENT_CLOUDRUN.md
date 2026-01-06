# デプロイ手順書（Google Cloud Run版）

## 概要

このドキュメントでは、実験ノート検索システム v2.0 を Google Cloud Run を使って本番環境にデプロイする手順を説明します。

### アーキテクチャ

- **フロントエンド**: Vercel (Next.js 15)
- **バックエンド**: Google Cloud Run (FastAPI + Docker)
- **データストレージ**: Google Cloud Storage / Filestore

---

## 前提条件

- Google Cloudアカウント
- Google Cloud プロジェクト（または新規作成）
- gcloud CLI インストール済み
- Dockerインストール済み（ローカルテスト用）
- GitHubアカウント
- Vercelアカウント
- OpenAI APIキー
- Cohere APIキー

---

## Part 1: Google Cloud の初期設定

### 1.1 gcloud CLI のインストールと認証

```bash
# gcloud CLIがインストールされていない場合
# macOS
brew install google-cloud-sdk

# Windows/Linux
# https://cloud.google.com/sdk/docs/install からダウンロード

# 認証
gcloud auth login

# プロジェクトの作成（または既存プロジェクトを使用）
gcloud projects create jikkennote-search --name="実験ノート検索システム"

# プロジェクトを設定
gcloud config set project jikkennote-search
```

### 1.2 必要なAPIの有効化

```bash
# Cloud Run API
gcloud services enable run.googleapis.com

# Container Registry API（イメージ保存用）
gcloud services enable containerregistry.googleapis.com

# Artifact Registry API（推奨）
gcloud services enable artifactregistry.googleapis.com

# Cloud Storage API（データ永続化用）
gcloud services enable storage-api.googleapis.com
```

### 1.3 Artifact Registry リポジトリの作成

```bash
# Docker イメージ用のリポジトリを作成
gcloud artifacts repositories create jikkennote-repo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="実験ノート検索システム用リポジトリ"

# Docker認証の設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

---

## Part 2: バックエンドのデプロイ（Cloud Run）

### 2.1 Dockerイメージのビルドとプッシュ

```bash
# プロジェクトルートに移動
cd /path/to/jikkennote-search

# Dockerイメージをビルド
docker build -t asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:latest ./backend

# イメージをArtifact Registryにプッシュ
docker push asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:latest
```

### 2.2 Cloud Storage バケットの作成（データ永続化用）

```bash
# バケット作成
gsutil mb -l asia-northeast1 gs://jikkennote-data

# ディレクトリ構造を作成
gsutil mkdir gs://jikkennote-data/chroma_db
gsutil mkdir gs://jikkennote-data/notes
gsutil mkdir gs://jikkennote-data/data
gsutil mkdir gs://jikkennote-data/master_dictionary.yaml
```

### 2.3 Cloud Run サービスのデプロイ

```bash
# Cloud Runにデプロイ
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
    --set-env-vars="HOST=0.0.0.0,PORT=8000" \
    --set-env-vars="CORS_ORIGINS=http://localhost:3000"
```

**オプション**: より細かい設定をする場合は、`--set-env-vars` を複数回使用：

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
    --set-env-vars="HOST=0.0.0.0" \
    --set-env-vars="PORT=8000" \
    --set-env-vars="CORS_ORIGINS=http://localhost:3000" \
    --set-env-vars="NOTES_NEW_FOLDER=/app/notes/new" \
    --set-env-vars="NOTES_ARCHIVE_FOLDER=/app/notes/archived" \
    --set-env-vars="CHROMA_DB_FOLDER=/app/chroma_db" \
    --set-env-vars="MASTER_DICT_PATH=/app/master_dictionary.yaml"
```

### 2.4 デプロイ後のURL確認

デプロイが完了すると、URLが表示されます：

```
Service [jikkennote-backend] revision [jikkennote-backend-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://jikkennote-backend-xxxxx-an.a.run.app
```

**このURLをメモしておきます**（フロントエンドで使用します）。

### 2.5 動作確認

```bash
# ヘルスチェック
curl https://jikkennote-backend-xxxxx-an.a.run.app/health

# 期待されるレスポンス
{
  "status": "healthy",
  "version": "2.0.0",
  "config": {
    "notes_new_folder": "/app/notes/new",
    "notes_archive_folder": "/app/notes/archived",
    "chroma_db_folder": "/app/chroma_db"
  }
}
```

---

## Part 3: データ永続化の設定（オプション）

Cloud Run はステートレスなため、コンテナが再起動するとデータが失われます。データを永続化する方法：

### オプション A: Cloud Storage FUSE（推奨）

Cloud Storage をファイルシステムとしてマウント（現在 Cloud Run では直接サポートされていないため、起動スクリプトで対応）。

### オプション B: Cloud SQL / Firestore

ChromaDB の代わりに Cloud SQL や Firestore を使用（アプリケーションの変更が必要）。

### オプション C: 外部ストレージマウント

Filestore（NFS）を使用してデータを永続化：

```bash
# Filestoreインスタンスの作成
gcloud filestore instances create jikkennote-fs \
    --zone=asia-northeast1-a \
    --tier=BASIC_HDD \
    --file-share=name="data",capacity=1TB \
    --network=name="default"

# Cloud Runサービスにマウント（現在プレビュー機能）
gcloud run services update jikkennote-backend \
    --add-volume=name=data,type=cloud-storage,bucket=jikkennote-data \
    --add-volume-mount=volume=data,mount-path=/app/data
```

**注意**: Cloud Run でのボリュームマウントは現在プレビュー機能です。本番環境では Cloud Storage との連携スクリプトを実装することを推奨します。

---

## Part 4: フロントエンドのデプロイ（Vercel）

### 4.1 Vercelプロジェクトの作成

1. [Vercel](https://vercel.com/) にアクセスしてログイン
2. 「Add New」 → 「Project」をクリック
3. GitHubリポジトリをインポート

### 4.2 プロジェクト設定

**Configure Project** 画面で：

1. **Framework Preset**: Next.js（自動検出）
2. **Root Directory**: `frontend` を選択
3. **Build Command**: `npm run build`（デフォルト）
4. **Output Directory**: `.next`（デフォルト）
5. **Install Command**: `npm install`（デフォルト）

### 4.3 環境変数の設定

「Environment Variables」セクションで追加：

```bash
# バックエンドのURL（Cloud RunのURL）
NEXT_PUBLIC_API_URL=https://jikkennote-backend-xxxxx-an.a.run.app
```

**重要**: Cloud Run のURLに置き換えてください。

### 4.4 デプロイ実行

1. 「Deploy」ボタンをクリック
2. ビルドログを確認
3. デプロイ完了後、URLが生成されます
   - 例: `https://jikkennote-search.vercel.app`
4. **このURLをメモしておきます**

---

## Part 5: CORS設定の更新

フロントエンドのデプロイが完了したら、バックエンドのCORS設定を更新します。

### 5.1 Cloud Run の環境変数を更新

```bash
# CORS設定を更新（VercelのURLを追加）
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --set-env-vars="CORS_ORIGINS=https://jikkennote-search.vercel.app,http://localhost:3000"
```

更新後、自動的に新しいリビジョンがデプロイされます。

---

## Part 6: 本番環境の初期設定

### 6.1 フロントエンドにアクセス

デプロイされたフロントエンド（`https://jikkennote-search.vercel.app`）にアクセス。

### 6.2 APIキーの設定

1. 「設定」ページ（`/settings`）を開く
2. 「APIキー」タブを選択
3. 以下を入力：
   - **OpenAI API Key**: あなたのOpenAI APIキー
   - **Cohere API Key**: あなたのCohere APIキー
4. 「設定を保存」をクリック

### 6.3 モデルの選択（オプション）

1. 「モデル選択」タブを選択
2. 使用するモデルを選択：
   - Embeddingモデル: `text-embedding-3-small`（推奨）
   - LLMモデル: `gpt-4o-mini`（推奨）
3. 「設定を保存」をクリック

---

## Part 7: データの取り込み

### 7.1 実験ノートのアップロード

Cloud Run はステートレスなため、ノートファイルを直接アップロードする方法：

**方法1**: Cloud Storage 経由

```bash
# ローカルのノートファイルをCloud Storageにアップロード
gsutil cp ./my-note.md gs://jikkennote-data/notes/new/

# バックエンドでCloud Storageから読み込むように実装
```

**方法2**: APIエンドポイント追加（推奨）

バックエンドにファイルアップロードAPIを追加（今後の拡張）。

### 7.2 ノートの取り込み

1. フロントエンドの「ノート管理」ページを開く
2. 「取り込み実行」をクリック
3. 新出単語の判定を行う
4. 辞書を更新

---

## トラブルシューティング

### Cloud Run のデプロイが失敗する

**原因**: イメージのビルドまたはプッシュエラー

**解決策**:
1. Dockerイメージが正しくビルドされているか確認
   ```bash
   docker images | grep backend
   ```
2. Artifact Registry へのプッシュ権限を確認
   ```bash
   gcloud auth configure-docker asia-northeast1-docker.pkg.dev
   ```
3. デプロイログを確認
   ```bash
   gcloud run services describe jikkennote-backend --region=asia-northeast1
   ```

### フロントエンドがバックエンドに接続できない

**原因**: CORS設定またはURL設定の誤り

**解決策**:
1. Vercelの環境変数 `NEXT_PUBLIC_API_URL` が正しいか確認
2. Cloud Run のCORS設定にVercelのドメインが含まれているか確認
   ```bash
   gcloud run services describe jikkennote-backend --region=asia-northeast1 --format="value(spec.template.spec.containers[0].env)"
   ```
3. ブラウザの開発者ツールでCORSエラーを確認

### データが永続化されない

**原因**: Cloud Run はステートレス

**解決策**:
1. Cloud Storage を使用してデータを保存
2. アプリケーションを変更して、起動時にCloud Storageからデータを読み込み、終了時に保存
3. または Filestore を使用（追加コストがかかります）

### メモリ不足エラー

**原因**: Cloud Run のデフォルトメモリが不足

**解決策**:
```bash
# メモリを増やす
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --memory=4Gi
```

---

## 本番環境テスト

**PRODUCTION_TEST_CHECKLIST.md** の手順に従って以下を確認：

- [ ] ヘルスチェック
- [ ] フロントエンドアクセス
- [ ] APIキー設定
- [ ] 検索機能
- [ ] ノートビューワー
- [ ] 辞書管理
- [ ] 検索履歴
- [ ] RAG評価

---

## モニタリングとログ

### ログの確認

```bash
# リアルタイムログ
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --follow

# 最新100行のログ
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --limit=100
```

### メトリクスの確認

Google Cloud Console で確認：
1. Cloud Run サービスを開く
2. 「METRICS」タブをクリック
3. リクエスト数、レイテンシ、エラー率を確認

---

## コスト最適化

### Cloud Run の課金

- リクエスト数に応じた課金
- コンピュート時間（CPU/メモリ使用量）
- ネットワーク送信量

### 最適化のヒント

1. **最小インスタンス数を0に設定**（コールドスタートを許容）
   ```bash
   gcloud run services update jikkennote-backend \
       --region=asia-northeast1 \
       --min-instances=0
   ```

2. **タイムアウトを適切に設定**
   ```bash
   gcloud run services update jikkennote-backend \
       --region=asia-northeast1 \
       --timeout=60
   ```

3. **不要なインスタンスを削除**
   ```bash
   gcloud run services delete jikkennote-backend \
       --region=asia-northeast1
   ```

---

## 更新とロールバック

### 新しいバージョンのデプロイ

```bash
# コードを更新後、イメージを再ビルド
docker build -t asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:v2 ./backend
docker push asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:v2

# 新しいイメージでデプロイ
gcloud run deploy jikkennote-backend \
    --image=asia-northeast1-docker.pkg.dev/jikkennote-search/jikkennote-repo/backend:v2 \
    --region=asia-northeast1
```

### ロールバック

```bash
# リビジョンの一覧を表示
gcloud run revisions list --service=jikkennote-backend --region=asia-northeast1

# 特定のリビジョンにロールバック
gcloud run services update-traffic jikkennote-backend \
    --region=asia-northeast1 \
    --to-revisions=jikkennote-backend-00001-xxx=100
```

---

## バックアップとリストア

### データのバックアップ

```bash
# Cloud Storageバケット全体をバックアップ
gsutil -m cp -r gs://jikkennote-data gs://jikkennote-data-backup
```

### データのリストア

```bash
# バックアップから復元
gsutil -m cp -r gs://jikkennote-data-backup/* gs://jikkennote-data/
```

---

## まとめ

Google Cloud Run を使用したデプロイが完了しました。

**デプロイ完了チェックリスト**:
- [ ] Cloud Run にバックエンドがデプロイされている
- [ ] バックエンドのヘルスチェックが成功する
- [ ] Vercel にフロントエンドがデプロイされている
- [ ] フロントエンドからバックエンドに接続できる
- [ ] CORS設定が正しい
- [ ] APIキーが設定されている
- [ ] 検索機能が動作する

**次のステップ**:
1. 本番環境テストを実施
2. ユーザーに共有
3. モニタリングとログ確認
4. 定期バックアップのスケジュール設定

問題が発生した場合は、上記のトラブルシューティングセクションを参照してください。
