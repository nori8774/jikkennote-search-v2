# API仕様書 - 実験ノート検索システム v3.0

## 1. API概要

### 1.1 ベースURL

**開発環境**
```
http://localhost:8000
```

**本番環境**
```
https://jikkennote-backend-285071263188.asia-northeast1.run.app
```

### 1.2 認証

**v3.0では、Firebase Authenticationを使用したユーザー認証を実装します。**

#### 1.2.1 認証ヘッダー（v3.0新規）
```
Authorization: Bearer {firebase_id_token}
X-Team-ID: {team_id}
```

- `Authorization`: Firebase ID Token（Google ログイン後に取得）
- `X-Team-ID`: 現在選択中のチームID

#### 1.2.2 APIキー（継続）
ユーザーは各自のOpenAI/Cohere APIキーをリクエストボディに含めて送信します（v2.0と同様）。

### 1.3 共通レスポンスフォーマット

**成功レスポンス**
```json
{
  "success": true,
  "message": "操作が成功しました",
  ...
}
```

**エラーレスポンス**
```json
{
  "detail": "エラーメッセージ"
}
```

### 1.4 HTTPステータスコード

| コード | 意味 | 用途 |
|-------|------|------|
| 200 | OK | 成功 |
| 400 | Bad Request | リクエスト不正 |
| 401 | Unauthorized | APIキー無効 |
| 404 | Not Found | リソース不在 |
| 500 | Internal Server Error | サーバーエラー |

---

## 2. エンドポイント一覧

### 2.1 検索関連

#### POST /search
実験ノート検索を実行する

**Request Body**
```json
{
  "purpose": "酸化反応の最適化",
  "materials": "エタノール、過酸化水素",
  "methods": "室温で24時間攪拌",
  "type": "定性",
  "instruction": "収率を重視",
  "openai_api_key": "sk-proj-...",
  "cohere_api_key": "...",
  "embedding_model": "text-embedding-3-small",
  "llm_model": "gpt-4o-mini",
  "custom_prompts": {
    "normalize": "カスタム正規化プロンプト...",
    "query_generation_veteran": "カスタムクエリ生成プロンプト...",
    ...
  },
  "evaluation_mode": false
}
```

**Request Schema**
```python
class SearchRequest(BaseModel):
    purpose: str  # 実験の目的（必須）
    materials: str  # 使用材料（必須）
    methods: str  # 実験手法（必須）
    type: Optional[str] = None  # 実験タイプ（定性/定量）
    instruction: Optional[str] = None  # 重点指示
    openai_api_key: str  # OpenAI APIキー（必須）
    cohere_api_key: str  # Cohere APIキー（必須）
    embedding_model: Optional[str] = "text-embedding-3-small"
    llm_model: Optional[str] = "gpt-4o-mini"
    custom_prompts: Optional[Dict[str, str]] = None
    evaluation_mode: Optional[bool] = False
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "検索が完了しました。上位3件の実験ノートを比較分析しました。",
  "retrieved_docs": [
    "# ID3-14: 酸化反応の収率改善\n\n## 目的・背景\n...",
    "# ID3-22: エタノール酸化実験\n\n## 目的・背景\n...",
    "# ID4-05: 過酸化水素を用いた酸化\n\n## 目的・背景\n..."
  ],
  "normalized_materials": "エタノール、過酸化水素",
  "search_query": "酸化反応の最適化において、エタノールと過酸化水素を用い..."
}
```

**Response Schema**
```python
class SearchResponse(BaseModel):
    success: bool
    message: str
    retrieved_docs: List[str]  # 検索結果のマークダウン（評価モードでは10件、通常は3件）
    normalized_materials: Optional[str] = None
    search_query: Optional[str] = None
```

**エラーレスポンス**
```json
{
  "detail": "OpenAI APIキーが無効です"
}
```

**cURLサンプル**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "酸化反応の最適化",
    "materials": "エタノール、過酸化水素",
    "methods": "室温で24時間攪拌",
    "openai_api_key": "sk-proj-...",
    "cohere_api_key": "..."
  }'
```

---

### 2.2 ノート管理

#### POST /ingest
実験ノートをChromaDBに取り込む（増分更新）

**Request Body**
```json
{
  "openai_api_key": "sk-proj-...",
  "source_folder": "notes/new",
  "post_action": "archive",
  "archive_folder": "notes/archived",
  "embedding_model": "text-embedding-3-small"
}
```

**Request Schema**
```python
class IngestRequest(BaseModel):
    openai_api_key: str
    source_folder: Optional[str] = None  # デフォルト: config.NOTES_NEW_FOLDER
    post_action: Optional[str] = "keep"  # "delete" | "archive" | "keep"
    archive_folder: Optional[str] = None
    embedding_model: Optional[str] = None
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "5件の新規ノートを取り込みました。",
  "new_notes": ["ID3-14", "ID3-15", "ID3-16", "ID3-17", "ID3-18"],
  "skipped_notes": ["ID3-10", "ID3-11"]
}
```

**Response Schema**
```python
class IngestResponse(BaseModel):
    success: bool
    message: str
    new_notes: List[str]  # 取り込んだノートID
    skipped_notes: List[str]  # 既存のためスキップしたノートID
```

---

#### GET /notes/{note_id}
実験ノートIDから全文を取得

**パスパラメータ**
- `note_id`: ノートID（例: `ID3-14`）

**Response (200 OK)**
```json
{
  "success": true,
  "note": {
    "id": "ID3-14",
    "content": "# ID3-14: 酸化反応の収率改善\n\n## 目的・背景\n...",
    "sections": {
      "purpose": "酸化反応の収率を改善する...",
      "materials": "- エタノール: 10mL\n- 過酸化水素: 5mL",
      "methods": "1. エタノールを反応容器に入れる\n2. ...",
      "results": "収率: 85%\n生成物: ..."
    }
  }
}
```

**Response Schema**
```python
class NoteResponse(BaseModel):
    success: bool
    note: Optional[Dict] = None
    error: Optional[str] = None

# note 内容
{
    "id": str,
    "content": str,  # マークダウン全文
    "sections": {
        "purpose": Optional[str],
        "materials": Optional[str],
        "methods": Optional[str],
        "results": Optional[str]
    }
}
```

**エラー (404)**
```json
{
  "success": false,
  "error": "ノートが見つかりません: ID9-99"
}
```

---

#### POST /ingest/analyze
新出単語を分析してLLMで類似候補を提案

**Request Body**
```json
{
  "note_ids": ["ID3-14", "ID3-15"],
  "note_contents": [
    "# ID3-14\n## 材料\n- DMSO: 10mL\n- TFA: 5mL",
    "# ID3-15\n## 材料\n- DMF: 20mL"
  ],
  "openai_api_key": "sk-proj-..."
}
```

**Request Schema**
```python
class AnalyzeRequest(BaseModel):
    note_ids: List[str]
    note_contents: List[str]
    openai_api_key: str
```

**Response (200 OK)**
```json
{
  "success": true,
  "new_terms": [
    {
      "term": "DMSO",
      "similar_candidates": [
        {
          "term": "ジメチルスルホキシド",
          "canonical": "ジメチルスルホキシド",
          "similarity": 0.95,
          "embedding_similarity": 0.92,
          "combined_score": 0.935
        }
      ],
      "llm_suggestion": {
        "decision": "variant",
        "reason": "DMSOはジメチルスルホキシドの略称です",
        "suggested_canonical": "ジメチルスルホキシド"
      }
    },
    {
      "term": "TFA",
      "similar_candidates": [],
      "llm_suggestion": {
        "decision": "new",
        "reason": "類似する既存物質が見つかりません",
        "suggested_canonical": null
      }
    }
  ]
}
```

**Response Schema**
```python
class AnalyzeResponse(BaseModel):
    success: bool
    new_terms: List[NewTerm]

class NewTerm(BaseModel):
    term: str
    similar_candidates: List[SimilarCandidate]
    llm_suggestion: LLMSuggestion

class SimilarCandidate(BaseModel):
    term: str
    canonical: str
    similarity: float  # 編集距離ベース
    embedding_similarity: float  # Embedding類似度
    combined_score: float  # 総合スコア

class LLMSuggestion(BaseModel):
    decision: str  # "variant" | "new"
    reason: str
    suggested_canonical: Optional[str] = None
```

---

### 2.3 正規化辞書管理

#### GET /dictionary
正規化辞書の全エントリを取得

**Response (200 OK)**
```json
{
  "success": true,
  "entries": [
    {
      "canonical": "エタノール",
      "variants": ["EtOH", "エチルアルコール", "ethanol"],
      "category": "溶媒",
      "note": "一般的な有機溶媒",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    },
    {
      "canonical": "ジメチルスルホキシド",
      "variants": ["DMSO", "dimethyl sulfoxide"],
      "category": "溶媒",
      "note": null,
      "created_at": "2025-01-10T15:00:00Z",
      "updated_at": "2025-01-10T15:00:00Z"
    }
  ]
}
```

**Response Schema**
```python
class DictionaryResponse(BaseModel):
    success: bool
    entries: List[DictionaryEntry]

class DictionaryEntry(BaseModel):
    canonical: str
    variants: List[str]
    category: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
```

---

#### POST /dictionary/update
正規化辞書を更新（新規追加または表記揺れ追加）

**Request Body**
```json
{
  "updates": [
    {
      "term": "DMSO",
      "decision": "variant",
      "canonical": "ジメチルスルホキシド",
      "category": "溶媒",
      "note": "略称"
    },
    {
      "term": "TFA",
      "decision": "new",
      "canonical": "トリフルオロ酢酸",
      "category": "試薬",
      "note": "強酸"
    }
  ]
}
```

**Request Schema**
```python
class DictionaryUpdateRequest(BaseModel):
    updates: List[DictionaryUpdate]

class DictionaryUpdate(BaseModel):
    term: str
    decision: str  # "new" | "variant"
    canonical: Optional[str] = None  # variantの場合は紐付け先
    category: Optional[str] = None
    note: Optional[str] = None
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "正規化辞書を更新しました",
  "updated_entries": 2
}
```

**Response Schema**
```python
class DictionaryUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_entries: int
```

---

#### GET /dictionary/export?format={format}
正規化辞書をエクスポート

**クエリパラメータ**
- `format`: `yaml` | `json` | `csv`（デフォルト: `yaml`）

**Response (200 OK)**
```
Content-Type: application/x-yaml
Content-Disposition: attachment; filename="master_dictionary.yaml"

エタノール:
  - EtOH
  - エチルアルコール
  - ethanol
ジメチルスルホキシド:
  - DMSO
  - dimethyl sulfoxide
```

**Response Type**
```
application/x-yaml (format=yaml)
application/json (format=json)
text/csv (format=csv)
```

---

#### POST /dictionary/import
正規化辞書をインポート

**Request**
```
Content-Type: multipart/form-data
file: <YAML/JSON/CSV file>
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "正規化辞書をインポートしました（50エントリ）"
}
```

---

### 2.4 プロンプト管理

#### GET /prompts
デフォルトプロンプトを取得

**Response (200 OK)**
```json
{
  "success": true,
  "prompts": {
    "normalize": {
      "name": "正規化プロンプト",
      "description": "材料名を正規化するためのプロンプト",
      "prompt": "以下の材料名を正規化してください:\n{input_materials}"
    },
    "query_generation_veteran": {
      "name": "ベテラン視点クエリ",
      "description": "ベテラン研究者の視点でクエリを生成",
      "prompt": "..."
    },
    ...
  }
}
```

**Response Schema**
```python
class PromptsResponse(BaseModel):
    success: bool
    prompts: Dict[str, PromptDetail]

class PromptDetail(BaseModel):
    name: str
    description: str
    prompt: str
```

---

#### GET /prompts/list
保存されているプロンプト一覧を取得

**Response (200 OK)**
```json
{
  "success": true,
  "prompts": [
    {
      "id": "my-custom-prompt",
      "name": "カスタムプロンプトセット1",
      "description": "収率重視の検索用",
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    },
    {
      "id": "another-prompt",
      "name": "安全性重視プロンプト",
      "description": "安全性を重視した検索",
      "created_at": "2025-01-12T09:00:00Z",
      "updated_at": "2025-01-12T09:00:00Z"
    }
  ]
}
```

---

#### POST /prompts/save
プロンプトセットを保存

**Request Body**
```json
{
  "name": "my-custom-prompt",
  "prompts": {
    "normalize": "カスタム正規化プロンプト...",
    "query_generation_veteran": "カスタムベテランプロンプト...",
    "query_generation_newcomer": "カスタム新人プロンプト...",
    "query_generation_manager": "カスタムマネージャープロンプト...",
    "compare": "カスタム比較プロンプト..."
  },
  "description": "収率重視の検索用プロンプト"
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "プロンプトを保存しました: my-custom-prompt"
}
```

**エラー (400)**
```json
{
  "detail": "プロンプトは最大50件までです"
}
```

---

#### GET /prompts/load/{name}
保存されているプロンプトを読み込み

**パスパラメータ**
- `name`: プロンプトID

**Response (200 OK)**
```json
{
  "success": true,
  "name": "my-custom-prompt",
  "description": "収率重視の検索用プロンプト",
  "prompts": {
    "normalize": "カスタム正規化プロンプト...",
    "query_generation_veteran": "カスタムベテランプロンプト...",
    ...
  },
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

**エラー (404)**
```json
{
  "detail": "プロンプトが見つかりません: unknown-prompt"
}
```

---

#### DELETE /prompts/delete/{name}
保存されているプロンプトを削除

**パスパラメータ**
- `name`: プロンプトID

**Response (200 OK)**
```json
{
  "success": true,
  "message": "プロンプトを削除しました: my-custom-prompt"
}
```

**エラー (404)**
```json
{
  "detail": "プロンプトが見つかりません"
}
```

---

#### PUT /prompts/update
プロンプトを更新

**Request Body**
```json
{
  "name": "my-custom-prompt",
  "prompts": {
    "normalize": "更新後の正規化プロンプト...",
    ...
  },
  "description": "更新後の説明"
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "プロンプトを更新しました"
}
```

---

### 2.5 ChromaDB管理

#### GET /chroma/info
ChromaDBの現在の設定情報を取得

**Response (200 OK)**
```json
{
  "success": true,
  "current_embedding_model": "text-embedding-3-small",
  "created_at": "2025-01-01T00:00:00Z",
  "last_updated": "2025-01-15T10:00:00Z"
}
```

**Response Schema**
```python
class ChromaDBInfoResponse(BaseModel):
    success: bool
    current_embedding_model: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
```

---

#### POST /chroma/reset
ChromaDBを完全にリセット（全データ削除）

**Response (200 OK)**
```json
{
  "success": true,
  "message": "ChromaDBをリセットしました。全ノートを再取り込みしてください。"
}
```

**Response Schema**
```python
class ChromaDBResetResponse(BaseModel):
    success: bool
    message: str
```

**エラー (500)**
```json
{
  "detail": "ChromaDBのリセットに失敗しました"
}
```

---

### 2.6 評価機能

#### POST /evaluate/import
評価用テストケースをExcel/CSVからインポート

**Request**
```
Content-Type: multipart/form-data
file: <Excel or CSV file>
```

**ファイルフォーマット**
```csv
test_case_id,query_purpose,query_materials,query_methods,note_id,rank,relevance
TC001,酸化反応の最適化,エタノール、過酸化水素,室温で24時間攪拌,ID3-14,1,5
TC001,酸化反応の最適化,エタノール、過酸化水素,室温で24時間攪拌,ID3-22,2,4
TC001,酸化反応の最適化,エタノール、過酸化水素,室温で24時間攪拌,ID4-05,3,3
TC002,還元反応の収率向上,...,
```

**Response (200 OK)**
```json
{
  "success": true,
  "test_cases": [
    {
      "id": "TC001",
      "query": {
        "purpose": "酸化反応の最適化",
        "materials": "エタノール、過酸化水素",
        "methods": "室温で24時間攪拌"
      },
      "ground_truth": [
        {"note_id": "ID3-14", "rank": 1, "relevance": 5},
        {"note_id": "ID3-22", "rank": 2, "relevance": 4},
        {"note_id": "ID4-05", "rank": 3, "relevance": 3}
      ]
    },
    ...
  ]
}
```

---

#### POST /evaluate
評価を実行してメトリクスを計算

**Request Body**
```json
{
  "test_case_id": "TC001",
  "query": {
    "purpose": "酸化反応の最適化",
    "materials": "エタノール、過酸化水素",
    "methods": "室温で24時間攪拌"
  },
  "ground_truth": [
    {"note_id": "ID3-14", "rank": 1, "relevance": 5},
    {"note_id": "ID3-22", "rank": 2, "relevance": 4},
    {"note_id": "ID4-05", "rank": 3, "relevance": 3}
  ],
  "openai_api_key": "sk-proj-...",
  "cohere_api_key": "..."
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "metrics": {
    "ndcg_10": 0.85,
    "precision_3": 0.67,
    "precision_5": 0.60,
    "precision_10": 0.50,
    "recall_10": 0.75,
    "mrr": 0.90
  },
  "ranking": [
    {"note_id": "ID3-14", "rank": 1, "score": 0.95},
    {"note_id": "ID4-05", "rank": 2, "score": 0.88},
    {"note_id": "ID3-22", "rank": 3, "score": 0.82},
    ...
  ],
  "comparison": [
    {
      "note_id": "ID3-14",
      "expected_rank": 1,
      "actual_rank": 1,
      "relevance": 5
    },
    {
      "note_id": "ID3-22",
      "expected_rank": 2,
      "actual_rank": 3,
      "relevance": 4
    },
    ...
  ]
}
```

**Response Schema**
```python
class EvaluateResponse(BaseModel):
    success: bool
    metrics: EvaluationMetrics
    ranking: List[RankingResult]
    comparison: List[ComparisonResult]

class EvaluationMetrics(BaseModel):
    ndcg_10: float
    precision_3: float
    precision_5: float
    precision_10: float
    recall_10: float
    mrr: float

class RankingResult(BaseModel):
    note_id: str
    rank: int
    score: float

class ComparisonResult(BaseModel):
    note_id: str
    expected_rank: int
    actual_rank: int
    relevance: int
```

---

### 2.7 ヘルスチェック

#### GET /health
APIサーバーのヘルスチェック

**Response (200 OK)**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## 3. エラーコード一覧

### 3.1 400 Bad Request

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `purpose, materials, methods は必須です` | 必須フィールドが空 | 全フィールドを入力 |
| `OpenAI APIキーが必要です` | APIキーが未入力 | 設定ページでAPIキーを入力 |
| `プロンプトは最大50件までです` | プロンプト保存上限 | 不要なプロンプトを削除 |
| `無効なファイル形式です` | 非対応ファイル | YAML/JSON/CSV形式で送信 |

### 3.2 401 Unauthorized

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `OpenAI APIキーが無効です` | APIキーが正しくない | 正しいAPIキー（sk-proj-...）を入力 |
| `Cohere APIキーが無効です` | APIキーが正しくない | 正しいCohereキーを入力 |

### 3.3 404 Not Found

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `ノートが見つかりません: {note_id}` | 指定ノートID不在 | ノートIDを確認 |
| `プロンプトが見つかりません: {name}` | 指定プロンプト不在 | プロンプト一覧を確認 |

### 3.4 500 Internal Server Error

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `検索エラー: {詳細}` | LangGraph実行エラー | ログを確認、再試行 |
| `ChromaDBのリセットに失敗しました` | DB操作エラー | 権限・パスを確認 |
| `GCS同期エラー` | GCS接続エラー | ネットワーク・認証確認 |

---

## 4. レート制限

現在、APIレート制限は実装されていません。

**将来的な制限案**
- リクエスト数: 100回/分
- 検索実行: 20回/分
- ノート取り込み: 10回/分

---

## 5. API使用例

### 5.1 TypeScript (Frontend)

```typescript
import { api } from '@/lib/api';

// 検索実行
const searchResult = await api.search({
  purpose: '酸化反応の最適化',
  materials: 'エタノール、過酸化水素',
  methods: '室温で24時間攪拌',
  instruction: '収率を重視',
  openai_api_key: localStorage.getItem('openai_api_key'),
  cohere_api_key: localStorage.getItem('cohere_api_key'),
  embedding_model: 'text-embedding-3-small',
  llm_model: 'gpt-4o-mini',
  evaluation_mode: false,
});

console.log(searchResult.retrieved_docs);
```

### 5.2 Python

```python
import requests

API_BASE_URL = "http://localhost:8000"

# 検索実行
response = requests.post(
    f"{API_BASE_URL}/search",
    json={
        "purpose": "酸化反応の最適化",
        "materials": "エタノール、過酸化水素",
        "methods": "室温で24時間攪拌",
        "openai_api_key": "sk-proj-...",
        "cohere_api_key": "...",
    }
)

result = response.json()
print(result["retrieved_docs"])
```

### 5.3 cURL

```bash
# 検索実行
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "酸化反応の最適化",
    "materials": "エタノール、過酸化水素",
    "methods": "室温で24時間攪拌",
    "openai_api_key": "sk-proj-...",
    "cohere_api_key": "..."
  }'

# ノートID取得
curl "http://localhost:8000/notes/ID3-14"

# プロンプト一覧
curl "http://localhost:8000/prompts/list"

# ChromaDB情報
curl "http://localhost:8000/chroma/info"
```

---

## 6. Webhooks（未実装）

将来的には以下のWebhookイベントを提供予定:
- `ingest.completed`: ノート取り込み完了時
- `evaluation.completed`: 評価実行完了時
- `dictionary.updated`: 辞書更新時

---

## 7. SDKサポート

現在、公式SDKは提供していません。

**フロントエンド用APIクライアント**
- `frontend/lib/api.ts` に全エンドポイント対応のクライアント実装済み

---

## 8. 変更履歴

### v2.0.0 (2025-01-15)
- 初版リリース
- 全エンドポイント実装
- ChromaDB管理機能追加
- プロンプト管理YAML化

---

## 9. 付録: リクエスト/レスポンス例（完全版）

### 9.1 検索リクエスト（フルオプション）

```json
{
  "purpose": "高収率での酸化反応の最適化",
  "materials": "エタノール (99.5%), 過酸化水素 (30%), 触媒A",
  "methods": "室温（25℃）で24時間攪拌、その後50℃で12時間加熱",
  "type": "定量",
  "instruction": "収率90%以上を目指す。安全性も考慮。",
  "openai_api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxx",
  "cohere_api_key": "xxxxxxxxxxxxxxxxxxxxxxxx",
  "embedding_model": "text-embedding-3-large",
  "llm_model": "gpt-4o",
  "custom_prompts": {
    "normalize": "以下の材料名を化学物質名に正規化してください:\n{input_materials}",
    "query_generation_veteran": "ベテラン研究者として、以下の条件で検索クエリを生成:\n目的: {input_purpose}\n材料: {normalized_materials}\n方法: {input_methods}\n重点: {instruction}",
    "query_generation_newcomer": "新人研究者として...",
    "query_generation_manager": "研究マネージャーとして...",
    "compare": "以下の3つの実験ノートを比較分析してください:\n{retrieved_docs}"
  },
  "evaluation_mode": false
}
```

### 9.2 検索レスポンス（フル）

```json
{
  "success": true,
  "message": "検索が完了しました。上位3件の実験ノートを比較分析しました。",
  "retrieved_docs": [
    "# ID3-14: 高収率酸化反応の条件検討\n\n## 目的・背景\n酸化反応の収率を90%以上に改善するため、触媒と温度条件を最適化する。\n\n## 材料\n- エタノール (99.5%): 50mL\n- 過酸化水素 (30%): 25mL\n- 触媒A: 0.5g\n- 溶媒: ジメチルスルホキシド 100mL\n\n## 方法\n1. エタノールとDMSOを反応容器に投入\n2. 触媒Aを添加し、室温で1時間攪拌\n3. 過酸化水素を滴下（30分かけて）\n4. 室温で24時間攪拌\n5. 50℃に昇温し、12時間反応\n6. 冷却後、生成物を単離\n\n## 結果・考察\n- 収率: 92%\n- 純度: 98%\n- 副生成物: 微量検出\n- 考察: 触媒Aの使用により高収率を達成。温度管理が重要。\n\n## 安全性・環境配慮\n- 過酸化水素の取り扱いに注意\n- ドラフト内で実施\n- 廃液は中和後廃棄",

    "# ID3-22: エタノール酸化反応の触媒スクリーニング\n\n## 目的・背景\n複数の触媒を比較検討し、最適触媒を選定する。\n\n## 材料\n- エタノール (99.5%): 30mL\n- 過酸化水素 (30%): 15mL\n- 触媒A, B, C: 各0.5g\n...",

    "# ID4-05: 過酸化水素濃度の影響評価\n\n## 目的・背景\n過酸化水素の濃度が収率に与える影響を評価。\n\n## 材料\n- エタノール (99.5%): 50mL\n- 過酸化水素: 10%, 20%, 30% (各25mL)\n..."
  ],
  "normalized_materials": "エタノール、過酸化水素、触媒A",
  "search_query": "【ベテラン視点】高収率（90%以上）での酸化反応において、エタノールと過酸化水素、触媒Aを使用し、室温攪拌後に50℃加熱する実験手法を検索。安全性にも配慮した条件を重視。\n\n【新人視点】エタノールの酸化反応で収率を高める方法を知りたい。過酸化水素と触媒を使うらしいが、具体的な温度や時間の条件は？\n\n【マネージャー視点】酸化反応プロジェクトで目標収率90%を達成するため、既存の成功事例（特にエタノール系）を調査。コスト・安全性・再現性の観点から評価したい。"
}
```

---

## 10. v3.0 新規/変更API ⭐

### 10.1 POST /search (変更)

**v3.0での変更点：**
- ヘッダーに`Authorization`と`X-Team-ID`を追加
- リクエストボディに`search_llm_model`と`summary_llm_model`パラメータを追加

**v3.0.1での変更点：**
- `search_mode`パラメータを追加（ハイブリッド検索対応）
- `hybrid_alpha`パラメータを追加（ハイブリッド検索の重み調整）

**リクエスト:**
```http
POST /search
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
X-Team-ID: team_abc123
Content-Type: application/json
```

```json
{
  "purpose": "...",
  "materials": "...",
  "methods": "...",
  "instruction": "...",
  "openai_api_key": "sk-proj-...",
  "cohere_api_key": "...",
  "embedding_model": "text-embedding-3-small",
  "search_llm_model": "gpt-5.2",  // v3.0新規
  "summary_llm_model": "gpt-3.5-turbo",  // v3.0新規
  "search_mode": "hybrid",  // v3.0.1新規: "semantic" | "keyword" | "hybrid"
  "hybrid_alpha": 0.7,  // v3.0.1新規: セマンティック重み（0.0-1.0）
  "custom_prompts": {...},
  "evaluation_mode": false
}
```

**パラメータ詳細:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|----------|------|
| purpose | string | ○ | - | 検索目的 |
| materials | string | ○ | - | 使用材料 |
| methods | string | ○ | - | 実験手法 |
| instruction | string | × | "" | 重点指示 |
| openai_api_key | string | ○ | - | OpenAI APIキー |
| cohere_api_key | string | ○ | - | Cohere APIキー |
| embedding_model | string | × | "text-embedding-3-small" | Embeddingモデル |
| search_llm_model | string | × | "gpt-4o-mini" | 検索・判定用LLM |
| summary_llm_model | string | × | "gpt-3.5-turbo" | 要約生成用LLM |
| search_mode | string | × | "semantic" | 検索モード: "semantic"（セマンティック検索）、"keyword"（キーワード検索）、"hybrid"（ハイブリッド検索） |
| hybrid_alpha | float | × | 0.7 | ハイブリッド検索のセマンティック重み（0.0〜1.0）。1.0で完全セマンティック、0.0で完全キーワード。0.7推奨 |
| custom_prompts | object | × | null | カスタムプロンプト |
| evaluation_mode | boolean | × | false | 評価モード（比較ノード無効化） |

### 10.2 POST /ingest/upload (新規)

**ローカルファイルアップロード用エンドポイント**

**リクエスト:**
```http
POST /ingest/upload
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
X-Team-ID: team_abc123
Content-Type: multipart/form-data
```

```
files: [file1.md, file2.md, ...]
```

**レスポンス:**
```json
{
  "success": true,
  "message": "3件のノートをアップロードしました",
  "uploaded_files": ["note1.md", "note2.md", "note3.md"],
  "new_terms": [
    {
      "term": "ポリエチレングリコール",
      "type": "new",
      "similar_terms": []
    },
    {
      "term": "PEG",
      "type": "variant",
      "similar_terms": ["ポリエチレングリコール"]
    }
  ]
}
```

### 10.3 POST /ingest/confirm-terms (新規)

**新出単語の確認・承認**

**リクエスト:**
```json
{
  "terms": [
    {
      "term": "PEG",
      "action": "merge",
      "canonical": "ポリエチレングリコール"
    },
    {
      "term": "新規化合物X",
      "action": "add"
    },
    {
      "term": "一般単語",
      "action": "skip"
    }
  ]
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "辞書を更新しました",
  "updated_terms": 2,
  "skipped_terms": 1
}
```

### 10.4 GET /teams (新規)

**ユーザーが所属するチーム一覧を取得**

**リクエスト:**
```http
GET /teams
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
```

**レスポンス:**
```json
{
  "success": true,
  "teams": [
    {
      "id": "team_abc123",
      "name": "材料科学研究室",
      "role": "member",
      "created_at": "2025-12-20T10:00:00Z"
    },
    {
      "id": "team_xyz789",
      "name": "有機合成チーム",
      "role": "admin",
      "created_at": "2025-12-15T14:30:00Z"
    }
  ]
}
```

### 10.5 POST /teams/create (新規)

**新しいチームを作成**

**リクエスト:**
```json
{
  "name": "新規研究チーム",
  "description": "次世代材料の研究開発"
}
```

**レスポンス:**
```json
{
  "success": true,
  "team": {
    "id": "team_new456",
    "name": "新規研究チーム",
    "invite_code": "ABC-XYZ-123"
  }
}
```

### 10.6 POST /teams/join (新規)

**招待コードでチームに参加**

**リクエスト:**
```json
{
  "invite_code": "ABC-XYZ-123"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "チーム「新規研究チーム」に参加しました",
  "team_id": "team_new456"
}
```

---

**作成日**: 2025-12-25
**最終更新**: 2025-12-30
**バージョン**: 3.0.1 (ハイブリッド検索機能追加)
