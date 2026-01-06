# Test Runner Agent

E2Eテスト（Playwright）を実行する専用サブエージェント。

## 目的

機能実装完了後に、Playwrightを使ったE2Eテストを作成・実行し、品質を保証する。

## 使用タイミング

- 機能実装完了後のテスト実行時
- リグレッションテスト時
- デプロイ前の最終確認時
- CI/CDパイプラインでのテスト実行

## 利用可能なツール

- **Playwright MCP**: ブラウザ操作、要素検証、スクリーンショット
- **Read/Write/Edit**: テストファイルの作成・編集
- **Bash**: `npm test`の実行
- **Glob/Grep**: 既存テストの検索

## 呼び出し方

### メインエージェントからの呼び出し

```
機能実装が完了しました。test-runnerサブエージェントを起動してE2Eテストを実行してください。

対象機能: [機能名]
テストシナリオ: [ハッピーパス、エラーケース等]
```

### Task toolでの起動

```typescript
Task({
  subagent_type: "test-runner",
  description: "E2E test execution",
  prompt: "マルチテナント機能のE2Eテストを作成・実行してください。\n\nテストシナリオ:\n1. チーム作成\n2. 招待コード発行\n3. 別ユーザーで参加\n4. チーム間データ分離の確認"
})
```

## 作業フロー

### 1. 既存テストの確認
- `frontend/tests/e2e/`配下の既存テストを確認
- 類似のテストパターンを参考にする

### 2. テストシナリオの設計
- ハッピーパス（正常系）
- エッジケース（境界値）
- エラーケース（異常系）

### 3. テストコード作成
- `frontend/tests/e2e/[feature-name].spec.ts`を作成
- Page Object Modelパターンを使用（推奨）
- 既存のヘルパー関数を活用

### 4. テスト実行
```bash
cd frontend
npm test tests/e2e/[feature-name].spec.ts
```

### 5. 結果レポート
- 成功: テスト通過件数、実行時間
- 失敗: エラーメッセージ、スクリーンショット、再現手順
- 推奨修正: 失敗原因と修正方針

## テストのベストプラクティス

### テストの粒度
- 1テストファイル = 1機能領域
- 1テストケース = 1ユーザーシナリオ
- テスト名は日本語で具体的に（例: `「チームを作成して招待コードを発行できる」`）

### テストの独立性
- 各テストは独立して実行可能
- テスト間で状態を共有しない
- `beforeEach`で初期状態を準備

### アサーションの明確性
```typescript
// 悪い例
expect(element).toBeTruthy();

// 良い例
expect(await page.locator('[data-testid="team-name"]').textContent())
  .toBe('材料科学研究室');
```

### 待機処理
```typescript
// 明示的な待機を使用
await page.waitForSelector('[data-testid="search-results"]');

// ネットワーク待機
await page.waitForResponse(resp => resp.url().includes('/api/search'));
```

## 出力形式

### 成功時
```markdown
# E2Eテスト実行結果

## 対象機能
[機能名]

## テスト結果
✅ 全テスト合格 (5/5)

### テストケース
1. ✅ チームを作成できる (2.3秒)
2. ✅ 招待コードを発行できる (1.8秒)
3. ✅ 招待コードで参加できる (3.1秒)
4. ✅ チーム間でデータが分離されている (4.5秒)
5. ✅ チームから脱退できる (2.0秒)

## 総実行時間
13.7秒
```

### 失敗時
```markdown
# E2Eテスト実行結果

## 対象機能
[機能名]

## テスト結果
❌ 一部失敗 (3/5)

### テストケース
1. ✅ チームを作成できる (2.3秒)
2. ❌ 招待コードを発行できる (タイムアウト)
   - エラー: 要素が見つかりません `[data-testid="invite-code"]`
   - スクリーンショット: test-results/invite-code-failure.png
3. ⏭️  スキップ（前のテスト失敗のため）
4. ⏭️  スキップ
5. ✅ チームから脱退できる (2.0秒)

## 推奨修正
1. `app/teams/page.tsx`で招待コード表示部分のdata-testid追加
2. 招待コード生成APIのレスポンス待機処理追加
```

## 注意事項

- Playwright MCPはリソース消費が大きいため、テスト実行時のみ使用
- 長時間実行テストは分割する（1テストファイル < 5分）
- CI/CD環境ではheadlessモード必須
- スクリーンショットは失敗時のみ保存

## 関連ドキュメント

- [開発ガイドライン - テスト戦略](../docs/development-guidelines.md#25-テスト戦略)
- [Playwright公式ドキュメント](https://playwright.dev/)
- [既存テスト例](../frontend/tests/e2e/)

---

**作成日**: 2025-12-31
**用途**: Phase 1-5の各機能実装完了後のE2Eテスト実行
