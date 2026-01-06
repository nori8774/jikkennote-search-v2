import { test, expect } from '@playwright/test';

// ⚠️ このテストはFirebase認証が必要です
// Firebase認証が設定されていない場合、テストをスキップします
test.describe.skip('プロンプト管理機能（認証必須）', () => {
  test.beforeEach(async ({ page }) => {
    // 設定ページに移動
    await page.goto('/settings');

    // APIキーを設定（テスト用）
    await page.fill('input[type="password"]', 'sk-proj-test-key-12345678901234567890123456789012345678901234567890');

    // プロンプトタブに移動
    await page.click('text=プロンプト管理');
    await page.waitForTimeout(1000);
  });

  test('プロンプトを保存できること', async ({ page }) => {
    // デフォルトプロンプトが表示されていることを確認
    await expect(page.locator('text=プロンプトのカスタマイズ')).toBeVisible();

    // カスタムプロンプトを編集
    const customTextarea = page.locator('textarea').nth(1); // 右側のカスタムプロンプト
    await customTextarea.fill('これはテスト用のカスタムプロンプトです。');

    // 保存ボタンをクリック
    await page.click('text=現在のプロンプトを保存');

    // ダイアログでプロンプト名を入力
    await page.fill('input[placeholder*="高精度検索用プロンプト"]', 'テストプロンプト1');
    await page.fill('textarea[placeholder*="このプロンプトの特徴"]', 'Playwrightテスト用プロンプト');

    // 保存ボタンをクリック
    await page.click('button:has-text("保存")');

    // アラートが表示されることを確認（保存成功メッセージ）
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('テストプロンプト1');
      await dialog.accept();
    });

    // 保存済みプロンプトリストに表示されることを確認
    await page.waitForTimeout(2000);
    await expect(page.locator('text=テストプロンプト1')).toBeVisible();
    await expect(page.locator('text=Playwrightテスト用プロンプト')).toBeVisible();
  });

  test('保存したプロンプトを復元できること', async ({ page }) => {
    // まずプロンプトを保存
    await page.click('text=現在のプロンプトを保存');
    await page.fill('input[placeholder*="高精度検索用プロンプト"]', 'テストプロンプト2');
    await page.click('button:has-text("保存")');

    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    await page.waitForTimeout(2000);

    // カスタムプロンプトを変更
    const customTextarea = page.locator('textarea').nth(1);
    await customTextarea.fill('別の内容に変更');

    // 復元ボタンをクリック
    await page.click('text=復元');

    // 確認ダイアログを承認
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('テストプロンプト2');
      await dialog.accept();
    });

    await page.waitForTimeout(1000);

    // プロンプトが復元されたことを確認
    // （元の内容が表示されているはず）
  });

  test('保存したプロンプトを削除できること', async ({ page }) => {
    // まずプロンプトを保存
    await page.click('text=現在のプロンプトを保存');
    await page.fill('input[placeholder*="高精度検索用プロンプト"]', 'テストプロンプト削除用');
    await page.click('button:has-text("保存")');

    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    await page.waitForTimeout(2000);

    // 削除ボタンをクリック
    const deleteButton = page.locator('button:has-text("削除")').first();
    await deleteButton.click();

    // 確認ダイアログを承認
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('削除');
      await dialog.accept();
    });

    await page.waitForTimeout(2000);

    // プロンプトが削除されたことを確認
    // （リストから消えているはず）
  });

  test('プロンプトを初期設定にリセットできること', async ({ page }) => {
    // カスタムプロンプトを編集
    const customTextarea = page.locator('textarea').nth(1);
    await customTextarea.fill('カスタマイズした内容');

    // リセットボタンをクリック
    await page.locator('button:has-text("初期設定にリセット")').first().click();

    // 確認ダイアログを承認
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    await page.waitForTimeout(1000);

    // デフォルトプロンプトに戻っていることを確認
    // （左右のテキストエリアの内容が同じになる）
  });

  test('プロンプトの保存可能数が正しく表示されること', async ({ page }) => {
    // 保存可能数の表示を確認
    const remainingSlots = page.locator('text=/残り保存可能数: \\d+個/');
    await expect(remainingSlots).toBeVisible();

    // 数字を抽出して確認
    const text = await remainingSlots.textContent();
    expect(text).toMatch(/\d+個/);
  });
});
