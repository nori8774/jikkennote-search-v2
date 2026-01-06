# プロジェクトメモリ - 実験ノート検索システム v2 (簡素化版)

## 技術スタック

### フロントエンド
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x
- **UI Library**: React 19
- **Styling**: Tailwind CSS 3.x
- **Markdown Rendering**: React Markdown 9.x
- **Testing**: Playwright 1.x (E2E)
- **Package Manager**: npm

### バックエンド
- **Language**: Python 3.12+
- **Web Framework**: FastAPI 0.115+
- **LLM Orchestration**: LangChain 0.3.13+, LangGraph 0.2.62+
- **Vector Database**: ChromaDB 0.6.3+
- **Embeddings**: OpenAI SDK 1.59+
- **Reranking**: Cohere SDK 5.14+
- **Data Validation**: Pydantic 2.x
- **Config Management**: PyYAML 6.0+

### インフラ
- **Frontend Hosting**: Vercel
- **Backend**: Google Cloud Run (コンテナ)
- **Storage**: Google Cloud Storage (GCS)
- **Database**: ChromaDB (永続化 on GCS)
- **Container**: Docker

---

## プロジェクト構造

### ディレクトリ構成

```
jikkennote-search/
├── .claude/                 # Claude Code開発環境設定
│   ├── agents/             # サブエージェント定義
│   ├── commands/           # カスタムコマンド（add-feature, review-docsなど）
│   ├── skills/             # スキル定義（steering, prd-writing等）
│   └── settings.json       # Claude Code設定
│
├── .steering/              # 作業単位ドキュメント
│   └── [日付]-[機能名]/   # 機能ごとのフォルダ
│       ├── requirements.md # 要件定義
│       ├── design.md       # 設計書
│       └── tasklist.md     # タスクリスト
│
├── frontend/                # Next.js フロントエンド
│   ├── app/                # App Router ページ
│   │   ├── page.tsx       # ホーム（ランディング）
│   │   ├── search/        # 検索ページ
│   │   ├── viewer/        # ノートビューワー
│   │   ├── ingest/        # ノート取り込み
│   │   ├── evaluate/      # RAG評価
│   │   └── settings/      # 設定（APIキー、モデル、プロンプト）
│   ├── components/        # 共通コンポーネント（予定）
│   ├── lib/              # ユーティリティ（予定）
│   ├── tests/            # E2Eテスト
│   └── package.json      # 依存関係
│
├── backend/              # FastAPI バックエンド
│   ├── server.py        # メインAPIサーバー
│   ├── agent.py         # LangGraph ワークフロー
│   ├── ingest.py        # ノート取り込みロジック
│   ├── utils.py         # ユーティリティ関数
│   ├── chroma_sync.py   # ChromaDB管理
│   ├── storage.py       # ストレージ抽象化（ローカル/GCS）
│   ├── prompt_manager.py # プロンプト管理
│   ├── config.py        # 設定管理
│   ├── master_dictionary.yaml # 正規化辞書
│   ├── chroma_db_config.json  # ChromaDB設定
│   ├── saved_prompts/   # 保存されたプロンプト（YAML）⭐ v3.0: prompts/から名称変更
│   └── requirements.txt # Python依存関係
│
├── docs/                # ドキュメント
│   ├── ideas/          # 初期要件、アイデアメモ
│   │   ├── initial-requirements.md
│   │   ├── v1-improvements.md
│   │   └── brainstorm-*.md
│   ├── archive/        # アーカイブされた旧ドキュメント
│   ├── product-requirements.md    # プロダクト要求定義書
│   ├── functional-design.md       # 機能設計書
│   ├── architecture.md            # 技術仕様書
│   ├── api-specification.md       # API仕様書
│   ├── repository-structure.md    # リポジトリ構造定義書
│   ├── development-guidelines.md  # 開発ガイドライン
│   └── glossary.md               # ユビキタス言語定義
│
├── CLAUDE.md           # このファイル（プロジェクトメモリ）
├── README.md           # プロジェクト概要
├── DEPLOYMENT.md       # デプロイ手順書
├── USER_MANUAL.md      # ユーザーマニュアル
└── PRODUCTION_TEST_CHECKLIST.md  # テストチェックリスト
```

---

## 開発プロセス

### 基本フロー

1. **ドキュメント確認**: 永続ドキュメント(`docs/`)で「何を作るか」を確認
2. **実装**: 機能要件に基づいて実装
3. **テスト**: E2Eテスト（Playwright）、APIテスト（手動）
4. **デプロイ**: Vercel（フロント）、Google Cloud Run（バックエンド）
5. **更新**: 必要に応じてドキュメント更新

### 重要なルール

#### 実装前の確認

新しい実装を始める前に、必ず以下を確認:

1. このCLAUDE.mdを読む
2. 関連する永続ドキュメント(`docs/`)を読む
3. `.steering/`配下の関連する作業単位ドキュメントを確認
4. Grepで既存の類似実装を検索
5. 既存パターンを理解してから実装開始

#### コーディング規約

**TypeScript**:
- 厳密な型定義（`strict: true`）
- 関数型プログラミング推奨
- Async/Await 使用
- 命名: camelCase（関数・変数）、PascalCase（コンポーネント・型）

**Python**:
- PEP 8 準拠
- Type hints 必須
- Docstring 記述
- 命名: snake_case（関数・変数）、PascalCase（クラス）

#### Git コミットメッセージ

```
<type>: <subject>

<body>

<footer>
```

**Type**:
- `Feat`: 新機能
- `Fix`: バグ修正
- `Docs`: ドキュメント
- `Style`: フォーマット
- `Refactor`: リファクタリング
- `Test`: テスト
- `Chore`: ビルド、ツール変更

---

## 作業単位ドキュメント管理

### .steeringディレクトリ

機能追加や改善作業ごとに、`.steering/[日付]-[機能名]/`配下に作業単位のドキュメントを作成します。

**ディレクトリ構成**:
```
.steering/
└── 20251230-Google-Drive統合/
    ├── requirements.md   # 要件定義（機能の目的、スコープ、制約）
    ├── design.md         # 設計書（データフロー、API設計、UI設計）
    └── tasklist.md       # タスクリスト（実装すべきタスクの一覧、チェックボックス付き）
```

**命名規則**:
- ディレクトリ名: `YYYYMMDD-[機能名]`（例: `20251230-Google-Drive統合`）
- ファイル名: 固定（`requirements.md`, `design.md`, `tasklist.md`）

**運用ルール**:

1. **作業開始時**:
   - `/add-feature [機能名]`コマンドを実行
   - ステアリングファイル3点が自動生成される
   - `requirements.md`: 機能の目的、制約、成功基準を記載
   - `design.md`: データフロー、API設計、UI設計を記載
   - `tasklist.md`: 実装すべきタスクをチェックボックス形式で記載

2. **実装中**:
   - `tasklist.md`の先頭から順にタスクを実施
   - 完了したタスクに`[x]`をマークする
   - タスクが大きすぎる場合はサブタスクに分割
   - 技術的理由でタスクが不要になった場合は理由を明記してスキップ

3. **実装完了後**:
   - 全タスク完了を確認
   - `tasklist.md`に振り返りを記載（実装完了日、計画と実績の差分、学んだこと）
   - 必要に応じて永続ドキュメント(`docs/`)を更新

**steeringスキルとの連携**:
- `.claude/skills/steering/SKILL.md`を参照
- **計画モード**: ステアリングファイル生成時に使用
- **実装モード**: tasklist.mdに従った実装時に使用
- **振り返りモード**: 実装完了後の記録時に使用

**テンプレート**:
- `.claude/skills/steering/templates/requirements.md`
- `.claude/skills/steering/templates/design.md`
- `.claude/skills/steering/templates/tasklist.md`

詳細なワークフローは `.claude/commands/add-feature.md` を参照。

---

## データ管理戦略

### ストレージ構成

#### ローカル開発環境

```
backend/
├── notes/
│   ├── new/         # 新規ノート
│   └── processed/   # 取り込み済みノート（削除しない）⭐ v3.0: archived/から名称変更
├── chroma_db/       # ChromaDB永続化
├── saved_prompts/   # プロンプトYAML ⭐ v3.0: prompts/から名称変更
└── master_dictionary.yaml  # 正規化辞書
```

#### 本番環境（GCS）

```
gs://jikkennote-storage/
└── teams/           # v3.0: マルチテナント対応
    └── {team_id}/
        ├── chroma-db/       # ChromaDB永続化
        ├── notes/
        │   ├── new/
        │   └── processed/   # v3.0: archived/から名称変更
        ├── saved_prompts/   # v3.0: prompts/から名称変更
        └── dictionary.yaml
```

### データフロー

#### 検索フロー

```
User Input (目的・材料・方法・重点指示)
  ↓
Frontend (Search Page) → API Request
  ↓
Backend (/search)
  ├─→ Normalize Node (utils.py: 材料名正規化)
  ├─→ Query Generation Node (agent.py: 3視点クエリ生成)
  ├─→ Search Node (ChromaDB検索 + Cohere Reranking)
  └─→ Compare Node (上位3件の比較分析)
  ↓
SearchResponse (retrieved_docs: Markdown[] )
  ↓
Frontend (結果表示 + 検索履歴保存)
```

#### ノート取り込みフロー

```
User Action: ノート配置（3つの方法）
  1. ローカルファイルアップロード（UIから直接アップロード）⭐ 推奨
  2. Google Drive連携（非IT系ユーザー向け、自動監視）
  3. GCS直接配置（開発者のみ、v3.0では非推奨）
  ↓
Backend (/ingest)
  ├─→ アップロードされたファイルまたはGoogle Driveから取得
  ├─→ notes/new/ に一時保存
  ├─→ 既存ID確認（増分更新）
  ├─→ Embedding生成 → ChromaDB追加
  ├─→ ChromaDB → GCS同期
  └─→ ファイル処理（processed/へ移動、削除しない）
  ↓
IngestResponse (new_notes: string[], skipped_notes: string[])
```

**非IT系ユーザー向け配慮（v3.0新規）**:
- **ローカルファイルアップロード**: ブラウザから直接ファイルをアップロード（ドラッグ&ドロップ対応）
- **Google Drive連携**: Google Driveフォルダを指定すると、定期的に新規ファイルを自動取り込み
- **GCS方式の廃止**: GCSに直接ファイルを配置する方式は専門知識が必要なため、v3.0で非推奨化
- **アーカイブ方針**: 取り込み済みノートは`processed/`に移動し、削除しない（Embeddingモデル変更時の再取り込みに対応）

---

## APIエンドポイント設計

### コア機能
- `POST /search` - 実験ノート検索
  - v3.0.1: ハイブリッド検索対応（`search_mode`, `hybrid_alpha`パラメータ追加）
  - 検索モード: セマンティック（デフォルト）、キーワード、ハイブリッド
- `POST /ingest` - ノート取り込み（増分更新）
- `GET /notes/{id}` - ノート取得

### プロンプト管理
- `GET /prompts` - デフォルトプロンプト取得
- `GET /prompts/list` - 保存済みプロンプト一覧
- `POST /prompts/save` - プロンプト保存
- `GET /prompts/load/{name}` - プロンプト読み込み
- `DELETE /prompts/delete/{name}` - プロンプト削除
- `PUT /prompts/update` - プロンプト更新

### ChromaDB管理
- `GET /chroma/info` - 現在のEmbeddingモデル情報
- `POST /chroma/reset` - ChromaDBリセット

### 評価機能
- `POST /evaluate/import` - テストケースインポート（Excel/CSV）
- `POST /evaluate` - RAG性能評価

### その他
- `GET /health` - ヘルスチェック
- `GET /config/folders` - フォルダパス取得
- `POST /config/folders` - フォルダパス更新

詳細は `/backend/server.py` または `docs/api-specification.md` を参照。

---

## セキュリティ設計

### APIキー管理

**フロントエンド**:
- localStorage に保存（平文）
- ユーザーが手動で入力
- リクエスト時にヘッダーまたはボディで送信
- HTTPS通信のみ

**バックエンド**:
- APIキーはサーバーに保存しない
- リクエストごとに受け取り、一時的にメモリで使用
- ログに出力しない

### CORS設定

```python
# server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ローカル開発
        os.getenv("FRONTEND_URL", "https://your-app.vercel.app")  # 本番環境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## デプロイ戦略

### フロントエンド（Vercel）

```bash
# GitHub連携で自動デプロイ
# main ブランチプッシュ → 自動ビルド&デプロイ

# 環境変数
NEXT_PUBLIC_API_URL=https://jikkennote-backend-xxx.run.app
```

### バックエンド（Google Cloud Run）

```bash
# 1. Dockerイメージビルド
docker build -t asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:latest backend/

# 2. Artifact Registryにプッシュ
docker push asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:latest

# 3. Cloud Runデプロイ
gcloud run deploy jikkennote-backend \
  --image asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars STORAGE_TYPE=gcs,GCS_BUCKET_NAME=jikkennote-storage
```

### ストレージ（Google Cloud Storage）

```bash
# バケット作成
gcloud storage buckets create gs://jikkennote-storage --location=asia-northeast1

# フォルダ構造作成
gsutil mkdir gs://jikkennote-storage/chroma-db
gsutil mkdir gs://jikkennote-storage/notes
gsutil mkdir gs://jikkennote-storage/prompts

# 初期ファイルアップロード
gsutil cp master_dictionary.yaml gs://jikkennote-storage/
```

---

## テスト戦略

### E2Eテスト（Playwright）

```bash
cd frontend
npm test                                # 全テスト実行
npm test tests/e2e/prompt-management.spec.ts  # 特定テスト実行
npx playwright test --debug             # デバッグモード
```

**テストカバレッジ**:
- プロンプト管理機能 ✅
- 評価機能 ✅
- その他（検索、ノート取り込み）は手動テスト

### APIテスト

```bash
# cURLでのテスト
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "テスト",
    "materials": "エタノール",
    "methods": "攪拌",
    "openai_api_key": "sk-proj-...",
    "cohere_api_key": "..."
  }' | jq .
```

---

## パフォーマンス目標

| 指標 | 目標値 |
|------|-------|
| 検索レスポンス | < 5秒 |
| ノート取り込み | < 10秒/件 |
| 新出単語抽出 | < 10秒/ノート |
| ページロード | < 2秒 |
| API応答時間 | < 3秒 |

---

## トラブルシューティング

### ChromaDB互換性エラー

**症状**: Embeddingモデル変更後、検索エラー

**対処**:
1. 設定ページで「ChromaDBをリセット」
2. 全ノート再取り込み
3. Embedding モデル確認

### 検索結果が不正確

**対処**:
1. プロンプトを編集（設定ページ）
2. 評価機能でnDCG測定

### ノート取り込みエラー

**対処**:
1. Markdown形式（.md）確認
2. セクション構造確認（## 材料、## 方法）
3. APIキー確認

---

## ドキュメント管理の原則

### 永続的ドキュメント(`docs/`)

- プロジェクト全体の「何を作るか」「どう作るか」を定義
- 頻繁に更新されない
- プロジェクトの「北極星」

### アイデアメモ(`docs/ideas/`)

- 壁打ち・ブレインストーミングの成果物
- 技術調査メモ
- 自由形式（構造化は最小限）

### プロジェクトメモリ(このファイル)

- 技術スタック、開発プロセス、ディレクトリ構造
- 開発者が最初に読むべき情報
- 実装時の指針

---

## リリース履歴

- **v2.0.0** (2026-01-07) - 機能簡素化版（正規化辞書管理・新出単語抽出機能を削除）
- **v1.x** - 旧バージョン（jikkennote-search_v1）

---

## 参考リンク

### 内部ドキュメント
- [初期要件・アイデアメモ](docs/ideas/initial-requirements.md)
- [プロダクト要求定義書](docs/product-requirements.md)
- [機能設計書](docs/functional-design.md)
- [技術仕様書](docs/architecture.md)
- [API仕様書](docs/api-specification.md)
- [開発ガイドライン](docs/development-guidelines.md)
- [ユーザーマニュアル](USER_MANUAL.md)
- [デプロイ手順書](DEPLOYMENT.md)

### 外部リソース
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)

---

**作成日**: 2026-01-07
**最終更新**: 2026-01-07
**バージョン**: 2.0.0 (機能簡素化版)
**管理者**: 開発チーム
