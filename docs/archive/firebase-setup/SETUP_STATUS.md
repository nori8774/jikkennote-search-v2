# Firebase認証 設定状況サマリー

**更新日**: 2026-01-01 03:30
**プロジェクト**: 実験ノート検索システム v3.0
**Firebaseプロジェクト**: `jikkennote-search-9e7b9`

---

## 📊 現在の設定状況

### ✅ 完了している設定

| 項目 | 状態 | 詳細 |
|------|------|------|
| フロントエンド（ローカル） | ✅ 完了 | `.env.local` に新しいFirebase設定済み |
| バックエンド（ローカル） | ✅ 完了 | `firebase-adminsdk.json` が正しいプロジェクト |
| バックエンド（本番） | ✅ 稼働中 | Cloud Run (asia-northeast1) |

### ⚠️ 要確認・設定が必要

| 項目 | 状態 | 対処方法 |
|------|------|----------|
| Vercel環境変数 | ⚠️ 要更新 | `QUICK_SETUP.sh` を実行 |
| Firebase Console - Google認証 | ❌ 未確認 | 手動設定が必要 |
| Firebase Console - Authorized Domains | ❌ 未確認 | 手動設定が必要 |
| Google Cloud Console - OAuth | ❌ 未確認 | 手動設定が必要 |

---

## 🚀 次にやるべきこと

### 優先度: 高 ⭐⭐⭐

#### 1. Vercel環境変数の更新とデプロイ

**実行方法（自動）:**
```bash
cd /Users/nori8774/jikkennote-search_v1
./QUICK_SETUP.sh
```

**または手動で実行:**
```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
vercel env add NEXT_PUBLIC_FIREBASE_API_KEY production --force
# （詳細は FIREBASE_AUTH_SETUP_COMPLETE.md を参照）
```

#### 2. Firebase Console での設定

**必須作業:**

1. **Google認証を有効化**
   - URL: https://console.firebase.google.com
   - プロジェクト: `jikkennote-search-9e7b9`
   - Authentication → Sign-in method → Google → 有効にする

2. **Authorized Domainsを追加**
   - Authentication → Settings → Authorized domains
   - 追加するドメイン:
     - `localhost`
     - `jikkennote-search-v2.vercel.app`
     - `jikkennote-search-9e7b9.firebaseapp.com`

#### 3. Google Cloud Console での設定

**必須作業:**

1. **OAuth リダイレクトURIを追加**
   - URL: https://console.cloud.google.com
   - プロジェクト: `jikkennote-search-9e7b9`
   - APIとサービス → 認証情報 → OAuth 2.0 クライアントID
   - 承認済みのリダイレクトURIに追加:
     - `https://jikkennote-search-v2.vercel.app/__/auth/handler`
     - `https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler`
     - `http://localhost:3000/__/auth/handler`

---

## 📝 設定後の動作確認

### ローカル環境

```bash
cd /Users/nori8774/jikkennote-search_v1/frontend
npm run dev
```

ブラウザ: http://localhost:3000/login

### 本番環境

ブラウザ: https://jikkennote-search-v2.vercel.app/login

### 期待される動作

1. 「Googleでログイン」ボタンをクリック
2. Googleアカウント選択画面が表示される
3. アカウントを選択
4. `/search` ページにリダイレクトされる
5. ヘッダーにユーザー名が表示される

---

## 🔍 よくあるエラーと対処法

### エラー: `redirect_uri_mismatch`

**原因**: Google Cloud ConsoleのリダイレクトURIが設定されていない

**対処**: ステップ3（Google Cloud Console での設定）を実行

---

### エラー: `auth/unauthorized-domain`

**原因**: Firebase ConsoleのAuthorized domainsにドメインが追加されていない

**対処**: ステップ2（Firebase Console での設定）を実行

---

### エラー: `Authentication required`（プロンプト保存時）

**原因**: ログインできていない、または設定が不完全

**対処**:
1. まずログインページ（`/login`）からログイン
2. ブラウザのコンソール（F12）でエラーを確認
3. 上記の設定が全て完了しているか確認

---

## 📚 関連ドキュメント

- **完全セットアップガイド**: `FIREBASE_AUTH_SETUP_COMPLETE.md`
- **OAuth 2.0 クライアントID作成手順**: `OAUTH_CLIENT_ID_CREATION.md` ⭐ NEW
- **クイックセットアップスクリプト**: `QUICK_SETUP.sh`
- **OAuth修正ガイド**: `OAUTH_REDIRECT_FIX.md`
- **プロジェクトメモリ**: `CLAUDE.md`

---

## 🆘 サポート

設定で困った場合は、以下の情報を確認してください:

1. **ブラウザのコンソールエラー** (F12 → Console)
2. **ネットワークエラー** (F12 → Network)
3. **Firebase Console のユーザー一覧** (Authentication → Users)

---

**現在のプロジェクト情報:**

- **Firebaseプロジェクト**: `jikkennote-search-9e7b9`
- **フロントエンド本番URL**: https://jikkennote-search-v2.vercel.app
- **バックエンドURL**: https://jikkennote-backend-285071263188.asia-northeast1.run.app
- **リージョン**: asia-northeast1（東京）

---

**最終更新**: 2026-01-01 03:30
**次回確認**: 設定完了後
