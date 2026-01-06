# ローカル開発環境 セットアップガイド

**作成日**: 2026-01-01
**目的**: Firebase認証を含むローカル環境でのテスト

---

## 🎯 問題の診断

### 現在発生しているエラー

```
jikkennote-backend-285071263188.asia-northeast1.run.app/teams:1
Failed to load resource: the server responded with a status of 401 (Unauthorized)
Error fetching teams: Error: Failed to fetch teams
```

### 原因

ローカル環境のフロントエンドが**本番バックエンド**にアクセスしていますが、プロジェクトIDが不一致のため、認証に失敗しています。

- **フロントエンド**: Firebaseプロジェクト `jikkennote-search-9e7b9` でログイン
- **本番バックエンド**: Firebaseプロジェクト `jikkennote-search-80a12`（古いプロジェクト）で検証

### 解決策

ローカルバックエンドを起動して、ローカル環境同士で接続します。

---

## 🚀 ローカル環境の起動方法

### 方法1: 自動起動スクリプト（推奨）

```bash
cd /Users/nori8774/jikkennote-search_v1
./START_LOCAL_ENV.sh
```

このスクリプトは以下を自動的に実行します：
1. 古いプロセスをクリーンアップ（ポート8000と3000）
2. バックエンドを起動（http://localhost:8000）
3. フロントエンドを起動（http://localhost:3000）

### 方法2: 手動起動

#### ステップ1: バックエンドを起動

```bash
cd /Users/nori8774/jikkennote-search_v1/backend
python3 server.py
```

**期待される出力:**
```
✅ Firebase Admin SDK initialized successfully
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### ステップ2: 別のターミナルでフロントエンドを起動

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
npm run dev
```

**期待される出力:**
```
  ▲ Next.js 15.5.9
  - Local:        http://localhost:3000
```

---

## ✅ 動作確認

### 1. バックエンドのヘルスチェック

```bash
curl http://localhost:8000/health
```

**期待されるレスポンス:**
```json
{
  "status": "healthy",
  "message": "Server is running",
  "version": "3.0.0"
}
```

### 2. フロントエンドにアクセス

ブラウザで http://localhost:3000/login を開く

### 3. ログインをテスト

1. 「Googleでログイン」ボタンをクリック
2. Googleアカウントを選択（nori8774@gmail.com）
3. ログイン成功後、`/search` ページにリダイレクトされる
4. ヘッダーにユーザー名が表示される

### 4. チーム情報の確認

ブラウザのコンソール（F12）で、以下のエラーが**出ないこと**を確認：
```
❌ jikkennote-backend-285071263188.asia-northeast1.run.app/teams:1
   Failed to load resource: 401 (Unauthorized)
```

代わりに、以下のログが表示される：
```
✅ localhost:8000/teams
   200 OK
```

---

## 🔧 設定ファイル

### frontend/.env.local

ローカル開発用の設定（すでに更新済み）:

```env
# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyBLupsnpgDj9RVTY5RhJx88yhYbtY1I_k8
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=jikkennote-search-9e7b9.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=jikkennote-search-9e7b9
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=jikkennote-search-9e7b9.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=109366953202
NEXT_PUBLIC_FIREBASE_APP_ID=1:109366953202:web:ccf40ca30cad14ae197c6b

# Backend API URL (Local development)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### backend/firebase-adminsdk.json

Firebaseプロジェクト `jikkennote-search-9e7b9` のサービスアカウント鍵:

```json
{
  "type": "service_account",
  "project_id": "jikkennote-search-9e7b9",
  ...
}
```

---

## 🐛 トラブルシューティング

### エラー: `Address already in use` (ポート8000)

**原因**: バックエンドのプロセスがすでに起動している

**対処法**:
```bash
lsof -ti:8000 | xargs kill -9
```

その後、再度バックエンドを起動

### エラー: `Address already in use` (ポート3000)

**原因**: フロントエンドのプロセスがすでに起動している

**対処法**:
```bash
lsof -ti:3000 | xargs kill -9
```

その後、再度フロントエンドを起動

### エラー: `ModuleNotFoundError: No module named 'fastapi'`

**原因**: Pythonの依存関係がインストールされていない

**対処法**:
```bash
cd /Users/nori8774/jikkennote-search_v1/backend
pip3 install -r requirements.txt
```

### エラー: `FileNotFoundError: firebase-adminsdk.json`

**原因**: Firebase Admin SDKの秘密鍵ファイルが見つからない

**対処法**:
1. Firebase Consoleから秘密鍵を再ダウンロード
2. `backend/firebase-adminsdk.json` として保存

### 依然として 401 Unauthorized エラーが出る

**確認事項**:

1. **バックエンドのログを確認**:
   ```bash
   tail -f /tmp/backend.log
   ```

   Firebase初期化のログを確認：
   ```
   ✅ Firebase Admin SDK initialized successfully
   ```

2. **フロントエンドが正しいURLにアクセスしているか確認**:

   ブラウザのNetwork タブ（F12 → Network）で、リクエストURLを確認：
   - ✅ `http://localhost:8000/teams`（正しい）
   - ❌ `https://jikkennote-backend-285071263188.asia-northeast1.run.app/teams`（間違い）

3. **FirebaseプロジェクトIDが一致しているか確認**:
   ```bash
   # フロントエンド
   cat frontend/.env.local | grep PROJECT_ID
   # 期待: NEXT_PUBLIC_FIREBASE_PROJECT_ID=jikkennote-search-9e7b9

   # バックエンド
   cat backend/firebase-adminsdk.json | jq -r '.project_id'
   # 期待: jikkennote-search-9e7b9
   ```

---

## 🎉 成功の確認

以下が全て確認できれば、ローカル環境のセットアップは完了です：

- [x] バックエンドが http://localhost:8000 で起動している
- [x] フロントエンドが http://localhost:3000 で起動している
- [x] `/login` ページでGoogleログインができる
- [x] ログイン後、`/search` ページにリダイレクトされる
- [x] ヘッダーにユーザー名が表示される
- [x] ブラウザのコンソールに 401 エラーが**出ない**
- [x] `/settings` → 「プロンプト管理」で「現在のプロンプトを保存」が動作する

---

## 📝 本番環境への切り替え

ローカル開発が完了したら、本番環境に戻す場合は以下を実行：

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
```

`.env.local` の `NEXT_PUBLIC_API_URL` を変更:
```env
# Backend API URL (Tokyo region - original)
NEXT_PUBLIC_API_URL=https://jikkennote-backend-285071263188.asia-northeast1.run.app
```

**注意**: 本番バックエンドを使う場合は、本番バックエンドの `firebase-adminsdk.json` も新しいプロジェクトに更新する必要があります。

---

## 🔗 関連ドキュメント

- **完全セットアップガイド**: `FIREBASE_AUTH_SETUP_COMPLETE.md`
- **OAuth 2.0 クライアントID作成**: `OAUTH_CLIENT_ID_CREATION.md`
- **設定状況サマリー**: `SETUP_STATUS.md`

---

**最終更新**: 2026-01-01
**次のステップ**: OAuth 2.0 クライアントIDを作成後、ローカル環境でテスト
