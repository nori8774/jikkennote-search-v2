# 今すぐデプロイ - ステップバイステップガイド

## 準備完了状態 ✅

- ✅ Gitリポジトリが初期化されました
- ✅ 初回コミットが完了しました (コミットID: d7f30f3)
- ✅ すべての設定ファイルが配置されました
- ✅ ドキュメントが完備されました

---

## ステップ 1: GitHubリポジトリの作成とプッシュ

### 1.1 GitHubで新しいリポジトリを作成

1. https://github.com/new にアクセス
2. リポジトリ名を入力（例: `jikkennote-search`）
3. **Private** または **Public** を選択
4. **「Initialize this repository with」のすべてのオプションをチェックしない**（既にローカルにコードがあるため）
5. 「Create repository」をクリック

### 1.2 ローカルリポジトリをGitHubにプッシュ

ターミナルで以下を実行：

```bash
# GitHubリポジトリのURLを設定（自分のユーザー名に置き換え）
git remote add origin https://github.com/YOUR_USERNAME/jikkennote-search.git

# メインブランチの名前を確認（既に main になっています）
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

**注意**: GitHubの認証が求められた場合は、Personal Access Token を使用してください。

---

## ステップ 2: バックエンドのデプロイ（Railway）

### 2.1 Railwayアカウントの準備

1. https://railway.app/ にアクセス
2. 「Start a New Project」または「Login with GitHub」でログイン

### 2.2 新しいプロジェクトを作成

1. ダッシュボードで「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. GitHubリポジトリを接続（初回の場合は認証が必要）
4. 作成した `jikkennote-search` リポジトリを選択

### 2.3 バックエンドサービスの設定

1. プロジェクトが作成されたら、「Settings」タブを開く
2. **Root Directory** を `backend` に設定
3. **Build Command**: 自動検出（Dockerfileを使用）
4. **Start Command**: 自動検出（`CMD ["python", "server.py"]`）

### 2.4 環境変数の設定

「Variables」タブで以下の環境変数を追加：

```bash
# CORS設定（後でVercelのURLに更新します）
CORS_ORIGINS=http://localhost:3000

# サーバー設定
HOST=0.0.0.0
PORT=8000
```

**オプション**（カスタマイズする場合のみ）：
```bash
NOTES_NEW_FOLDER=/app/notes/new
NOTES_ARCHIVE_FOLDER=/app/notes/archived
CHROMA_DB_FOLDER=/app/chroma_db
MASTER_DICT_PATH=/app/master_dictionary.yaml
```

### 2.5 ボリュームの設定（データ永続化）

1. 「Settings」タブの「Volumes」セクション
2. 「Add Volume」をクリック
3. 以下のボリュームを追加：
   - マウントパス: `/app/chroma_db`
   - マウントパス: `/app/notes`
   - マウントパス: `/app/data`

### 2.6 デプロイ実行

1. 「Deployments」タブで自動的にデプロイが開始されます
2. ビルドログを確認してエラーがないことを確認
3. デプロイ完了後、「Settings」 → 「Domains」でURLを確認
   - 例: `https://jikkennote-search-backend.up.railway.app`
4. **このURLをメモしておきます**（フロントエンドで使用します）

### 2.7 動作確認

ブラウザまたはcurlでヘルスチェック：

```bash
curl https://YOUR-BACKEND-URL.railway.app/health
```

期待されるレスポンス：
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "config": {...}
}
```

---

## ステップ 3: フロントエンドのデプロイ（Vercel）

### 3.1 Vercelアカウントの準備

1. https://vercel.com/ にアクセス
2. 「Sign Up」または「Login with GitHub」でログイン

### 3.2 新しいプロジェクトをインポート

1. ダッシュボードで「Add New」 → 「Project」をクリック
2. 「Import Git Repository」を選択
3. GitHubから `jikkennote-search` リポジトリを選択
4. 「Import」をクリック

### 3.3 プロジェクトの設定

**Configure Project** 画面で：

1. **Framework Preset**: Next.js（自動検出）
2. **Root Directory**: `frontend` を選択
3. **Build Command**: `npm run build`（デフォルト）
4. **Output Directory**: `.next`（デフォルト）
5. **Install Command**: `npm install`（デフォルト）

### 3.4 環境変数の設定

「Environment Variables」セクションで追加：

```bash
# バックエンドのURL（ステップ2.6でメモしたURL）
NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL.railway.app
```

**重要**: `YOUR-BACKEND-URL` を実際のRailway URLに置き換えてください。

### 3.5 デプロイ実行

1. 「Deploy」ボタンをクリック
2. ビルドログを確認
3. デプロイ完了後、自動的に本番URLが生成されます
   - 例: `https://jikkennote-search.vercel.app`
4. **このURLをメモしておきます**

### 3.6 カスタムドメインの設定（オプション）

1. プロジェクト設定の「Domains」タブ
2. カスタムドメインを追加
3. DNSレコードを設定

---

## ステップ 4: CORS設定の更新

フロントエンドのデプロイが完了したら、バックエンドのCORS設定を更新します。

### 4.1 RailwayでCORS環境変数を更新

1. Railwayのダッシュボードに戻る
2. プロジェクトを選択
3. 「Variables」タブを開く
4. `CORS_ORIGINS` を編集：

```bash
# VercelのURLを追加（カンマ区切り）
CORS_ORIGINS=https://jikkennote-search.vercel.app,http://localhost:3000
```

5. 保存すると自動的に再デプロイされます

---

## ステップ 5: 本番環境の初期設定

### 5.1 フロントエンドにアクセス

デプロイされたフロントエンド（`https://jikkennote-search.vercel.app`）にアクセス

### 5.2 APIキーの設定

1. 「設定」ページ（`/settings`）を開く
2. 「APIキー」タブを選択
3. 以下を入力：
   - **OpenAI API Key**: あなたのOpenAI APIキー
   - **Cohere API Key**: あなたのCohere APIキー
4. 「設定を保存」をクリック

### 5.3 モデルの選択（オプション）

1. 「モデル選択」タブを選択
2. 使用するモデルを選択：
   - Embeddingモデル: `text-embedding-3-small`（推奨）
   - LLMモデル: `gpt-4o-mini`（推奨）
3. 「設定を保存」をクリック

---

## ステップ 6: 初期データの投入

### 6.1 実験ノートの準備

ローカルでMarkdown形式の実験ノートを作成：

```markdown
# 実験ノート ID3-14

## 目的・背景
ポリマーAとポリマーBの混合物を合成

## 材料
- ポリマーA: 10g
- ポリマーB: 5g
- トルエン: 100ml

## 方法
1. フラスコに投入
2. 加熱して混合

## 結果
収率: 85%
```

### 6.2 ノートファイルのアップロード

**方法1**: SSH経由（Railwayの場合）

```bash
# Railway CLIをインストール
npm install -g @railway/cli

# ログイン
railway login

# プロジェクトにリンク
railway link

# ファイルをアップロード（カスタムスクリプトが必要）
```

**方法2**: APIエンドポイント経由（将来的な拡張）

現在のシステムではファイルアップロードAPIがないため、SSH経由でアクセスするか、ローカル環境でノートを取り込んでからChromaDBをバックアップ・リストアする方法を推奨します。

### 6.3 ノートの取り込み

1. フロントエンドの「ノート管理」ページを開く
2. 「取り込み実行」をクリック
3. 新出単語の判定を行う
4. 辞書を更新

---

## ステップ 7: 動作確認

### 7.1 機能テスト

**PRODUCTION_TEST_CHECKLIST.md** の手順に従って以下を確認：

- [ ] ヘルスチェック
- [ ] ホームページ表示
- [ ] APIキー設定
- [ ] 検索機能
- [ ] ノートビューワー
- [ ] 辞書管理
- [ ] 検索履歴

### 7.2 パフォーマンステスト

- [ ] 検索レスポンスタイム: 10秒以内
- [ ] ページロード時間: 3秒以内
- [ ] エラーがないことを確認

### 7.3 セキュリティテスト

- [ ] HTTPS通信
- [ ] CORS設定が正しく動作
- [ ] APIキーがlocalStorageに安全に保存

---

## トラブルシューティング

### フロントエンドがバックエンドに接続できない

**原因**: CORS設定またはURL設定の誤り

**解決策**:
1. Vercelの環境変数 `NEXT_PUBLIC_API_URL` が正しいか確認
2. RailwayのCORS設定にVercelのドメインが含まれているか確認
3. ブラウザの開発者ツールでCORSエラーを確認

### バックエンドのビルドが失敗する

**原因**: Dockerビルドエラー

**解決策**:
1. Railwayのビルドログを確認
2. `requirements.txt` の依存関係を確認
3. Dockerfileの構文エラーをチェック

### データが永続化されない

**原因**: ボリュームがマウントされていない

**解決策**:
1. Railwayでボリュームが設定されているか確認
2. マウントパスが正しいか確認（`/app/chroma_db` 等）

---

## 完了チェックリスト

デプロイが完了したら、以下を確認：

- [ ] GitHubリポジトリにコードがプッシュされている
- [ ] Railwayでバックエンドがデプロイされている
- [ ] バックエンドのヘルスチェックが成功する
- [ ] Vercelでフロントエンドがデプロイされている
- [ ] フロントエンドからバックエンドに接続できる
- [ ] APIキーが設定されている
- [ ] 検索機能が動作する
- [ ] PRODUCTION_TEST_CHECKLIST.md の主要項目に合格

---

## 次のステップ

デプロイが完了したら：

1. **ユーザーに共有**
   - URLを共有: `https://jikkennote-search.vercel.app`
   - USER_MANUAL.md を配布

2. **モニタリング設定**
   - Vercel Analytics を有効化
   - Railway Metrics を確認

3. **定期バックアップ**
   - ChromaDB のバックアップスケジュール設定
   - 辞書のバックアップ

4. **フィードバック収集**
   - ユーザーからのフィードバックを収集
   - 改善点をリストアップ

---

**おめでとうございます！** 🎉

実験ノート検索システム v2.0 のデプロイが完了しました。

問題が発生した場合は、DEPLOYMENT.md のトラブルシューティングセクションを参照してください。
