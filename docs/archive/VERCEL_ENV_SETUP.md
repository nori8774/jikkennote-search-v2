# Vercel 環境変数設定手順

## 問題
フロントエンドで "URL is not valid or contains user credentials." エラーが発生しています。

## 原因
Vercelの環境変数 `NEXT_PUBLIC_API_URL` が正しく設定されていない可能性があります。

## 解決方法

### 方法1: Vercel ダッシュボードから設定（推奨）

1. **Vercelダッシュボードにアクセス**
   - https://vercel.com/dashboard にアクセス
   - `jikkennote-search` プロジェクトを選択

2. **Settings → Environment Variables に移動**
   - 左サイドバーの「Settings」をクリック
   - 「Environment Variables」タブを選択

3. **環境変数を追加/更新**
   - 変数名: `NEXT_PUBLIC_API_URL`
   - 値: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
   - 適用環境: Production, Preview, Development すべてにチェック

4. **保存して再デプロイ**
   - 「Save」をクリック
   - 自動的に再デプロイが開始されます

### 方法2: Vercel CLI から設定

```bash
cd /Users/nori8774/jikkennote-search/frontend

# Production環境に設定
vercel env add NEXT_PUBLIC_API_URL production
# プロンプトが表示されたら以下を入力:
# https://jikkennote-backend-285071263188.asia-northeast1.run.app

# Preview環境にも設定（任意）
vercel env add NEXT_PUBLIC_API_URL preview

# Development環境にも設定（任意）
vercel env add NEXT_PUBLIC_API_URL development
```

### 方法3: 自動プッシュで再デプロイ

GitHubに最新のコードがプッシュ済みなので、Vercelが自動的に再デプロイします。
ただし、環境変数が設定されていない場合は、方法1か方法2で設定する必要があります。

## 確認手順

### 1. Vercelデプロイ状況を確認

https://vercel.com/nori8774/jikkennote-search にアクセスして、最新のデプロイ状況を確認。

### 2. フロントエンドにアクセスしてテスト

https://jikkennote-search.vercel.app にアクセスして以下をテスト:

1. 設定ページを開く
2. APIキーを入力（OpenAI, Cohere）
3. 検索を実行してエラーが出ないか確認

### 3. ブラウザの開発者ツールで確認

1. F12キーで開発者ツールを開く
2. Consoleタブでエラーを確認
3. Networkタブでバックエンドへのリクエストを確認
   - リクエストURL: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/...`
   - ステータスコード: 200 OK または CORS エラー

## トラブルシューティング

### CORSエラーが出る場合

バックエンドのCORS設定を確認:

```bash
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --format="value(spec.template.spec.containers[0].env)" | grep CORS
```

必要に応じて更新:

```bash
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --update-env-vars="CORS_ORIGINS=https://jikkennote-search.vercel.app,http://localhost:3000" \
    --project=jikkennote-search
```

### 環境変数が反映されない場合

1. Vercelダッシュボードで環境変数を再確認
2. 手動で再デプロイを実行:
   - Deploymentsページに移動
   - 最新デプロイメントの右側にある「...」をクリック
   - 「Redeploy」を選択

## 現在のシステム構成

- **フロントエンド**: https://jikkennote-search.vercel.app
- **バックエンド**: https://jikkennote-backend-285071263188.asia-northeast1.run.app
- **ストレージ**: gs://jikkennote-storage

## 次のステップ

環境変数設定後、以下の機能をテスト:

1. ✅ ヘルスチェック
2. ⬜ 検索機能
3. ⬜ ノート取り込み（GCS経由）
4. ⬜ 正規化辞書管理
5. ⬜ 検索履歴
6. ⬜ 性能評価
