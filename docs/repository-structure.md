# リポジトリ構造定義書 - 実験ノート検索システム v3.0

## ディレクトリ構成

```
jikkennote-search/
├── .claude/                       # Claude Code開発環境設定
│   ├── agents/                   # サブエージェント定義
│   │   ├── doc-reviewer.md       # ドキュメントレビューエージェント
│   │   └── implementation-validator.md  # 実装検証エージェント
│   ├── commands/                 # カスタムコマンド
│   │   ├── add-feature.md        # 新機能追加コマンド
│   │   ├── review-docs.md        # ドキュメントレビューコマンド
│   │   └── setup-project.md      # プロジェクトセットアップコマンド
│   ├── skills/                   # スキル定義
│   │   ├── steering/             # 作業単位ドキュメント管理
│   │   ├── prd-writing/          # PRD作成
│   │   ├── functional-design/    # 機能設計書作成
│   │   ├── architecture-design/  # アーキテクチャ設計書作成
│   │   ├── repository-structure/ # リポジトリ構造定義書作成
│   │   ├── development-guidelines/  # 開発ガイドライン作成
│   │   └── glossary-creation/    # 用語集作成
│   └── settings.json             # Claude Code設定
│
├── .steering/                     # 作業単位ドキュメント（将来追加予定）
│   └── [日付]-[機能名]/          # 機能ごとのフォルダ（例: 20251230-Google-Drive統合）
│       ├── requirements.md       # 要件定義（目的、スコープ、制約）
│       ├── design.md             # 設計書（データフロー、API設計、UI設計）
│       └── tasklist.md           # タスクリスト（実装タスク、チェックボックス付き）
│
├── frontend/                      # Next.js フロントエンド
│   ├── app/                      # App Router ページ
│   │   ├── page.tsx             # ホーム（ランディングページ）
│   │   ├── search/              # 検索ページ
│   │   │   └── page.tsx         # 実験ノート検索UI
│   │   ├── viewer/              # ノートビューワー
│   │   │   └── page.tsx         # ノートID入力→全文表示
│   │   ├── ingest/              # ノート取り込み
│   │   │   └── page.tsx         # 新規ノート取り込み、新出単語判定
│   │   ├── dictionary/          # 辞書管理
│   │   │   └── page.tsx         # 正規化辞書の閲覧・編集・エクスポート
│   │   ├── evaluate/            # RAG評価
│   │   │   └── page.tsx         # 性能評価、Excel/CSVインポート
│   │   ├── settings/            # 設定
│   │   │   └── page.tsx         # APIキー、モデル選択、プロンプト管理
│   │   └── layout.tsx           # ルートレイアウト
│   │
│   ├── components/              # 共通コンポーネント
│   │   ├── Button.tsx           # ボタンコンポーネント（実装済み）
│   │   ├── Header.tsx           # ヘッダーコンポーネント（実装済み）
│   │   ├── Loading.tsx          # ローディングインジケータ（実装済み）
│   │   └── Toast.tsx            # トースト通知コンポーネント（実装済み）
│   │
│   ├── lib/                     # ユーティリティ
│   │   ├── api.ts              # APIクライアント関数（実装済み）
│   │   ├── types.ts            # 型定義（実装済み）
│   │   ├── storage.ts          # localStorage抽象化（実装済み）
│   │   └── promptStorage.ts    # プロンプト保存ロジック（実装済み）
│   │
│   ├── tests/                   # テスト
│   │   └── e2e/                # E2Eテスト（Playwright）
│   │       ├── prompt-management.spec.ts
│   │       ├── evaluation.spec.ts
│   │       └── chromadb-management.spec.ts
│   │
│   ├── public/                  # 静的ファイル
│   │   └── favicon.ico
│   │
│   ├── package.json             # 依存関係
│   ├── tsconfig.json            # TypeScript設定
│   ├── next.config.ts           # Next.js設定
│   ├── tailwind.config.ts       # Tailwind CSS設定
│   └── playwright.config.ts     # Playwright設定
│
├── backend/                     # FastAPI バックエンド
│   ├── server.py               # メインAPIサーバー（FastAPI）
│   ├── agent.py                # LangGraph ワークフロー
│   ├── ingest.py               # ノート取り込みロジック
│   ├── utils.py                # ユーティリティ関数（正規化など）
│   ├── chroma_sync.py          # ChromaDB管理
│   ├── storage.py              # ストレージ抽象化（ローカル/GCS）
│   ├── prompt_manager.py       # プロンプト管理（YAML保存/読み込み）
│   ├── config.py               # 設定管理（環境変数、デフォルト値）
│   │
│   ├── master_dictionary.yaml  # 正規化辞書
│   ├── chroma_db_config.json   # ChromaDB設定（現在のEmbeddingモデル）
│   │
│   ├── saved_prompts/          # 保存されたプロンプト（YAML）
│   │   └── (ユーザーが設定画面で保存したプロンプト)
│   │
│   ├── notes/                  # 実験ノート（ローカル開発）
│   │   ├── new/               # 新規ノート（取り込み前）
│   │   ├── archived/          # 旧アーカイブ（v2.0以前、非推奨）
│   │   └── processed/         # 取り込み済みノート（v3.0以降、削除しない）
│   │
│   ├── chroma_db/              # ChromaDB永続化（ローカル開発）
│   │
│   ├── requirements.txt        # Python依存関係
│   ├── Dockerfile             # Dockerイメージ定義
│   └── .env.example           # 環境変数テンプレート
│
├── docs/                       # ドキュメント
│   ├── ideas/                 # 初期要件、アイデアメモ
│   │   └── initial-requirements.md
│   │
│   ├── product-requirements.md      # プロダクト要求定義書
│   ├── functional-design.md         # 機能設計書
│   ├── architecture.md              # 技術仕様書
│   ├── api-specification.md         # API仕様書
│   ├── repository-structure.md      # このファイル
│   ├── development-guidelines.md    # 開発ガイドライン
│   └── glossary.md                  # ユビキタス言語定義
│
├── CLAUDE.md                   # プロジェクトメモリ
├── README.md                   # プロジェクト概要
├── DEPLOYMENT_CLOUDRUN.md      # Cloud Runデプロイ手順書
├── DEPLOY_NOW_CLOUDRUN.md      # Cloud Run即時デプロイ手順書
├── DEPLOY_CONTINUE.sh          # デプロイ継続スクリプト
├── DEPLOY_GCS.sh               # GCS同期スクリプト
├── USER_MANUAL.md              # ユーザーマニュアル
├── PRODUCTION_TEST_CHECKLIST.md  # 本番環境テストチェックリスト
│
└── .gitignore                  # Git除外ファイル
```

---

## ファイル・フォルダ詳細

### フロントエンド (`frontend/`)

#### `app/` (Next.js App Router)

| ファイル/フォルダ | 説明 |
|-----------------|------|
| `page.tsx` | ホーム（ランディングページ） |
| `search/page.tsx` | 実験ノート検索UI、検索結果表示、コピー機能 |
| `viewer/page.tsx` | ノートビューワー、ノートID入力→全文表示 |
| `ingest/page.tsx` | ノート取り込み、新出単語判定UI |
| `dictionary/page.tsx` | 正規化辞書管理、閲覧・編集・エクスポート |
| `evaluate/page.tsx` | RAG性能評価、Excel/CSVインポート |
| `settings/page.tsx` | 設定（APIキー、モデル選択、プロンプト管理） |
| `layout.tsx` | ルートレイアウト、グローバルスタイル |

#### `components/` (共通コンポーネント)

| ファイル | 説明 |
|---------|------|
| `Button.tsx` | ボタンコンポーネント（primary, secondary, danger等） |
| `Header.tsx` | ヘッダーコンポーネント（ナビゲーション） |
| `Loading.tsx` | ローディングインジケータ（スピナー） |
| `Toast.tsx` | トースト通知コンポーネント（成功、エラー等） |

**今後追加予定**: Modal, Input, Card等

#### `lib/` (ユーティリティ)

| ファイル | 説明 |
|---------|------|
| `api.ts` | APIクライアント関数（fetch wrappers、型安全なAPI呼び出し） |
| `types.ts` | 型定義（SearchRequest, IngestResponse等） |
| `storage.ts` | localStorage抽象化（APIキー、検索履歴保存） |
| `promptStorage.ts` | プロンプト保存ロジック（YAML形式、名前付き保存） |

#### `tests/e2e/` (E2Eテスト)

| ファイル | 説明 |
|---------|------|
| `prompt-management.spec.ts` | プロンプト管理機能のE2Eテスト（保存、読み込み、削除） |
| `evaluation.spec.ts` | RAG評価機能のE2Eテスト（Excel/CSVインポート、nDCG計算） |
| `chromadb-management.spec.ts` | ChromaDB管理機能のE2Eテスト（Embeddingモデル変更検出、リセット） |

---

### バックエンド (`backend/`)

#### メインファイル

| ファイル | 説明 |
|---------|------|
| `server.py` | FastAPIメインサーバー、全エンドポイント定義 |
| `agent.py` | LangGraphワークフロー（AgentState、ノード定義） |
| `ingest.py` | ノート取り込みロジック、増分更新、新出単語抽出 |
| `term_extractor.py` | 新出単語抽出（Sudachi + LLM）⭐ v3.0新規 |
| `dictionary.py` | 辞書管理ロジック（CRUD操作）⭐ v3.0新規 |
| `evaluation.py` | RAG性能評価（nDCG計算）⭐ v3.0新規 |
| `history.py` | 検索履歴管理 ⭐ v3.0新規 |
| `prompts.py` | プロンプトテンプレート定義 ⭐ v3.0新規 |
| `utils.py` | ユーティリティ関数（正規化、セクション抽出） |
| `chroma_sync.py` | ChromaDB管理（初期化、同期、リセット、ハイブリッド検索） |
| `storage.py` | ストレージ抽象化（ローカル/GCS切り替え） |
| `prompt_manager.py` | プロンプト管理（YAML保存/読み込み） |
| `config.py` | 設定管理（環境変数、デフォルト値） |

#### データファイル

| ファイル | 説明 |
|---------|------|
| `master_dictionary.yaml` | 正規化辞書（化学物質名の表記揺れマッピング、本番ではGCSに保存） |
| `master_dictionary_sample.yaml` | 正規化辞書のサンプル（開発用） |
| `chroma_db_config.json` | ChromaDB設定（現在のEmbeddingモデル情報、モデル変更検出に使用） |
| `saved_prompts/*.yaml` | 保存されたプロンプト（ユーザーがUIで保存、名前なしファイルも存在） |

#### フォルダ

| フォルダ | 説明 |
|---------|------|
| `notes/new/` | 新規ノート（取り込み前） |
| `notes/archived/` | 旧アーカイブノート（v2.0以前、非推奨） |
| `notes/processed/` | 取り込み済みノート（v3.0以降、削除しない） |
| `chroma_db/` | ChromaDB永続化フォルダ（ローカル開発） |
| `saved_prompts/` | YAMLプロンプトファイル格納 |

#### 設定ファイル

| ファイル | 説明 |
|---------|------|
| `requirements.txt` | Python依存パッケージリスト |
| `Dockerfile` | Dockerイメージ定義（本番環境用） |
| `.env.example` | 環境変数テンプレート |

---

### ドキュメント (`docs/`)

#### 正式版ドキュメント

| ファイル | 説明 |
|---------|------|
| `product-requirements.md` | プロダクト要求定義書（FR-001〜FR-116、v3.0新機能含む） |
| `functional-design.md` | 機能設計書（データフロー、コンポーネント設計） |
| `architecture.md` | 技術仕様書（システムアーキテクチャ、技術スタック） |
| `api-specification.md` | API仕様書（全エンドポイント仕様） |
| `repository-structure.md` | このファイル（リポジトリ構造定義） |
| `development-guidelines.md` | 開発ガイドライン（セットアップ、テスト、デプロイ） |
| `glossary.md` | ユビキタス言語定義（専門用語集） |

#### アイデア・メモ

| フォルダ | 説明 |
|---------|------|
| `ideas/` | 初期要件、ブレスト成果物 |
| `ideas/initial-requirements.md` | プロジェクト初期アイデアメモ |

---

### ルートファイル

| ファイル | 説明 |
|---------|------|
| `CLAUDE.md` | プロジェクトメモリ（技術スタック、開発プロセス） |
| `README.md` | プロジェクト概要、セットアップ、使い方 |
| `DEPLOYMENT_CLOUDRUN.md` | Cloud Runデプロイ手順書 |
| `DEPLOY_NOW_CLOUDRUN.md` | Cloud Run即時デプロイ手順書 |
| `DEPLOY_CONTINUE.sh` | デプロイ継続スクリプト |
| `DEPLOY_GCS.sh` | GCS同期スクリプト |
| `USER_MANUAL.md` | エンドユーザー向け完全マニュアル |
| `PRODUCTION_TEST_CHECKLIST.md` | 本番環境テストチェックリスト |
| `.gitignore` | Git除外ファイル（node_modules, .env等） |

---

## 環境別構成

### ローカル開発環境

```
backend/
├── notes/new/        # 新規ノート
├── notes/archived/   # 旧アーカイブ（v2.0以前、非推奨）
├── notes/processed/  # 取り込み済みノート（v3.0以降、削除しない）
├── chroma_db/        # ChromaDB永続化
└── saved_prompts/    # プロンプトYAML
```

### 本番環境（Google Cloud Storage） - v3.0 マルチテナント対応

```
gs://jikkennote-storage/
└── teams/
    ├── team_abc123/           # チーム1
    │   ├── chroma-db/         # ChromaDB永続化（チーム専用）
    │   ├── notes/
    │   │   ├── new/          # 取り込み待ちノート
    │   │   └── processed/    # 取り込み済みノート（アーカイブ）
    │   ├── prompts/          # チーム専用プロンプト
    │   └── dictionary.yaml   # チーム専用辞書
    │
    └── team_xyz789/           # チーム2
        └── (同じ構造)
```

**v3.0での変更点：**
- チームごとに完全に独立したデータ構造
- `teams/{team_id}/`配下に全データを分離
- 他チームのデータにはアクセス不可

### ノート管理戦略の変更（v2.0 → v3.0）

| バージョン | ディレクトリ | 取り込み後の処理 | 理由 |
|-----------|------------|----------------|------|
| **v2.0以前** | `notes/archived/` | ノートを移動後、削除 | ディスク容量削減 |
| **v3.0以降** | `notes/processed/` | ノートを移動、**削除しない** | Embeddingモデル変更時の再取り込みに対応 |

**重要**: v3.0では、Embeddingモデルを変更した場合、ChromaDBをリセットして全ノートを再取り込みする必要があります。`processed/`フォルダにノートを保存することで、この操作が可能になります。

**関連機能**:
- FR-110（ノート取り込み改善）: 増分更新、新出単語自動抽出
- FR-108（ChromaDB管理）: Embeddingモデル変更検出、ChromaDBリセット

---

## ファイル命名規則

### フロントエンド

- **ページファイル**: `page.tsx` (App Router規約)
- **コンポーネント**: `PascalCase.tsx` (例: `Button.tsx`)
- **ユーティリティ**: `camelCase.ts` (例: `api.ts`, `utils.ts`)

### バックエンド

- **Pythonファイル**: `snake_case.py` (例: `chroma_sync.py`)
- **設定ファイル**: `snake_case.yaml` / `.json` (例: `master_dictionary.yaml`)
- **ノートファイル**: `ID{番号}-{タイトル}.md` (例: `ID3-14-酸化反応.md`)

### ドキュメント

- **正式版**: `kebab-case.md` (例: `product-requirements.md`)
- **アイデアメモ**: `kebab-case.md` (例: `initial-requirements.md`)

---

## Git管理

### `.gitignore`に含まれるもの

```
# Node.js
node_modules/
.next/

# Python
__pycache__/
*.pyc
.venv/
venv/

# 環境変数
.env
.env.local

# ビルド成果物
dist/
build/

# ChromaDB
backend/chroma_db/

# 実験ノート（個人情報保護）
backend/notes/new/*.md
backend/notes/processed/*.md
backend/notes/archived/*.md

# 辞書・設定ファイル（チーム固有データ）
backend/master_dictionary.yaml
backend/chroma_db_config.json

# プロンプト（ユーザー固有設定）
backend/saved_prompts/*.yaml
```

---

## 依存関係管理

### フロントエンド

- **管理**: `frontend/package.json`
- **ロックファイル**: `frontend/package-lock.json`
- **インストール**: `npm install`

### バックエンド

- **管理**: `backend/requirements.txt`
- **インストール**: `pip install -r requirements.txt`
- **仮想環境**: `.venv/` (gitignore済み)

---

## ビルド・デプロイ成果物

### フロントエンド

- **ビルド**: `frontend/.next/`
- **本番**: Vercel Edge Network (自動デプロイ)

### バックエンド

- **ローカル**: `python backend/server.py`
- **本番**: Docker Image → Google Cloud Run

---

## バージョン履歴

### v3.0.1 (2025-12-31)
- `.claude/`ディレクトリ追加（Claude Code開発環境設定）
- `.steering/`ディレクトリ追加（作業単位ドキュメント管理、将来追加予定）
- `backend/notes/processed/`追加（取り込み済みノート保存、v3.0新方針を明記）
- `backend/saved_prompts/`に名称変更（旧`prompts/`）
- `backend/term_extractor.py`, `dictionary.py`, `evaluation.py`, `history.py`, `prompts.py`追加（v3.0新規ファイル）
- `frontend/components/`に実装済みファイルを明記（Button, Header, Loading, Toast）
- `frontend/lib/`に実装済みファイルを明記（api, types, storage, promptStorage）
- E2Eテストに`chromadb-management.spec.ts`を追加
- ルートファイルを実際の構成に修正（DEPLOYMENT_CLOUDRUN.md等）
- ノート管理戦略の変更（v2.0 vs v3.0）を明記
- `.gitignore`の記載を実際の設定に合わせて修正

### v3.0.0 (2025-12-29)
- 初版作成（v1改善点を反映）
- マルチテナント対応のディレクトリ構造
- v3.0新機能（FR-109〜FR-116）を反映

---

**作成日**: 2025-12-29
**最終更新**: 2025-12-31
**バージョン**: 3.0.1 (レビュー結果を反映、実装との整合性確保)
