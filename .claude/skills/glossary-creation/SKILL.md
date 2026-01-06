---
name: glossary-creation
description: 用語集を作成するための詳細ガイドとテンプレート。用語集作成時にのみ使用。
allowed-tools: Read, Write
---

# 用語集作成スキル (実験ノート検索システム v2.0)

このスキルは、実験ノート検索システムの用語集を作成するためのガイドです。

## プロジェクト固有の前提条件

### 既存の用語集
このプロジェクトには既に完成した用語集が存在します:
- **ファイルパス**: `docs/glossary.md`
- **優先順位**: 既存の用語集が最優先。このスキルは参考資料として使用。

### 依存ドキュメント
用語集は以下のドキュメントを参照して作成します:
- `docs/product-requirements.md` - PRD
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書

## 出力先

作成した用語集は以下に保存してください:
```
docs/glossary.md
```

## プロジェクト固有の重要用語

### RAG関連
- **RAG (Retrieval-Augmented Generation)**: 検索拡張生成
- **nDCG@10**: 検索精度の評価指標
- **Embedding**: テキストをベクトル化する技術
- **Reranking**: ベクトル検索結果の再順位付け

### システム固有
- **Agent**: LangGraphで定義されたワークフロー
- **AgentState**: LangGraphワークフローの状態
- **ChromaDB**: ベクトルデータベース
- **正規化辞書 (Master Dictionary)**: 表記揺れをマッピングした辞書
- **新出単語**: ノート取り込み時に辞書に存在しない単語

### 評価関連
- **Precision@K**: 上位K件中の正解割合
- **Recall@K**: 全正解中、上位K件に含まれる割合
- **MRR (Mean Reciprocal Rank)**: 平均逆順位

### 技術用語
- **LangChain**: LLMアプリケーション開発ライブラリ
- **LangGraph**: ステートフルエージェント管理ライブラリ
- **Cohere Rerank**: リランキングAPI

詳細なガイドは、参照プロジェクトの `.claude/skills/glossary-creation/` を参照してください。
