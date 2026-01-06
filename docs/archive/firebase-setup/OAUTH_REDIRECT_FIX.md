# OAuth リダイレクトURIエラーの修正手順

## エラー内容

```
エラー 400: redirect_uri_mismatch
アクセスをブロック: このアプリのリクエストは無効です
```

このエラーは、Google OAuth設定でリダイレクトURIが正しく設定されていないために発生します。

---

## 修正手順

### 1. Google Cloud Console にアクセス

1. ブラウザで https://console.cloud.google.com を開く
2. Googleアカウントでログイン（Firebase プロジェクトを作成したアカウント）
3. 画面上部のプロジェクト選択ドロップダウンから **`jikkennote-search-80a12`** を選択

### 2. OAuth認証情報の設定ページに移動

1. 左側のナビゲーションメニューから **「APIとサービス」** → **「認証情報」** をクリック
2. 「OAuth 2.0 クライアントID」セクションを探す
3. **「Webクライアント（Firebase用に自動作成）」** という名前のクライアントIDをクリック
   - 名前が異なる場合は、「クライアントの種類: ウェブアプリケーション」のものを選択

### 3. 承認済みのリダイレクトURIを追加

「承認済みのリダイレクトURI」セクションで **「URIを追加」** ボタンをクリックし、以下のURIを1つずつ追加します：

#### 必須: Firebase標準URI（通常は既に存在）
```
https://jikkennote-search-80a12.firebaseapp.com/__/auth/handler
```

#### ローカル開発用
```
http://localhost:3000/__/auth/handler
http://localhost:3001/__/auth/handler
http://localhost:3003/__/auth/handler
```

#### Vercel本番用
```
https://jikkennote-search-v2.vercel.app/__/auth/handler
```

#### 現在のVercelプレビュー用（必要に応じて）
```
https://jikkennote-search-v2-i8xe8pwff-nori8774s-projects.vercel.app/__/auth/handler
```

**重要**:
- 各URIの末尾は `/__/auth/handler` で終わる必要があります
- `http://` と `https://` を間違えないように注意

### 4. 保存

画面下部の **「保存」** ボタンをクリックします。

---

## Firebase Consoleでの設定確認

### 1. Firebase Console にアクセス

1. https://console.firebase.google.com を開く
2. プロジェクト **`jikkennote-search-80a12`** を選択

### 2. 承認済みドメインを確認

1. 左メニューから **「Authentication」** をクリック
2. 上部タブの **「Settings」** をクリック
3. 下にスクロールして **「Authorized domains」** セクションを見つける

### 3. 必要なドメインを追加

以下のドメインが含まれているか確認し、なければ追加します：

- `localhost`
- `jikkennote-search-v2.vercel.app`
- `jikkennote-search-80a12.firebaseapp.com`（デフォルトで存在）
- `jikkennote-search-80a12.web.app`（デフォルトで存在）

現在のVercelプレビュー環境でテストする場合は、以下も追加：
- `jikkennote-search-v2-i8xe8pwff-nori8774s-projects.vercel.app`

**注意**: プレビュー環境のURLは毎回変わるため、開発時はローカル環境（localhost）でテストすることを推奨します。

---

## 設定反映までの待ち時間

Google Cloud Consoleでの設定変更が反映されるまで、**5〜10分程度**かかる場合があります。

保存後、少し待ってから再度ログインを試してください。

---

## ローカル環境でのテスト（推奨）

設定変更後、まずはローカル環境でテストすることをお勧めします：

```bash
# フロントエンドディレクトリに移動
cd frontend

# 開発サーバーを起動
npm run dev
```

ブラウザで http://localhost:3000/login にアクセスし、ログインをテストしてください。

---

## トラブルシューティング

### まだエラーが出る場合

1. **ブラウザのキャッシュをクリア**
   - Cmd+Shift+R (Mac) または Ctrl+Shift+R (Windows) で強制リロード

2. **シークレットモード/プライベートブラウジングで試す**
   - キャッシュの影響を排除

3. **設定を再確認**
   - Google Cloud Console: リダイレクトURIが正しく保存されているか
   - Firebase Console: Authorized domainsが正しく設定されているか

4. **Firebase コンソールでGoogle認証が有効になっているか確認**
   - Firebase Console → Authentication → Sign-in method
   - 「Google」が「有効」になっているか確認

---

## 参考情報

- Firebase Authentication ドキュメント: https://firebase.google.com/docs/auth
- Google Cloud OAuth設定: https://cloud.google.com/docs/authentication
- Vercelドメイン設定: https://vercel.com/docs/concepts/projects/domains
