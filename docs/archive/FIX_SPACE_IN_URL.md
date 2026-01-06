# URLのスペース問題の修正

## 問題

環境変数のURLに余分なスペースが含まれています：

```
https://jikkennote-backend-285071263188.asia-northeast1.run.app /ingest
                                                              ↑ スペース
```

これが `%20` にエンコードされてエラーになっています。

## 修正手順

### ステップ1: Vercel環境変数を開く

以下のURLにアクセス:
```
https://vercel.com/nori8774/jikkennote-search/settings/environment-variables
```

### ステップ2: NEXT_PUBLIC_API_URL を編集

1. `NEXT_PUBLIC_API_URL` の横にある「Edit」ボタンをクリック

2. **値を確認:**
   - 現在の値に **スペースが入っていないか確認**
   - 特に **末尾のスペース** に注意

3. **正しい値に修正:**
   ```
   https://jikkennote-backend-285071263188.asia-northeast1.run.app
   ```

   **重要:**
   - 先頭にスペースなし
   - 末尾にスペースなし
   - URLの途中にスペースなし

4. **コピー&ペーストを推奨:**

   以下をコピーして貼り付け:
   ```
   https://jikkennote-backend-285071263188.asia-northeast1.run.app
   ```

5. 「Save」をクリック

### ステップ3: 再デプロイを待つ

- 自動的に再デプロイが開始されます
- 1-2分待ってください

### ステップ4: デプロイメント完了を確認

Vercel Deploymentsページを開く:
```
https://vercel.com/nori8774/jikkennote-search/deployments
```

最新のデプロイメントが「Ready」になるまで待つ。

---

## テスト手順

### 1. シークレットモードで開く

- **Windows**: Ctrl+Shift+N
- **Mac**: Cmd+Shift+N

### 2. フロントエンドにアクセス

```
https://jikkennote-search.vercel.app
```

### 3. 開発者ツールで確認

F12 → Console:

```javascript
// 環境変数を確認（スペースがないか）
const apiUrl = 'https://jikkennote-backend-285071263188.asia-northeast1.run.app';
console.log('API URL length:', apiUrl.length);
console.log('API URL:', apiUrl);
console.log('Has trailing space:', apiUrl !== apiUrl.trim());

// テストリクエスト
fetch(`${apiUrl}/health`)
  .then(res => res.json())
  .then(data => console.log('✅ Backend Health:', data))
  .catch(err => console.error('❌ Error:', err));
```

### 4. 取り込みをテスト

1. 設定ページでAPIキーを入力（まだの場合）
2. 取り込みページを開く: https://jikkennote-search.vercel.app/ingest
3. F12 → Networkタブを開く
4. 「取り込み実行」をクリック
5. Networkタブで `/ingest` リクエストを確認

**期待される結果:**
- Request URL: `https://jikkennote-backend-285071263188.asia-northeast1.run.app/ingest` （スペースなし）
- Status: 200 OK

---

## 確認チェックリスト

### ✅ 環境変数

Vercel環境変数ページで:
- [ ] `NEXT_PUBLIC_API_URL` の値に先頭のスペースがない
- [ ] 値に末尾のスペースがない
- [ ] 値が `https://jikkennote-backend-285071263188.asia-northeast1.run.app` のみ
- [ ] Production環境にチェックが入っている

### ✅ デプロイメント

- [ ] 最新のデプロイメントが「Ready」
- [ ] デプロイメント時刻が環境変数保存後

### ✅ 動作確認

- [ ] Console でテストが成功
- [ ] Network タブで正しいURLにリクエストされている（%20なし）
- [ ] 取り込み実行が成功

---

## よくある間違い

### ❌ 間違い1: コピペ時にスペースが入る

```
https://jikkennote-backend-285071263188.asia-northeast1.run.app
                                                              ↑ 末尾にスペース
```

### ❌ 間違い2: 手入力でタイプミス

手入力は避けて、必ずコピー&ペーストしてください。

### ❌ 間違い3: 改行が含まれる

複数行にわたってペーストした場合、改行文字が入ることがあります。

---

## 正しい設定の例

Vercel環境変数:

| 名前 | 値 | 環境 |
|------|-----|------|
| NEXT_PUBLIC_API_URL | https://jikkennote-backend-285071263188.asia-northeast1.run.app | Production ✓ |

**値の文字数:** 72文字

---

修正後、もう一度テストしてください！
