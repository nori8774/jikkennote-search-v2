---
name: architecture-design
description: アーキテクチャ設計書を作成するための詳細ガイドとテンプレート。アーキテクチャ設計書作成時にのみ使用。
allowed-tools: Read, Write
---

# アーキテクチャ設計書作成スキル (実験ノート検索システム v2.0)

このスキルは、実験ノート検索システムのアーキテクチャ設計書を作成するためのガイドです。

## プロジェクト固有の前提条件

### 既存のアーキテクチャ設計書
このプロジェクトには既に完成したアーキテクチャ設計書が存在します:
- **ファイルパス**: `docs/architecture.md`
- **優先順位**: 既存のアーキテクチャ設計書が最優先。このスキルは参考資料として使用。

### 依存ドキュメント
アーキテクチャ設計書は以下のドキュメントを参照して作成します:
- `docs/product-requirements.md` - PRD
- `docs/functional-design.md` - 機能設計書

## 出力先

作成したアーキテクチャ設計書は以下に保存してください:
```
docs/architecture.md
```

## プロジェクト固有の技術スタック

### フロントエンド
- **フレームワーク**: Next.js 15 (App Router)
- **言語**: TypeScript 5.x
- **UI**: React 19 + Tailwind CSS
- **状態管理**: React Context

### バックエンド
- **フレームワーク**: FastAPI
- **言語**: Python 3.12+
- **AIフレームワーク**: LangChain + LangGraph
- **ベクトルDB**: ChromaDB
- **Reranking**: Cohere Rerank API

### インフラ
- **フロントエンド**: Vercel
- **バックエンド**: Google Cloud Run
- **ストレージ**: Google Cloud Storage (本番環境)
- **認証**: なし（URLアクセスベース）

### セキュリティ
- **APIキー管理**: ユーザーがブラウザ上で入力・保存（localStorage）
- **CORS**: Vercelドメインのみ許可

### パフォーマンス要件
- 検索レスポンス時間: < 5秒
- 新出単語抽出処理: < 10秒/ノート
- ChromaDBベクトル検索: 1000件まで1秒以内

詳細なガイドは、参照プロジェクトの `.claude/skills/architecture-design/` を参照してください。
