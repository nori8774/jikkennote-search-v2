# デプロイ手順書

## 概要

このドキュメントでは、実験ノート検索システム v2.0 を本番環境にデプロイする手順を説明します。

### アーキテクチャ

- **フロントエンド**: Vercel (Next.js 15)
- **バックエンド**: Railway / Render (FastAPI + Docker)

バックエンドはローカルファイルシステムにアクセスする必要があるため、Vercel Serverless Functionsではなく、常時起動サーバー（Railway/Render）にデプロイします。

---

## 前提条件

- GitHubアカウント
- Vercelアカウント
- Railway または Render アカウント
- OpenAI APIキー
- Cohere APIキー

---

## Part 1: バックエンドのデプロイ（Railway）

### 1.1 Railwayプロジェクトの作成

1. [Railway](https://railway.app/) にアクセスしてログイン
2. 「New Project」をクリック
3. 「Deploy from GitHub repo」を選択
4. GitHubリポジトリを接続

### 1.2 環境変数の設定

Railwayのダッシュボードで以下の環境変数を設定：

#### 基本設定

```bash
# CORS設定（Vercelのドメインに置き換え）
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000

# サーバー設定
HOST=0.0.0.0
PORT=8000

# フォルダパス設定（デフォルト値で問題なければ省略可）
NOTES_NEW_FOLDER=notes/new
NOTES_PROCESSED_FOLDER=notes/processed
NOTES_ARCHIVE_FOLDER=notes/archived
CHROMA_DB_FOLDER=/app/chroma_db
MASTER_DICTIONARY_PATH=master_dictionary.yaml
```

#### Google Drive統合（オプション） ⭐

Google Driveを使用してノートを共有する場合：

```bash
# ストレージタイプ（local / gcs / google_drive）
STORAGE_TYPE=google_drive

# Google Drive設定
GOOGLE_DRIVE_FOLDER_ID=your_shared_folder_id
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/google-credentials.json
```

**Google Drive認証情報の設定**:

1. Google Cloud Consoleでサービスアカウントを作成
2. サービスアカウントキー（JSON）をダウンロード
3. Railwayの環境変数 `GOOGLE_DRIVE_CREDENTIALS_JSON` に JSON内容を設定
4. `server.py` の起動時に環境変数から `/app/google-credentials.json` に書き出し

**共有フォルダの構成**:
```
📁 共有フォルダ（GOOGLE_DRIVE_FOLDER_ID）
├── 📁 notes/
│   ├── 📁 new/        ← 新規ノート
│   └── 📁 processed/  ← 取り込み済みノート
└── 📄 master_dictionary.yaml ← 正規化辞書
```

### 1.3 ボリュームのマウント（オプション）

データの永続化が必要な場合、Railwayのボリューム機能を使用：

1. ダッシュボードの「Variables」タブを開く
2. 「Volume」セクションで新しいボリュームを作成
3. マウントパス: `/app/chroma_db`（ChromaDBの永続化）
4. マウントパス: `/app/notes`（ノートファイルの永続化）
5. マウントパス: `/app/data`（履歴・評価データの永続化）

### 1.4 デプロイ実行

1. `backend` ディレクトリをルートディレクトリとして設定
2. 「Deploy」をクリック
3. ビルドログを確認してエラーがないことを確認
4. デプロイ完了後、URLをコピー（例: `https://your-backend.railway.app`）

### 1.5 動作確認

```bash
# ヘルスチェック
curl https://your-backend.railway.app/health

# レスポンス例
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

## Part 2: フロントエンドのデプロイ（Vercel）

### 2.1 Vercelプロジェクトの作成

1. [Vercel](https://vercel.com/) にアクセスしてログイン
2. 「Add New」 → 「Project」をクリック
3. GitHubリポジトリをインポート

### 2.2 プロジェクト設定

**Framework Preset**: Next.js

**Root Directory**: `frontend`

**Build Command**: `npm run build` (デフォルト)

**Output Directory**: `.next` (デフォルト)

**Install Command**: `npm install` (デフォルト)

### 2.3 環境変数の設定

Vercelのプロジェクト設定で以下の環境変数を追加：

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

**重要**: RailwayでデプロイしたバックエンドのURLを使用してください。

### 2.4 デプロイ実行

1. 「Deploy」をクリック
2. ビルドログを確認
3. デプロイ完了後、自動的にURLが生成されます（例: `https://your-app.vercel.app`）

### 2.5 カスタムドメインの設定（オプション）

1. Vercelのプロジェクト設定 → 「Domains」
2. カスタムドメインを追加
3. DNSレコードを設定

---

## Part 3: CORS設定の更新

フロントエンドのデプロイが完了したら、バックエンドのCORS設定を更新します。

### 3.1 RailwayでCORS設定を更新

1. Railwayのダッシュボードで環境変数を編集
2. `CORS_ORIGINS` を更新：

```bash
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

3. 保存して再デプロイ

---

## Part 4: 本番環境の初期設定

### 4.1 APIキーの設定

1. デプロイされたフロントエンド（`https://your-app.vercel.app`）にアクセス
2. 設定ページ（`/settings`）を開く
3. APIキータブで以下を入力：
   - OpenAI API Key
   - Cohere API Key
4. 「設定を保存」をクリック

### 4.2 初期データの取り込み

1. ノート管理ページ（`/ingest`）を開く
2. 実験ノートファイルをバックエンドサーバーの `/app/notes/new` ディレクトリに配置
   - **方法1**: SSH経由でファイルをアップロード
   - **方法2**: APIエンドポイントを追加してファイルアップロード機能を実装
3. 「取り込み実行」をクリック

### 4.3 辞書のインポート

1. 辞書管理ページ（`/dictionary`）を開く
2. 既存の辞書ファイル（YAML/JSON/CSV）をインポート

---

## Part 5: 本番環境テスト

### 5.1 機能テスト

- [ ] ヘルスチェック: `https://your-backend.railway.app/health`
- [ ] フロントエンドアクセス: `https://your-app.vercel.app`
- [ ] 検索機能: 検索ページで実験ノートを検索
- [ ] ノートビューワー: 実験ノートIDで閲覧
- [ ] ノート取り込み: 新しいノートを取り込み
- [ ] 辞書管理: 辞書の閲覧・編集・エクスポート
- [ ] 検索履歴: 履歴の確認・削除
- [ ] RAG評価: テストケースのインポート・評価実行

### 5.2 パフォーマンステスト

- [ ] 検索レスポンスタイム: 10秒以内
- [ ] ノート取り込み: 100件で5分以内
- [ ] 辞書エクスポート: 1000エントリで10秒以内

### 5.3 セキュリティテスト

- [ ] HTTPS通信: すべてのAPIリクエストがHTTPS
- [ ] CORS設定: 不正なオリジンからのアクセスがブロックされる
- [ ] APIキー: localStorageに保存され、サーバーには送信されない

---

## トラブルシューティング

### バックエンドが起動しない

**原因**: Dockerビルドエラー

**解決策**:
1. Railwayのビルドログを確認
2. `requirements.txt` の依存関係を確認
3. Dockerfileの構文エラーをチェック

### フロントエンドからバックエンドに接続できない

**原因**: CORS設定またはURL設定の誤り

**解決策**:
1. Vercelの環境変数 `NEXT_PUBLIC_API_URL` が正しいか確認
2. RailwayのCORS設定にVercelのドメインが含まれているか確認
3. ブラウザの開発者ツールでCORSエラーを確認

### ノートが取り込めない

**原因**: ファイルアクセス権限の問題

**解決策**:
1. Railwayでボリュームがマウントされているか確認
2. ファイルパスが正しいか確認（`/app/notes/new`）
3. バックエンドのログでエラーを確認

### 検索結果が表示されない

**原因**: ChromaDBが初期化されていない

**解決策**:
1. ノートを取り込んでChromaDBにデータを追加
2. ボリュームが正しくマウントされているか確認

---

## バックアップとリストア

### データのバックアップ

1. **ChromaDB**: `/app/chroma_db` ディレクトリをバックアップ
2. **実験ノート**: `/app/notes` ディレクトリをバックアップ
3. **辞書**: `/app/master_dictionary.yaml` をバックアップ
4. **履歴・評価データ**: `/app/data` ディレクトリをバックアップ

```bash
# Railwayからファイルをダウンロード
railway run tar -czf backup.tar.gz /app/chroma_db /app/notes /app/data /app/master_dictionary.yaml
railway run cat backup.tar.gz > backup.tar.gz
```

### データのリストア

```bash
# バックアップファイルをアップロードしてリストア
railway run tar -xzf backup.tar.gz -C /
```

---

## モニタリングとメンテナンス

### ログの確認

**Railway**:
1. ダッシュボードの「Deployments」タブ
2. 最新のデプロイを選択
3. 「Logs」でリアルタイムログを確認

**Vercel**:
1. プロジェクトダッシュボード
2. 「Functions」タブでサーバーレス関数のログを確認

### パフォーマンスモニタリング

- Vercel Analytics: フロントエンドのパフォーマンス
- Railway Metrics: バックエンドのCPU・メモリ使用量

### アップデート手順

1. ローカルで変更をコミット
2. GitHubにプッシュ
3. Vercel/Railwayが自動的にデプロイ
4. デプロイ完了後、動作確認

---

## 代替デプロイオプション

### Render でのデプロイ

Railwayの代わりにRenderを使用する場合：

1. [Render](https://render.com/) にアクセス
2. 「New」 → 「Web Service」を選択
3. GitHubリポジトリを接続
4. 以下を設定：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Root Directory**: `backend`
5. 環境変数を設定（RailwayとUTF-8）
6. 「Create Web Service」をクリック

---

## まとめ

本番環境へのデプロイが完了しました。以下の点を確認してください：

- ✅ フロントエンド: Vercelにデプロイ済み
- ✅ バックエンド: Railwayにデプロイ済み
- ✅ CORS設定: 正しく設定済み
- ✅ 環境変数: すべて設定済み
- ✅ 機能テスト: すべて合格
- ✅ セキュリティ: HTTPS通信・CORS保護

問題が発生した場合は、トラブルシューティングセクションを参照してください。
