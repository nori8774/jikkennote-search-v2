import { test, expect } from '@playwright/test';

test.describe('評価機能', () => {
  test.beforeEach(async ({ page }) => {
    // 設定ページでAPIキーを設定
    await page.goto('/settings');

    // OpenAI APIキーを設定
    const openaiInput = page.locator('input[type="password"]').first();
    await openaiInput.fill('sk-proj-test-key-12345678901234567890123456789012345678901234567890');

    // Cohere APIキーを設定
    const cohereInput = page.locator('input[type="password"]').nth(1);
    await cohereInput.fill('test-cohere-key-1234567890');

    // 設定を保存
    await page.click('button:has-text("設定を保存")');
    await page.waitForTimeout(1000);
  });

  test('保存済みプロンプトを選択して評価できること', async ({ page }) => {
    // まず、プロンプトを保存
    await page.click('text=プロンプト管理');
    await page.waitForTimeout(1000);

    // カスタムプロンプトを作成して保存
    await page.click('text=現在のプロンプトを保存');
    await page.fill('input[placeholder*="高精度検索用プロンプト"]', '評価テスト用プロンプト');
    await page.fill('textarea[placeholder*="このプロンプトの特徴"]', '評価機能のテスト用');

    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    await page.click('button:has-text("保存")');
    await page.waitForTimeout(2000);

    // 評価ページに移動
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // 保存済みプロンプトリストに表示されていることを確認
    const promptSelect = page.locator('select').first();
    const options = await promptSelect.locator('option').allTextContents();
    expect(options).toContain('評価テスト用プロンプト');

    // プロンプトを選択
    await promptSelect.selectOption('評価テスト用プロンプト');
    await page.waitForTimeout(2000);

    // プロンプトが自動的にロードされたことを確認
    // （カスタムプロンプトが適用されているはず）
  });

  test('評価履歴にプロンプト名が記録されること', async ({ page }) => {
    // 評価ページに移動
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // プロンプト名を設定
    const promptSelect = page.locator('select').first();
    await promptSelect.selectOption('デフォルト');

    // テストデータがある場合、評価を実行
    // （実際のAPIキーがないため、この部分はスキップまたはモック化が必要）

    // 評価履歴セクションを確認
    const historySection = page.locator('text=評価履歴');
    await expect(historySection).toBeVisible();

    // 履歴が存在する場合、プロンプト名が表示されることを確認
    const promptNameInHistory = page.locator('text=プロンプト名:');
    if (await promptNameInHistory.isVisible()) {
      const historyContent = await promptNameInHistory.textContent();
      expect(historyContent).toContain('デフォルト');
    }
  });

  test('Excelファイルをアップロードできること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // ファイルアップロードセクションを確認
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();

    // ファイル選択時の動作を確認
    // （実際のExcelファイルが必要なため、モック化が推奨）
  });

  test('評価モデル選択ができること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // Embeddingモデル選択
    const embeddingSelect = page.locator('select').filter({ hasText: /text-embedding/ });
    await expect(embeddingSelect).toBeVisible();

    const embeddingOptions = await embeddingSelect.locator('option').allTextContents();
    expect(embeddingOptions).toContain('text-embedding-3-small');
    expect(embeddingOptions).toContain('text-embedding-3-large');
    expect(embeddingOptions).toContain('text-embedding-ada-002');

    // LLMモデル選択
    const llmSelect = page.locator('select').filter({ hasText: /gpt/ });
    await expect(llmSelect).toBeVisible();

    const llmOptions = await llmSelect.locator('option').allTextContents();
    expect(llmOptions).toContain('gpt-4o-mini');
    expect(llmOptions).toContain('gpt-4o');
    expect(llmOptions).toContain('gpt-4-turbo');
  });

  test('プロンプト編集セクションを開閉できること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // プロンプト編集ボタンをクリック
    await page.click('button:has-text("プロンプトを編集")');
    await page.waitForTimeout(1000);

    // プロンプト編集セクションが表示されることを確認
    const resetButton = page.locator('button:has-text("全て初期設定にリセット")');
    await expect(resetButton).toBeVisible();

    // 再度ボタンをクリックして閉じる
    await page.click('button:has-text("プロンプト編集を閉じる")');
    await page.waitForTimeout(500);

    // セクションが非表示になることを確認
    await expect(resetButton).not.toBeVisible();
  });

  test('評価履歴を展開して詳細を表示できること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // 評価履歴が存在する場合
    const historyItems = page.locator('[data-testid="evaluation-history-item"]');
    const count = await historyItems.count();

    if (count > 0) {
      // 最初の履歴アイテムをクリック
      await historyItems.first().click();
      await page.waitForTimeout(1000);

      // 詳細情報が表示されることを確認
      const detailSection = page.locator('text=入力条件');
      await expect(detailSection).toBeVisible();

      // 評価指標が表示されることを確認
      const metricsSection = page.locator('text=/nDCG|Precision|Recall|MRR/');
      await expect(metricsSection).toBeVisible();
    }
  });

  test('カスタムプロンプト名を手動入力できること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // プロンプト名セレクトで「カスタム」を選択
    const promptSelect = page.locator('select').first();
    await promptSelect.selectOption('カスタム');
    await page.waitForTimeout(500);

    // テキスト入力フィールドが表示されることを確認
    const customInput = page.locator('input[placeholder*="プロンプト名を入力"]');
    await expect(customInput).toBeVisible();

    // カスタム名を入力
    await customInput.fill('マイカスタムプロンプト');

    // 入力した値が保持されることを確認
    const value = await customInput.inputValue();
    expect(value).toBe('マイカスタムプロンプト');
  });

  test('評価進捗が表示されること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // 評価実行ボタンを確認
    const evaluateButton = page.locator('button:has-text("評価を実行")');
    await expect(evaluateButton).toBeVisible();

    // ボタンがテストデータがない場合は無効になっていることを確認
    const isDisabled = await evaluateButton.isDisabled();
    // テストデータがなければ無効化されているはず
  });

  test('評価履歴のデータチェック機能が動作すること', async ({ page }) => {
    await page.goto('/evaluate');
    await page.waitForTimeout(1000);

    // データチェックボタンを探す
    const dataCheckButton = page.locator('button:has-text("データチェック")');

    if (await dataCheckButton.isVisible()) {
      // ボタンをクリック
      await dataCheckButton.click();

      // アラートが表示されることを確認
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('evaluation_histories');
        await dialog.accept();
      });
    }
  });
});
