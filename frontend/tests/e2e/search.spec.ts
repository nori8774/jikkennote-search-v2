import { test, expect } from '@playwright/test';

test.describe('検索機能', () => {
  test.beforeEach(async ({ page }) => {
    // APIキーをlocalStorageに設定
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('openai_api_key', 'sk-test-dummy-key-for-testing');
      localStorage.setItem('cohere_api_key', 'test-cohere-key');
    });
  });

  test('検索ページが正しく表示される', async ({ page }) => {
    await page.goto('/search');

    // 検索フォームの要素が存在することを確認
    await expect(page.locator('h1')).toHaveText('実験ノート検索');
    await expect(page.getByPlaceholder('実験の目的や背景を入力...')).toBeVisible();
    await expect(page.getByPlaceholder('使用する材料を入力...')).toBeVisible();
    await expect(page.getByPlaceholder('実験の手順を入力...')).toBeVisible();
    await expect(page.getByRole('button', { name: '検索' })).toBeVisible();
  });

  test('検索条件が空の場合、検索ボタンが無効', async ({ page }) => {
    await page.goto('/search');

    const searchButton = page.getByRole('button', { name: '検索' });
    await expect(searchButton).toBeDisabled();
  });

  test('検索条件を入力すると検索ボタンが有効になる', async ({ page }) => {
    await page.goto('/search');

    // 検索条件を入力
    await page.getByPlaceholder('実験の目的や背景を入力...').fill('テスト目的');
    await page.getByPlaceholder('使用する材料を入力...').fill('テスト材料');
    await page.getByPlaceholder('実験の手順を入力...').fill('テスト手順');

    const searchButton = page.getByRole('button', { name: '検索' });
    await expect(searchButton).toBeEnabled();
  });

  test('検索モード選択が動作する', async ({ page }) => {
    await page.goto('/search');

    // 検索モードのセレクトボックスを確認
    const selectBox = page.locator('select');
    await expect(selectBox).toBeVisible();

    // セマンティック検索がデフォルト
    await expect(selectBox).toHaveValue('semantic');

    // キーワード検索に変更
    await selectBox.selectOption('keyword');
    await expect(selectBox).toHaveValue('keyword');

    // ハイブリッド検索に変更
    await selectBox.selectOption('hybrid');
    await expect(selectBox).toHaveValue('hybrid');
  });
});
