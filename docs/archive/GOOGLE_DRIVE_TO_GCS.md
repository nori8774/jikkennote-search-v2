# Google Drive から GCS への移行ガイド

## 現在の問題

「URL is not valid or contains user credentials.」エラーが発生する理由：

**Google Driveは現在サポートされていません**

- ❌ Google Drive: `https://drive.google.com/drive/folders/...`
- ✅ Google Cloud Storage (GCS): `gs://jikkennote-storage/notes/new/`

本システムはGoogle Cloud Storage (GCS)を使用するように設計されています。

## 解決策：Google DriveからGCSへファイルをコピー

### 方法1: 手動でダウンロード→アップロード

#### ステップ1: Google Driveからダウンロード

1. Google Driveのフォルダにアクセス:
   ```
   https://drive.google.com/drive/folders/1TX1Kx8kRiVnGXIzAkg6zIM9-l2XO8mjX
   ```

2. すべてのファイルを選択してダウンロード
   - ブラウザで右クリック → 「ダウンロード」
   - または、全選択（Ctrl+A / Cmd+A）→ 右クリック → ダウンロード

3. ZIPファイルを展開

#### ステップ2: GCSにアップロード

ローカルにダウンロードしたファイルをGCSにアップロード:

```bash
# ファイルを1つアップロード
gsutil cp /path/to/your/note.md gs://jikkennote-storage/notes/new/

# フォルダごとアップロード
gsutil -m cp -r /path/to/your/notes/* gs://jikkennote-storage/notes/new/
```

### 方法2: Google Drive API経由（高度な方法）

将来的にGoogle Driveサポートを追加する場合の参考情報です。

#### 必要な手順

1. Google Cloud Consoleで Drive APIを有効化
2. サービスアカウントを作成
3. Google Driveフォルダをサービスアカウントと共有
4. バックエンドコードにGoogle Drive連携を追加

**注意**: 現時点では実装されていません。

---

## GCSの使い方（本番環境）

### 1. ファイルのアップロード

実験ノートをGCSにアップロード:

```bash
# 単一ファイル
gsutil cp ID3-14.md gs://jikkennote-storage/notes/new/

# 複数ファイル
gsutil -m cp *.md gs://jikkennote-storage/notes/new/

# フォルダごと
gsutil -m cp -r ./my_notes/* gs://jikkennote-storage/notes/new/
```

### 2. GCS上のファイルを確認

```bash
# ファイル一覧を表示
gsutil ls gs://jikkennote-storage/notes/new/

# 詳細表示
gsutil ls -l gs://jikkennote-storage/notes/new/
```

### 3. フロントエンドから取り込み

1. https://jikkennote-search.vercel.app にアクセス
2. 「ノート取り込み」ページを開く
3. **ソースフォルダ欄は空欄のまま**（デフォルトで `notes/new` が使われます）
4. 「取り込み実行」をクリック

### 4. フォルダパスの指定方法

フロントエンドでフォルダパスを指定する場合：

- ✅ 正しい: `notes/new` （GCS上のパス）
- ✅ 正しい: `notes/custom_folder`
- ❌ 間違い: `https://drive.google.com/...` （Google Drive URL）
- ❌ 間違い: `gs://jikkennote-storage/notes/new` （gs://プレフィックスは不要）
- ❌ 間違い: `/Users/...` （ローカルパス、本番環境では使えません）

---

## トラブルシューティング

### エラー: URL is not valid or contains user credentials

**原因**: Google DriveのURLまたは不正なパスを指定している

**解決策**:
1. ソースフォルダ欄を**空欄**にする（推奨）
2. または、GCS上のパスを指定: `notes/new`

### エラー: No files found

**原因**: GCSにファイルがアップロードされていない

**解決策**:
```bash
# ファイルがあるか確認
gsutil ls gs://jikkennote-storage/notes/new/

# なければアップロード
gsutil cp your_note.md gs://jikkennote-storage/notes/new/
```

### エラー: OpenAI APIキーが設定されていません

**解決策**:
1. 設定ページを開く
2. OpenAI API Keyを入力
3. 保存

---

## サンプルワークフロー

### 完全な取り込みフロー

```bash
# 1. ローカルで実験ノートを作成
echo "# 実験ノート ID3-15

## 目的
新規材料の合成

## 材料
- NaOH: 10g
- エタノール: 50mL

## 方法
1. NaOHを溶解
2. 加熱還流
" > ID3-15.md

# 2. GCSにアップロード
gsutil cp ID3-15.md gs://jikkennote-storage/notes/new/

# 3. 確認
gsutil ls gs://jikkennote-storage/notes/new/

# 4. フロントエンドで取り込み実行
# → https://jikkennote-search.vercel.app/ingest
# → ソースフォルダ欄は空欄
# → 「取り込み実行」をクリック
```

---

## よくある質問

### Q: Google Driveを使い続けたいのですが？

A: 現在、Google Driveの直接サポートはありません。以下の方法があります：
1. Google DriveからダウンロードしてGCSにアップロード（推奨）
2. ローカル環境でのみ使用（`STORAGE_TYPE=local`で起動）
3. Google Drive APIサポートの追加実装をリクエスト

### Q: ローカル環境で Google Drive を使えますか？

A: ローカル環境であれば、Google Driveのファイルをローカルにダウンロードして使用できます：

```bash
# ローカル環境での起動（backend）
cd backend
STORAGE_TYPE=local python server.py
```

フロントエンドのソースフォルダに:
```
/Users/your_name/Google Drive/実験ノート/
```

### Q: GCSの料金は？

A: GCSの料金（アジア地域）:
- **ストレージ**: 約$0.02/GB/月
- **操作**: 読み取り $0.004/10,000回
- **データ転送**: 国内なら無料（同一リージョン）

実験ノート（100ファイル、各10KB）の場合:
- ストレージ: 1MB = **約$0.00002/月**（ほぼ無料）

---

## 次のステップ

1. ✅ Google DriveからファイルをダウンロードGCSにアップロード
2. ✅ フロントエンドで取り込み実行（ソースフォルダ欄は空欄）
3. ✅ 検索機能をテスト

質問があれば遠慮なくお尋ねください！
