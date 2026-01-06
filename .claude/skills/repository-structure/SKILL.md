---
name: repository-structure
description: リポジトリ構造定義書を作成するための詳細ガイドとテンプレート。リポジトリ構造定義書作成時にのみ使用。
allowed-tools: Read, Write
---

# リポジトリ構造定義書作成スキル (実験ノート検索システム v2.0)

このスキルは、実験ノート検索システムのリポジトリ構造定義書を作成するためのガイドです。

## プロジェクト固有の前提条件

### 既存のリポジトリ構造定義書
このプロジェクトには既に完成したリポジトリ構造定義書が存在します:
- **ファイルパス**: `docs/repository-structure.md`
- **優先順位**: 既存のリポジトリ構造定義書が最優先。このスキルは参考資料として使用。

### 依存ドキュメント
リポジトリ構造定義書は以下のドキュメントを参照して作成します:
- `docs/product-requirements.md` - PRD
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書

## 出力先

作成したリポジトリ構造定義書は以下に保存してください:
```
docs/repository-structure.md
```

## プロジェクト固有のディレクトリ構造

### 主要構成
```
jikkennote-search/
├── frontend/          # Next.js フロントエンド
│   ├── app/          # App Router ページ
│   ├── tests/        # E2Eテスト (Playwright)
│   └── package.json
│
├── backend/          # FastAPI バックエンド
│   ├── server.py     # メインAPIサーバー
│   ├── agent.py      # LangGraph ワークフロー
│   ├── ingest.py     # ノート取り込みロジック
│   ├── chroma_sync.py # ChromaDB管理
│   └── requirements.txt
│
├── docs/             # ドキュメント
│   ├── ideas/       # 初期要件、アイデアメモ
│   └── ...          # 正式版ドキュメント
│
└── .claude/          # Claude Code設定
    ├── commands/    # カスタムコマンド
    ├── agents/      # サブエージェント
    └── skills/      # スキル定義
```

### 命名規則
- **フロントエンド**: PascalCase.tsx (コンポーネント), camelCase.ts (ユーティリティ)
- **バックエンド**: snake_case.py (Pythonファイル)
- **ドキュメント**: kebab-case.md

詳細なガイドは、参照プロジェクトの `.claude/skills/repository-structure/` を参照してください。
