import { test, expect } from '@playwright/test';

test.describe('設定ページ（認証不要機能）', () => {
  test.beforeEach(async ({ page }) => {
    // 設定ページに移動
    await page.goto('/settings');
  });

  test('APIキータブが表示されること', async ({ page }) => {
    // APIキータブが表示されることを確認
    await expect(page.locator('text=APIキー')).toBeVisible();
  });

  test('モデル選択タブが表示されること', async ({ page }) => {
    await page.click('text=モデル選択');
    await expect(page.locator('text=Embeddingモデル')).toBeVisible();
    await expect(page.locator('text=LLMモデル')).toBeVisible();
  });

  test('プロンプト管理タブが表示されること', async ({ page }) => {
    await page.click('text=プロンプト管理');
    await expect(page.locator('text=プロンプトのカスタマイズ')).toBeVisible();
  });

  test('ChromaDB情報が表示されること', async ({ page }) => {
    await page.click('text=モデル選択');
    await expect(page.locator('text=ChromaDB管理')).toBeVisible();
  });
});
