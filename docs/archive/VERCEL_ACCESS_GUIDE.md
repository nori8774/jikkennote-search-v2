# Vercel ダッシュボードへのアクセス手順

## ステップ1: Vercelダッシュボードを開く

以下のURLにアクセス:
```
https://vercel.com/dashboard
```

ログイン済みなので、プロジェクト一覧が表示されるはずです。

## ステップ2: jikkennote-search プロジェクトを探す

ダッシュボードで「jikkennote-search」プロジェクトを探してクリック。

**見つからない場合:**
- 画面上部の検索ボックスで「jikkennote」と検索
- または、すべてのプロジェクトをスクロールして探す

## ステップ3: プロジェクト設定を開く

プロジェクトページが開いたら:

1. **上部のタブから「Settings」をクリック**
2. **左サイドバーから「Environment Variables」をクリック**

## ステップ4: 環境変数を確認・編集

`NEXT_PUBLIC_API_URL` を探して:

1. **値を確認** - スペースが含まれていないか
2. **Editボタンをクリック**
3. **値を修正:**
   ```
   https://jikkennote-backend-285071263188.asia-northeast1.run.app
   ```
4. **Saveをクリック**

---

## 別の方法: vercel.json から確認

ローカルのターミナルで、vercel.json を確認:

```bash
cat /Users/nori8774/jikkennote-search/frontend/vercel.json
```

もし `NEXT_PUBLIC_API_URL` が設定されていれば、そこを修正することもできます。

---

## まだ404が出る場合

### 確認1: プロジェクト名を確認

```bash
# frontend ディレクトリに移動
cd /Users/nori8774/jikkennote-search/frontend

# package.json のプロジェクト名を確認
cat package.json | grep name
```

### 確認2: Vercelにログインしているか確認

ブラウザで:
```
https://vercel.com/
```

右上のアイコンをクリックして、ログイン状態を確認。

---

## トラブルシューティング

### 問題1: プロジェクトが見つからない

**原因**: 別のアカウントでデプロイされている可能性

**対処法**:
1. ブラウザで https://jikkennote-search.vercel.app にアクセス
2. ページ下部の「Deployed by Vercel」をクリック
3. デプロイ情報ページが開く
4. そこから設定ページにアクセス

### 問題2: 権限がない

**原因**: 別のアカウントがオーナー

**対処法**: プロジェクトのオーナーに連絡して、環境変数を設定してもらう

---

## 最も簡単な方法

以下のURLを順番に試してください:

```
https://vercel.com/dashboard
```

↓ プロジェクトをクリック後

```
Settings → Environment Variables
```

それでもダメなら、次のステップに進みましょう。
