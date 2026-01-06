# 設計仕様書 - 実験ノート検索システム v3.0

## 関連ドキュメント

このドキュメントは、実験ノート検索システムv3.0の詳細な機能設計を定義します。他のドキュメントと合わせてお読みください。

### プロジェクト全体

- **[README.md](../README.md)**: プロジェクト概要とクイックスタート
- **[CLAUDE.md](../CLAUDE.md)**: プロジェクトメモリ（技術スタック、開発プロセス、ディレクトリ構造）

### 要件・設計ドキュメント

- **[product-requirements.md](./product-requirements.md)**: プロダクト要求定義書（PRD）
  - v3.0新機能の要件定義（FR-109〜FR-116）
  - 機能優先度とユーザーストーリー
- **[architecture.md](./architecture.md)**: 技術仕様書
  - システムアーキテクチャ詳細
  - 技術選定理由とトレードオフ
- **[api-specification.md](./api-specification.md)**: API仕様書
  - 全エンドポイントのリクエスト/レスポンス定義
  - v3.0新規エンドポイント: `/ingest/upload`, `/teams`, `/google-drive/*`
- **[development-guidelines.md](./development-guidelines.md)**: 開発ガイドライン
  - コーディング規約、Git運用ルール
  - テスト戦略とデプロイフロー
- **[repository-structure.md](./repository-structure.md)**: リポジトリ構造定義書
  - ディレクトリ構成と各ファイルの役割
- **[glossary.md](./glossary.md)**: ユビキタス言語定義
  - プロジェクト内で使用する用語の統一定義

### ユーザー向けドキュメント

- **[USER_MANUAL.md](../USER_MANUAL.md)**: ユーザーマニュアル
  - 各機能の使い方（検索、ノート取り込み、評価等）
- **[DEPLOYMENT.md](../DEPLOYMENT.md)**: デプロイ手順書
  - Vercel/Cloud Runへのデプロイ方法
- **[PRODUCTION_TEST_CHECKLIST.md](../PRODUCTION_TEST_CHECKLIST.md)**: 本番テストチェックリスト

### セクション間の参照

- **v3.0新機能の詳細**: [Section 10](#10-v30-新機能詳細設計-)
  - マルチテナント対応: [10.1](#101-マルチテナント対応)
  - ノート取り込み改善: [10.2](#102-ノート取り込み改善)
  - モデル2段階選択: [10.3](#103-モデル2段階選択)
  - ハイブリッド検索: [10.6](#106-ハイブリッド検索--重要)
  - 再検索機能: [10.7](#107-再検索機能詳細設計fr-113)
  - コピー機能強化: [10.8](#108-コピー機能強化詳細設計fr-114)
  - 評価機能改善: [10.9](#109-評価機能改善詳細設計fr-115)
  - シーケンス図: [10.10](#1010-シーケンス図--v30)
- **データモデル**: [Section 3](#3-データモデル)
- **API設計**: [api-specification.md](./api-specification.md)
- **パフォーマンス測定**: [Section 7.4](#74-パフォーマンス測定方法--v30更新)
- **テストケース**: [Section 10.4](#104-v30新機能テストケース-)

---

## 1. システムアーキテクチャ

### 1.1 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 App Router)                           │
│  Deployment: Vercel                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Auth (Firebase) ⭐ v3.0新規                          │  │
│  │ - Google Login - Team Selection - Team Management   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌───────────┬───────────┬───────────┬──────────────────┐  │
│  │ Search    │ History   │ Viewer    │ Settings         │  │
│  │ Page      │ Page      │ Page      │ Page             │  │
│  │ - 再検索  │ - 再検索  │ - コピー  │ - モデル2段階   │  │
│  │   v3.0    │   v3.0    │   v3.0    │   選択 v3.0     │  │
│  ├───────────┼───────────┼───────────┼──────────────────┤  │
│  │ Evaluate  │ Ingest    │ Dictionary│ Team Mgmt        │  │
│  │ Page      │ Page      │ Page      │ Page             │  │
│  │ - @5      │ - ローカル │           │ ⭐ v3.0新規      │  │
│  │   v3.0    │   Upload  │           │                  │  │
│  │           │   v3.0    │           │                  │  │
│  │           │ - GDrive  │           │                  │  │
│  │           │   v3.0    │           │                  │  │
│  └───────────┴───────────┴───────────┴──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Shared Components                                    │   │
│  │ - Button, Input, Modal, Toast, ProgressBar          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ State Management (localStorage + Firebase) ⭐ v3.0更新│   │
│  │ - API Keys, Search History, User Preferences         │   │
│  │ - User Auth Token, Current Team ID ⭐ v3.0新規       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ REST API (HTTPS)
                         │ + Firebase Auth Headers ⭐ v3.0新規
                         │
┌────────────────────────┴─────────────────────────────────────┐
│  Backend API (FastAPI + Python 3.12)                         │
│  Deployment: Google Cloud Run                                │
│  Multi-tenant Architecture ⭐ v3.0新規                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Endpoints                                        │   │
│  │ /search (hybrid search ⭐ v3.0.1)                   │   │
│  │ /ingest/upload (local files ⭐ v3.0)                │   │
│  │ /google-drive/* (GDrive integration ⭐ v3.0)        │   │
│  │ /teams/* (team management ⭐ v3.0)                  │   │
│  │ /prompts/*, /dictionary/*, /chroma/*                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Core Modules                                         │   │
│  │ - agent.py (LangGraph workflow + model 2-stage)     │   │
│  │ - ingest.py (Sudachi + LLM term extraction v3.0)    │   │
│  │ - utils.py (Normalization)                          │   │
│  │ - chroma_sync.py (ChromaDB per team ⭐ v3.0)        │   │
│  │ - storage.py (Team-based GCS paths ⭐ v3.0)         │   │
│  │ - prompt_manager.py (YAML prompt storage)           │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────┬──────────────┬──────────────┬───────────────────┘
            │              │              │
            │              │              │
┌───────────┴────────┐ ┌──┴──────────┐ ┌─┴──────────────────┐
│ External Services  │ │ ChromaDB    │ │ Google Cloud       │
│                    │ │ (Vector DB) │ │ Storage (GCS)      │
│ - OpenAI API       │ │             │ │ ⭐ v3.0マルチテナント│
│ - Cohere API       │ │ Hybrid      │ │                    │
│ - Firebase Auth    │ │ Search      │ │ teams/{team_id}/:  │
│   ⭐ v3.0新規      │ │ ⭐ v3.0.1   │ │ - chroma-db/       │
│ - Google Drive API │ │             │ │ - notes/           │
│   ⭐ v3.0新規      │ │ Per-team    │ │   - new/           │
│                    │ │ Collection  │ │   - processed/     │
│                    │ │ ⭐ v3.0     │ │ - prompts/         │
│                    │ │             │ │ - dictionary.yaml  │
└────────────────────┘ └─────────────┘ └────────────────────┘
```

**v3.0主要変更点**:
- **マルチテナント対応**: Firebase認証によるチーム別データ分離
- **モデル2段階選択**: 検索判定用LLM / 要約生成用LLMを個別選択可能
- **ハイブリッド検索** (v3.0.1): セマンティック + キーワード検索の融合
- **ローカルファイルアップロード**: ブラウザから直接ノート取り込み
- **Google Drive連携**: Driveフォルダからの自動ノート同期
- **新出単語抽出改善**: Sudachi形態素解析 + LLMによる高精度抽出
- **再検索機能**: 検索結果から簡単に条件を変更して再検索
- **コピー機能強化**: ビューワー・検索結果から検索画面へコピー
- **評価機能改善**: @5メトリクス追加、CSV一括エクスポート

### 1.2 データフロー

#### 1.2.1 検索フロー（v3.0更新）

```
User Input (目的・材料・方法・重点指示)
  │
  ├─→ Frontend (Search Page)
  │     └─→ API Request with:
  │           - Authorization: Bearer {firebase_token}  ⭐ v3.0新規
  │           - X-Team-ID: {team_id}  ⭐ v3.0新規
  │           - custom_prompts, embedding_model
  │           - search_llm_model, summary_llm_model  ⭐ v3.0新規
  │           - search_mode, hybrid_alpha  ⭐ v3.0.1新規
  │
  ├─→ Backend API (/search)
  │     │
  │     ├─→ Verify Firebase Token  ⭐ v3.0新規
  │     ├─→ Load Team-specific Data (teams/{team_id}/)  ⭐ v3.0新規
  │     │
  │     ├─→ LangGraph Agent (agent.py)
  │     │     │
  │     │     ├─→ Normalize Node (utils.py)
  │     │     │     └─→ Load teams/{team_id}/dictionary.yaml  ⭐ v3.0更新
  │     │     │     └─→ Normalize material names
  │     │     │
  │     │     ├─→ Query Generation Node (prompts, search_llm_model)  ⭐ v3.0更新
  │     │     │     └─→ Generate 3 perspective queries
  │     │     │         (Veteran, Newcomer, Manager)
  │     │     │
  │     │     ├─→ Search Node (search_mode, hybrid_alpha)  ⭐ v3.0.1更新
  │     │     │     ├─→ ChromaDB Hybrid Search (top 100)  ⭐ v3.0.1更新
  │     │     │     └─→ Cohere Reranking (top 10)
  │     │     │
  │     │     └─→ Compare Node (if not evaluation_mode, summary_llm_model)  ⭐ v3.0更新
  │     │           └─→ Generate comparison report (top 3)
  │     │
  │     └─→ Return SearchResponse
  │
  └─→ Frontend Display Results
        └─→ Save to Search History (localStorage)
```

#### 1.2.2 ノート取り込みフロー（v3.0更新）

```
User Action: Upload Notes (3つの方法)  ⭐ v3.0更新
  ├─→ 1. ローカルファイルアップロード（推奨）  ⭐ v3.0新規
  ├─→ 2. Google Drive連携  ⭐ v3.0新規
  └─→ 3. GCS直接配置（開発者向け、非推奨）
  │
  ├─→ Frontend (Ingest Page)
  │     └─→ POST /ingest/upload with:  ⭐ v3.0新規エンドポイント
  │           - Authorization: Bearer {firebase_token}  ⭐ v3.0新規
  │           - X-Team-ID: {team_id}  ⭐ v3.0新規
  │           - files[] (multipart/form-data)
  │
  ├─→ Backend (ingest.py)
  │     │
  │     ├─→ Verify Firebase Token  ⭐ v3.0新規
  │     ├─→ Load Team-specific Data (teams/{team_id}/)  ⭐ v3.0新規
  │     │
  │     ├─→ Save to teams/{team_id}/notes/new/  ⭐ v3.0更新
  │     │
  │     ├─→ Check existing IDs in ChromaDB
  │     │     └─→ Skip already ingested notes (増分更新)
  │     │
  │     ├─→ Parse new notes
  │     │     ├─→ Extract sections (目的・材料・方法・結果)
  │     │     └─→ Normalize materials with teams/{team_id}/dictionary.yaml  ⭐ v3.0更新
  │     │
  │     ├─→ POST /ingest/analyze (if new terms detected)
  │     │     ├─→ Extract unknown terms with Sudachi + LLM  ⭐ v3.0更新
  │     │     ├─→ LLM similarity check (複合語 vs 表記揺れ vs 新規)  ⭐ v3.0更新
  │     │     └─→ Return suggestions to user
  │     │
  │     ├─→ User confirms dictionary updates
  │     │     └─→ POST /dictionary/update (teams/{team_id}/)  ⭐ v3.0更新
  │     │
  │     ├─→ Vectorize with OpenAI Embeddings
  │     │     └─→ Add to ChromaDB (teams/{team_id}/chroma-db)  ⭐ v3.0更新
  │     │
  │     ├─→ Sync ChromaDB to GCS (teams/{team_id}/)  ⭐ v3.0更新
  │     │
  │     └─→ Move to teams/{team_id}/notes/processed/  ⭐ v3.0更新（削除しない）
  │
  └─→ Frontend: Display ingest results + new terms UI
```

#### 1.2.3 評価フロー（v3.0更新）

```
User Action: Upload Evaluation Excel/CSV
  │
  ├─→ Frontend (Evaluate Page)
  │     └─→ POST /evaluate/import with:
  │           - Authorization: Bearer {firebase_token}  ⭐ v3.0新規
  │           - X-Team-ID: {team_id}  ⭐ v3.0新規
  │           - file (multipart/form-data)
  │
  ├─→ Backend: Parse Excel/CSV
  │     ├─→ Verify Firebase Token  ⭐ v3.0新規
  │     └─→ Return test_cases[]
  │
  ├─→ User: Select test cases and execute
  │     └─→ POST /evaluate for each test case with:
  │           - Authorization: Bearer {firebase_token}  ⭐ v3.0新規
  │           - X-Team-ID: {team_id}  ⭐ v3.0新規
  │           - search_llm_model, summary_llm_model  ⭐ v3.0新規
  │           - search_mode, hybrid_alpha  ⭐ v3.0.1新規
  │
  ├─→ Backend: Run search with test query
  │     ├─→ Get top 10 results
  │     └─→ Calculate metrics:
  │           - nDCG@5, nDCG@10  ⭐ v3.0更新（@5追加）
  │           - Precision@5, Precision@10  ⭐ v3.0更新（@5追加）
  │           - Recall@10
  │           - MRR
  │
  └─→ Frontend: Display results
        ├─→ Metrics chart (radar/bar)
        ├─→ Ranking comparison table
        ├─→ Save to evaluation history (max 50件)  ⭐ v3.0更新（5→50件）
        └─→ CSV出力機能  ⭐ v3.0新規
```

---

## 2. コンポーネント設計

### 2.1 フロントエンド構成

#### 2.1.1 ページコンポーネント（⭐ v3.0更新）

| ページ | パス | 責務 | v3.0更新内容 |
|--------|------|------|------------|
| Search Page | `/` | 検索UI、結果表示、コピー機能 | ⭐ 再検索モーダル、ハイブリッド検索モード選択 |
| History Page | `/history` | 検索履歴テーブル、再検索 | ⭐ モデル2段階選択情報の表示 |
| Viewer Page | `/viewer` | ノートID入力→全文表示 | ⭐ 検索画面へのコピー機能強化 |
| Ingest Page | `/ingest` | ノート取り込み、新出単語管理 | ⭐ ローカルアップロード、Google Drive連携、Sudachi+LLM抽出 |
| Dictionary Page | `/dictionary` | 正規化辞書CRUD | （v2.0と同様） |
| Evaluate Page | `/evaluate` | RAG性能評価 | ⭐ @5メトリクス追加、CSV一括エクスポート |
| Settings Page | `/settings` | APIキー、モデル、プロンプト、ChromaDB管理 | ⭐ モデル2段階選択UI |
| **Team Mgmt Page** | **`/teams`** | **チーム管理、ユーザー管理** | **⭐ v3.0新規ページ** |

#### 2.1.2 共通コンポーネント

**Button.tsx**
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger' | 'success';
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}
```

**Input.tsx**
```typescript
interface InputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'password' | 'number';
  disabled?: boolean;
}
```

**Modal.tsx**
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}
```

**Toast.tsx**
```typescript
interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}
```

**ProgressBar.tsx**
```typescript
interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
}
```

**使用例**:
```typescript
// Ingest Page: ノート取り込み進捗表示
<ProgressBar
  current={processedCount}
  total={totalNotes}
  label="ノート取り込み中"
/>

// 検索ボタン
<Button
  variant="primary"
  onClick={handleSearch}
  disabled={isSearching}
>
  {isSearching ? '検索中...' : '検索'}
</Button>

// 再検索モーダル ⭐ v3.0新規
<Modal
  isOpen={isReSearchModalOpen}
  onClose={() => setIsReSearchModalOpen(false)}
  title="再検索"
>
  <Input
    value={refinementInstruction}
    onChange={setRefinementInstruction}
    placeholder="重点指示を入力..."
  />
  <Button variant="primary" onClick={handleReSearch}>
    再検索実行
  </Button>
</Modal>

// 成功通知
<Toast
  message="ノートの取り込みが完了しました"
  type="success"
  duration={3000}
/>
```

### 2.2 バックエンド構成

#### 2.2.1 モジュール構成（⭐ v3.0マルチテナント対応）

**server.py** (FastAPI Application)
- API endpoint definitions
- Request/Response validation (Pydantic models)
- Firebase Authentication middleware ⭐ v3.0新規
  - `authenticate_request()`: Firebase ID Token検証
  - Team ID抽出とリクエストコンテキスト設定
- Error handling and CORS configuration

**agent.py** (LangGraph Workflow) ⭐ v3.0更新
- State definition (AgentState) with team_id context
- Nodes:
  - normalize_node (team-specific dictionary)
  - query_generation_node (search_llm_model)
  - search_node (hybrid search support ⭐ v3.0.1)
  - compare_node (summary_llm_model)
- Workflow graph construction
- Streaming support

**ingest.py** (Note Processing) ⭐ v3.0更新
- parse_markdown_note(): Extract sections from markdown
- extract_new_terms(): Sudachi + LLM term extraction ⭐ v3.0新規
- get_existing_ids(): Check ChromaDB for duplicates (per team)
- ingest_notes(): Main ingestion logic with incremental updates
  - Team-specific paths: `teams/{team_id}/notes/`

**utils.py** (Utilities) ⭐ v3.0更新
- load_master_dict(team_id): Load team-specific dictionary ⭐ v3.0更新
- normalize_text(): Apply normalization rules
- extract_note_sections(): Parse markdown sections

**chroma_sync.py** (ChromaDB Management) ⭐ v3.0更新
- get_chroma_vectorstore(team_id): Initialize ChromaDB per team ⭐ v3.0更新
  - Collection naming: `team_{team_id}_notes`
- sync_chroma_to_gcs(team_id): Upload ChromaDB to GCS per team ⭐ v3.0更新
  - Path: `teams/{team_id}/chroma-db/`
- get_current_embedding_model(team_id): Retrieve team config ⭐ v3.0更新
- save_embedding_model_config(team_id): Track changes per team ⭐ v3.0更新
- reset_chroma_db(team_id): Complete database reset per team ⭐ v3.0更新

**storage.py** (Storage Abstraction) ⭐ v3.0更新
- Unified interface for local filesystem and GCS
- Methods: read_file(), write_file(), list_files(), delete_file(), move_file()
- Team-based path resolution: `teams/{team_id}/{resource}` ⭐ v3.0新規
- Environment-based switching (local vs GCS)

**prompt_manager.py** (Prompt Management) ⭐ v3.0更新
- save_prompt_to_yaml(team_id): Save prompts per team ⭐ v3.0更新
- load_prompt_from_yaml(team_id): Load prompts per team ⭐ v3.0更新
- list_saved_prompts(team_id): Get all saved prompts per team ⭐ v3.0更新
- delete_prompt_file(team_id): Remove YAML file per team ⭐ v3.0更新
- update_prompt_yaml(team_id): Update existing prompt per team ⭐ v3.0更新

**config.py** (Configuration)
- Environment variables
- Default model configurations
- Team-based folder paths ⭐ v3.0更新
- API base URLs
- Firebase Admin SDK configuration ⭐ v3.0新規

---

## 3. データモデル

### 3.1 フロントエンド型定義

#### SearchRequest
```typescript
interface SearchRequest {
  purpose: string;
  materials: string;
  methods: string;
  type?: string;
  instruction?: string;
  openai_api_key: string;
  cohere_api_key: string;
  embedding_model?: string;
  search_llm_model?: string;  // クエリ生成・検索判定用LLM ⭐ v3.0新規（gpt-4o, gpt-4o-mini, gpt-5, gpt-5.1, gpt-5.2）
  summary_llm_model?: string;  // 要約生成用LLM ⭐ v3.0新規（gpt-3.5-turbo, gpt-4o-mini, gpt-4o）
  search_mode?: 'semantic' | 'keyword' | 'hybrid';  // ⭐ v3.0.1新規: 検索モード
  hybrid_alpha?: number;  // ⭐ v3.0.1新規: ハイブリッド検索の重み（0.0-1.0, デフォルト0.7）
  custom_prompts?: Record<string, string>;
  evaluation_mode?: boolean;
}
```

#### SearchResponse
```typescript
interface SearchResponse {
  success: boolean;
  message: string;
  retrieved_docs: string[];
  normalized_materials?: string;
  search_query?: string;
}
```

#### NoteResponse
```typescript
interface NoteResponse {
  success: boolean;
  note?: {
    id: string;
    content: string;
    sections: {
      purpose?: string;
      materials?: string;
      methods?: string;
      results?: string;
    };
  };
  error?: string;
}
```

#### EvaluationResult
```typescript
interface EvaluationResult {
  testCaseId: string;
  metrics: {
    ndcg_5: number;  // ⭐ v3.0新規
    ndcg_10: number;
    precision_5: number;
    precision_10: number;
    recall_10: number;
    mrr: number;
  };
  ranking: {
    noteId: string;
    rank: number;
    score: number;
    groundTruthRank?: number;
    relevance?: number;
  }[];
  // v3.0: モデル設定の記録
  embeddingModel: string;
  searchLlmModel: string;
  summaryLlmModel: string;
  searchMode?: string;
  hybridAlpha?: number;
}
```

#### SearchHistory (localStorage)
```typescript
interface SearchHistory {
  id: string;
  timestamp: Date;
  query: {
    purpose: string;
    materials: string;
    methods: string;
    instruction?: string;
  };
  results: {
    noteId: string;
    score: number;
    rank: number;
  }[];
  embeddingModel: string;
  searchLlmModel: string;  // クエリ生成・検索判定用LLMモデル ⭐ v3.0新規
  summaryLlmModel: string;  // 要約生成用LLMモデル ⭐ v3.0新規
  searchMode?: string;  // 'semantic', 'keyword', 'hybrid' ⭐ v3.0.1新規
  hybridAlpha?: number;  // 0.0-1.0 ⭐ v3.0.1新規
}
```

### 3.2 バックエンドデータモデル

#### AgentState (LangGraph)
```python
class AgentState(TypedDict):
    input_purpose: str
    input_materials: str
    input_methods: str
    input_type: Optional[str]
    instruction: Optional[str]
    normalized_materials: str
    search_query: str
    search_mode: Optional[str]  # 'semantic', 'keyword', 'hybrid' ⭐ v3.0.1新規
    hybrid_alpha: Optional[float]  # 0.0-1.0 (デフォルト0.7) ⭐ v3.0.1新規
    search_llm_model: Optional[str]  # 検索・判定用LLM ⭐ v3.0新規（gpt-4o, gpt-4o-mini, gpt-5, gpt-5.1, gpt-5.2）
    summary_llm_model: Optional[str]  # 要約生成用LLM ⭐ v3.0新規（gpt-3.5-turbo, gpt-4o-mini, gpt-4o）
    retrieved_docs: List[str]
    final_output: str
```

#### DictionaryEntry (master_dictionary.yaml)
```yaml
エタノール:
  - EtOH
  - エチルアルコール
  - ethanol
  - C2H5OH
```

#### PromptYAML (prompts/*.yaml)
```yaml
name: "プロンプト名"
description: "プロンプトの説明"
created_at: "2025-01-01T00:00:00Z"
updated_at: "2025-01-01T00:00:00Z"
prompts:
  normalize: |
    正規化プロンプト内容
  query_generation_veteran: |
    ベテラン視点クエリ生成プロンプト
  query_generation_newcomer: |
    新人視点クエリ生成プロンプト
  query_generation_manager: |
    マネージャー視点クエリ生成プロンプト
  compare: |
    比較分析プロンプト
```

#### ChromaDB Config (chroma_db_config.json)
```json
{
  "embedding_model": "text-embedding-3-small",
  "created_at": "2025-01-01T00:00:00Z",
  "last_updated": "2025-01-01T00:00:00Z"
}
```

#### Team Model ⭐ v3.0新規
```python
class Team(TypedDict):
    team_id: str  # Unique team identifier
    team_name: str
    created_at: datetime
    updated_at: datetime
    owner_uid: str  # Firebase UID of team owner
    members: List[TeamMember]
    settings: TeamSettings

class TeamMember(TypedDict):
    user_id: str  # Firebase UID
    email: str
    display_name: str
    role: str  # 'owner', 'admin', 'member'
    joined_at: datetime

class TeamSettings(TypedDict):
    default_embedding_model: Optional[str]
    default_search_llm_model: Optional[str]
    default_summary_llm_model: Optional[str]
    search_mode: Optional[str]  # 'semantic', 'keyword', 'hybrid'
    hybrid_alpha: Optional[float]
```

#### User Model ⭐ v3.0新規
```python
class User(TypedDict):
    user_id: str  # Firebase UID
    email: str
    display_name: str
    photo_url: Optional[str]
    created_at: datetime
    last_login: datetime
    current_team_id: Optional[str]  # Currently selected team
    team_memberships: List[str]  # List of team IDs user belongs to
```

**Firestore Collections Structure**: ⭐ v3.0新規
```
/teams/{team_id}
  - team_name: string
  - created_at: timestamp
  - owner_uid: string
  - members: array of TeamMember objects
  - settings: TeamSettings object

/users/{user_id}
  - email: string
  - display_name: string
  - photo_url: string
  - created_at: timestamp
  - last_login: timestamp
  - current_team_id: string
  - team_memberships: array of team IDs
```

---

## 4. 技術スタック詳細

### 4.1 フロントエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Next.js | 15.x | React framework with App Router |
| React | 19.x | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.x | Styling |
| React Markdown | 9.x | Markdown rendering |
| Playwright | 1.x | E2E testing |

### 4.2 バックエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.12+ | Core language |
| FastAPI | 0.115+ | Web framework |
| LangChain | 0.3.13+ | LLM orchestration |
| LangGraph | 0.2.62+ | Workflow management |
| ChromaDB | 0.6.3+ | Vector database |
| OpenAI SDK | 1.59+ | Embeddings & LLM |
| Cohere SDK | 5.14+ | Reranking |
| PyYAML | 6.0+ | YAML parsing |
| Pydantic | 2.x | Data validation |

### 4.3 インフラ

| サービス | 用途 |
|---------|------|
| Vercel | フロントエンドホスティング |
| Google Cloud Run | バックエンドAPI (コンテナ) |
| Google Cloud Storage (GCS) | ファイルストレージ、ChromaDB永続化 |
| Docker | コンテナ化 |

---

## 5. セキュリティ設計

### 5.1 APIキー管理

**フロントエンド**
- localStorage に保存（暗号化なし）
- ユーザーが手動で入力
- ページロード時に読み込み
- リクエスト時にヘッダーまたはボディで送信

**バックエンド**
- APIキーはサーバーに保存しない
- リクエストごとに受け取り、一時的にメモリで使用
- ログに出力しない
- レスポンスに含めない

### 5.2 通信セキュリティ

- HTTPS通信のみ（Vercel/GCP標準）
- CORS設定: フロントエンドドメインのみ許可
- Rate limiting（FastAPI middleware）

### 5.3 入力検証

- Pydanticによるリクエストバリデーション
- ファイルパスのサニタイズ（パストラバーサル対策）
- 最大ファイルサイズ制限
- 許可された拡張子のみ処理（.md, .yaml, .csv, .xlsx）

### 5.4 データ保護（⭐ v3.0更新）

- **Firebase Authentication**: ID Tokenによるユーザー認証 ⭐ v3.0新規
- **マルチテナント分離**: チームごとにデータを完全分離 ⭐ v3.0新規
  - GCS: `teams/{team_id}/` フォルダで物理分離
  - ChromaDB: `team_{team_id}_notes` コレクションで論理分離
- **APIキー管理**: ユーザーが各自のAPIキーで外部サービス（OpenAI、Cohere）を利用
- **GCSバケット**: プロジェクト内で権限制御、サービスアカウント認証
- **ChromaDB**: 永続化ストレージに保存、チーム間データ漏洩防止

---

## 6. デプロイアーキテクチャ

### 6.1 フロントエンド (Vercel)

```
GitHub Repository
  │
  ├─→ Vercel Auto Deploy (main branch)
  │     │
  │     ├─→ Build: next build
  │     └─→ Deploy to Edge Network
  │
  └─→ Environment Variables:
        - NEXT_PUBLIC_API_URL=https://backend-url.run.app
```

### 6.2 バックエンド (Google Cloud Run)

```
Docker Build
  │
  ├─→ Dockerfile
  │     ├─→ FROM python:3.12-slim
  │     ├─→ COPY requirements.txt
  │     ├─→ RUN pip install -r requirements.txt
  │     ├─→ COPY backend/ /app/
  │     └─→ CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
  │
  ├─→ Push to Google Container Registry (GCR)
  │
  └─→ Deploy to Cloud Run
        ├─→ Service Name: jikkennote-backend
        ├─→ Region: asia-northeast1
        ├─→ Memory: 2GB
        ├─→ CPU: 2
        ├─→ Concurrency: 10
        ├─→ Min Instances: 0
        ├─→ Max Instances: 5
        └─→ Environment Variables:
              - GCS_BUCKET_NAME=jikkennote-storage
              - STORAGE_TYPE=gcs
              - FIREBASE_PROJECT_ID={project_id}  ⭐ v3.0新規
              - FIREBASE_CREDENTIALS={service_account_json}  ⭐ v3.0新規
```

### 6.3 ストレージ (Google Cloud Storage) ⭐ v3.0マルチテナント構造

```
GCS Bucket: jikkennote-storage
  │
  └─→ teams/  ⭐ v3.0新規: チームごとにデータ分離
        │
        ├─→ {team_id_1}/
        │     │
        │     ├─→ chroma-db/
        │     │     └─→ (ChromaDB persistent files per team)
        │     │
        │     ├─→ notes/
        │     │     ├─→ new/
        │     │     └─→ processed/  ⭐ v3.0更新: archived → processed
        │     │
        │     ├─→ prompts/
        │     │     └─→ *.yaml (saved prompts per team)
        │     │
        │     └─→ dictionary.yaml  (team-specific normalization dictionary)
        │
        ├─→ {team_id_2}/
        │     └─→ (同様の構造)
        │
        └─→ ...

⭐ v3.0変更点:
- チームごとに完全に独立したフォルダ構造
- `teams/{team_id}/` 配下に全てのデータを配置
- チーム間でのデータ漏洩を防止
- `archived/` → `processed/` に名称変更（削除せず保存）
```

---

## 7. パフォーマンス設計

### 7.1 フロントエンド最適化

- Next.js App Router: Server Components でサーバーサイドレンダリング
- Code splitting: 各ページで必要なコードのみロード
- Image optimization: Next.js Image component
- Caching: SWR for API responses

### 7.2 バックエンド最適化

**ChromaDB**
- インデックス最適化（デフォルト設定）
- バッチ処理（50件ずつ）
- 既存ID確認で増分更新

**LLM API**
- 非同期処理（複数クエリ生成を並列実行）
- ストリーミングレスポンス（agent.py）
- モデル選択による速度調整

**Cohere Reranking**
- Top 100→Top 10に絞り込み
- 関連度スコアでソート

### 7.3 目標性能指標

| 指標 | 目標値 |
|------|-------|
| 検索レスポンス | < 5秒 |
| ノート取り込み | < 10秒/件 |
| 新出単語抽出 | < 10秒/ノート |
| ページロード | < 2秒 |
| API応答時間 | < 3秒 |

### 7.4 パフォーマンス測定方法 ⭐ v3.0更新

#### 7.4.1 フロントエンド測定

**Web Vitals（Vercel Analytics）:**
```typescript
// Next.js built-in Web Vitals reporting
export function reportWebVitals(metric: NextWebVitalsMetric) {
  console.log(metric);
  // Vercel Analyticsに自動送信される
  // - LCP (Largest Contentful Paint): ページロード速度
  // - FID (First Input Delay): 入力応答性
  // - CLS (Cumulative Layout Shift): レイアウト安定性
  // - FCP (First Contentful Paint): 初回描画
  // - TTFB (Time to First Byte): サーバー応答時間
}
```

**手動測定（Performance API）:**
```typescript
// frontend/lib/performance.ts
export const measureApiCall = async (name: string, apiCall: () => Promise<any>) => {
  const startTime = performance.now();

  try {
    const result = await apiCall();
    const endTime = performance.now();
    const duration = endTime - startTime;

    console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`);

    // localStorageに記録（開発時のみ）
    if (process.env.NODE_ENV === 'development') {
      const metrics = JSON.parse(localStorage.getItem('perf_metrics') || '[]');
      metrics.push({ name, duration, timestamp: new Date().toISOString() });
      localStorage.setItem('perf_metrics', JSON.stringify(metrics.slice(-100))); // 最新100件保持
    }

    return result;
  } catch (error) {
    const endTime = performance.now();
    console.error(`[Performance Error] ${name}: ${(endTime - startTime).toFixed(2)}ms`, error);
    throw error;
  }
};

// 使用例
const searchResults = await measureApiCall('Search API', () =>
  fetch('/api/search', { method: 'POST', body: JSON.stringify(query) })
);
```

#### 7.4.2 バックエンド測定

**FastAPI Middleware（リクエスト時間測定）:**
```python
# backend/server.py
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # ログ出力
    print(f"[Performance] {request.method} {request.url.path}: {process_time:.3f}s")

    return response
```

**LangGraph ノード別測定:**
```python
# backend/agent.py
import time
from functools import wraps

def measure_node_performance(node_name: str):
    """ノードのパフォーマンスを測定するデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(state):
            start_time = time.time()
            result = func(state)
            elapsed = time.time() - start_time
            print(f"[Node Performance] {node_name}: {elapsed:.3f}s")
            return result
        return wrapper
    return decorator

@measure_node_performance("normalize")
def normalize_node(state: AgentState) -> AgentState:
    # 正規化処理
    ...

@measure_node_performance("query_generation")
def query_generation_node(state: AgentState) -> AgentState:
    # クエリ生成処理（LLM呼び出し）
    ...

@measure_node_performance("search")
def search_node(state: AgentState) -> AgentState:
    # ChromaDB検索 + Cohere Reranking
    ...

@measure_node_performance("compare")
def compare_node(state: AgentState) -> AgentState:
    # 比較分析処理（LLM呼び出し）
    ...
```

**ChromaDB検索時間測定:**
```python
# backend/chroma_sync.py
def search_with_timing(vectorstore, query, k=100):
    start = time.time()
    results = vectorstore.similarity_search(query, k=k)
    elapsed = time.time() - start
    print(f"[ChromaDB Search] {k} docs: {elapsed:.3f}s")
    return results
```

#### 7.4.3 Cloud Run監視（Google Cloud Monitoring）

**メトリクス収集:**
- **リクエスト数**: `/search`, `/ingest` など各エンドポイント別
- **レイテンシ分布**: P50, P95, P99
- **エラー率**: 4xx, 5xx エラーの割合
- **メモリ使用率**: コンテナのメモリ消費
- **CPU使用率**: コンテナのCPU消費
- **コールドスタート頻度**: インスタンス起動回数

**アラート設定:**
```yaml
# Cloud Monitoring Alert Policy
conditions:
  - displayName: "API response time > 5s"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"'
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_DELTA
      comparison: COMPARISON_GT
      thresholdValue: 5000  # 5秒
      duration: 300s  # 5分間継続

  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GT
      thresholdValue: 0.05
```

#### 7.4.4 本番環境での継続的測定

**ログ集約（Cloud Logging）:**
```python
# backend/logger.py
import logging
import json

# 構造化ログ設定
logging.basicConfig(
    format='%(message)s',
    level=logging.INFO
)

def log_performance_metrics(endpoint: str, duration: float, **kwargs):
    """パフォーマンスメトリクスを構造化ログとして出力"""
    log_entry = {
        "severity": "INFO",
        "type": "performance",
        "endpoint": endpoint,
        "duration_ms": round(duration * 1000, 2),
        **kwargs
    }
    logging.info(json.dumps(log_entry))

# 使用例
@app.post("/search")
async def search_endpoint(request: SearchRequest):
    start = time.time()
    result = perform_search(request)
    duration = time.time() - start

    log_performance_metrics(
        endpoint="/search",
        duration=duration,
        search_mode=request.search_mode,
        team_id=request.team_id,
        num_results=len(result.retrieved_docs)
    )

    return result
```

**週次パフォーマンスレポート:**
```bash
# Cloud Loggingからパフォーマンスデータを抽出
gcloud logging read 'jsonPayload.type="performance"' \
  --format=json \
  --freshness=7d \
  | jq -r '.[] | [.jsonPayload.endpoint, .jsonPayload.duration_ms] | @csv' \
  > performance_weekly.csv

# 統計値計算（Python/Pandas等で処理）
# - エンドポイント別の平均レスポンス時間
# - P50, P95, P99レイテンシ
# - 目標値との比較
```

---

## 8. エラーハンドリング設計

### 8.1 フロントエンド

**APIエラー**
```typescript
try {
  const result = await api.search(request);
} catch (error) {
  if (error.message.includes('401')) {
    alert('APIキーが無効です。設定ページで確認してください。');
  } else {
    alert(`エラー: ${error.message}`);
  }
}
```

**バリデーション**
```typescript
if (!purpose.trim() || !materials.trim() || !methods.trim()) {
  alert('目的・材料・方法は必須です。');
  return;
}
```

### 8.2 バックエンド

**HTTPException**
```python
from fastapi import HTTPException

if not openai_api_key:
    raise HTTPException(status_code=400, detail="OpenAI APIキーが必要です")
```

**Try-Catch with Logging**
```python
try:
    result = agent_graph.invoke(state)
except Exception as e:
    print(f"Agent error: {e}")
    raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")
```

**ChromaDB Error Handling**
```python
try:
    vectorstore.add_documents(documents=batch)
except Exception as e:
    print(f"バッチ {batch_num} エラー: {str(e)}")
    continue  # Skip failed batch
```

---

## 9. 拡張性設計

### 9.1 v3.0で実装済みの拡張機能 ⭐

**マルチテナント対応** ✅ v3.0実装済み
- Firebase Authenticationによるチーム認証
- GCSでフォルダ分離: `gs://bucket/teams/{team_id}/`
- ChromaDB コレクション分離: `team_{team_id}_notes`
- チーム管理ページ（ユーザー招待、権限管理）

**ハイブリッド検索** ✅ v3.0.1実装済み
- セマンティック検索 + キーワード検索の融合
- α値（0.0-1.0）で重み調整可能

**モデル2段階選択** ✅ v3.0実装済み
- クエリ生成・検索判定用LLM: 高速・コスト重視
- 要約生成用LLM: 高品質重視

### 9.2 将来的な機能追加候補

**通知機能**
- WebSocket 導入で進捗リアルタイム表示
- メール通知（取り込み完了、評価結果）

**高度な検索機能**
- ファセット検索（カテゴリ、日付範囲）
- フィルタリング（材料、手法）
- 保存された検索条件

**協働機能の強化**
- ノートへのコメント・アノテーション
- 変更履歴追跡・バージョン管理
- チーム内での検索履歴共有

### 9.3 モジュール追加ガイドライン

**新しいエンドポイント追加**
1. `server.py` に Pydantic モデル定義
2. エンドポイント実装 (`@app.post("/new-endpoint")`)
3. `frontend/lib/api.ts` にクライアント関数追加
4. フロントエンドページで呼び出し

**新しいノード追加（LangGraph）**
1. `agent.py` に新ノード関数定義
2. `AgentState` に必要なフィールド追加
3. ワークフローに `.add_node()` でノード追加
4. `.add_edge()` でフロー接続

**新しいページ追加**
1. `frontend/app/{page-name}/page.tsx` 作成
2. ナビゲーションに追加
3. API 呼び出しロジック実装
4. UI コンポーネント組み立て

---

## 10. テスト設計

### 10.1 フロントエンドテスト

**E2E Tests (Playwright)**
- `tests/e2e/prompt-management.spec.ts`
- `tests/e2e/evaluation.spec.ts`
- `tests/e2e/search.spec.ts` (未実装)
- `tests/e2e/ingest.spec.ts` (未実装)

**Unit Tests**
- React Testing Library
- Jest
- 各コンポーネントの動作検証

### 10.2 バックエンドテスト

**API Tests (pytest)**
```python
def test_search_endpoint():
    response = client.post("/search", json={
        "purpose": "テスト",
        "materials": "試薬A",
        "methods": "方法1",
        "openai_api_key": "sk-test",
        "cohere_api_key": "test"
    })
    assert response.status_code == 200
```

**Integration Tests**
- ChromaDB との連携テスト
- GCS との連携テスト
- LangGraph ワークフローテスト

### 10.3 テストカバレッジ目標

| コンポーネント | 目標カバレッジ |
|--------------|--------------|
| API Endpoints | 80%+ |
| Core Modules | 70%+ |
| UI Components | 60%+ |

### 10.4 v3.0新機能テストケース ⭐

#### Firebase認証テスト
```typescript
describe('Firebase Authentication', () => {
  test('Google Loginが成功し、IDトークンを取得できる', async () => {
    const { user, idToken } = await signInWithGoogle();
    expect(user).toBeDefined();
    expect(idToken).toMatch(/^[\w-]+\.[\w-]+\.[\w-]+$/);
  });

  test('認証ヘッダーが正しく設定される', async () => {
    const token = 'test-firebase-token';
    const headers = getAuthHeaders(token, 'team-123');
    expect(headers['Authorization']).toBe(`Bearer ${token}`);
    expect(headers['X-Team-ID']).toBe('team-123');
  });
});
```

#### マルチテナント分離テスト
```python
def test_team_data_isolation():
    """異なるチームのデータが完全に分離されていることを確認"""
    # Team Aでノート追加
    response_a = client.post("/ingest/upload",
        headers={"X-Team-ID": "team-a"},
        files={"file": test_note_a}
    )
    assert response_a.status_code == 200

    # Team Bで検索（Team Aのノートが見えないこと）
    response_b = client.post("/search",
        headers={"X-Team-ID": "team-b"},
        json={"purpose": "test", ...}
    )
    results = response_b.json()["retrieved_docs"]
    assert test_note_a["id"] not in results
```

#### ハイブリッド検索テスト
```python
def test_hybrid_search():
    """ハイブリッド検索モードのテスト"""
    # セマンティック検索
    response_semantic = client.post("/search", json={
        "search_mode": "semantic",
        ...
    })

    # キーワード検索
    response_keyword = client.post("/search", json={
        "search_mode": "keyword",
        ...
    })

    # ハイブリッド検索（α=0.5）
    response_hybrid = client.post("/search", json={
        "search_mode": "hybrid",
        "hybrid_alpha": 0.5,
        ...
    })

    assert response_hybrid.status_code == 200
    # ハイブリッド結果がセマンティックとキーワードの中間であることを確認
```

#### モデル2段階選択テスト
```python
def test_two_stage_model_selection():
    """検索判定用と要約用のLLMモデルが分離されていることを確認"""
    response = client.post("/search", json={
        "search_llm_model": "gpt-4o-mini",
        "summary_llm_model": "gpt-4o",
        ...
    })
    assert response.status_code == 200
    # AgentStateに両方のモデルが設定されていることを確認
```

#### 再検索機能テスト
```typescript
describe('Re-search Feature', () => {
  test('再検索モーダルが開き、重点指示を変更して再検索できる', async () => {
    render(<SearchPage />);

    // 初回検索
    await performSearch();

    // 再検索ボタンをクリック
    fireEvent.click(screen.getByText('再検索'));

    // モーダルが表示される
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // 重点指示を変更
    const input = screen.getByPlaceholderText('重点指示を入力...');
    fireEvent.change(input, { target: { value: '安全性を重視' } });

    // 再検索実行
    fireEvent.click(screen.getByText('再検索実行'));

    // 元のクエリが保持され、重点指示のみが更新されたことを確認
    expect(mockApiCall).toHaveBeenCalledWith(expect.objectContaining({
      instruction: '安全性を重視'
    }));
  });
});
```

#### コピー機能強化テスト
```typescript
describe('Enhanced Copy Feature', () => {
  test('ビューワーから検索画面へ全項目がコピーされる', async () => {
    const note = {
      sections: {
        purpose: 'テスト目的',
        materials: 'エタノール',
        methods: '攪拌'
      }
    };

    copyAllToSearch(note);

    const copied = JSON.parse(localStorage.getItem('copied_search_query'));
    expect(copied.purpose).toBe('テスト目的');
    expect(copied.materials).toBe('エタノール');
    expect(copied.methods).toBe('攪拌');
  });
});
```

#### 評価機能改善テスト
```python
def test_evaluation_with_at_5_metrics():
    """@5メトリクスが正しく計算されることを確認"""
    response = client.post("/evaluate", json={
        "test_cases": [...],
        ...
    })

    result = response.json()["results"][0]
    assert "ndcg_5" in result["metrics"]
    assert "precision_5" in result["metrics"]
    assert result["metrics"]["ndcg_5"] >= 0.0
    assert result["metrics"]["ndcg_5"] <= 1.0
```

---

## 11. 運用設計

### 11.1 ログ設計

**フロントエンド**
- Console.log (開発環境のみ)
- エラー追跡: Sentry (本番環境)

**バックエンド**
- Python logging module
- ログレベル: DEBUG, INFO, WARNING, ERROR
- 出力先: stdout (Cloud Run Logs)

**重要ログ**
- API リクエスト/レスポンス
- ChromaDB 操作
- エラー詳細（スタックトレース含む）

### 11.2 モニタリング

**Vercel**
- アクセス数、レスポンスタイム
- ビルド成功/失敗

**Google Cloud Run**
- CPU/メモリ使用率
- リクエスト数、レスポンスタイム
- エラーレート

**ChromaDB**
- ドキュメント数
- 検索クエリ応答時間

### 11.3 バックアップ戦略

**ChromaDB**
- GCS 自動同期（毎回 ingest 後）
- 手動バックアップ機能（設定画面）

**正規化辞書**
- GCS に保存（自動同期）
- バージョン管理（更新日時記録）

**プロンプト**
- YAML ファイル（GCS）
- エクスポート機能

---

## 12. 設計原則

### 12.1 コーディング規約

**TypeScript**
- 厳密な型定義（`strict: true`）
- 関数型プログラミング推奨
- Async/Await 使用

**Python**
- PEP 8 準拠
- Type hints 必須
- Docstring 記述

### 12.2 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| ファイル | kebab-case | `prompt-management.tsx` |
| コンポーネント | PascalCase | `SearchPage` |
| 関数 | camelCase | `handleSave` |
| 定数 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| 型 | PascalCase | `SearchRequest` |

### 12.3 ディレクトリ構成

```
jikkennote-search/
├─ frontend/
│  ├─ app/
│  │  ├─ page.tsx (Search)
│  │  ├─ history/
│  │  ├─ viewer/
│  │  ├─ ingest/
│  │  ├─ dictionary/
│  │  ├─ evaluate/
│  │  └─ settings/
│  ├─ components/
│  │  ├─ Button.tsx
│  │  ├─ Input.tsx
│  │  └─ ...
│  ├─ lib/
│  │  └─ api.ts
│  └─ tests/
│     └─ e2e/
│
├─ backend/
│  ├─ server.py
│  ├─ agent.py
│  ├─ ingest.py
│  ├─ utils.py
│  ├─ chroma_sync.py
│  ├─ storage.py
│  ├─ prompt_manager.py
│  ├─ config.py
│  ├─ prompts/
│  │  └─ *.yaml
│  └─ chroma_db_config.json
│
├─ docs/
│  ├─ 01_REQUIREMENTS.md
│  ├─ 02_DESIGN.md (this file)
│  ├─ 03_API.md
│  └─ 04_DEVELOPMENT.md
│
└─ README.md
```

---

## 10. v3.0 新機能詳細設計 ⭐

### 10.1 マルチテナント対応

#### 10.1.1 認証フロー

```
User Access
  │
  ├─→ Firebase Authentication (Google Login)
  │     └─→ ID Token取得
  │
  ├─→ Team Selection UI
  │     └─→ ユーザーが所属するチーム一覧を表示
  │     └─→ チーム選択 → Team ID保存（localStorage）
  │
  └─→ All API Requests
        └─→ Headers: Authorization: Bearer {ID_TOKEN}
        └─→ Headers: X-Team-ID: {TEAM_ID}
```

#### 10.1.2 データ分離

**GCS構造:**
```
gs://jikkennote-storage/
└── teams/
    ├── team_abc123/
    │   ├── chroma-db/
    │   ├── notes/
    │   │   ├── new/
    │   │   └── processed/
    │   ├── dictionary.yaml
    │   └── prompts/
    └── team_xyz789/
        └── (同じ構造)
```

**アクセス制御:**
- バックエンドで`X-Team-ID`を検証
- 各APIエンドポイントでチームIDを基にパス構築
- 他チームのデータには絶対にアクセスできない

#### 10.1.3 Firebase SDK初期化（Frontend）

**Firebase設定ファイル:**
```typescript
// frontend/lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Google ログイン
export const signInWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();
    localStorage.setItem('firebase_token', idToken);
    return { user: result.user, idToken };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// ログアウト
export const logOut = async () => {
  try {
    await signOut(auth);
    localStorage.removeItem('firebase_token');
    localStorage.removeItem('current_team_id');
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

// トークン更新（有効期限: 1時間）
export const refreshIdToken = async () => {
  const user = auth.currentUser;
  if (user) {
    const idToken = await user.getIdToken(true); // force refresh
    localStorage.setItem('firebase_token', idToken);
    return idToken;
  }
  return null;
};
```

**認証状態の監視:**
```typescript
// frontend/lib/useAuth.ts
import { useEffect, useState } from 'react';
import { auth, refreshIdToken } from './firebase';
import { onAuthStateChanged, User } from 'firebase/auth';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);

      if (currentUser) {
        // トークンを定期的に更新（50分ごと）
        const tokenRefreshInterval = setInterval(async () => {
          await refreshIdToken();
        }, 50 * 60 * 1000);

        return () => clearInterval(tokenRefreshInterval);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return { user, loading };
};
```

#### 10.1.4 Firebase SDK初期化（Backend）

**Firebase Admin SDK設定:**
```python
# backend/firebase_admin.py
import firebase_admin
from firebase_admin import credentials, auth
import os

# Firebase Admin SDK初期化
def initialize_firebase_admin():
    """Firebase Admin SDKを初期化"""
    if not firebase_admin._apps:
        # サービスアカウントキーのパス（環境変数または直接指定）
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized")

# トークン検証
def verify_firebase_token(id_token: str) -> dict:
    """
    Firebase ID Tokenを検証し、ユーザー情報を返す

    Args:
        id_token: Firebase ID Token

    Returns:
        decoded_token: {
            'uid': str,
            'email': str,
            'name': str,
            ...
        }

    Raises:
        HTTPException: トークンが無効な場合
    """
    from fastapi import HTTPException

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="無効なFirebase ID Tokenです")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Firebase ID Tokenの有効期限が切れています")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"認証エラー: {str(e)}")

# チーム所属確認
def verify_team_membership(user_id: str, team_id: str) -> bool:
    """
    ユーザーが指定されたチームに所属しているか確認

    Args:
        user_id: Firebase UID
        team_id: チームID

    Returns:
        bool: 所属している場合True
    """
    # Firestore/Cloud SQLからユーザーのチーム所属情報を取得
    # PoC仕様のため、簡易実装（GCSのメタデータまたはFirestore使用）
    from .storage import get_storage
    storage = get_storage()

    # teams/{team_id}/members/{user_id}.json の存在確認
    member_file = f"teams/{team_id}/members/{user_id}.json"
    try:
        storage.read_file(member_file)
        return True
    except:
        return False
```

**認証ミドルウェア:**
```python
# backend/auth_middleware.py
from fastapi import HTTPException, Header
from .firebase_admin import verify_firebase_token, verify_team_membership
from typing import Optional

async def authenticate_request(
    authorization: Optional[str] = Header(None),
    x_team_id: Optional[str] = Header(None)
) -> dict:
    """
    リクエストを認証し、ユーザー情報とチームIDを返す

    Args:
        authorization: "Bearer {id_token}"
        x_team_id: チームID

    Returns:
        {
            'user_id': str,
            'email': str,
            'team_id': str
        }

    Raises:
        HTTPException: 認証失敗時
    """
    # Authorizationヘッダーチェック
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorizationヘッダーが必要です")

    id_token = authorization.replace("Bearer ", "")

    # トークン検証
    decoded_token = verify_firebase_token(id_token)
    user_id = decoded_token['uid']
    email = decoded_token.get('email', '')

    # X-Team-IDヘッダーチェック
    if not x_team_id:
        raise HTTPException(status_code=400, detail="X-Team-IDヘッダーが必要です")

    # チーム所属確認
    if not verify_team_membership(user_id, x_team_id):
        raise HTTPException(status_code=403, detail="このチームへのアクセス権限がありません")

    return {
        'user_id': user_id,
        'email': email,
        'team_id': x_team_id
    }
```

**エンドポイントでの使用例:**
```python
# backend/server.py
from .auth_middleware import authenticate_request

@app.post("/search")
async def search(
    request: SearchRequest,
    auth_info: dict = Depends(authenticate_request)
):
    """
    検索エンドポイント（認証必須）

    auth_info = {
        'user_id': 'firebase_uid_123',
        'email': 'user@example.com',
        'team_id': 'team_abc123'
    }
    """
    team_id = auth_info['team_id']

    # チーム別のデータパスを構築
    team_chroma_path = f"teams/{team_id}/chroma-db"
    team_dictionary_path = f"teams/{team_id}/dictionary.yaml"

    # 以降の処理...
```

#### 10.1.5 チーム選択UI状態遷移

**状態遷移図:**
```
[未ログイン]
   │
   ├─→ Googleログインボタンクリック
   │
[Firebase認証中]
   │
   ├─→ 認証成功
   │     └─→ ID Token取得 → localStorage保存
   │
[チーム選択画面]
   │
   ├─→ GET /teams でチーム一覧取得
   │     └─→ ユーザーが所属するチーム表示
   │
   ├─→ チーム選択
   │     └─→ current_team_id を localStorage保存
   │
   ├─→ 新規チーム作成
   │     └─→ POST /teams/create → 招待コード発行
   │
   ├─→ チームに参加
   │     └─→ 招待コード入力 → POST /teams/join
   │
[メイン画面（検索/履歴/設定等）]
   │
   ├─→ 全APIリクエストに以下を付与:
   │     - Authorization: Bearer {firebase_token}
   │     - X-Team-ID: {current_team_id}
   │
   ├─→ チーム切り替え
   │     └─→ [チーム選択画面]に戻る
   │
   └─→ ログアウト
         └─→ localStorage削除 → [未ログイン]
```

**チーム選択UIコンポーネント:**
```typescript
// frontend/components/TeamSelector.tsx
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Team {
  id: string;
  name: string;
  role: 'admin' | 'member';
  created_at: string;
}

export const TeamSelector = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [inviteCode, setInviteCode] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    const token = localStorage.getItem('firebase_token');
    const response = await fetch(`${API_URL}/teams`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    setTeams(data.teams);
  };

  const selectTeam = (teamId: string) => {
    localStorage.setItem('current_team_id', teamId);
    router.push('/search'); // メイン画面へ遷移
  };

  const joinTeam = async () => {
    const token = localStorage.getItem('firebase_token');
    const response = await fetch(`${API_URL}/teams/join`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ invite_code: inviteCode })
    });

    if (response.ok) {
      await fetchTeams(); // チーム一覧を再取得
      setInviteCode('');
    }
  };

  return (
    <div className="team-selector">
      <h2>チームを選択</h2>

      {teams.map(team => (
        <div key={team.id} className="team-card" onClick={() => selectTeam(team.id)}>
          <h3>{team.name}</h3>
          <span className="role-badge">{team.role}</span>
        </div>
      ))}

      <div className="actions">
        <button onClick={() => setShowCreateModal(true)}>
          新規チーム作成
        </button>

        <div className="join-team">
          <input
            type="text"
            placeholder="招待コードを入力"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
          />
          <button onClick={joinTeam}>チームに参加</button>
        </div>
      </div>
    </div>
  );
};
```

#### 10.1.6 トークン管理とエラーハンドリング

**トークン有効期限対策:**
```typescript
// frontend/lib/api.ts
export const callAPI = async (endpoint: string, options: RequestInit = {}) => {
  let token = localStorage.getItem('firebase_token');
  const teamId = localStorage.getItem('current_team_id');

  // リクエスト実行
  let response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'X-Team-ID': teamId || '',
    }
  });

  // トークン期限切れの場合、リフレッシュして再試行
  if (response.status === 401) {
    const newToken = await refreshIdToken();

    if (!newToken) {
      // リフレッシュ失敗 → ログイン画面へ
      localStorage.clear();
      window.location.href = '/login';
      throw new Error('セッションが期限切れです。再ログインしてください。');
    }

    // 新しいトークンで再試行
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${newToken}`,
        'X-Team-ID': teamId || '',
      }
    });
  }

  // チーム権限エラー
  if (response.status === 403) {
    alert('このチームへのアクセス権限がありません。');
    window.location.href = '/teams'; // チーム選択画面へ
    throw new Error('Access denied');
  }

  return response;
};
```

**エラーハンドリングパターン:**
```typescript
// 例: 検索API呼び出し
const search = async (query: SearchRequest) => {
  try {
    const response = await callAPI('/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query)
    });

    return await response.json();
  } catch (error) {
    if (error.message.includes('期限切れ')) {
      // セッション期限切れ → ログイン画面へ自動遷移（callAPI内で処理済み）
    } else if (error.message.includes('Access denied')) {
      // 権限エラー → チーム選択画面へ自動遷移（callAPI内で処理済み）
    } else {
      // その他のエラー
      console.error('Search error:', error);
      alert('検索に失敗しました。もう一度お試しください。');
    }
    throw error;
  }
};
```

### 10.2 ノート取り込み改善

#### 10.2.1 ローカルファイルアップロード

**UI Flow:**
```
Ingest Page
  │
  ├─→ ファイル選択ボタン (<input type="file" accept=".md" multiple>)
  │     └─→ ファイルリスト表示
  │
  ├─→ アップロードボタン
  │     └─→ FormData生成
  │     └─→ POST /ingest/upload
  │           ├─ Headers: X-Team-ID
  │           └─ Body: files[] (multipart/form-data)
  │
  └─→ Backend処理
        ├─→ teams/{team_id}/notes/new/ に保存
        ├─→ 辞書自動抽出（Sudachi + LLM）
        ├─→ ユーザー確認UI表示
        ├─→ Embedding生成 → ChromaDB追加
        └─→ teams/{team_id}/notes/processed/ に移動
```

#### 10.2.2 Sudachi + LLM 辞書抽出

**処理フロー:**
```python
# 1. Sudachi形態素解析
from sudachipy import Dictionary
tokenizer = Dictionary().create()
tokens = tokenizer.tokenize(note_content, mode=TokenizeMode.C)

# 2. 化学物質・作業名候補を抽出
candidates = [token.surface() for token in tokens if is_technical_term(token)]

# 3. LLMで判定
for candidate in candidates:
    similar_terms = search_in_dictionary(candidate)

    llm_prompt = f"""
    新出単語: {candidate}
    既存辞書の類似語: {similar_terms}

    これは以下のどれか判定してください:
    1. 複合語（例: 「抗原抗体反応」 vs 「抗原」「抗体」）
    2. 表記揺れ（例: 「こうげんこうたい反応」 → 「抗原抗体反応」）
    3. 新規用語
    """

    llm_response = llm.invoke(llm_prompt)

    # 4. ユーザー確認UIに渡す
    return {"candidate": candidate, "type": llm_response.type, "similar": similar_terms}
```

**ユーザー確認UI:**
- 新出単語リスト表示
- 各単語に「複合語」「表記揺れ」「新規」ラベル
- 表記揺れの場合、紐付け先を選択
- 承認/却下ボタン

#### 10.2.3 API設計（POST /ingest/upload）

**エンドポイント詳細:**
```python
# backend/server.py
from fastapi import UploadFile, File, Form
from typing import List

@app.post("/ingest/upload")
async def ingest_upload(
    files: List[UploadFile] = File(...),
    auth_info: dict = Depends(authenticate_request)
):
    """
    ローカルファイルをアップロードしてノート取り込み

    Args:
        files: アップロードされたMarkdownファイルのリスト
        auth_info: 認証情報（Firebase + Team ID）

    Returns:
        {
            "success": bool,
            "message": str,
            "uploaded_files": List[str],  # アップロードされたファイル名
            "new_terms": List[NewTerm],  # 新出単語候補
            "next_step": str  # "confirm_terms" | "ingest_complete"
        }
    """
    team_id = auth_info['team_id']
    uploaded_files = []
    new_terms = []

    # 1. ファイルをteams/{team_id}/notes/new/に保存
    storage = get_storage()
    for file in files:
        # ファイル名検証
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail=f"Markdownファイル(.md)のみ対応しています: {file.filename}")

        # ファイルサイズ制限（10MB）
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"ファイルサイズが大きすぎます（10MB以下）: {file.filename}")

        # 保存
        file_path = f"teams/{team_id}/notes/new/{file.filename}"
        storage.write_file(file_path, content.decode('utf-8'))
        uploaded_files.append(file.filename)

    # 2. 新出単語抽出
    note_contents = []
    note_ids = []

    for filename in uploaded_files:
        file_path = f"teams/{team_id}/notes/new/{filename}"
        content = storage.read_file(file_path)
        note_contents.append(content)

        # ノートIDを抽出（ファイル名またはマークダウン内から）
        note_id = extract_note_id(content) or filename.replace('.md', '')
        note_ids.append(note_id)

    # /ingest/analyzeを内部的に呼び出し
    new_terms = await analyze_new_terms(note_ids, note_contents, auth_info['openai_api_key'])

    # 3. 新出単語があればユーザー確認待ち、なければ即座に取り込み
    if new_terms:
        return {
            "success": True,
            "message": f"{len(uploaded_files)}件のノートをアップロードしました。新出単語の確認が必要です。",
            "uploaded_files": uploaded_files,
            "new_terms": new_terms,
            "next_step": "confirm_terms"
        }
    else:
        # 新出単語がない場合、即座に取り込み
        ingest_result = await ingest_notes(team_id, auth_info['openai_api_key'])
        return {
            "success": True,
            "message": f"{len(uploaded_files)}件のノートを取り込みました。",
            "uploaded_files": uploaded_files,
            "new_terms": [],
            "next_step": "ingest_complete",
            "new_notes": ingest_result['new_notes'],
            "skipped_notes": ingest_result['skipped_notes']
        }
```

**Request/Response Schema:**
```python
# リクエスト
# Content-Type: multipart/form-data
# files: List[UploadFile]  # Markdownファイル（複数可）

# レスポンス
class IngestUploadResponse(BaseModel):
    success: bool
    message: str
    uploaded_files: List[str]
    new_terms: List[NewTerm]  # 新出単語候補
    next_step: Literal["confirm_terms", "ingest_complete"]
    new_notes: Optional[List[str]] = None  # 取り込み完了時のノートID
    skipped_notes: Optional[List[str]] = None  # スキップされたノートID

class NewTerm(BaseModel):
    term: str
    type: Literal["compound", "variant", "new"]  # 複合語、表記揺れ、新規
    similar_terms: List[str]  # 類似候補
    llm_suggestion: str  # LLMの判定理由
```

**Frontend実装:**
```typescript
// frontend/app/ingest/page.tsx
const uploadNotes = async (files: File[]) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await callAPI('/ingest/upload', {
    method: 'POST',
    body: formData,
    // Content-Typeは自動設定される（multipart/form-data）
  });

  const result = await response.json();

  if (result.next_step === 'confirm_terms') {
    // 新出単語確認UIを表示
    setNewTerms(result.new_terms);
    setShowTermConfirmModal(true);
  } else {
    // 取り込み完了
    alert(`取り込み完了: ${result.new_notes.length}件`);
    setResult(result);
  }
};
```

#### 10.2.4 Google Drive連携設計

**Google Drive API統合:**
```python
# backend/google_drive.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

class GoogleDriveClient:
    """Google Drive APIクライアント"""

    def __init__(self, credentials_json: dict):
        """
        Args:
            credentials_json: Google OAuth2認証情報
        """
        self.creds = Credentials.from_authorized_user_info(credentials_json)
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files(self, folder_id: str, mime_type: str = 'text/markdown') -> List[dict]:
        """
        指定フォルダ内のファイル一覧を取得

        Args:
            folder_id: Google DriveフォルダID
            mime_type: MIMEタイプ（デフォルト: text/markdown）

        Returns:
            [
                {
                    'id': 'file_id',
                    'name': 'note.md',
                    'modifiedTime': '2025-01-15T10:00:00.000Z'
                },
                ...
            ]
        """
        query = f"'{folder_id}' in parents and mimeType='{mime_type}' and trashed=false"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()

        return results.get('files', [])

    def download_file(self, file_id: str) -> str:
        """
        ファイルをダウンロード

        Args:
            file_id: Google DriveファイルID

        Returns:
            ファイル内容（文字列）
        """
        request = self.service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        return file_buffer.getvalue().decode('utf-8')

    def get_folder_changes(self, folder_id: str, page_token: str = None) -> dict:
        """
        フォルダの変更を監視

        Args:
            folder_id: Google DriveフォルダID
            page_token: 前回のページトークン（初回はNone）

        Returns:
            {
                'changes': [{'fileId': '...', 'type': 'file', 'removed': False}, ...],
                'newStartPageToken': '...'
            }
        """
        if page_token is None:
            # 初回: 現在のページトークンを取得
            response = self.service.changes().getStartPageToken().execute()
            page_token = response.get('startPageToken')

        changes = self.service.changes().list(
            pageToken=page_token,
            spaces='drive',
            fields='changes(fileId, removed, file(id, name, parents)), newStartPageToken'
        ).execute()

        # 指定フォルダ内の変更のみフィルタ
        filtered_changes = [
            change for change in changes.get('changes', [])
            if not change.get('removed') and
               folder_id in change.get('file', {}).get('parents', [])
        ]

        return {
            'changes': filtered_changes,
            'newStartPageToken': changes.get('newStartPageToken')
        }
```

**Google Drive連携エンドポイント:**
```python
# backend/server.py
@app.post("/google-drive/connect")
async def connect_google_drive(
    request: GoogleDriveConnectRequest,
    auth_info: dict = Depends(authenticate_request)
):
    """
    Google Driveフォルダを接続

    Args:
        folder_id: Google DriveフォルダID
        credentials: Google OAuth2認証情報

    Returns:
        {
            "success": True,
            "message": "Google Driveフォルダを接続しました",
            "folder_name": "実験ノート",
            "file_count": 15
        }
    """
    team_id = auth_info['team_id']

    # Google Drive接続情報を保存
    storage = get_storage()
    config = {
        "folder_id": request.folder_id,
        "credentials": request.credentials,
        "connected_at": datetime.now().isoformat()
    }
    storage.write_file(
        f"teams/{team_id}/google_drive_config.json",
        json.dumps(config)
    )

    # フォルダ内のファイル数を取得
    drive_client = GoogleDriveClient(request.credentials)
    files = drive_client.list_files(request.folder_id)

    return {
        "success": True,
        "message": "Google Driveフォルダを接続しました",
        "file_count": len(files)
    }

@app.post("/google-drive/sync")
async def sync_google_drive(
    auth_info: dict = Depends(authenticate_request)
):
    """
    Google Driveフォルダと同期（新規ファイルをダウンロード）

    Returns:
        {
            "success": True,
            "new_files": ["note1.md", "note2.md"],
            "next_step": "confirm_terms" | "ingest_complete"
        }
    """
    team_id = auth_info['team_id']
    storage = get_storage()

    # Google Drive設定を読み込み
    config_path = f"teams/{team_id}/google_drive_config.json"
    config = json.loads(storage.read_file(config_path))

    drive_client = GoogleDriveClient(config['credentials'])
    folder_id = config['folder_id']

    # 新規ファイルを取得
    page_token = config.get('page_token')
    changes = drive_client.get_folder_changes(folder_id, page_token)

    new_files = []
    for change in changes['changes']:
        file_id = change['fileId']
        file_name = change['file']['name']

        # ダウンロード
        content = drive_client.download_file(file_id)

        # teams/{team_id}/notes/new/に保存
        storage.write_file(f"teams/{team_id}/notes/new/{file_name}", content)
        new_files.append(file_name)

    # ページトークンを更新
    config['page_token'] = changes['newStartPageToken']
    storage.write_file(config_path, json.dumps(config))

    # 新出単語抽出 + 取り込み（/ingest/upload と同じフロー）
    # ...

    return {
        "success": True,
        "new_files": new_files,
        "next_step": "confirm_terms"  # or "ingest_complete"
    }
```

**Frontend実装（Google Drive連携）:**
```typescript
// frontend/app/ingest/page.tsx
const connectGoogleDrive = async () => {
  // Google OAuth2フロー（Firebase Authenticationとは別）
  const credentials = await authenticateWithGoogle();

  // フォルダID入力
  const folderId = prompt('Google DriveフォルダIDを入力してください');

  const response = await callAPI('/google-drive/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      folder_id: folderId,
      credentials: credentials
    })
  });

  const result = await response.json();
  alert(`接続完了: ${result.file_count}件のファイルが見つかりました`);
};

const syncGoogleDrive = async () => {
  const response = await callAPI('/google-drive/sync', {
    method: 'POST'
  });

  const result = await response.json();

  if (result.next_step === 'confirm_terms') {
    // 新出単語確認UIを表示
    setNewTerms(result.new_terms);
    setShowTermConfirmModal(true);
  } else {
    alert(`同期完了: ${result.new_files.length}件の新規ノートを取り込みました`);
  }
};
```

#### 10.2.5 アーカイブ方針

**取り込み済みノートの扱い:**
- **v2.0まで**: 取り込み後、`notes/new/`から削除またはarchiveフォルダに移動
- **v3.0**: `notes/processed/`に移動し、削除しない

**理由:**
- Embeddingモデル変更時、ChromaDBをリセットして全ノート再取り込みが必要
- `processed/`に保存しておくことで、再取り込みが容易

**実装:**
```python
# backend/ingest.py
def move_to_processed(team_id: str, note_filename: str):
    """
    取り込み済みノートをprocessed/に移動

    Args:
        team_id: チームID
        note_filename: ノートファイル名
    """
    storage = get_storage()

    source_path = f"teams/{team_id}/notes/new/{note_filename}"
    dest_path = f"teams/{team_id}/notes/processed/{note_filename}"

    # 移動
    content = storage.read_file(source_path)
    storage.write_file(dest_path, content)
    storage.delete_file(source_path)

    print(f"Moved {note_filename} to processed/")
```

**UI表示:**
```typescript
// frontend/app/ingest/page.tsx
<div className="processed-notes">
  <h3>取り込み済みノート</h3>
  <p>Embeddingモデル変更時、これらのノートを再取り込みできます</p>
  <ul>
    {processedNotes.map(note => (
      <li key={note}>{note}</li>
    ))}
  </ul>
  <button onClick={reIngestProcessedNotes}>
    全ノート再取り込み（ChromaDBリセット後）
  </button>
</div>
```

### 10.3 モデル2段階選択

#### 10.3.1 設定ページUI

```typescript
// Settings Page
<div>
  <h3>検索・判定用LLM</h3>
  <select value={searchLLM} onChange={(e) => setSearchLLM(e.target.value)}>
    <option value="gpt-4o">gpt-4o</option>
    <option value="gpt-4o-mini">gpt-4o-mini</option>
    <option value="gpt-5">gpt-5 (新規)</option>
    <option value="gpt-5.1">gpt-5.1 (新規)</option>
    <option value="gpt-5.2">gpt-5.2 (新規、最新)</option>
  </select>

  <h3>要約生成用LLM</h3>
  <select value={summaryLLM} onChange={(e) => setSummaryLLM(e.target.value)}>
    <option value="gpt-3.5-turbo">gpt-3.5-turbo (推奨、高速)</option>
    <option value="gpt-4o-mini">gpt-4o-mini</option>
    <option value="gpt-4o">gpt-4o</option>
  </select>
</div>
```

#### 10.3.2 Backend処理

```python
# agent.py
class SearchAgent:
    def __init__(
        self,
        openai_api_key: str,
        cohere_api_key: str,
        search_llm_model: str = "gpt-4o-mini",  # 検索・判定用
        summary_llm_model: str = "gpt-3.5-turbo",  # 要約生成用
        ...
    ):
        # 検索・判定用LLM（正規化、クエリ生成、検索）
        self.search_llm = ChatOpenAI(
            model=search_llm_model,
            temperature=0,
            api_key=openai_api_key
        )

        # 要約生成用LLM（比較ノード）
        self.summary_llm = ChatOpenAI(
            model=summary_llm_model,
            temperature=0,
            api_key=openai_api_key
        )

    def _compare_node(self, state: AgentState):
        """比較・要約生成ノード（summary_llm使用）"""
        response = self.summary_llm.invoke(prompt)
        return {"messages": [response]}
```

### 10.4 再検索機能

#### 10.4.1 UI実装

```typescript
// Search Page
const [refinementInstruction, setRefinementInstruction] = useState('');

// 検索結果表示後
{result && (
  <div>
    <h2>検索結果</h2>
    {/* 結果表示 */}

    <div className="re-search-section">
      <h3>重点指示を追加して再検索</h3>
      <input
        type="text"
        placeholder="例: 材料の量に注目して..."
        value={refinementInstruction}
        onChange={(e) => setRefinementInstruction(e.target.value)}
      />
      <Button onClick={handleReSearch}>再検索</Button>
    </div>
  </div>
)}

const handleReSearch = async () => {
  const response = await api.search({
    purpose,  // そのまま
    materials,  // そのまま
    methods,  // そのまま
    instruction: refinementInstruction,  // 追加指示のみ更新
    ...
  });
  setResult(response);
};
```

### 10.5 評価機能改善

#### 10.5.1 CSV出力

```typescript
// Evaluate Page
const exportToCSV = (history: EvaluationHistory) => {
  const rows = [
    // ヘッダー
    ['条件ID', 'Embeddingモデル', 'LLMモデル', 'プロンプト名',
     'nDCG@10', 'Precision@10', 'Recall@10', 'MRR',
     ...Array.from({length: 10}, (_, i) => `正解${i+1}_検出ランク`)
    ],

    // データ行
    ...history.results.map(result => {
      const ranks = result.ground_truth.map(gt => {
        const found = result.candidates.find(c => c.noteId === gt.noteId);
        return found ? found.rank.toString() : '未検出';
      });

      return [
        result.condition_id,
        history.embedding_model,
        history.llm_model,
        history.promptName || 'デフォルト',
        result.metrics.ndcg_10.toFixed(3),
        result.metrics.precision_10.toFixed(3),
        result.metrics.recall_10.toFixed(3),
        result.metrics.mrr.toFixed(3),
        ...ranks
      ];
    })
  ];

  const csv = rows.map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `evaluation_${history.id}.csv`;
  a.click();
};
```

### 10.6 ハイブリッド検索 ⭐ 重要

#### 10.6.1 背景と問題

**現在の問題:**
- 全項目入力時：正しくヒット ✅
- 一部項目を「なし」にした場合：ヒットしなくなる ❌
- 例: ID1-2のノートと同じ材料・方法で検索しても、目的を「なし」にするとヒットしない

**原因分析:**
- セマンティック検索（Embedding）は文章の意味的類似性で検索
- 「目的」フィールドは文章が多く、セマンティック検索が適している
- 「材料」「方法」フィールドは固有名詞（化学物質名、作業名）が重要
- 固有名詞はキーワード検索の方が精度が高い可能性

#### 10.6.2 検索モード設計

**3つの検索モード:**

1. **セマンティック検索（デフォルト）**
   - 現在の実装
   - Embedding + ChromaDB
   - 文章の意味的類似性で検索

2. **キーワード検索**
   - BM25アルゴリズム
   - トークンの出現頻度と文書の長さを考慮
   - 固有名詞・専門用語に強い

3. **ハイブリッド検索（推奨）**
   - セマンティック + キーワードの組み合わせ
   - 両者のスコアを重み付けで統合
   - 最も精度が高い

#### 10.6.3 UI設計

**検索ページ:**
```typescript
// Search Page
const [searchMode, setSearchMode] = useState<'semantic' | 'keyword' | 'hybrid'>('semantic');
const [hybridAlpha, setHybridAlpha] = useState(0.7);  // セマンティックの重み

<div className="search-mode-section">
  <label>検索モード:</label>
  <select value={searchMode} onChange={(e) => setSearchMode(e.target.value)}>
    <option value="semantic">セマンティック検索（デフォルト）</option>
    <option value="keyword">キーワード検索</option>
    <option value="hybrid">ハイブリッド検索（推奨）</option>
  </select>

  {searchMode === 'hybrid' && (
    <div className="hybrid-config">
      <label>セマンティック重み: {hybridAlpha.toFixed(1)}</label>
      <input
        type="range"
        min="0"
        max="1"
        step="0.1"
        value={hybridAlpha}
        onChange={(e) => setHybridAlpha(parseFloat(e.target.value))}
      />
      <span className="weight-info">
        セマンティック: {(hybridAlpha * 100).toFixed(0)}%
        / キーワード: {((1 - hybridAlpha) * 100).toFixed(0)}%
      </span>
    </div>
  )}
</div>
```

**設定ページ（デフォルト値設定）:**
```typescript
// Settings Page
<div className="hybrid-search-settings">
  <h3>ハイブリッド検索設定</h3>
  <div>
    <label>デフォルト検索モード:</label>
    <select value={defaultSearchMode} onChange={handleDefaultSearchModeChange}>
      <option value="semantic">セマンティック検索</option>
      <option value="keyword">キーワード検索</option>
      <option value="hybrid">ハイブリッド検索</option>
    </select>
  </div>
  <div>
    <label>デフォルトセマンティック重み:</label>
    <input
      type="number"
      min="0"
      max="1"
      step="0.1"
      value={defaultHybridAlpha}
      onChange={handleDefaultHybridAlphaChange}
    />
    <span className="help-text">
      0.7が推奨（セマンティック70%、キーワード30%）
    </span>
  </div>
</div>
```

#### 10.6.4 Backend実装

**ChromaDBのハイブリッド検索API:**
```python
# agent.py - Search Node
def _search_node(self, state: AgentState):
    search_mode = state.get("search_mode", "semantic")
    hybrid_alpha = state.get("hybrid_alpha", 0.7)

    if search_mode == "semantic":
        # 従来のセマンティック検索
        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=100
        )

    elif search_mode == "keyword":
        # キーワード検索（BM25）
        results = self.chroma_collection.query(
            query_texts=[query_text],  # テキスト直接指定
            n_results=100,
            include=["documents", "metadatas", "distances"]
        )

    elif search_mode == "hybrid":
        # ハイブリッド検索
        # ChromaDBのネイティブサポートを使用
        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],  # セマンティック
            query_texts=[query_text],  # キーワード
            n_results=100,
            where=None,
            where_document=None,
            include=["documents", "metadatas", "distances"]
        )

        # スコア統合（alpha: セマンティックの重み）
        # ChromaDBが自動で統合するが、手動で調整も可能
        # score = alpha * semantic_score + (1 - alpha) * keyword_score

    # 以下、Cohere Rerankingなどの処理は共通
    reranked_results = self.cohere_rerank(results, query_text)

    return {"retrieved_docs": reranked_results[:10]}
```

**API Request/Response:**
```python
# server.py
class SearchRequest(BaseModel):
    purpose: str
    materials: str
    methods: str
    instruction: str = ""
    search_mode: Literal["semantic", "keyword", "hybrid"] = "semantic"  # 新規
    hybrid_alpha: float = 0.7  # 新規（0.0〜1.0）
    openai_api_key: str
    cohere_api_key: str
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    # ...

@app.post("/search")
async def search(request: SearchRequest):
    agent = SearchAgent(
        openai_api_key=request.openai_api_key,
        cohere_api_key=request.cohere_api_key,
        embedding_model=request.embedding_model,
        llm_model=request.llm_model,
        # ...
    )

    result = agent.run(
        purpose=request.purpose,
        materials=request.materials,
        methods=request.methods,
        instruction=request.instruction,
        search_mode=request.search_mode,  # 新規
        hybrid_alpha=request.hybrid_alpha,  # 新規
        # ...
    )

    return result
```

#### 10.6.5 実装詳細

**ChromaDBのハイブリッド検索サポート:**
- ChromaDB 0.4.0以降、BM25 + Embeddingのハイブリッド検索をネイティブサポート
- `query_embeddings`（セマンティック）と`query_texts`（キーワード）を同時に渡すことでハイブリッド検索が実行される
- スコア統合はChromaDB内部で自動実行

**スコア統合アルゴリズム:**
```python
# ChromaDB内部の処理（参考）
def hybrid_score(semantic_score, keyword_score, alpha=0.7):
    """
    alpha: セマンティックスコアの重み（0.0〜1.0）

    alpha = 1.0 → 完全にセマンティック検索
    alpha = 0.0 → 完全にキーワード検索
    alpha = 0.7 → セマンティック70%、キーワード30%（推奨）
    """
    return alpha * semantic_score + (1 - alpha) * keyword_score
```

**BM25アルゴリズム:**
- トークンの出現頻度（TF: Term Frequency）
- 文書全体でのトークンの希少性（IDF: Inverse Document Frequency）
- 文書の長さによる正規化
- 化学物質名のような固有名詞の検索に強い

#### 10.6.6 期待効果

**検索精度の向上:**
1. **目的のみの検索**
   - セマンティック検索で文脈を理解
   - 「〇〇の効果を調べる」→ 類似の目的を持つノートを発見

2. **材料のみの検索**
   - キーワード検索で固有名詞を正確に捕捉
   - 「エタノール 100ml」→ エタノールを含むノートを確実にヒット

3. **方法のみの検索**
   - ハイブリッド検索で手順と化学物質名の両方を考慮
   - 「エタノールを攪拌」→ 手順の意味とエタノールの名前の両方で検索

4. **部分検索の改善**
   - 一部フィールドを「なし」にした場合でも精度を維持
   - ID1-2問題の解決

**ユーザーの柔軟性:**
- 検索対象の特性に応じて最適なモードを選択
- デフォルトはセマンティックで、必要に応じて切り替え
- ハイブリッド検索の重みを調整して最適化

### 10.7 再検索機能詳細設計（FR-113）

#### 10.7.1 UI設計

**モーダル構成:**
```typescript
// frontend/types/search.ts
interface ReSearchModal {
  isOpen: boolean;
  originalQuery: {
    purpose: string;
    materials: string;
    methods: string;
  };
  refinementInstruction: string;
}
```

**配置:**
- **デスクトップ**: 検索結果画面の右上に「重点指示を追加して再検索」ボタン
- **モバイル**: 画面下部に固定表示（スティッキーボタン）

**UI実装:**
```typescript
// frontend/app/search/page.tsx
const [showReSearchModal, setShowReSearchModal] = useState(false);
const [refinementInstruction, setRefinementInstruction] = useState('');

// 検索結果表示後
{result && (
  <>
    <div className="search-results">
      {/* 検索結果表示 */}
    </div>

    {/* デスクトップ用ボタン */}
    <div className="re-search-button-desktop">
      <button
        onClick={() => setShowReSearchModal(true)}
        className="btn-secondary"
      >
        重点指示を追加して再検索
      </button>
    </div>

    {/* モバイル用固定ボタン */}
    <div className="re-search-button-mobile sticky-bottom">
      <button
        onClick={() => setShowReSearchModal(true)}
        className="btn-secondary btn-full-width"
      >
        重点指示を追加して再検索
      </button>
    </div>

    {/* 再検索モーダル */}
    <Modal isOpen={showReSearchModal} onClose={() => setShowReSearchModal(false)}>
      <h3>重点指示を追加して再検索</h3>

      <div className="original-query">
        <h4>元の検索条件</h4>
        <p><strong>目的:</strong> {query.purpose}</p>
        <p><strong>材料:</strong> {query.materials}</p>
        <p><strong>方法:</strong> {query.methods}</p>
      </div>

      <div className="refinement-input">
        <label>重点指示を入力</label>
        <textarea
          placeholder="例: 材料の量に注目して検索してください"
          value={refinementInstruction}
          onChange={(e) => setRefinementInstruction(e.target.value)}
          rows={3}
        />
      </div>

      <div className="modal-actions">
        <button onClick={handleReSearch} className="btn-primary">
          再検索
        </button>
        <button onClick={() => setShowReSearchModal(false)} className="btn-secondary">
          キャンセル
        </button>
      </div>
    </Modal>
  </>
)}
```

#### 10.7.2 データフロー

**シーケンス:**
```
User clicks "再検索" button
  ↓
Modal opens with original query pre-filled (read-only)
  ↓
User enters refinement instruction
  ↓
POST /search with:
  - purpose: (元のまま)
  - materials: (元のまま)
  - methods: (元のまま)
  - instruction: (新しい重点指示)
  - 他のパラメータ: (元のまま)
  ↓
Results replace current display
  ↓
Both searches saved to history:
  - originalSearch: { purpose, materials, methods }
  - refinedSearch: { purpose, materials, methods, instruction }
```

**再検索ハンドラー:**
```typescript
const handleReSearch = async () => {
  try {
    const response = await callAPI('/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        purpose: query.purpose,  // そのまま
        materials: query.materials,  // そのまま
        methods: query.methods,  // そのまま
        instruction: refinementInstruction,  // 追加指示のみ更新
        openai_api_key: apiKeys.openai,
        cohere_api_key: apiKeys.cohere,
        embedding_model: settings.embeddingModel,
        search_llm_model: settings.searchLLMModel,
        summary_llm_model: settings.summaryLLMModel,
        search_mode: settings.searchMode,
        hybrid_alpha: settings.hybridAlpha,
        custom_prompts: settings.customPrompts,
      })
    });

    const newResult = await response.json();
    setResult(newResult);

    // 履歴に両方の検索を保存
    saveToHistory({
      query: { ...query, instruction: refinementInstruction },
      result: newResult,
      timestamp: new Date().toISOString(),
      isRefinement: true,  // 再検索フラグ
      originalSearchId: currentSearchId,  // 元の検索ID
    });

    setShowReSearchModal(false);
    setRefinementInstruction('');
  } catch (error) {
    console.error('Re-search error:', error);
    alert('再検索に失敗しました。もう一度お試しください。');
  }
};
```

#### 10.7.3 履歴管理

**SearchHistory型拡張:**
```typescript
interface SearchHistory {
  id: string;
  timestamp: Date;
  query: {
    purpose: string;
    materials: string;
    methods: string;
    instruction?: string;
  };
  results: {
    noteId: string;
    score: number;
    rank: number;
  }[];
  embeddingModel: string;
  llmModel: string;
  isRefinement?: boolean;  // 再検索フラグ
  originalSearchId?: string;  // 元の検索ID（再検索の場合）
}
```

**履歴表示:**
```typescript
// frontend/app/history/page.tsx
<table className="history-table">
  <thead>
    <tr>
      <th>日時</th>
      <th>目的</th>
      <th>材料</th>
      <th>方法</th>
      <th>重点指示</th>
      <th>結果数</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    {history.map(item => (
      <tr key={item.id} className={item.isRefinement ? 'refinement-row' : ''}>
        <td>{new Date(item.timestamp).toLocaleString()}</td>
        <td>{item.query.purpose}</td>
        <td>{item.query.materials}</td>
        <td>{item.query.methods}</td>
        <td>
          {item.query.instruction || '-'}
          {item.isRefinement && (
            <span className="badge-refinement">再検索</span>
          )}
        </td>
        <td>{item.results.length}件</td>
        <td>
          <button onClick={() => restoreSearch(item)}>復元</button>
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

### 10.8 コピー機能強化詳細設計（FR-114）

#### 10.8.1 ビューワー画面のコピー機能

**UI配置:**
```typescript
// frontend/app/viewer/page.tsx
<div className="note-viewer">
  <div className="note-header">
    <h2>{note.id}</h2>

    {/* 一括コピーボタン */}
    <button onClick={copyAllToSearch} className="btn-primary">
      検索条件として一括コピー
    </button>
  </div>

  {/* 目的セクション */}
  <div className="section">
    <div className="section-header">
      <h3>目的</h3>
      <button onClick={() => copySectionToSearch('purpose')} className="btn-copy-small">
        <CopyIcon /> コピー
      </button>
    </div>
    <div className="section-content">
      {note.sections.purpose}
    </div>
  </div>

  {/* 材料セクション */}
  <div className="section">
    <div className="section-header">
      <h3>材料</h3>
      <button onClick={() => copySectionToSearch('materials')} className="btn-copy-small">
        <CopyIcon /> コピー
      </button>
    </div>
    <div className="section-content">
      {note.sections.materials}
    </div>
  </div>

  {/* 方法セクション */}
  <div className="section">
    <div className="section-header">
      <h3>方法</h3>
      <button onClick={() => copySectionToSearch('methods')} className="btn-copy-small">
        <CopyIcon /> コピー
      </button>
    </div>
    <div className="section-content">
      {note.sections.methods}
    </div>
  </div>
</div>
```

**コピー実装:**
```typescript
const copyAllToSearch = () => {
  // localStorageに保存
  localStorage.setItem('copied_search_query', JSON.stringify({
    purpose: note.sections.purpose,
    materials: note.sections.materials,
    methods: note.sections.methods,
  }));

  // トースト通知
  showToast({
    message: '検索ページに遷移します',
    type: 'success',
    duration: 2000
  });

  // 検索ページへ遷移
  router.push('/search');
};

const copySectionToSearch = (section: 'purpose' | 'materials' | 'methods') => {
  const currentQuery = JSON.parse(localStorage.getItem('copied_search_query') || '{}');

  currentQuery[section] = note.sections[section];

  localStorage.setItem('copied_search_query', JSON.stringify(currentQuery));

  showToast({
    message: `${section}をコピーしました`,
    type: 'success',
    duration: 2000
  });

  router.push('/search');
};
```

**検索ページでの読み込み:**
```typescript
// frontend/app/search/page.tsx
useEffect(() => {
  const copiedQuery = localStorage.getItem('copied_search_query');

  if (copiedQuery) {
    const query = JSON.parse(copiedQuery);

    setPurpose(query.purpose || '');
    setMaterials(query.materials || '');
    setMethods(query.methods || '');

    // 読み込み後、localStorageから削除
    localStorage.removeItem('copied_search_query');

    showToast({
      message: 'コピーした内容を入力フォームに反映しました',
      type: 'info',
      duration: 3000
    });
  }
}, []);
```

#### 10.8.2 検索画面（検索結果リスト）のコピー機能

**UI配置:**
```typescript
// frontend/app/search/page.tsx - 検索結果表示
{result && result.retrieved_docs.map((doc, index) => (
  <div key={index} className="note-card">
    <div className="note-card-header">
      <h4>{extractNoteId(doc)}</h4>
      <div className="copy-buttons">
        <button onClick={() => copyField('purpose', doc)} className="btn-copy-icon">
          <CopyIcon /> 目的
        </button>
        <button onClick={() => copyField('materials', doc)} className="btn-copy-icon">
          <CopyIcon /> 材料
        </button>
        <button onClick={() => copyField('methods', doc)} className="btn-copy-icon">
          <CopyIcon /> 方法
        </button>
        <button onClick={() => copyAll(doc)} className="btn-copy-icon">
          <CopyIcon /> 一括
        </button>
      </div>
    </div>

    <div className="note-card-content">
      <ReactMarkdown>{doc}</ReactMarkdown>
    </div>
  </div>
))}
```

**コピー実装（即座に反映）:**
```typescript
const copyField = (field: 'purpose' | 'materials' | 'methods', doc: string) => {
  const sections = extractSections(doc);

  // 左側フォームに即座に反映
  if (field === 'purpose') {
    setPurpose(sections.purpose);
  } else if (field === 'materials') {
    setMaterials(sections.materials);
  } else if (field === 'methods') {
    setMethods(sections.methods);
  }

  // ボタンを一瞬グリーンに変化（視覚的フィードバック）
  setHighlightedButton(`${field}-${extractNoteId(doc)}`);
  setTimeout(() => setHighlightedButton(null), 500);
};

const copyAll = (doc: string) => {
  const sections = extractSections(doc);

  setPurpose(sections.purpose);
  setMaterials(sections.materials);
  setMethods(sections.methods);

  showToast({
    message: '全フィールドをコピーしました',
    type: 'success',
    duration: 2000
  });
};
```

**モバイル対応（横スクロール）:**
```css
/* frontend/styles/search.css */
.copy-buttons {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 768px) {
  .copy-buttons {
    padding-bottom: 0.5rem;
  }
}
```

### 10.9 評価機能改善詳細設計（FR-115）

#### 10.9.1 CSV出力機能

**出力カラム定義:**
```typescript
const CSV_COLUMNS = [
  '条件ID',
  'Embeddingモデル',
  '検索・判定用LLM',
  '要約生成用LLM',
  'プロンプト名',
  'nDCG@5',
  'nDCG@10',
  'Precision@5',
  'Precision@10',
  'Recall@10',
  'MRR',
  '正解1_検出ランク',
  '正解2_検出ランク',
  '正解3_検出ランク',
  '正解4_検出ランク',
  '正解5_検出ランク',
  '正解6_検出ランク',
  '正解7_検出ランク',
  '正解8_検出ランク',
  '正解9_検出ランク',
  '正解10_検出ランク',
];
```

**CSV生成実装:**
```typescript
// frontend/app/evaluate/page.tsx
const exportToCSV = (history: EvaluationHistory) => {
  const rows = [
    // ヘッダー行
    CSV_COLUMNS,

    // データ行
    ...history.results.map(result => {
      // 正解ノートの検出ランクを計算
      const ranks = result.ground_truth.map(gt => {
        const found = result.candidates.find(c => c.noteId === gt.noteId);
        return found ? found.rank.toString() : '未検出';
      });

      return [
        result.condition_id,
        history.embedding_model,
        history.search_llm_model,
        history.summary_llm_model,
        history.promptName || 'デフォルト',
        result.metrics.ndcg_5.toFixed(3),
        result.metrics.ndcg_10.toFixed(3),
        result.metrics.precision_5.toFixed(3),
        result.metrics.precision_10.toFixed(3),
        result.metrics.recall_10.toFixed(3),
        result.metrics.mrr.toFixed(3),
        ...ranks,
      ];
    })
  ];

  // CSV文字列生成
  const csv = rows.map(row => row.join(',')).join('\n');

  // BOM付きUTF-8でエクスポート（Excelで正しく開くため）
  const bom = '\uFEFF';
  const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `evaluation_${history.id}_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};
```

**UI配置:**
```typescript
<div className="evaluation-history">
  <h3>評価履歴</h3>
  {evaluationHistory.map(history => (
    <div key={history.id} className="history-item">
      <div className="history-header">
        <span>{history.timestamp}</span>
        <span>{history.embedding_model}</span>
        <span>nDCG@5: {history.averageNDCG5.toFixed(3)}</span>
        <button onClick={() => exportToCSV(history)} className="btn-export">
          CSV出力
        </button>
      </div>
    </div>
  ))}
</div>
```

#### 10.9.2 UI改善

**デバッグ表示削除:**
```typescript
// 削除前（v2.0）
{debugInfo && (
  <div className="debug-info">
    <h4>デバッグ情報</h4>
    <pre>{JSON.stringify(request, null, 2)}</pre>
  </div>
)}

// 削除後（v3.0）
// デバッグ情報表示を完全に削除
```

**評価履歴保存件数拡大:**
```typescript
// v2.0
const MAX_HISTORY = 5;

// v3.0
const MAX_HISTORY = 50;

// localStorageに保存
const saveEvaluationHistory = (newHistory: EvaluationHistory) => {
  const histories = JSON.parse(localStorage.getItem('evaluation_histories') || '[]');

  histories.unshift(newHistory);

  // 最大50件を保持
  if (histories.length > MAX_HISTORY) {
    histories.splice(MAX_HISTORY);
  }

  localStorage.setItem('evaluation_histories', JSON.stringify(histories));
};
```

#### 10.9.3 @5と@10の両方を出力

**メトリクス定義拡張:**
```typescript
interface EvaluationMetrics {
  ndcg_5: number;  // v3.0新規
  ndcg_10: number;  // 既存
  precision_5: number;  // v3.0新規
  precision_10: number;  // 既存
  recall_10: number;  // 既存
  mrr: number;  // 既存
}
```

**バックエンド計算:**
```python
# backend/evaluate.py
def calculate_metrics(ground_truth: List[dict], candidates: List[dict]) -> dict:
    """
    評価指標を計算

    Returns:
        {
            'ndcg_5': float,
            'ndcg_10': float,
            'precision_5': float,
            'precision_10': float,
            'recall_10': float,
            'mrr': float
        }
    """
    # nDCG@5とnDCG@10を両方計算
    ndcg_5 = calculate_ndcg(ground_truth, candidates, k=5)
    ndcg_10 = calculate_ndcg(ground_truth, candidates, k=10)

    # Precision@5とPrecision@10を両方計算
    precision_5 = calculate_precision(ground_truth, candidates, k=5)
    precision_10 = calculate_precision(ground_truth, candidates, k=10)

    # Recall@10（変更なし）
    recall_10 = calculate_recall(ground_truth, candidates, k=10)

    # MRR（変更なし）
    mrr = calculate_mrr(ground_truth, candidates)

    return {
        'ndcg_5': ndcg_5,
        'ndcg_10': ndcg_10,
        'precision_5': precision_5,
        'precision_10': precision_10,
        'recall_10': recall_10,
        'mrr': mrr
    }
```

**UI表示:**
```typescript
<div className="metrics-display">
  <div className="metric-group">
    <h4>主要指標（@5）</h4>
    <p>nDCG@5: {metrics.ndcg_5.toFixed(3)}</p>
    <p>Precision@5: {metrics.precision_5.toFixed(3)}</p>
  </div>

  <div className="metric-group">
    <h4>参考指標（@10）</h4>
    <p>nDCG@10: {metrics.ndcg_10.toFixed(3)}</p>
    <p>Precision@10: {metrics.precision_10.toFixed(3)}</p>
    <p>Recall@10: {metrics.recall_10.toFixed(3)}</p>
  </div>

  <div className="metric-group">
    <h4>その他</h4>
    <p>MRR: {metrics.mrr.toFixed(3)}</p>
  </div>
</div>
```

### 10.10 シーケンス図 ⭐ v3.0

#### 10.10.1 Firebase認証シーケンス

```
User                Frontend              Firebase Auth         Backend API           Firestore
 │                     │                        │                    │                    │
 │  Google Login       │                        │                    │                    │
 ├───────────────────→ │                        │                    │                    │
 │                     │  signInWithPopup()     │                    │                    │
 │                     ├───────────────────────→│                    │                    │
 │                     │                        │                    │                    │
 │                     │  ← User + ID Token    │                    │                    │
 │                     │←───────────────────────┤                    │                    │
 │                     │                        │                    │                    │
 │                     │  Store token (localStorage)                 │                    │
 │                     │                        │                    │                    │
 │                     │  GET /teams            │                    │                    │
 │                     ├────────────────────────┼───────────────────→│                    │
 │                     │  Authorization: Bearer {token}              │                    │
 │                     │                        │                    │                    │
 │                     │                        │                    │  Verify ID Token   │
 │                     │                        │                    ├───────────────────→│
 │                     │                        │                    │                    │
 │                     │                        │                    │  Extract user_id   │
 │                     │                        │                    │←───────────────────┤
 │                     │                        │                    │                    │
 │                     │                        │                    │  Query teams by user_id
 │                     │                        │                    ├───────────────────→│
 │                     │                        │                    │                    │
 │                     │                        │                    │  ← team_memberships│
 │                     │                        │                    │←───────────────────┤
 │                     │                        │                    │                    │
 │                     │  ← Team list           │                    │                    │
 │                     │←───────────────────────┴────────────────────┤                    │
 │                     │                        │                    │                    │
 │  Display team list  │                        │                    │                    │
 │←────────────────────┤                        │                    │                    │
 │                     │                        │                    │                    │
 │  Select Team A      │                        │                    │                    │
 ├───────────────────→ │                        │                    │                    │
 │                     │  Store team_id (localStorage)               │                    │
 │                     │                        │                    │                    │
```

#### 10.10.2 ハイブリッド検索シーケンス

```
User            Frontend (Search)         Backend (/search)        ChromaDB          Cohere Rerank
 │                    │                           │                     │                  │
 │  Input query       │                           │                     │                  │
 │  + select mode     │                           │                     │                  │
 ├──────────────────→ │                           │                     │                  │
 │                    │                           │                     │                  │
 │                    │  POST /search             │                     │                  │
 │                    │  {                        │                     │                  │
 │                    │    search_mode: 'hybrid', │                     │                  │
 │                    │    hybrid_alpha: 0.5,     │                     │                  │
 │                    │    ...                    │                     │                  │
 │                    │  }                        │                     │                  │
 │                    ├──────────────────────────→│                     │                  │
 │                    │  Headers:                 │                     │                  │
 │                    │    Authorization: Bearer  │                     │                  │
 │                    │    X-Team-ID: team-123    │                     │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Verify token       │                  │
 │                    │                           │  Extract team_id    │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Normalize materials│                  │
 │                    │                           │  (load team dict)   │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Generate 3 queries │                  │
 │                    │                           │  (search_llm_model) │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Semantic search    │                  │
 │                    │                           ├────────────────────→│                  │
 │                    │                           │  query + embedding  │                  │
 │                    │                           │                     │                  │
 │                    │                           │  ← top 100 docs (S) │                  │
 │                    │                           │←────────────────────┤                  │
 │                    │                           │                     │                  │
 │                    │                           │  Keyword search     │                  │
 │                    │                           ├────────────────────→│                  │
 │                    │                           │  query (BM25)       │                  │
 │                    │                           │                     │                  │
 │                    │                           │  ← top 100 docs (K) │                  │
 │                    │                           │←────────────────────┤                  │
 │                    │                           │                     │                  │
 │                    │                           │  Hybrid fusion:     │                  │
 │                    │                           │  score = α*S + (1-α)*K                │
 │                    │                           │  (α = hybrid_alpha) │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Cohere rerank top 100                │
 │                    │                           ├─────────────────────┴─────────────────→│
 │                    │                           │                                        │
 │                    │                           │  ← top 10 reranked docs                │
 │                    │                           │←───────────────────────────────────────┤
 │                    │                           │                     │                  │
 │                    │                           │  Compare top 3      │                  │
 │                    │                           │  (summary_llm_model)│                  │
 │                    │                           │                     │                  │
 │                    │  ← SearchResponse         │                     │                  │
 │                    │  { retrieved_docs[] }     │                     │                  │
 │                    │←──────────────────────────┤                     │                  │
 │                    │                           │                     │                  │
 │  Display results   │                           │                     │                  │
 │←───────────────────┤                           │                     │                  │
 │                    │  Save to search history   │                     │                  │
 │                    │  (localStorage)           │                     │                  │
 │                    │                           │                     │                  │
```

#### 10.10.3 ローカルファイルアップロードシーケンス

```
User            Frontend (Ingest)         Backend (/ingest/upload)  Storage (GCS)    Sudachi + LLM
 │                    │                           │                     │                  │
 │  Select files      │                           │                     │                  │
 ├──────────────────→ │                           │                     │                  │
 │                    │                           │                     │                  │
 │  Drag & Drop       │                           │                     │                  │
 ├──────────────────→ │                           │                     │                  │
 │                    │                           │                     │                  │
 │                    │  POST /ingest/upload      │                     │                  │
 │                    │  multipart/form-data      │                     │                  │
 │                    ├──────────────────────────→│                     │                  │
 │                    │  Headers:                 │                     │                  │
 │                    │    Authorization: Bearer  │                     │                  │
 │                    │    X-Team-ID: team-123    │                     │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Save to temp       │                  │
 │                    │                           │  teams/{id}/notes/new/                │
 │                    │                           ├────────────────────→│                  │
 │                    │                           │                     │                  │
 │                    │                           │  Parse markdown     │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Extract terms      │                  │
 │                    │                           ├─────────────────────┴─────────────────→│
 │                    │                           │  Sudachi tokenize    +                 │
 │                    │                           │  LLM similarity check                  │
 │                    │                           │                     │                  │
 │                    │                           │  ← new_terms[]                         │
 │                    │                           │←───────────────────────────────────────┤
 │                    │                           │                     │                  │
 │                    │  ← { new_terms[] }        │                     │                  │
 │                    │←──────────────────────────┤                     │                  │
 │                    │                           │                     │                  │
 │  Display new terms │                           │                     │                  │
 │  for confirmation  │                           │                     │                  │
 │←───────────────────┤                           │                     │                  │
 │                    │                           │                     │                  │
 │  Confirm updates   │                           │                     │                  │
 ├──────────────────→ │                           │                     │                  │
 │                    │  POST /dictionary/update  │                     │                  │
 │                    ├──────────────────────────→│                     │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Update dict.yaml   │                  │
 │                    │                           ├────────────────────→│                  │
 │                    │                           │                     │                  │
 │                    │                           │  Generate embeddings│                  │
 │                    │                           │  Add to ChromaDB    │                  │
 │                    │                           │                     │                  │
 │                    │                           │  Move to processed/ │                  │
 │                    │                           ├────────────────────→│                  │
 │                    │                           │                     │                  │
 │                    │  ← Success                │                     │                  │
 │                    │←──────────────────────────┤                     │                  │
 │                    │                           │                     │                  │
 │  Display success   │                           │                     │                  │
 │←───────────────────┤                           │                     │                  │
 │                    │                           │                     │                  │
```

---

**作成日**: 2025-12-25
**最終更新**: 2025-12-30
**バージョン**: 3.0.1 (ハイブリッド検索機能追加)
