# GitHubアカウントでVercelにログイン

## 問題

Googleアカウント (nori8774@gmail.com) でログインしているため、GitHubから連携したプロジェクトが見つかりません。

## 解決策：GitHubアカウントでログインし直す

### ステップ1: 現在のアカウントからログアウト

1. Vercelを開く: https://vercel.com/
2. 右上のアカウントアイコンをクリック
3. **「Log Out」**をクリック

### ステップ2: GitHubアカウントでログイン

1. https://vercel.com/login にアクセス
2. **「Continue with GitHub」**をクリック
3. GitHubの認証画面が表示される
4. 許可する

### ステップ3: プロジェクトを確認

ログイン後、ダッシュボードで「jikkennote-search」プロジェクトが表示されるはずです。

---

## 環境変数の設定

### ステップ1: プロジェクトを開く

ダッシュボードで「jikkennote-search」をクリック

### ステップ2: Settings → Environment Variables

1. 上部タブの「Settings」をクリック
2. 左サイドバーの「Environment Variables」をクリック

### ステップ3: NEXT_PUBLIC_API_URL を設定

**既に存在する場合:**
1. 「Edit」をクリック
2. 値を以下に変更（コピー&ペースト）:
   ```
   https://jikkennote-backend-285071263188.asia-northeast1.run.app
   ```
3. Environmentは「Production」にチェック
4. 「Save」をクリック

**存在しない場合:**
1. 「Add New」をクリック
2. Name: `NEXT_PUBLIC_API_URL`
3. Value: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
4. Environment: Production にチェック
5. 「Save」をクリック

---

## 再デプロイの確認

### 自動再デプロイを待つ

環境変数を保存すると、自動的に再デプロイが始まります。

1. **Deploymentsタブを開く**
2. 一番上のデプロイメントが「Building」→「Ready」になるまで待つ（1-2分）

### 完了を確認

デプロイメントが「Ready」になったら完了です。

---

## テスト

### ステップ1: 新しいシークレットウィンドウを開く

- **Windows**: Ctrl+Shift+N
- **Mac**: Cmd+Shift+N

### ステップ2: フロントエンドにアクセス

```
https://jikkennote-search.vercel.app
```

### ステップ3: 開発者ツールで確認

F12 → Console:

```javascript
// バックエンドとの接続をテスト
fetch('https://jikkennote-backend-285071263188.asia-northeast1.run.app/health')
  .then(res => res.json())
  .then(data => console.log('✅ Backend:', data))
  .catch(err => console.error('❌ Error:', err));
```

### ステップ4: 取り込みをテスト

1. 設定ページでAPIキーを入力: https://jikkennote-search.vercel.app/settings
2. 取り込みページを開く: https://jikkennote-search.vercel.app/ingest
3. **F12 → Networkタブを開く**
4. ソースフォルダ欄: **空欄**
5. 「取り込み実行」をクリック

**期待される結果:**
- Request URL: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest`（%20なし）
- Status: 200 OK
- Response: 成功メッセージ

---

## トラブルシューティング

### 問題1: GitHubでログインできない

**対処法:**
1. GitHubにログインしているか確認
2. ブラウザのCookieをクリア
3. シークレットモードで試す

### 問題2: プロジェクトが見つからない

**対処法:**
1. 検索ボックスで「jikkennote」を検索
2. アカウント切り替えボタンがあれば、正しいアカウントを選択
3. GitHubリポジトリとの連携を再確認

### 問題3: まだ %20 エラーが出る

**原因:** キャッシュまたは古いビルド

**対処法:**
1. Vercel Deploymentsで最新のデプロイメント時刻を確認
2. 環境変数保存後にデプロイされているか確認
3. 手動で再デプロイ（Deployments → ... → Redeploy）
4. ブラウザのキャッシュをクリア（Ctrl+Shift+Delete）
5. 新しいシークレットウィンドウで開く

---

## 確認チェックリスト

### ✅ ログイン

- [ ] GitHubアカウントでログインしている
- [ ] Vercelダッシュボードで「jikkennote-search」が見える

### ✅ 環境変数

- [ ] `NEXT_PUBLIC_API_URL` が設定されている
- [ ] 値に**スペースがない**
- [ ] Production環境にチェックが入っている

### ✅ デプロイメント

- [ ] 最新のデプロイメントが「Ready」
- [ ] デプロイ時刻が環境変数保存後

### ✅ 動作確認

- [ ] シークレットモードで開いている
- [ ] Console でバックエンドテストが成功
- [ ] Network タブで正しいURL（%20なし）
- [ ] 取り込み実行が成功

---

## 次のステップ

すべてのチェックリストが ✅ になったら:

1. ✅ 検索機能をテスト
2. ✅ ノートビューワーをテスト
3. ✅ 辞書管理をテスト
4. ✅ 評価機能をテスト

システムが正常に動作するはずです！
