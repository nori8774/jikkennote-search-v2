# ユビキタス言語定義（用語集） - 実験ノート検索システム v3.0

## はじめに

このドキュメントは、実験ノート検索システムで使用される専門用語と概念を定義します。開発者、ユーザー、ステークホルダー間で共通の理解を持つために使用します。

---

## A-Z

### Agent

LangGraphで定義されたワークフロー。ノード（処理単位）とエッジ（遷移）で構成され、ステート（状態）を管理しながら実行される。

**例**: `backend/agent.py`で定義されたAgentState、normalize_node、query_generation_node、search_node、compare_node。

### AgentState

LangGraphワークフローで使用される状態（TypedDict）。各ノードの入力・出力を保持する。

**フィールド例**:
- `input_purpose`: 実験の目的
- `input_materials`: 使用材料
- `normalized_materials`: 正規化後の材料
- `search_query`: 生成されたクエリ
- `retrieved_docs`: 検索結果

### API Key

外部サービス（OpenAI, Cohere）にアクセスするための認証鍵。ユーザーがブラウザのlocalStorageに保存し、リクエストごとに送信する。

**セキュリティ**: サーバー側では保存せず、リクエストごとに受け取る。

---

## C

### ChromaDB

オープンソースのベクトルデータベース。Embeddingベクトルを保存し、類似度検索を高速に実行する。

**保存先**:
- ローカル開発: `backend/chroma_db/`
- 本番環境: Google Cloud Storage

**設定**: `chroma_db_config.json`に現在のEmbeddingモデルを記録。

### Claude Code

Anthropic社が提供する公式CLI開発環境。サブエージェント、スキル、カスタムコマンドを使った高度な開発ワークフローをサポート。

**プロジェクトでの使用**:
- `.claude/agents/`: doc-reviewer、implementation-validatorなどのサブエージェント定義
- `.claude/commands/`: add-feature、review-docsなどのカスタムコマンド
- `.claude/skills/`: steering、prd-writing、functional-designなどのスキル
- `.claude/settings.json`: プロジェクト固有の設定

**主要機能**:
- **Steering機能**: 作業単位ドキュメント管理（.steering/配下）
- **サブエージェント**: 独立したコンテキストで複雑なタスクを実行
- **スキル**: 再利用可能な専門タスク定義

**関連**: Steering、作業単位ドキュメント

### Cohere Rerank

Cohere社が提供するリランキングAPI。ベクトル検索で取得した上位候補（例: 100件）を、より精度の高い関連度順に並べ替える。

**使用箇所**: `backend/agent.py`のsearch_nodeで、ChromaDB検索結果をリランキング。

---

## E

### Embedding

テキストを固定長のベクトル（数値配列）に変換する技術。意味的に類似したテキストは近いベクトルになる。

**使用モデル**:
- `text-embedding-3-small` (デフォルト)
- `text-embedding-3-large`
- `text-embedding-ada-002`

**用途**: 実験ノートをベクトル化してChromaDBに保存、検索時にクエリもベクトル化して類似度検索。

### Evaluation Mode

評価モード。検索結果を上位10件まで返し、比較分析（Compare Node）をスキップする。RAG性能評価時に使用。

**通常モード**: 上位3件を返し、比較分析レポートを生成。

---

## G

### Google Cloud Storage (GCS)

Google Cloudのオブジェクトストレージサービス。本番環境で実験ノート、正規化辞書、ChromaDBデータを永続化。

**バケット構成** (v3.0マルチテナント対応):
```
gs://jikkennote-storage/
└── teams/
    └── {team_id}/
        ├── chroma-db/
        ├── notes/
        │   ├── new/
        │   └── processed/  # v3.0: archivedから名称変更、削除しない
        ├── saved_prompts/  # v3.0: promptsから名称変更
        └── dictionary.yaml
```

**v3.0での変更点**:
- チームごとに独立したデータ領域（`teams/{team_id}/`）
- `archived/` → `processed/`に名称変更（削除せず保持）
- `prompts/` → `saved_prompts/`に名称変更

### Google Drive連携

Google Driveフォルダを監視し、新規ノート（.mdファイル）を自動的に取り込む機能。非IT系ユーザー向け。

**設定** (v3.0新機能):
- `GOOGLE_DRIVE_ENABLED`: true/false
- `GOOGLE_DRIVE_FOLDER_ID`: 監視対象フォルダID
- `GOOGLE_DRIVE_CHECK_INTERVAL`: チェック間隔（秒）

**認証**: OAuth 2.0（credentials.json + token.json）

**フロー**:
1. Google Driveフォルダに.mdファイルを配置
2. バックエンドが定期的にチェック（デフォルト: 300秒間隔）
3. 新規ファイルを自動取り込み
4. 取り込み後、`processed/`に移動

**利点**:
- GCSの知識不要
- ブラウザから直接ファイルアップロード可能
- チーム内でフォルダを共有して協業可能

**関連機能**: FR-110（ノート取り込み改善）、Ingest

---

## H

### Hybrid Search (ハイブリッド検索)

セマンティック検索とキーワード検索を組み合わせた検索手法。`hybrid_alpha`パラメータで重み付けを調整できる。

**使用方法** (v3.0.1新機能):
- `search_mode`: "semantic" (デフォルト) | "keyword" | "hybrid"
- `hybrid_alpha`: 0.0（キーワード重視）〜 1.0（セマンティック重視）

**例**:
```json
{
  "search_mode": "hybrid",
  "hybrid_alpha": 0.5  // 両方を均等に
}
```

**推奨設定**:
- 専門用語が多い場合: `hybrid_alpha: 0.3`（キーワード重視）
- 自然文で検索する場合: `hybrid_alpha: 0.7`（セマンティック重視）

**用途**: 専門用語の完全一致とセマンティック理解を両立させる。

**関連**: ChromaDB、Semantic Search、Keyword Search

---

## I

### Ingest（取り込み）

新規実験ノート（Markdownファイル）をChromaDBに追加する処理。

**フロー** (v3.0):
1. `notes/new/`からMarkdownファイル読み込み（またはGoogle Driveから取得）
2. 既存ID確認（増分更新）
3. 新出単語抽出
4. 正規化辞書更新（ユーザー判定後）
5. Embedding生成 → ChromaDB追加
6. ファイル処理: `processed/`に移動（v3.0では削除しない）⭐

**増分更新**: 既存ノートをスキップし、新規ノートのみ処理。

**v3.0での重要な変更**: 取り込み済みノートは`notes/processed/`に移動し、**削除しない**。これにより、Embeddingモデル変更時の全ノート再取り込みが可能。

---

## L

### LangChain

Pythonライブラリ。LLM（Large Language Model）を使ったアプリケーション開発を支援。

**使用箇所**: Embedding生成、LLMプロンプト実行、ベクトルストア連携。

### LangGraph

LangChainのワークフロー管理ライブラリ。ステートフルなエージェントをグラフ構造で定義。

**使用箇所**: `backend/agent.py`で検索ワークフロー（normalize → query_generation → search → compare）を定義。

### LLM (Large Language Model)

大規模言語モデル。テキスト生成、分類、要約などのタスクを実行。

**使用モデル**:
- `gpt-4o-mini` (デフォルト)
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

**用途**: クエリ生成、比較分析レポート生成、新出単語の表記揺れ判定。

---

## M

### Master Dictionary

正規化辞書。化学物質名の表記揺れをマッピングしたYAMLファイル。

**フォーマット**:
```yaml
エタノール:
  - EtOH
  - エチルアルコール
  - ethanol
  - C2H5OH
```

**用途**: 検索時に材料名を統一し、検索精度を向上。

### Multi-tenant（マルチテナント）

複数のチームが独立したデータ領域を持つアーキテクチャ。v3.0で導入。

**GCS構造** (v3.0):
```
gs://jikkennote-storage/
└── teams/
    ├── team_a/
    │   ├── chroma-db/
    │   ├── notes/
    │   ├── saved_prompts/
    │   └── dictionary.yaml
    └── team_b/
        └── ...
```

**Team ID**: チームを一意に識別する文字列。環境変数`TEAM_ID`で指定。

**分離レベル**: 完全分離（チーム間でデータ共有なし）

**将来拡張**: チーム管理UI、アクセス制御、使用量制限など

**関連**: Google Cloud Storage

---

## N

### nDCG@5 (Normalized Discounted Cumulative Gain at 5)

検索精度の評価指標。上位5件の順位と関連度を考慮したスコア。**v3.0では主要KPIとして設定**。

**計算式**:
- DCG@5 = Σ (relevance_i / log2(i+1)) for i=1 to 5
- IDCG = 理想的なランキングでのDCG
- nDCG@5 = DCG@5 / IDCG@5

**目標値**: nDCG@5 ≥ 0.85（主要指標）

**@5を重視する理由**:
- 実験ノートの特性: 材料の容量違い、触媒違い、温度違いなど、似たようなノートが多数存在
- ユーザーは通常、上位5件程度を詳細に確認する
- @10のランキング下位はどれがヒットしてもおかしくない状態になるため、@5で評価する方が実用的

**関連**: nDCG@10、Precision@5、評価機能

### nDCG@10 (Normalized Discounted Cumulative Gain at 10)

検索精度の評価指標。上位10件の順位と関連度を考慮したスコア。**v3.0では参考指標として使用**。

**計算式**:
- DCG@10 = Σ (relevance_i / log2(i+1)) for i=1 to 10
- IDCG = 理想的なランキングでのDCG
- nDCG@10 = DCG@10 / IDCG@10

**目標値**: nDCG@10 ≥ 0.8（参考指標）

**用途**: 全体的な検索精度の確認。主要指標はnDCG@5。

### Normalization（正規化）

材料名の表記揺れを統一する処理。マスター辞書を使用して、異なる表記を共通の名称に変換。

**例**:
- "EtOH" → "エタノール"
- "DMSO" → "ジメチルスルホキシド"

**実装**: `backend/utils.py`の`normalize_text()`関数。

### Note ID

実験ノートの一意識別子。形式: `ID{番号}-{サブ番号}` (例: `ID3-14`)

**用途**: ノート検索、ビューワー表示、履歴管理。

---

## P

### Precision@K

検索精度の評価指標。上位K件中、正解（関連ノート）の割合。

**例**: Precision@3 = 0.67 → 上位3件中2件が正解

### Processed フォルダ

取り込み済み実験ノートを保存するフォルダ。v3.0で`archived/`から名称変更。

**パス**:
- ローカル: `backend/notes/processed/`
- GCS: `gs://jikkennote-storage/teams/{team_id}/notes/processed/`

**v3.0での重要な変更**: 以前のバージョンでは取り込み後にファイルを削除していたが、v3.0では`processed/`フォルダに移動して**削除しない**。これにより、Embeddingモデル変更時の全ノート再取り込みが可能になる。

**役割**:
- 増分更新時のスキップ判定
- Embeddingモデル変更時の再取り込みソース
- 監査ログ（どのノートが取り込まれたか）

**関連**: Ingest、Embedding、Notes フォルダ

### Prompt

LLMに送信する指示文。ユーザーの意図を理解し、適切な出力を生成するための重要な要素。

**プロンプト種類**:
- **正規化プロンプト**: 材料名を正規化
- **クエリ生成プロンプト**: 3視点（ベテラン/新人/マネージャー）でクエリ生成
- **比較プロンプト**: 上位3件を比較分析

**管理**: YAML形式で保存、UI上で編集可能（最大50件）。

---

## R

### RAG (Retrieval-Augmented Generation)

検索拡張生成。ベクトル検索で関連文書を取得し、それを元にLLMで回答を生成する手法。

**フロー**:
1. ユーザークエリをEmbedding化
2. ChromaDBで類似文書を検索
3. Cohere Rerankでリランキング
4. 検索結果を元にLLMで分析レポート生成

### Recall@K

検索精度の評価指標。全正解中、上位K件に含まれる割合。

**例**: Recall@10 = 0.75 → 全正解4件中3件が上位10件に含まれる

### Reranking

ベクトル検索で得られた候補を、より高精度なモデルで再順位付けする処理。

**使用サービス**: Cohere Rerank API

**効果**: 検索精度（nDCG）の向上

---

## S

### Saved Prompts フォルダ

ユーザーが保存したカスタムプロンプトを格納するフォルダ。v3.0で`prompts/`から名称変更。

**パス**:
- ローカル: `backend/saved_prompts/`
- GCS: `gs://jikkennote-storage/teams/{team_id}/saved_prompts/`

**保存形式**: YAML（`.yaml`拡張子）

**管理**:
- 最大50件まで保存可能
- プロンプト管理UI（設定ページ）から作成・編集・削除
- デフォルトプロンプトとの切り替えが可能

**プロンプト種類**:
- 正規化プロンプト
- クエリ生成プロンプト
- 比較プロンプト

**関連**: Prompt、Prompt Management

### Search History

検索履歴。ユーザーの過去の検索クエリと結果を保存。

**保存内容**:
- 検索クエリ（目的・材料・方法・重点指示）
- 検索日時
- 上位10件のノートID + スコア
- 使用したプロンプト名

**保存先**: localStorage（ブラウザ）

### Section

実験ノート内のセクション。Markdownの見出し（`##`）で区切られた領域。

**主要セクション**:
- 目的・背景
- 材料
- 方法
- 結果

**用途**: セクション別にコピー、検索条件への反映。

### Steering（作業単位ドキュメント）

機能追加や改善作業ごとに作成する作業単位のドキュメント管理手法。Claude Code環境で使用。

**保存場所**: `.steering/[日付]-[機能名]/`

**ファイル構成**:
```
.steering/
└── 20251230-Google-Drive統合/
    ├── requirements.md   # 要件定義（目的、スコープ、制約）
    ├── design.md         # 設計書（データフロー、API設計、UI設計）
    └── tasklist.md       # タスクリスト（実装タスク一覧）
```

**ワークフロー**:
1. **計画モード**: `/add-feature`コマンドでステアリングファイル生成
2. **実装モード**: `tasklist.md`に従って実装、完了タスクに`[x]`をマーク
3. **振り返りモード**: 実装完了後、振り返りを記録

**目的**:
- 作業単位での要件・設計・タスク管理
- 永続ドキュメント(`docs/`)との整合性維持
- 実装履歴の記録

**関連**: Claude Code、`.claude/skills/steering`

---

## T

### Test Case

RAG性能評価用のテストケース。検索クエリと期待される正解ランキングを含む。

**構成**:
- `test_case_id`: テストケースID
- `query`: 検索クエリ（目的・材料・方法）
- `ground_truth`: 正解ランキング（ノートID + 関連度）

**フォーマット**: Excel/CSV

---

## V

### Vector Search

ベクトル検索。Embeddingベクトル間の類似度（コサイン類似度など）を計算し、類似文書を検索。

**使用DB**: ChromaDB

**フロー**:
1. クエリをEmbedding化
2. ChromaDBで類似ベクトル検索（上位100件）
3. Cohere Rerankで再順位付け（上位10件）

---

## 日本語索引

### 表記揺れ

同じ化学物質・概念を異なる表記で記述すること。

**例**:
- エタノール = EtOH = エチルアルコール = ethanol
- ジメチルスルホキシド = DMSO = dimethyl sulfoxide

**対策**: 正規化辞書（Master Dictionary）で統一。

### 新出単語

ノート取り込み時に、正規化辞書に存在しない単語。

**判定**:
- **新規物質**: 辞書に追加（新規エントリ作成）
- **表記揺れ**: 既存物質の別名として追加
- **スキップ**: 辞書に追加しない

**判定支援**: LLMで類似単語を検索し、編集距離・Embedding類似度で候補提示。

### 正規化辞書

化学物質名の表記揺れをマッピングした辞書。YAML形式で保存。

→ **Master Dictionary**参照

### 増分更新

新規データのみを処理し、既存データをスキップする更新方式。

**メリット**: 処理時間の短縮、無駄なAPI呼び出しの削減

**実装**: ノート取り込み時、既存IDをChromaDBで確認し、新規ノートのみ処理。

### 比較分析レポート

検索結果の上位3件を比較し、LLMが生成するMarkdown形式のレポート。

**内容**:
- 各ノートの要約
- 共通点・相違点
- 推奨事項

**生成**: Compare Nodeで実行。

---

## 略語

| 略語 | 正式名称 | 説明 |
|------|---------|------|
| RAG | Retrieval-Augmented Generation | 検索拡張生成 |
| LLM | Large Language Model | 大規模言語モデル |
| nDCG | Normalized Discounted Cumulative Gain | 正規化割引累積利得 |
| MRR | Mean Reciprocal Rank | 平均逆順位 |
| GCS | Google Cloud Storage | Googleクラウドストレージ |
| API | Application Programming Interface | アプリケーションプログラミングインターフェース |
| YAML | YAML Ain't Markup Language | データシリアライゼーション形式 |
| CSV | Comma-Separated Values | カンマ区切り値形式 |
| UI | User Interface | ユーザーインターフェース |
| UX | User Experience | ユーザーエクスペリエンス |

---

## バージョン履歴

| バージョン | 日付 | 主な変更内容 |
|-----------|------|------------|
| 3.0.1 | 2025-12-31 | v3.0新機能用語追加（Hybrid Search、Google Drive連携、Steering、Multi-tenant、Claude Code）、ディレクトリ名変更反映（prompts→saved_prompts、archived→processed） |
| 3.0 | 2025-12-29 | マルチテナント対応、ノート取り込み改善、モデル2段階選択、GCS構造変更を反映 |
| 2.0.5 | 2025-12-19 | Phase 6 デプロイ・ドキュメント関連用語追加 |
| 2.0 | 2025-12-19 | Phase 1-5 実装完了版 |
| 1.0 | - | 初版（既存システム LangChain_v2 ベース） |

---

## 関連ドキュメント

- [プロダクト要求定義書](product-requirements.md)
- [機能設計書](functional-design.md)
- [技術仕様書](architecture.md)
- [API仕様書](api-specification.md)
- [リポジトリ構造定義書](repository-structure.md)
- [開発ガイドライン](development-guidelines.md)

---

**作成日**: 2025-12-29
**最終更新**: 2025-12-31
**バージョン**: 3.0.1 (v3.0新機能を追加、ディレクトリ構造の変更を反映)
