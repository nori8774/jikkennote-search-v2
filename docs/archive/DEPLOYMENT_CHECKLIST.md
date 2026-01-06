# デプロイチェックリスト（マルチテナント対応版）

## 事前準備

### 1. ローカル環境の確認

- [ ] バックエンドがローカルで正常に動作している
- [ ] フロントエンドがローカルで正常に動作している
- [ ] マルチテナント機能（チーム作成・参加）が動作している
- [ ] ノート取り込みが各チームで独立して動作している

### 2. Google Cloudの設定確認

```bash
# プロジェクトIDの確認
gcloud config get-value project
# 期待値: jikkennote-search

# GCSバケットの確認
gsutil ls gs://jikkennote-storage
# 期待値: master_dictionary.yaml, chroma_db/, notes/ が表示される

# Dockerが起動しているか確認
docker ps
# エラーが出なければOK
```

### 3. Firebase設定の確認

- [ ] Firebase Consoleでプロジェクトが有効になっている
- [ ] Firebase Authentication（Google認証）が有効になっている
- [ ] Firestore Databaseが有効になっている

## デプロイ手順

### ステップ1: 初回セットアップ（初回のみ）

```bash
cd /Users/nori8774/jikkennote-search_v1
./DEPLOY_SETUP.sh
```

**確認事項**:
- [ ] サービスアカウント `jikkennote-backend@jikkennote-search.iam.gserviceaccount.com` が作成された
- [ ] GCS権限が付与された
- [ ] Firestore権限が付与された
- [ ] Firebase権限が付与された
- [ ] Artifact Registryリポジトリが作成された

### ステップ2: バックエンドのデプロイ

```bash
cd /Users/nori8774/jikkennote-search_v1
./DEPLOY_CONTINUE.sh
```

**所要時間**: 約5-10分

**確認事項**:
- [ ] Dockerイメージのビルドが成功
- [ ] Artifact Registryへのプッシュが成功
- [ ] Cloud Runへのデプロイが成功
- [ ] ヘルスチェックが成功（`/health` エンドポイントが200を返す）

デプロイ後、バックエンドURLをメモ:
```
バックエンドURL: https://jikkennote-backend-XXXXXXXXXX-an.a.run.app
```

### ステップ3: フロントエンドのデプロイ（Vercel）

#### 3-1. Vercelプロジェクトの作成（初回のみ）

1. https://vercel.com/ にアクセス
2. GitHubアカウントでログイン
3. 「Add New Project」をクリック
4. リポジトリを選択（または新規インポート）
5. プロジェクト設定:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`（デフォルト）
   - **Output Directory**: `.next`（デフォルト）

#### 3-2. 環境変数の設定

Vercelの「Settings」→「Environment Variables」で以下を設定:

| Variable Name | Value | Environment |
|---------------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://jikkennote-backend-XXXXXXXXXX-an.a.run.app` | Production |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase ConsoleのAPIキー | Production |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | `jikkennote-search.firebaseapp.com` | Production |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | `jikkennote-search` | Production |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | `jikkennote-search.appspot.com` | Production |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase ConsoleのSender ID | Production |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase ConsoleのApp ID | Production |

**Firebase設定の取得方法**:
1. Firebase Console (https://console.firebase.google.com/) を開く
2. プロジェクト「jikkennote-search」を選択
3. プロジェクト設定（歯車アイコン）→「全般」タブ
4. 「マイアプリ」セクションでWebアプリの設定を確認

#### 3-3. デプロイ実行

1. Vercelで「Deploy」をクリック
2. デプロイ完了を待つ（約2-3分）
3. デプロイされたURLをメモ:
   ```
   フロントエンドURL: https://YOUR-PROJECT.vercel.app
   ```

### ステップ4: CORSの更新

フロントエンドのデプロイ後、バックエンドのCORS設定を更新:

```bash
cd /Users/nori8774/jikkennote-search_v1

# VercelのURLを環境変数に設定
export VERCEL_URL="https://YOUR-PROJECT.vercel.app"

# CORS設定を更新
gcloud run services update jikkennote-backend \
    --region=asia-northeast1 \
    --update-env-vars="CORS_ORIGINS=${VERCEL_URL},http://localhost:3000" \
    --project=jikkennote-search
```

**確認事項**:
- [ ] CORS更新が成功
- [ ] フロントエンドからバックエンドへのリクエストが成功

## 動作確認

### 1. 基本動作の確認

1. **フロントエンドにアクセス**: https://YOUR-PROJECT.vercel.app
2. **ログイン**: Googleアカウントでログイン
3. **チーム作成**: 新しいチームを作成
4. **ノートアップロード**: テストノートをアップロード
5. **ノート取り込み**: 取り込みが成功することを確認
6. **検索**: 取り込んだノートが検索できることを確認

### 2. マルチテナント機能の確認

1. **別のチームを作成**: 2つ目のチームを作成
2. **異なるノートをアップロード**: チームごとに異なるノートを取り込み
3. **データ分離の確認**: 各チームで他のチームのノートが表示されないことを確認

### 3. GCS連携の確認

```bash
# GCSにチームデータが保存されているか確認
gsutil ls -r gs://jikkennote-storage/teams/

# 期待される出力:
# gs://jikkennote-storage/teams/{team_id_1}/
# gs://jikkennote-storage/teams/{team_id_1}/chroma-db/
# gs://jikkennote-storage/teams/{team_id_1}/notes/
# gs://jikkennote-storage/teams/{team_id_2}/
# ...
```

## トラブルシューティング

### バックエンドのログ確認

```bash
gcloud run services logs read jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search \
    --limit=100
```

### サービスの詳細確認

```bash
gcloud run services describe jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search
```

### よくあるエラー

#### 1. 403 Forbidden (GCS)
**原因**: サービスアカウントに権限がない
**解決**: `DEPLOY_SETUP.sh`を再実行

#### 2. 401 Unauthorized (Firebase)
**原因**: Firebase設定が正しくない
**解決**:
- サービスアカウントにFirebase Admin権限があるか確認
- Firebase Consoleでプロジェクトが有効か確認

#### 3. CORS Error
**原因**: CORS設定が正しくない
**解決**: ステップ4のCORS更新を実行

## ロールバック手順

問題が発生した場合:

```bash
# 以前のリビジョンにロールバック
gcloud run services update-traffic jikkennote-backend \
    --to-revisions=REVISION_NAME=100 \
    --region=asia-northeast1 \
    --project=jikkennote-search

# リビジョン一覧の確認
gcloud run revisions list \
    --service=jikkennote-backend \
    --region=asia-northeast1 \
    --project=jikkennote-search
```

## デプロイ後の確認事項

- [ ] フロントエンドでログインできる
- [ ] チームが作成できる
- [ ] ノートがアップロードできる
- [ ] ノートが取り込める
- [ ] 検索が動作する
- [ ] 各チームのデータが分離されている
- [ ] GCSにデータが保存されている
- [ ] バックエンドログにエラーがない

## 完了！

すべてのチェック項目が完了したら、デプロイ成功です！ 🎉

---

**デプロイ日時**: _______________
**デプロイ担当**: _______________
**バックエンドURL**: _______________
**フロントエンドURL**: _______________
