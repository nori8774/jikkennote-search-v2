# 認証エラーの診断と解決方法

**更新日**: 2026-01-01
**状況**: ローカル環境でプロンプト保存時に認証エラーが発生

---

## 📋 現在の状況

### ✅ 正常に動作している部分

1. **バックエンド (localhost:8000)**: 正常稼働中
   - Firebase Admin SDK: 正常初期化済み
   - 認証ミドルウェア: 正常動作
   - ヘルスチェック: ✅ OK
   - ChromaDB情報取得: ✅ OK (認証不要)

2. **フロントエンド (localhost:3000)**: 起動中
   - Firebase設定: 正しく設定済み (`jikkennote-search-9e7b9`)
   - API接続: localhost:8000 に正しく設定

### ❌ エラーが発生している箇所

**エラーメッセージ**:
```
認証情報が取得できていません。ページを再読み込みしてください。
```

**エラー発生場所**:
- `/settings` ページでプロンプトを保存しようとしたとき
- コード: `frontend/app/settings/page.tsx:197`

**原因**:
```typescript
if (!idToken || !currentTeamId) {
  setSaveError('認証情報が取得できていません。ページを再読み込みしてください。');
  return;
}
```

つまり、以下のいずれかが `null` です：
- `idToken`: Firebase ID Token (ログインしていないとnull)
- `currentTeamId`: 現在選択中のチームID (チーム未選択またはログインしていないとnull)

---

## 🔍 根本原因

**ユーザーがログインしていない**

ローカル環境で `/settings` ページに直接アクセスしているため、ログイン処理が行われていません。

Firebase認証を使うには、以下の手順が必要です：
1. **OAuth 2.0 クライアントIDの作成** (Google Cloud Console)
2. **Googleログインの実行** (`/login` ページでログイン)
3. **チームの選択** (ログイン後、自動的に最初のチームが選択される)

---

## ✅ 解決方法

### ステップ1: OAuth 2.0 クライアントIDの作成（必須）

まだ完了していない場合は、以下のドキュメントに従ってOAuth 2.0 クライアントIDを作成してください：

👉 **[OAUTH_CLIENT_ID_CREATION.md](./OAUTH_CLIENT_ID_CREATION.md)**

**要点**:
1. Google Cloud Console → プロジェクト `jikkennote-search-9e7b9` を選択
2. APIとサービス → 認証情報 → OAuth 2.0 クライアントIDを作成
3. 承認済みのリダイレクトURIに以下を追加：
   ```
   http://localhost:3000/__/auth/handler
   http://localhost:3001/__/auth/handler
   https://jikkennote-search-v2.vercel.app/__/auth/handler
   https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler
   ```

### ステップ2: Firebase Console でGoogle認証を有効化（必須）

1. Firebase Console: https://console.firebase.google.com
2. プロジェクト: `jikkennote-search-9e7b9` を選択
3. Authentication → Sign-in method → **Google** を有効化
4. Authentication → Settings → Authorized domains に以下を追加：
   ```
   localhost
   jikkennote-search-v2.vercel.app
   jikkennote-search-9e7b9.firebaseapp.com
   ```

### ステップ3: ローカル環境でログイン

OAuth設定が完了したら、以下の手順でログインしてください：

```bash
# 1. ブラウザで http://localhost:3000/login を開く
# 2. 「Googleでログイン」ボタンをクリック
# 3. Googleアカウント (nori8774@gmail.com) を選択
# 4. ログイン成功後、/search ページにリダイレクトされる
```

### ステップ4: 動作確認

ログイン後、以下を確認してください：

1. **ヘッダーにユーザー名が表示される**
   - 右上に「nori8774@gmail.com」または表示名が表示される

2. **チームが選択されている**
   - ヘッダーにチーム名が表示される
   - または、チーム選択ドロップダウンが表示される

3. **プロンプト保存が動作する**
   - `/settings` ページに移動
   - プロンプト管理タブを開く
   - プロンプト名を入力して「保存」をクリック
   - エラーが出ずに保存成功する

---

## 🐛 トラブルシューティング

### エラー: redirect_uri_mismatch

**原因**: OAuth 2.0 クライアントIDのリダイレクトURIが設定されていない

**対処法**: ステップ1を再確認し、リダイレクトURIを正しく設定してください

### エラー: auth/unauthorized-domain

**原因**: Firebase ConsoleのAuthorized domainsに `localhost` が追加されていない

**対処法**: ステップ2を再確認し、Authorized domainsを設定してください

### エラー: チーム一覧が取得できない (401 Unauthorized)

**症状**: ログイン後、以下のエラーがコンソールに表示される
```
GET http://localhost:8000/teams 401 (Unauthorized)
```

**原因**: ログインは成功したが、ID Tokenが正しく送信されていない

**対処法**:
1. ブラウザを完全にリロード (Cmd+Shift+R)
2. ブラウザのコンソール (F12) で以下を確認：
   ```javascript
   // Local Storageを確認
   localStorage.getItem('current_team_id')
   ```
3. 上記がnullの場合、一度ログアウトして再ログイン

### ログインボタンをクリックしても何も起こらない

**原因**: OAuth 2.0 クライアントIDが未作成、またはリダイレクトURIが間違っている

**対処法**:
1. ブラウザのコンソール (F12 → Console) でエラーメッセージを確認
2. ステップ1を再実行し、設定が正しいか確認
3. 設定変更後、5〜10分待ってから再試行

---

## 📚 関連ドキュメント

- [OAUTH_CLIENT_ID_CREATION.md](./OAUTH_CLIENT_ID_CREATION.md) - OAuth 2.0 クライアントID作成手順
- [FIREBASE_AUTH_SETUP_COMPLETE.md](./FIREBASE_AUTH_SETUP_COMPLETE.md) - Firebase認証 完全セットアップガイド
- [LOCAL_DEV_GUIDE.md](./LOCAL_DEV_GUIDE.md) - ローカル開発環境セットアップガイド
- [SETUP_STATUS.md](./SETUP_STATUS.md) - 設定状況サマリー

---

## 🎯 まとめ

**現在のエラーの本質**: ログインしていないため、`idToken` と `currentTeamId` が `null`

**解決に必要なステップ**:
1. ✅ バックエンド起動 (完了済み - localhost:8000)
2. ✅ フロントエンド起動 (完了済み - localhost:3000)
3. ❌ OAuth 2.0 クライアントID作成 (要確認)
4. ❌ Firebase Console設定 (要確認)
5. ❌ ログイン実行 (要実行)

**次にやるべきこと**:
👉 **[OAUTH_CLIENT_ID_CREATION.md](./OAUTH_CLIENT_ID_CREATION.md)** を開いて、OAuth設定を完了させてください

---

**最終更新**: 2026-01-01
**作成者**: Claude Code
