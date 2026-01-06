---
name: development-guidelines
description: 開発ガイドラインを作成するための詳細ガイドとテンプレート。開発ガイドライン作成時にのみ使用。
allowed-tools: Read, Write
---

# 開発ガイドライン作成スキル (実験ノート検索システム v2.0)

このスキルは、実験ノート検索システムの開発ガイドラインを作成するためのガイドです。

## プロジェクト固有の前提条件

### 既存の開発ガイドライン
このプロジェクトには既に完成した開発ガイドラインが存在します:
- **ファイルパス**: `docs/development-guidelines.md`
- **優先順位**: 既存の開発ガイドラインが最優先。このスキルは参考資料として使用。

### 依存ドキュメント
開発ガイドラインは以下のドキュメントを参照して作成します:
- `docs/product-requirements.md` - PRD
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/repository-structure.md` - リポジトリ構造定義書

## 出力先

作成した開発ガイドラインは以下に保存してください:
```
docs/development-guidelines.md
```

## プロジェクト固有の開発環境

### 環境セットアップ
**バックエンド**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

**フロントエンド**:
```bash
cd frontend
npm install
npm run dev
```

### テスト実行
```bash
# E2Eテスト (Frontend)
cd frontend
npm test

# Pythonテスト (Backend)
cd backend
python -m pytest
```

### コーディング規約
- **TypeScript**: ESLint + Prettier
- **Python**: Black + Flake8
- **命名**: camelCase (TS), snake_case (Python)

### Git運用
- **ブランチ**: main（本番）
- **コミットメッセージ**: Conventional Commits形式推奨

詳細なガイドは、参照プロジェクトの `.claude/skills/development-guidelines/` を参照してください。
