---
name: steering
description: 作業指示毎の作業計画、タスクリストをドキュメントに記録するためのスキル。ユーザーからの指示をトリガーとした作業計画時、実装時、検証時に読み込む。
allowed-tools: Read, Write, Edit
---

# Steering スキル

ステアリングファイル（`.steering/`）に基づいた実装を支援し、tasklist.mdの進捗管理を確実に行うスキルです。

## スキルの目的

- ステアリングファイル（requirements.md, design.md, tasklist.md）の作成支援
- tasklist.mdに基づいた段階的な実装管理
- **進捗の自動追跡とtasklist.md更新の強制**
- 実装完了後の振り返り記録

## 使用タイミング

このスキルは以下のタイミングで使用してください：

1. **作業計画時**: ステアリングファイルを作成する時
2. **実装時**: tasklist.mdに従って実装する時
3. **検証時**: 実装完了後の振り返りを記録する時

## テンプレートの参照

以下のテンプレートを使用してステアリングファイルを作成してください:
- `.claude/skills/steering/templates/requirements.md`
- `.claude/skills/steering/templates/design.md`
- `.claude/skills/steering/templates/tasklist.md`

詳細な使用方法は、`.claude/commands/add-feature.md`を参照してください。
