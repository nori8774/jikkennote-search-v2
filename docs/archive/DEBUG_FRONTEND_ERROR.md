# フロントエンドエラーのデバッグ手順

## エラー内容
「URL is not valid or contains user credentials.」

## 原因
Vercelの環境変数 `NEXT_PUBLIC_API_URL` が正しく設定されていないか、反映されていません。

## デバッグ手順

### ステップ1: ブラウザの開発者ツールでエラーを確認

1. **ブラウザで F12 キーを押す**
2. **Console タブを開く**
3. エラーメッセージ全体をコピー

### ステップ2: API URLを確認

**Console タブで以下を入力して実行:**

```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
```

期待される結果: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`

もし `undefined` や別の値が表示される場合、環境変数が正しく設定されていません。

### ステップ3: Network タブで確認

1. **Network タブを開く**
2. 「取り込み実行」ボタンをもう一度クリック
3. `/ingest` リクエストを探す
4. リクエストURLを確認

期待される結果: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest`

---

## 解決方法

### 方法1: Vercel環境変数を設定（推奨）

#### 1-1. Vercelダッシュボードにアクセス

以下のURLを開く:
```
https://vercel.com/nori8774/jikkennote-search/settings/environment-variables
```

#### 1-2. 環境変数を追加/更新

既存の `NEXT_PUBLIC_API_URL` を探す：

- **存在する場合**: 編集して値を確認
  - 正しい値: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
  - 間違った値があれば修正

- **存在しない場合**: 新規追加
  - 名前: `NEXT_PUBLIC_API_URL`
  - 値: `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
  - 環境: Production, Preview, Development すべてチェック

#### 1-3. 保存して再デプロイを待つ

- 「Save」をクリック
- 自動的に再デプロイが開始されます
- 数分待ってから再度テスト

### 方法2: 手動で再デプロイ

環境変数を保存後、手動で再デプロイ:

1. Vercel ダッシュボードで Deployments タブを開く
2. 最新のデプロイメントの「...」メニューをクリック
3. 「Redeploy」を選択
4. 完了まで待つ（約1-2分）

### 方法3: ブラウザキャッシュをクリア

環境変数が設定済みの場合、ブラウザキャッシュが原因の可能性:

1. **Chrome/Edge**: Ctrl+Shift+Delete (Windows) / Cmd+Shift+Delete (Mac)
2. 「キャッシュされた画像とファイル」を選択
3. 「データを削除」
4. ページをリロード（Ctrl+R / Cmd+R）

または、**シークレットモード**で開く:
- Chrome/Edge: Ctrl+Shift+N (Windows) / Cmd+Shift+N (Mac)
- https://jikkennote-search.vercel.app にアクセス

---

## 確認チェックリスト

再デプロイ後、以下を確認:

### ✅ 環境変数の確認

Vercel環境変数ページで:
- [ ] `NEXT_PUBLIC_API_URL` が存在する
- [ ] 値が `https://jikkennote-backend-285071263188.asia-northeast1.run.app`
- [ ] Production にチェックが入っている

### ✅ デプロイメントの確認

Vercel Deploymentsページで:
- [ ] 最新のデプロイメントが "Ready" 状態
- [ ] デプロイメント時刻が環境変数保存後

### ✅ フロントエンドの確認

ブラウザで https://jikkennote-search.vercel.app を開いて:
- [ ] F12 → Console で `process.env.NEXT_PUBLIC_API_URL` を実行
- [ ] 正しいURLが表示される
- [ ] 取り込み実行ボタンを押してエラーが出ない

### ✅ バックエンドの確認

念のためバックエンドも確認:

```bash
# ヘルスチェック
curl https://jikkennote-backend-285071263188.asia-northeast1.run.app/health

# 期待される出力:
# {"status":"healthy",...}
```

---

## よくある問題と解決策

### 問題1: 環境変数を設定したのに反映されない

**原因**: 再デプロイが必要
**解決策**: Vercel Deploymentsから手動で再デプロイ

### 問題2: シークレットモードでも同じエラー

**原因**: 環境変数が本当に設定されていない
**解決策**: Vercel環境変数ページを再確認

### 問題3: "Production" にチェックを入れ忘れた

**原因**: 本番環境に環境変数が適用されていない
**解決策**: 環境変数を編集して "Production" にチェック

---

## 追加のデバッグ情報

### フロントエンドのビルドログを確認

Vercel Deploymentsページで:
1. 最新のデプロイメントをクリック
2. 「Building」セクションを展開
3. ビルドログで `NEXT_PUBLIC_API_URL` が表示されているか確認

### バックエンドのログを確認

```bash
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --limit=50
```

---

## まだ解決しない場合

以下の情報を提供してください：

1. ブラウザのConsoleタブのエラー全文
2. ブラウザのNetworkタブで `/ingest` リクエストのURL
3. `process.env.NEXT_PUBLIC_API_URL` の値
4. Vercel環境変数の設定スクリーンショット

これらの情報があれば、より具体的な解決策を提案できます。
