# "Load failed" エラーのデバッグ

## ステップ1: Networkタブで詳細を確認

**F12 → Networkタブ**を開いて、以下を確認してください：

### 確認1: リクエストURL

`/ingest` リクエストをクリックして確認:

- **Request URL**: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest`
  - ✅ `%20` が含まれていない → 環境変数は正しい
  - ❌ `%20` が含まれている → 環境変数がまだ反映されていない

### 確認2: Status Code

- **Status**: 何が表示されていますか？
  - `(failed)` → ネットワークエラー、CORS、または接続失敗
  - `404` → エンドポイントが存在しない
  - `500` → バックエンドのエラー
  - `400` または `422` → リクエストの形式が間違っている

### 確認3: Consoleタブのエラー

**Consoleタブ**に赤いエラーメッセージがありますか？

よくあるエラー:
- `Access to fetch at ... has been blocked by CORS policy` → CORSエラー
- `Failed to fetch` → ネットワークエラー
- `OpenAI APIキーが設定されていません` → APIキーエラー

---

## よくある原因と解決策

### 原因1: CORSエラー

**症状:**
- Consoleに「CORS policy」エラー
- Networkタブで Status が `(failed)`

**確認方法:**

ローカルのターミナルで:
```bash
# バックエンドのCORS設定を確認
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --format="value(spec.template.spec.containers[0].env)" | grep CORS
```

**期待される出力:**
```
CORS_ORIGINS=https://jikkennote-search.vercel.app,http://localhost:3000
```

**修正方法:**

```bash
# CORS設定を更新
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --update-env-vars="CORS_ORIGINS=https://jikkennote-search.vercel.app,http://localhost:3000" \
    --project=jikkennote-search
```

### 原因2: APIキーが設定されていない

**症状:**
- Consoleに「OpenAI APIキーが設定されていません」エラー

**解決方法:**

1. https://jikkennote-search.vercel.app/settings を開く
2. **OpenAI API Key** を入力
3. **Cohere API Key** を入力
4. 「保存」をクリック

**確認:**

Consoleで:
```javascript
console.log('OpenAI Key:', !!localStorage.getItem('openai_api_key'));
console.log('Cohere Key:', !!localStorage.getItem('cohere_api_key'));
```

両方とも `true` になるはずです。

### 原因3: バックエンドがダウンしている

**症状:**
- Status が `(failed)` または `502`, `503`

**確認方法:**

ローカルのターミナルで:
```bash
# バックエンドのヘルスチェック
curl https://jikkennote-backend-285071263188.asia-northeast1.run.app/health
```

**期待される出力:**
```json
{"status":"healthy","message":"Server is running","version":"2.0.0",...}
```

**エラーが出る場合:**

バックエンドのログを確認:
```bash
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --limit=50
```

### 原因4: リクエストボディが間違っている

**症状:**
- Status が `400` または `422`

**確認方法:**

Networkタブで `/ingest` リクエストをクリック:
1. **Payload** タブを開く
2. リクエストボディを確認

**期待される形式:**
```json
{
  "openai_api_key": "sk-...",
  "source_folder": "",
  "post_action": "keep",
  "archive_folder": "",
  "embedding_model": "text-embedding-3-small"
}
```

---

## デバッグ用のテストリクエスト

Consoleで以下を実行して、直接テスト:

```javascript
// テスト1: バックエンドのヘルスチェック
fetch('https://jikkennote-backend-285071263188.asia-northeast1.run.app/health')
  .then(res => res.json())
  .then(data => console.log('✅ Health OK:', data))
  .catch(err => console.error('❌ Health failed:', err));

// テスト2: APIキーを確認
const openaiKey = localStorage.getItem('openai_api_key');
const cohereKey = localStorage.getItem('cohere_api_key');
console.log('OpenAI Key exists:', !!openaiKey);
console.log('Cohere Key exists:', !!cohereKey);

// テスト3: Ingest APIをテスト（APIキーが設定されている場合）
if (openaiKey) {
  fetch('https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      openai_api_key: openaiKey,
      source_folder: '',
      post_action: 'keep',
      archive_folder: '',
      embedding_model: 'text-embedding-3-small'
    })
  })
  .then(res => res.json())
  .then(data => console.log('✅ Ingest OK:', data))
  .catch(err => console.error('❌ Ingest failed:', err));
}
```

---

## 報告してください

以下の情報を教えてください：

### 1. Networkタブの情報

- **Request URL**: （完全なURL）
- **Status**: （200, 404, 500, (failed) など）
- **%20が含まれているか**: はい/いいえ

### 2. Consoleタブのエラー

赤いエラーメッセージをコピペしてください。

### 3. ヘルスチェックの結果

ローカルのターミナルで実行:
```bash
curl https://jikkennote-backend-285071263188.asia-northeast1.run.app/health
```

結果をコピペしてください。

### 4. APIキーの設定状況

- OpenAI API Keyを設定済み: はい/いいえ
- Cohere API Keyを設定済み: はい/いいえ

---

これらの情報があれば、具体的な解決策を提示できます！
