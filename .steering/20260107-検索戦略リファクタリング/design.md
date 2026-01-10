# 設計書

## アーキテクチャ概要

2コレクション構成 + 軸別検索戦略を採用。材料・方法軸は同一コレクションを異なる検索方式で検索し、結果をブレンドしてリランキングする。

```
┌─────────────────────────────────────────────────────────────┐
│                     ノート取り込み (ingest.py)               │
├─────────────────────────────────────────────────────────────┤
│  Markdown Note                                              │
│       │                                                     │
│       ├──→ extract_sections() ─→ materials + methods 結合   │
│       │                            (辞書正規化のみ)          │
│       │                                                     │
│       └──→ combined (ノート全体)                            │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │ materials_methods_  │    │ combined_           │        │
│  │ collection_{team}   │    │ collection_{team}   │        │
│  └─────────────────────┘    └─────────────────────┘        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      検索実行 (agent.py)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 材料軸: materials_methods_collection                 │   │
│  │         → BM25 キーワード検索                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 方法軸: materials_methods_collection                 │   │
│  │         → セマンティック検索                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 総合軸: combined_collection                          │   │
│  │         → セマンティック検索                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│               ┌─────────────────────┐                      │
│               │  スコアブレンド     │                      │
│               │  (RRF or Linear)    │                      │
│               └─────────────────────┘                      │
│                            │                                │
│                            ▼                                │
│               ┌─────────────────────┐                      │
│               │  Cohere Rerank      │                      │
│               └─────────────────────┘                      │
│                            │                                │
│                            ▼                                │
│               ┌─────────────────────┐                      │
│               │  Top 3 (通常) /     │                      │
│               │  Top 10 (評価)      │                      │
│               └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. config.py - 設定変更

**責務**:
- コレクション名の定義変更（3→2コレクション）
- 検索軸ごとの検索方式設定

**実装の要点**:
```python
# 変更前
MATERIALS_COLLECTION_NAME = "materials_collection"
METHODS_COLLECTION_NAME = "methods_collection"
COMBINED_COLLECTION_NAME = "combined_collection"

# 変更後
MATERIALS_METHODS_COLLECTION_NAME = "materials_methods_collection"
COMBINED_COLLECTION_NAME = "combined_collection"

# 軸別検索方式設定（新規）
AXIS_SEARCH_MODES = {
    "material": "keyword",    # BM25
    "method": "semantic",     # ベクトル
    "combined": "semantic"    # ベクトル
}
```

### 2. chroma_sync.py - コレクション管理

**責務**:
- `get_team_multi_collection_vectorstores()` を2コレクション対応に変更
- `reset_team_collections()` を2コレクション対応に変更

**実装の要点**:
- 戻り値を `{"materials_methods": vs, "combined": vs}` に変更
- 旧コレクション（materials, methods）もリセット対象に含める（マイグレーション対応）

### 3. ingest.py - 取り込み処理簡素化

**責務**:
- 省略形展開処理の削除
- サフィックスマッピング処理の削除
- 材料+方法結合チャンクの生成

**実装の要点**:
```python
def extract_sections(content: str) -> Dict[str, str]:
    # 変更: materials_methodsを追加
    return {
        "materials_methods": materials + "\n\n" + methods,  # 新規
        "combined": content
    }
```

- `expand_shortcuts_from_materials()` 呼び出しを削除
- `apply_suffix_mapping()` 呼び出しを削除
- 2コレクションへの登録に変更

### 4. agent.py - 検索ロジック変更

**責務**:
- 軸別検索方式の適用（材料軸: BM25、方法・総合軸: セマンティック）
- スコアブレンドとリランキングの実装

**実装の要点**:

```python
def _multi_axis_search_node(self, state: AgentState):
    # 材料軸: BM25キーワード検索
    material_results = self._keyword_search_on_vectorstore(
        self.vectorstores["materials_methods"],
        state.get("material_query"),
        k=config.VECTOR_SEARCH_K
    )

    # 方法軸: セマンティック検索（同じコレクション）
    method_results = self.vectorstores["materials_methods"].similarity_search_with_relevance_scores(
        state.get("method_query"),
        k=config.VECTOR_SEARCH_K
    )

    # 総合軸: セマンティック検索
    combined_results = self.vectorstores["combined"].similarity_search_with_relevance_scores(
        state.get("combined_query"),
        k=config.VECTOR_SEARCH_K
    )
```

## データフロー

### ノート取り込みフロー
```
1. Markdownファイル読み込み
2. extract_sections() でセクション抽出
   - materials_methods: 材料 + 方法を結合
   - combined: ノート全体
3. 辞書正規化（名寄せ）を適用
4. 2コレクションに登録
   - materials_methods_collection_{team_id}
   - combined_collection_{team_id}
```

### 検索フロー
```
1. クエリ生成（材料軸、方法軸、総合軸）
2. 軸別検索実行
   - 材料軸: materials_methods_collection → BM25
   - 方法軸: materials_methods_collection → セマンティック
   - 総合軸: combined_collection → セマンティック
3. スコアブレンド（RRF or Linear）
4. Cohere Rerank
5. Top N 返却
```

## エラーハンドリング戦略

### コレクション移行エラー
- 旧コレクションが残っている場合: リセット時に一括削除
- 新コレクションが空の場合: 再取り込みを促すメッセージ表示

### 検索エラー
- コレクションが見つからない場合: 空の結果を返却し、ログに警告出力
- BM25検索でドキュメントが0件の場合: 空リストを返却

## テスト戦略

### ユニットテスト
- `extract_sections()` の材料+方法結合確認
- BM25検索のスコア計算確認

### 統合テスト
- E2Eテスト: 取り込み→検索→結果返却の一連フロー

## 依存ライブラリ

新規追加なし（既存のライブラリで対応可能）

## ディレクトリ構造

```
backend/
├── config.py              # 変更: コレクション名、検索方式設定
├── chroma_sync.py         # 変更: 2コレクション対応
├── ingest.py              # 変更: 取り込み処理簡素化
├── agent.py               # 変更: 軸別検索戦略
└── experimenter_profile.py # 変更なし（省略形展開呼び出し元で削除）
```

## 実装の順序

1. **config.py**: コレクション名、検索方式設定の変更
2. **chroma_sync.py**: 2コレクション対応
3. **ingest.py**: 取り込み処理簡素化
4. **agent.py**: 軸別検索戦略の実装
5. **テスト**: 動作確認
6. **ドキュメント**: CLAUDE.md, API仕様書の更新

## セキュリティ考慮事項

- 変更なし（既存のセキュリティ設計を維持）

## パフォーマンス考慮事項

- 取り込み時間: LLM呼び出し削減により短縮が期待される
- 検索時間: 2コレクション→3軸検索のため、若干増加の可能性あり
- メモリ使用量: コレクション数削減により若干減少

## 将来の拡張性

- ブレンド比率のUI調整機能
- 軸別検索方式のUI選択機能
- 検索戦略のA/Bテスト機能
