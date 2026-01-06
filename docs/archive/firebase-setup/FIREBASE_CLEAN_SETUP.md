# Firebase認証 クリーンセットアップガイド

**作成日**: 2026-01-01
**目的**: 既存の設定をクリーンにして、新しいFirebaseプロジェクトで認証を再構築

---

## 📋 概要

現在の問題を解決するため、Firebaseプロジェクトを新規作成し、最初から正しい設定で構築します。

**所要時間**: 30〜40分

---

## ステップ1: 既存の設定を確認（削除不要）

既存のFirebaseプロジェクトは削除せず、そのまま残しておきます。
新しいプロジェクトを作成し、そちらに切り替えます。

**現在のプロジェクト**:
- `jikkennote-search-9e7b9` (新)
- `jikkennote-search-80a12` (旧)

**方針**: 新しいプロジェクトをもう1つ作成します。

---

## ステップ2: 新しいFirebaseプロジェクトを作成

### 2-1. Firebase Consoleにアクセス

1. ブラウザで https://console.firebase.google.com を開く
2. Googleアカウント（nori8774@gmail.com）でログイン

### 2-2. 新しいプロジェクトを作成

1. **「プロジェクトを追加」** ボタンをクリック

2. **プロジェクト名を入力**:
   ```
   jikkennote-search-v3
   ```
   - プロジェクトIDは自動生成されます（例: `jikkennote-search-v3-xxxxx`）
   - このIDを後で使うので、メモしておいてください

3. **Google アナリティクスの設定**:
   - 「このプロジェクトでGoogle アナリティクスを有効にする」はOFFでOK
   - または、デフォルトのままでOK

4. **「プロジェクトを作成」** をクリック

5. プロジェクト作成完了まで待つ（1〜2分）

---

## ステップ3: Firebase Authenticationを設定

### 3-1. Authenticationを有効化

1. 左メニューから **「Authentication」** をクリック
2. **「始める」** ボタンをクリック

### 3-2. Google認証を有効化

1. **「Sign-in method」** タブをクリック
2. **「Google」** の行をクリック
3. **「有効にする」** トグルをONにする
4. **「プロジェクトの公開名」** を入力:
   ```
   実験ノート検索システム
   ```
5. **「プロジェクトのサポートメール」** を選択:
   ```
   nori8774@gmail.com
   ```
6. **「保存」** をクリック

### 3-3. Authorized Domainsを設定

1. 同じ「Authentication」画面で、上部の **「Settings」** タブをクリック
2. 下にスクロールして **「Authorized domains」** セクションを見つける
3. デフォルトで以下が含まれていることを確認:
   - `localhost`
   - `{プロジェクトID}.firebaseapp.com`

4. もし `localhost` が含まれていなければ、**「Add domain」** で追加:
   ```
   localhost
   ```

5. Vercelドメインも追加:
   ```
   jikkennote-search-v2.vercel.app
   ```

---

## ステップ4: Firebase Webアプリを登録

### 4-1. Webアプリを追加

1. Firebase Consoleのトップページ（プロジェクト概要）に戻る
2. **「ウェブ」** アイコン（`</>`）をクリック
3. **アプリのニックネーム** を入力:
   ```
   実験ノート検索システム Web
   ```
4. **「Firebase Hosting」** のチェックはOFF
5. **「アプリを登録」** をクリック

### 4-2. Firebase設定をコピー

表示された設定をメモしてください（後で使います）:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "jikkennote-search-v3-xxxxx.firebaseapp.com",
  projectId: "jikkennote-search-v3-xxxxx",
  storageBucket: "jikkennote-search-v3-xxxxx.firebasestorage.app",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456"
};
```

**「コンソールに進む」** をクリック

---

## ステップ5: Firebase Admin SDKのサービスアカウント鍵を取得

### 5-1. サービスアカウント鍵を生成

1. Firebase Console → プロジェクト設定（⚙️アイコン）をクリック
2. **「サービス アカウント」** タブをクリック
3. 下にスクロールして **「新しい秘密鍵の生成」** ボタンをクリック
4. 確認ダイアログで **「キーを生成」** をクリック
5. JSONファイルがダウンロードされる

### 5-2. サービスアカウント鍵を配置

ダウンロードしたJSONファイルを以下の場所に配置:

```bash
# ファイル名を変更してbackendディレクトリに配置
mv ~/Downloads/jikkennote-search-v3-xxxxx-firebase-adminsdk-xxxxx.json \
   /Users/nori8774/jikkennote-search_v1/backend/firebase-adminsdk.json
```

---

## ステップ6: Google Cloud ConsoleでOAuth 2.0を設定

### 6-1. Google Cloud Consoleにアクセス

1. ブラウザで https://console.cloud.google.com を開く
2. 画面上部のプロジェクト選択ドロップダウンをクリック
3. **新しく作成したプロジェクト**（`jikkennote-search-v3-xxxxx`）を選択

### 6-2. OAuth同意画面を設定

1. 左メニュー → **「APIとサービス」** → **「OAuth同意画面」** をクリック

2. **User Type** を選択:
   - **「外部」** を選択
   - **「作成」** をクリック

3. **アプリ情報** を入力:
   - アプリ名: `実験ノート検索システム`
   - ユーザーサポートメール: `nori8774@gmail.com`
   - デベロッパーの連絡先情報: `nori8774@gmail.com`

4. **「保存して次へ」** をクリック

5. **スコープ** 画面:
   - そのまま **「保存して次へ」** をクリック

6. **テストユーザー** 画面:
   - **「ADD USERS」** をクリック
   - メールアドレスを追加: `nori8774@gmail.com`
   - **「追加」** → **「保存して次へ」** をクリック

7. **概要** 画面:
   - **「ダッシュボードに戻る」** をクリック

### 6-3. OAuth 2.0 クライアントIDを作成

1. 左メニュー → **「APIとサービス」** → **「認証情報」** をクリック

2. 上部の **「+ 認証情報を作成」** → **「OAuth クライアント ID」** をクリック

3. **アプリケーションの種類**:
   - **「ウェブ アプリケーション」** を選択

4. **名前** を入力:
   ```
   実験ノート検索システム Webクライアント
   ```

5. **承認済みのJavaScript生成元** (空欄でOK)

6. **承認済みのリダイレクトURI** を追加:
   - **「URIを追加」** をクリックし、以下を1つずつ追加:
   ```
   http://localhost:3000/__/auth/handler
   http://localhost:3001/__/auth/handler
   https://jikkennote-search-v2.vercel.app/__/auth/handler
   https://jikkennote-search-v3-xxxxx.firebaseapp.com/__/auth/handler
   ```

   **重要**: 最後のURLの `xxxxx` は実際のプロジェクトIDに置き換えてください

7. **「作成」** をクリック

8. クライアントIDとシークレットが表示される画面:
   - **「OK」** をクリック（後で確認できます）

---

## ステップ7: フロントエンドの設定を更新

### 7-1. `.env.local` を更新

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
```

以下の内容で `.env.local` を更新してください（ステップ4-2でコピーした値を使用）:

```env
# Firebase Configuration (New Project)
NEXT_PUBLIC_FIREBASE_API_KEY=【ステップ4-2のapiKey】
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=【ステップ4-2のauthDomain】
NEXT_PUBLIC_FIREBASE_PROJECT_ID=【ステップ4-2のprojectId】
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=【ステップ4-2のstorageBucket】
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=【ステップ4-2のmessagingSenderId】
NEXT_PUBLIC_FIREBASE_APP_ID=【ステップ4-2のappId】

# Backend API URL (Local development)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ステップ8: バックエンドのサービスアカウント鍵を確認

ステップ5-2で配置した `backend/firebase-adminsdk.json` が正しい場所にあることを確認:

```bash
ls -la /Users/nori8774/jikkennote-search_v1/backend/firebase-adminsdk.json
```

ファイルの内容を確認（project_idが新しいプロジェクトIDになっているか）:

```bash
cat /Users/nori8774/jikkennote-search_v1/backend/firebase-adminsdk.json | grep project_id
```

**期待される出力**:
```json
  "project_id": "jikkennote-search-v3-xxxxx",
```

---

## ステップ9: ローカル環境で動作確認

### 9-1. バックエンドを再起動

```bash
cd /Users/nori8774/jikkennote-search_v1/backend

# 既存のバックエンドを停止
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# 新しい設定でバックエンドを起動
python3 server.py > /tmp/backend.log 2>&1 &

# 起動確認
sleep 5
curl -s http://localhost:8000/health | jq .
```

**期待される出力**:
```json
{
  "status": "healthy",
  "message": "Server is running",
  "version": "2.0.0",
  ...
}
```

### 9-2. フロントエンドを再起動

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend

# 既存のフロントエンドを停止
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# フロントエンドを起動
npm run dev
```

### 9-3. ログインをテスト

1. ブラウザで http://localhost:3000/login を開く
2. ブラウザのキャッシュをクリア（Cmd+Shift+R）
3. **「Googleでログイン」** ボタンをクリック
4. Googleアカウント（nori8774@gmail.com）を選択
5. ログイン成功後、`/search` ページにリダイレクトされる
6. ヘッダーにユーザー名が表示される

**成功の確認**:
- ✅ ログインポップアップが開く
- ✅ Googleアカウント選択画面が表示される
- ✅ ログイン成功後、`/search` にリダイレクト
- ✅ ヘッダーにユーザー名が表示される
- ✅ コンソールエラーがない

---

## ステップ10: Vercel環境変数を更新

ローカルで動作確認ができたら、Vercelの環境変数を更新します。

### 10-1. 既存の環境変数を削除

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend

vercel env rm NEXT_PUBLIC_FIREBASE_API_KEY production --yes
vercel env rm NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN production --yes
vercel env rm NEXT_PUBLIC_FIREBASE_PROJECT_ID production --yes
vercel env rm NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET production --yes
vercel env rm NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID production --yes
vercel env rm NEXT_PUBLIC_FIREBASE_APP_ID production --yes
```

### 10-2. 新しい環境変数を追加

```bash
# API Key
echo "【ステップ4-2のapiKey】" | vercel env add NEXT_PUBLIC_FIREBASE_API_KEY production

# Auth Domain
echo "【ステップ4-2のauthDomain】" | vercel env add NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN production

# Project ID
echo "【ステップ4-2のprojectId】" | vercel env add NEXT_PUBLIC_FIREBASE_PROJECT_ID production

# Storage Bucket
echo "【ステップ4-2のstorageBucket】" | vercel env add NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET production

# Messaging Sender ID
echo "【ステップ4-2のmessagingSenderId】" | vercel env add NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID production

# App ID
echo "【ステップ4-2のappId】" | vercel env add NEXT_PUBLIC_FIREBASE_APP_ID production
```

### 10-3. Vercelに再デプロイ

```bash
vercel --prod --yes
```

---

## ステップ11: 本番環境で動作確認

1. ブラウザで https://jikkennote-search-v2.vercel.app/login を開く
2. ブラウザのキャッシュをクリア（Cmd+Shift+R）
3. **「Googleでログイン」** をクリック
4. ログインをテスト

**成功の確認**:
- ✅ 本番環境でもログインが成功する
- ✅ `/settings` → プロンプト管理で保存が動作する

---

## 🎉 セットアップ完了チェックリスト

以下を全て確認してください：

### Firebaseプロジェクト

- [ ] 新しいFirebaseプロジェクト（`jikkennote-search-v3-xxxxx`）を作成した
- [ ] Authentication → Sign-in method で「Google」が有効
- [ ] Authentication → Settings → Authorized domains に以下が含まれる：
  - [ ] `localhost`
  - [ ] `jikkennote-search-v2.vercel.app`
  - [ ] `{プロジェクトID}.firebaseapp.com`

### Google Cloud Console

- [ ] OAuth同意画面を設定した
- [ ] OAuth 2.0 クライアントIDを作成した
- [ ] 承認済みのリダイレクトURIに以下が含まれる：
  - [ ] `http://localhost:3000/__/auth/handler`
  - [ ] `https://jikkennote-search-v2.vercel.app/__/auth/handler`
  - [ ] `https://{プロジェクトID}.firebaseapp.com/__/auth/handler`

### ローカル環境

- [ ] `frontend/.env.local` を新しい設定に更新した
- [ ] `backend/firebase-adminsdk.json` が新しいプロジェクトの鍵になっている
- [ ] ローカルでログインが成功する

### 本番環境

- [ ] Vercelの環境変数を更新した
- [ ] Vercelに再デプロイした
- [ ] 本番環境でログインが成功する
- [ ] `/settings` → プロンプト管理で保存が動作する

---

## 🐛 トラブルシューティング

### エラー: `redirect_uri_mismatch`

**原因**: OAuth 2.0 クライアントIDのリダイレクトURIが正しく設定されていない

**対処法**:
1. Google Cloud Console → APIとサービス → 認証情報
2. OAuth 2.0 クライアントIDをクリック
3. 承認済みのリダイレクトURIを確認・修正
4. 保存後、5〜10分待ってから再試行

### エラー: `auth/unauthorized-domain`

**原因**: Firebase ConsoleのAuthorized domainsにドメインが含まれていない

**対処法**:
1. Firebase Console → Authentication → Settings
2. Authorized domainsに `localhost` と `jikkennote-search-v2.vercel.app` を追加

### ログインポップアップが開かない

**対処法**:
1. ブラウザのポップアップブロッカーを無効化
2. シークレットモード/プライベートブラウジングで試す
3. 別のブラウザで試す

---

## 📝 次のステップ

セットアップが完了したら：

1. チーム機能のテスト（`/teams` ページ）
2. プロンプト保存機能のテスト（`/settings` → プロンプト管理）
3. ノート取り込み機能のテスト（`/ingest`）

---

**最終更新**: 2026-01-01
**作成者**: Claude Code
**所要時間**: 30〜40分

---

## 💡 ヒント

- 設定変更後は5〜10分待つと反映されます
- エラーが出た場合は、ブラウザのキャッシュをクリア（Cmd+Shift+R）
- 不明な点があれば、各ステップのスクリーンショットを確認してください
