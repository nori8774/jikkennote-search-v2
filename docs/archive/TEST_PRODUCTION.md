# 本番環境テスト手順

## 1. 最新デプロイメントの確認

Vercelで新しいデプロイメントが作成されたようです。

### 確認方法

1. **Vercel Deploymentsページを開く:**
   ```
   https://vercel.com/nori8774/jikkennote-search/deployments
   ```

2. **最上位のデプロイメントを確認:**
   - ステータスが「Ready」になっているか
   - デプロイ時刻が最新か
   - 環境が「Production」か

---

## 2. フロントエンドのテスト

### ステップ1: シークレットモードで開く

**キャッシュの影響を避けるため、必ずシークレットモードで開いてください:**

- Chrome/Edge: **Ctrl+Shift+N** (Windows) / **Cmd+Shift+N** (Mac)
- Firefox: **Ctrl+Shift+P** (Windows) / **Cmd+Shift+P** (Mac)

### ステップ2: フロントエンドにアクセス

```
https://jikkennote-search.vercel.app
```

### ステップ3: 開発者ツールで環境変数を確認

1. **F12キーを押す**
2. **Consoleタブを開く**
3. **以下を入力して Enter:**

```javascript
// API URLを確認
console.log('API_URL:', window.location.origin)

// 次に、実際のAPIをテスト
fetch('https://jikkennote-backend-285071263188.asia-northeast1.run.app/health')
  .then(res => res.json())
  .then(data => console.log('Backend Health:', data))
  .catch(err => console.error('Backend Error:', err))
```

**期待される出力:**
```
Backend Health: {status: "healthy", message: "Server is running", version: "2.0.0", ...}
```

---

## 3. APIキーの設定

### ステップ1: 設定ページを開く

```
https://jikkennote-search.vercel.app/settings
```

### ステップ2: APIキーを入力

1. **OpenAI API Key** を入力
2. **Cohere API Key** を入力
3. 「保存」をクリック

### ステップ3: 保存を確認

Consoleで確認:
```javascript
// localStorageを確認
console.log('OpenAI Key exists:', !!localStorage.getItem('openai_api_key'))
console.log('Cohere Key exists:', !!localStorage.getItem('cohere_api_key'))
```

---

## 4. ノート取り込みのテスト

### ステップ1: GCS上のファイルを確認

ローカルのターミナルで:
```bash
# ファイル一覧を表示
gsutil ls gs://jikkennote-storage/notes/new/
```

**ファイルがあることを確認してください。**

### ステップ2: 取り込みページを開く

```
https://jikkennote-search.vercel.app/ingest
```

### ステップ3: 開発者ツールのNetworkタブを開く

1. **F12キー → Networkタブ**
2. 「Preserve log」にチェック（リクエストを保持）

### ステップ4: 取り込み実行

1. ソースフォルダ欄: **空欄のまま**
2. 取り込み後のアクション: **ファイルを残す**
3. 「取り込み実行」ボタンをクリック

### ステップ5: Networkタブで確認

**`/ingest` リクエストを探す:**

- **リクエストURL**: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest`
- **Method**: POST
- **Status**: 200 (成功の場合)

**失敗した場合:**
- Status Code を確認（400, 404, 500など）
- Responseタブでエラーメッセージを確認

### ステップ6: Consoleタブでエラーを確認

エラーが出た場合、Consoleタブに詳細が表示されます。

---

## 5. エラーパターンと対処法

### エラー1: `Failed to fetch`

**原因**: CORSエラーまたはバックエンドがダウン

**対処法:**
```bash
# バックエンドのヘルスチェック
curl https://jikkennote-backend-285071263188.asia-northeast1.run.app/health

# CORS設定を確認
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --format="value(spec.template.spec.containers[0].env)" | grep CORS
```

### エラー2: `URL is not valid or contains user credentials`

**原因**: 環境変数が反映されていない

**対処法:**

Consoleで確認:
```javascript
// フロントエンドのコードを直接確認
fetch('https://jikkennote-backend-285071263188.asia-northeast1.run.app/health')
  .then(res => res.json())
  .then(data => console.log('Direct fetch works:', data))
```

これが成功する場合、フロントエンドコードの問題ではなく、ビルド時の環境変数の問題です。

### エラー3: `OpenAI APIキーが設定されていません`

**原因**: localStorageにAPIキーが保存されていない

**対処法:**
1. 設定ページでAPIキーを再入力
2. 保存後、localStorageを確認（上記参照）

### エラー4: `404 Not Found`

**原因**: バックエンドのエンドポイントが存在しない

**対処法:**
```bash
# バックエンドのエンドポイント一覧を確認
curl https://jikkennote-backend-285071263188.asia-northeast1.run.app/
```

---

## 6. 成功時の挙動

取り込みが成功すると:

1. **成功メッセージが表示される**
   - 「〇件の新規ノートを取り込みました」

2. **取り込み結果が表示される**
   - 新規取り込み: ノートIDのリスト
   - スキップ: 既存のノートIDのリスト

3. **新出単語分析の確認ダイアログ**
   - 「新出単語の分析を実行しますか？」
   - 「はい」をクリックすると分析開始

---

## 7. 完全な動作確認チェックリスト

### ✅ デプロイメント
- [ ] Vercel Deploymentsで最新が「Ready」
- [ ] Production環境にデプロイされている

### ✅ 環境変数
- [ ] Vercel環境変数に `NEXT_PUBLIC_API_URL` が設定されている
- [ ] Production環境にチェックが入っている

### ✅ バックエンド
- [ ] ヘルスチェックが成功する
- [ ] CORS設定にVercel URLが含まれている

### ✅ フロントエンド
- [ ] シークレットモードで開ける
- [ ] Consoleでバックエンドとの通信が成功する
- [ ] APIキーが保存されている

### ✅ GCS
- [ ] ノートファイルがアップロードされている
- [ ] `gsutil ls` でファイルが見える

### ✅ 取り込み機能
- [ ] 取り込み実行でエラーが出ない
- [ ] 成功メッセージが表示される
- [ ] 取り込み結果が表示される

### ✅ 検索機能
- [ ] 検索ページで検索できる
- [ ] 検索結果が表示される

---

## 次のステップ

すべてのチェックリストが ✅ になったら、システムが正常に動作しています！

1. 検索機能をテスト
2. ノートビューワーをテスト
3. 辞書管理機能をテスト
4. 評価機能をテスト

問題が発生した場合は、エラーメッセージとConsole/Networkタブの情報を提供してください。
