# Firebase認証 完全セットアップガイド

**作成日**: 2026-01-01
**プロジェクト**: 実験ノート検索システム v3.0
**Firebaseプロジェクト**: `jikkennote-search-9e7b9`

---

## 📋 現在の設定状況

### ✅ 完了している設定

1. **フロントエンド（ローカル環境）**
   - ファイル: `frontend/.env.local`
   - Firebaseプロジェクト: `jikkennote-search-9e7b9`
   - 設定状態: ✅ 完了

2. **バックエンド（ローカル環境）**
   - ファイル: `backend/firebase-adminsdk.json`
   - Firebaseプロジェクト: `jikkennote-search-9e7b9`
   - 設定状態: ✅ 完了

3. **バックエンド（本番環境 - Cloud Run）**
   - URL: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
   - リージョン: asia-northeast1（東京）
   - 設定状態: ✅ 稼働中

### ⚠️ 要確認・設定が必要な項目

4. **Vercel本番環境の環境変数**
   - 設定状態: ⚠️ 要確認（新しいFirebaseプロジェクトの値になっているか不明）

5. **Google Cloud Console - OAuth設定**
   - 設定状態: ❌ 未設定の可能性が高い

6. **Firebase Console - Authentication設定**
   - 設定状態: ❌ 未設定の可能性が高い

7. **Firebase Console - Authorized Domains**
   - 設定状態: ❌ 未設定の可能性が高い

---

## 🔧 必須セットアップ手順

以下の手順を**順番通りに**実行してください。

---

## ステップ1: Vercelの環境変数を更新

### 1-1. 現在の環境変数を削除

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
vercel env rm NEXT_PUBLIC_FIREBASE_API_KEY production
vercel env rm NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN production
vercel env rm NEXT_PUBLIC_FIREBASE_PROJECT_ID production
vercel env rm NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET production
vercel env rm NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID production
vercel env rm NEXT_PUBLIC_FIREBASE_APP_ID production
```

### 1-2. 新しい環境変数を追加

```bash
# API Key
echo "AIzaSyBLupsnpgDj9RVTY5RhJx88yhYbtY1I_k8" | vercel env add NEXT_PUBLIC_FIREBASE_API_KEY production

# Auth Domain
echo "jikkennote-search-9e7b9.firebaseapp.com" | vercel env add NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN production

# Project ID
echo "jikkennote-search-9e7b9" | vercel env add NEXT_PUBLIC_FIREBASE_PROJECT_ID production

# Storage Bucket
echo "jikkennote-search-9e7b9.firebasestorage.app" | vercel env add NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET production

# Messaging Sender ID
echo "109366953202" | vercel env add NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID production

# App ID
echo "1:109366953202:web:ccf40ca30cad14ae197c6b" | vercel env add NEXT_PUBLIC_FIREBASE_APP_ID production
```

### 1-3. 環境変数を確認

```bash
vercel env ls production
```

**期待される出力**:
```
NEXT_PUBLIC_FIREBASE_API_KEY                Encrypted  Production  Just now
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN            Encrypted  Production  Just now
NEXT_PUBLIC_FIREBASE_PROJECT_ID             Encrypted  Production  Just now
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET         Encrypted  Production  Just now
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID    Encrypted  Production  Just now
NEXT_PUBLIC_FIREBASE_APP_ID                 Encrypted  Production  Just now
NEXT_PUBLIC_API_URL                         Encrypted  Production  XXX
```

---

## ステップ2: Firebase Consoleでの設定

### 2-1. Firebase Console にアクセス

1. ブラウザで https://console.firebase.google.com を開く
2. Googleアカウント（nori8774@gmail.com）でログイン
3. プロジェクト **`jikkennote-search-9e7b9`** を選択

### 2-2. Google認証を有効化

1. 左メニューから **「Authentication」** をクリック
2. 上部タブの **「Sign-in method」** をクリック
3. **「Google」** の行を探してクリック
4. **「有効にする」** トグルをONにする
5. **「プロジェクトの公開名」** を入力（例: 実験ノート検索システム）
6. **「プロジェクトのサポートメール」** を選択（nori8774@gmail.com）
7. **「保存」** をクリック

### 2-3. Authorized Domainsを設定

1. 同じ「Authentication」画面で、上部タブの **「Settings」** をクリック
2. 下にスクロールして **「Authorized domains」** セクションを見つける
3. **「Add domain」** ボタンをクリックし、以下のドメインを1つずつ追加：

```
localhost
jikkennote-search-v2.vercel.app
jikkennote-search-9e7b9.firebaseapp.com
```

**注意**: 各ドメインを追加後、必ず **「Add」** をクリックしてください。

---

## ステップ3: Google Cloud Consoleでの設定

### 3-1. Google Cloud Console にアクセス

1. ブラウザで https://console.cloud.google.com を開く
2. 画面上部のプロジェクト選択ドロップダウンをクリック
3. **`jikkennote-search-9e7b9`** を選択

### 3-2. OAuth 2.0 クライアントIDを設定

1. 左メニューから **「APIとサービス」** → **「認証情報」** をクリック
2. 「OAuth 2.0 クライアントID」セクションを探す

**⚠️ OAuth 2.0 クライアントIDが表示されていない場合**

OAuth 2.0 クライアントIDが何も表示されていない場合は、手動で作成する必要があります。

👉 **詳細な作成手順は `OAUTH_CLIENT_ID_CREATION.md` を参照してください**

作成後、このステップに戻ってください。

---

3. **「Webクライアント（Firebase用）」** または作成したクライアント名をクリック
   - 複数ある場合は、「ウェブアプリケーション」タイプのものを選択

### 3-3. 承認済みのリダイレクトURIを追加

「承認済みのリダイレクトURI」セクションで、**「URIを追加」** ボタンをクリックし、以下のURIを**1つずつ**追加：

```
https://jikkennote-search-v2.vercel.app/__/auth/handler
https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler
http://localhost:3000/__/auth/handler
http://localhost:3001/__/auth/handler
http://localhost:3003/__/auth/handler
```

**重要ポイント**:
- URIの末尾は必ず `/__/auth/handler` で終わる
- `http://` と `https://` を正確に入力
- 末尾にスラッシュ（`/`）を追加しない
- 各URIを追加後、**「追加」**ボタンをクリック

### 3-4. 保存

画面下部の **「保存」** ボタンをクリック

---

## ステップ4: Vercelに再デプロイ

環境変数を更新したので、本番環境に再デプロイします。

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
vercel --prod --yes
```

**期待される出力**:
```
Production: https://jikkennote-search-v2-XXXXX.vercel.app
Aliased: https://jikkennote-search-v2.vercel.app
```

---

## ステップ5: 動作確認

### 5-1. ローカル環境でテスト

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
npm run dev
```

ブラウザで http://localhost:3000/login を開き、「Googleでログイン」をテスト

### 5-2. 本番環境でテスト

1. ブラウザで https://jikkennote-search-v2.vercel.app/login を開く
2. 「Googleでログイン」ボタンをクリック
3. Googleアカウントを選択
4. ログイン成功後、`/search` ページにリダイレクトされる

---

## 🔍 トラブルシューティング

### エラー: `redirect_uri_mismatch`

**原因**: Google Cloud ConsoleのリダイレクトURIが正しく設定されていない

**対処法**:
1. Google Cloud Console → APIとサービス → 認証情報を確認
2. 承認済みのリダイレクトURIに以下が含まれているか確認：
   - `https://jikkennote-search-v2.vercel.app/__/auth/handler`
   - `https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler`
3. URIの末尾が `/__/auth/handler` で終わっているか確認
4. 保存後、5〜10分待ってから再度テスト

### エラー: `auth/unauthorized-domain`

**原因**: Firebase ConsoleのAuthorized domainsにドメインが追加されていない

**対処法**:
1. Firebase Console → Authentication → Settings → Authorized domainsを確認
2. 以下のドメインが含まれているか確認：
   - `localhost`
   - `jikkennote-search-v2.vercel.app`
3. 不足しているドメインを追加
4. ブラウザのキャッシュをクリア（Cmd+Shift+R）

### エラー: `Authentication required`（プロンプト保存時）

**原因**: Firebaseログインができていない、またはID Tokenが取得できていない

**対処法**:
1. ログインページ（`/login`）からログインしているか確認
2. ブラウザのコンソール（F12 → Console）でエラーメッセージを確認
3. Firebase設定（API Key、Auth Domain等）が正しいか確認

### Google Cloud Consoleの設定が反映されない

**対処法**:
1. 設定変更後、5〜10分待つ
2. ブラウザのキャッシュをクリア
3. シークレットモード/プライベートブラウジングで試す

---

## 📝 設定完了チェックリスト

以下を全て確認してください：

### フロントエンド設定

- [ ] `frontend/.env.local` にFirebase設定が記載されている
- [ ] Vercelの本番環境変数が新しいFirebaseプロジェクト（`jikkennote-search-9e7b9`）の値になっている
- [ ] Vercelに再デプロイした

### バックエンド設定

- [ ] `backend/firebase-adminsdk.json` が存在し、プロジェクトID が `jikkennote-search-9e7b9`
- [ ] Cloud Runバックエンド（asia-northeast1）が稼働中

### Firebase Console設定

- [ ] Authentication → Sign-in method で「Google」が有効
- [ ] Authentication → Settings → Authorized domains に以下が追加済み：
  - [ ] `localhost`
  - [ ] `jikkennote-search-v2.vercel.app`
  - [ ] `jikkennote-search-9e7b9.firebaseapp.com`

### Google Cloud Console設定

- [ ] APIとサービス → 認証情報 → OAuth 2.0 クライアントID を開いた
- [ ] 承認済みのリダイレクトURIに以下が追加済み：
  - [ ] `https://jikkennote-search-v2.vercel.app/__/auth/handler`
  - [ ] `https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler`
  - [ ] `http://localhost:3000/__/auth/handler`
- [ ] 保存ボタンをクリックした

### 動作確認

- [ ] ローカル環境（http://localhost:3000/login）でログインが成功する
- [ ] 本番環境（https://jikkennote-search-v2.vercel.app/login）でログインが成功する
- [ ] ログイン後、`/search` ページにリダイレクトされる
- [ ] `/settings` → 「プロンプト管理」で「現在のプロンプトを保存」が動作する

---

## 🆘 それでも動かない場合

### 1. ブラウザのコンソールを確認

F12キーを押して、Consoleタブを確認してください。エラーメッセージが表示されている場合、そのメッセージを記録してください。

### 2. ネットワークタブを確認

F12キー → Networkタブで、ログインボタンをクリックした際のリクエスト/レスポンスを確認してください。

### 3. Firebase Consoleでユーザーを確認

Firebase Console → Authentication → Users で、ログインしたユーザーが表示されているか確認してください。

### 4. 環境変数を再確認

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
cat .env.local
vercel env ls production
```

すべての環境変数が正しく設定されているか確認してください。

---

## 📚 参考情報

- **Firebaseプロジェクト名**: `jikkennote-search-9e7b9`
- **本番URL**: https://jikkennote-search-v2.vercel.app
- **バックエンドURL**: https://jikkennote-backend-285071263188.asia-northeast1.run.app
- **リージョン**: asia-northeast1（東京）

---

**最終更新**: 2026-01-01
**作成者**: Claude Code
