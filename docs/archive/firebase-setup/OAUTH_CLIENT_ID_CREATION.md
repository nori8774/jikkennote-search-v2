# OAuth 2.0 クライアントIDの作成手順

**作成日**: 2026-01-01
**問題**: Google Cloud Consoleに「OAuth 2.0 クライアントID」が表示されていない

---

## 解決方法: OAuth 2.0 クライアントIDを手動で作成

### ステップ1: Google Cloud Consoleにアクセス

1. https://console.cloud.google.com を開く
2. プロジェクト **`jikkennote-search-9e7b9`** を選択

### ステップ2: 同意画面を設定（初回のみ）

OAuth 2.0 クライアントIDを作成する前に、OAuth同意画面の設定が必要です。

1. 左メニューから **「APIとサービス」** → **「OAuth同意画面」** をクリック

2. **User Type（ユーザータイプ）** を選択:
   - **「外部」** を選択（個人開発の場合）
   - 「作成」ボタンをクリック

3. **アプリ情報**を入力:
   - **アプリ名**: `実験ノート検索システム`
   - **ユーザーサポートメール**: `nori8774@gmail.com`（プルダウンから選択）
   - **アプリのロゴ**: （省略可能）
   - **アプリドメイン**: （省略可能）
   - **承認済みドメイン**:
     - `vercel.app` を追加
     - `firebaseapp.com` を追加
   - **デベロッパーの連絡先情報**: `nori8774@gmail.com`

4. **「保存して次へ」** をクリック

5. **スコープ**:
   - デフォルトのまま **「保存して次へ」** をクリック

6. **テストユーザー**:
   - **「ADD USERS」** をクリック
   - `nori8774@gmail.com` を追加
   - **「保存して次へ」** をクリック

7. **概要**:
   - 内容を確認して **「ダッシュボードに戻る」** をクリック

### ステップ3: OAuth 2.0 クライアントIDを作成

1. 左メニューから **「APIとサービス」** → **「認証情報」** をクリック

2. 上部の **「+ 認証情報を作成」** ボタンをクリック

3. **「OAuth クライアント ID」** を選択

4. **アプリケーションの種類** で **「ウェブ アプリケーション」** を選択

5. **名前**を入力:
   ```
   Webクライアント（Firebase用）
   ```

6. **承認済みの JavaScript 生成元**に以下を追加:
   - **「URIを追加」** をクリックして1つずつ追加
   ```
   https://jikkennote-search-v2.vercel.app
   https://jikkennote-search-9e7b9.firebaseapp.com
   http://localhost:3000
   http://localhost:3001
   http://localhost:3003
   ```

7. **承認済みのリダイレクトURI**に以下を追加:
   - **「URIを追加」** をクリックして1つずつ追加
   ```
   https://jikkennote-search-v2.vercel.app/__/auth/handler
   https://jikkennote-search-9e7b9.firebaseapp.com/__/auth/handler
   http://localhost:3000/__/auth/handler
   http://localhost:3001/__/auth/handler
   http://localhost:3003/__/auth/handler
   ```

8. **「作成」** ボタンをクリック

9. **OAuth クライアントが作成されました** ダイアログが表示される:
   - **クライアントID**と**クライアントシークレット**が表示されます
   - **メモ不要**（Firebaseが自動的に使用します）
   - **「OK」** をクリック

### ステップ4: 作成されたクライアントIDを確認

1. 「OAuth 2.0 クライアントID」セクションに、今作成したクライアントIDが表示されます

2. クライアント名: **「Webクライアント（Firebase用）」**

3. 今後設定を変更する場合は、このクライアント名をクリックして編集できます

---

## 重要な注意点

### ❗ リダイレクトURIの形式

- **JavaScript生成元**: `https://example.com`（末尾にスラッシュなし）
- **リダイレクトURI**: `https://example.com/__/auth/handler`（末尾に`/__/auth/handler`）

間違えやすいポイント:
- ❌ `https://example.com/` （末尾のスラッシュは不要）
- ❌ `https://example.com/__/auth/handler/` （末尾のスラッシュは不要）
- ✅ `https://example.com/__/auth/handler` （正しい）

### 📝 設定後の待ち時間

OAuth設定を変更した後、Googleのサーバーに反映されるまで **5〜10分** かかる場合があります。

設定完了後、少し待ってからログインをテストしてください。

---

## 次のステップ

OAuth 2.0 クライアントIDの作成が完了したら、元のガイドに戻って以下を確認してください:

1. ✅ OAuth 2.0 クライアントIDが作成された
2. ✅ 承認済みのリダイレクトURIが正しく設定された
3. ⏭️ `FIREBASE_AUTH_SETUP_COMPLETE.md` のステップ4に進む（Vercelに再デプロイ）

---

## トラブルシューティング

### 「OAuth同意画面」の設定が見つからない

**対処法**:
1. Google Cloud Consoleで正しいプロジェクト（`jikkennote-search-9e7b9`）を選択しているか確認
2. 左メニュー → 「APIとサービス」 → 「OAuth同意画面」をクリック

### 「承認済みドメイン」に追加できない

**対処法**:
1. ドメインの所有権を確認する必要がある場合があります
2. `vercel.app` と `firebaseapp.com` は通常、確認不要です
3. 追加できない場合はスキップして次に進んでください

### クライアントID作成時に「同意画面が未設定」エラー

**対処法**:
1. ステップ2（同意画面の設定）を先に完了してください
2. 同意画面の設定は1回だけ行えば、以降は不要です

---

**最終更新**: 2026-01-01
**関連ドキュメント**: FIREBASE_AUTH_SETUP_COMPLETE.md
