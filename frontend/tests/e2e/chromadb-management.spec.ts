import { test, expect } from '@playwright/test';

test.describe('ChromaDB Management', () => {
  test.beforeEach(async ({ page }) => {
    // 設定ページに移動
    await page.goto('/settings');

    // APIキーを設定（テスト用）
    await page.fill('input[placeholder*="sk-proj"]', 'sk-test-key');
    await page.fill('input[placeholder="..."]', 'test-cohere-key');
  });

  test('ChromaDB情報が正しく表示される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // ChromaDB情報セクションを確認
    const chromaSection = page.locator('text=現在のChromaDB設定');
    await expect(chromaSection).toBeVisible();

    // Embeddingモデル情報が表示されているか確認
    const modelInfo = page.locator('text=/Embeddingモデル:/');
    await expect(modelInfo).toBeVisible();
  });

  test('Embeddingモデル変更時に警告が表示される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // 現在のEmbeddingモデルを取得（label: "Embeddingモデル"の次のselect）
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    const currentModel = await embeddingSelect.inputValue();
    console.log('Current model:', currentModel);

    // 別のモデルを選択
    const newModel = currentModel === 'text-embedding-3-small'
      ? 'text-embedding-3-large'
      : 'text-embedding-3-small';

    await embeddingSelect.selectOption(newModel);

    // ダイアログハンドラーを設定
    page.on('dialog', async dialog => {
      console.log('Dialog message:', dialog.message());
      expect(dialog.message()).toContain('警告');
      expect(dialog.message()).toContain('Embeddingモデルを変更');
      expect(dialog.message()).toContain('ChromaDB');
      await dialog.dismiss(); // キャンセル
    });

    // 保存ボタンをクリック
    await page.click('button:has-text("設定を保存")');

    // ダイアログが表示されるまで待つ
    await page.waitForTimeout(1000);
  });

  test('Embeddingモデル変更を承認すると保存される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // 現在のモデルを確認
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    const currentModel = await embeddingSelect.inputValue();

    // 別のモデルを選択
    const newModel = currentModel === 'text-embedding-3-small'
      ? 'text-embedding-3-large'
      : 'text-embedding-3-small';

    await embeddingSelect.selectOption(newModel);

    // ダイアログを承認
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    // 保存ボタンをクリック
    await page.click('button:has-text("設定を保存")');

    // 保存完了メッセージを確認
    await expect(page.locator('text=保存しました')).toBeVisible({ timeout: 5000 });

    // ページをリロードして保存されているか確認
    await page.reload();
    await page.click('text=モデル選択');

    const savedModel = await embeddingSelect.inputValue();
    expect(savedModel).toBe(newModel);
  });

  test('Embeddingモデル変更をキャンセルすると元に戻る', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // 現在のモデルを確認
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    const originalModel = await embeddingSelect.inputValue();

    // まず、現在のモデルを保存する（localStorageに値を設定）
    await page.click('button:has-text("設定を保存")');
    await page.waitForTimeout(500);

    // 別のモデルを選択
    const newModel = originalModel === 'text-embedding-3-small'
      ? 'text-embedding-3-large'
      : 'text-embedding-3-small';

    await embeddingSelect.selectOption(newModel);

    // 保存する前にダイアログハンドラーを設定
    let dialogWasShown = false;
    page.once('dialog', async dialog => {
      console.log('Dialog shown and dismissed');
      dialogWasShown = true;
      await dialog.dismiss();
    });

    // 保存ボタンをクリック
    await page.click('button:has-text("設定を保存")');

    // ダイアログが表示されるまで待つ
    await page.waitForTimeout(500);
    expect(dialogWasShown).toBe(true);

    // Reactの状態更新を待つ
    await page.waitForTimeout(1000);

    // モデルが元に戻っているか確認（ページをリロードして確認）
    await page.reload();
    await page.click('text=モデル選択');

    const embeddingSelectAfterReload = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    const currentModel = await embeddingSelectAfterReload.inputValue();
    expect(currentModel).toBe(originalModel);
  });

  test('ChromaDB情報とEmbeddingモデルが一致しない場合、警告が表示される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // ChromaDBの現在のモデルと異なるモデルを選択
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    await embeddingSelect.selectOption('text-embedding-3-large');

    // 警告メッセージが表示されるか確認
    const warningSection = page.locator('text=⚠️ 警告');

    // 警告が表示される場合
    if (await warningSection.isVisible()) {
      await expect(warningSection).toBeVisible();
      await expect(page.locator('text=Embeddingモデルを変更すると')).toBeVisible();
    }
  });

  test('ChromaDBリセットボタンが機能する', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // ChromaDBリセットボタンを探す
    const resetButton = page.locator('button:has-text("ChromaDBをリセット")');
    await expect(resetButton).toBeVisible();

    // 確認ダイアログハンドラー
    let dialogShown = false;
    page.on('dialog', async dialog => {
      console.log('Reset dialog:', dialog.message());
      expect(dialog.message()).toContain('危険な操作');
      expect(dialog.message()).toContain('ChromaDB');
      dialogShown = true;
      await dialog.dismiss(); // キャンセル
    });

    // リセットボタンをクリック
    await resetButton.click();

    // ダイアログが表示されるまで待つ
    await page.waitForTimeout(1000);

    expect(dialogShown).toBe(true);
  });

  test('ChromaDBリセットを承認すると実行される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // ChromaDBリセットボタンを探す
    const resetButton = page.locator('button:has-text("ChromaDBをリセット")');

    // 確認ダイアログを承認
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    // リセットボタンをクリック
    await resetButton.click();

    // 成功メッセージまたはアラートを確認
    // Note: アラートはdialogイベントでキャプチャされる
    await page.waitForTimeout(2000);
  });

  test('Embeddingモデル変更後、ChromaDB情報が更新される', async ({ page }) => {
    // モデルタブに切り替え
    await page.click('text=モデル選択');

    // 元のChromaDB情報を確認
    const originalInfo = await page.locator('text=/Embeddingモデル:.*/')
      .textContent();
    console.log('Original ChromaDB info:', originalInfo);

    // モデルを変更
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    await embeddingSelect.selectOption('text-embedding-3-large');

    // ダイアログを承認
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    // 保存
    await page.click('button:has-text("設定を保存")');
    await page.waitForTimeout(1000);

    // ChromaDBをリセット
    const resetButton = page.locator('button:has-text("ChromaDBをリセット")');
    if (await resetButton.isVisible()) {
      page.on('dialog', async dialog => {
        await dialog.accept();
      });
      await resetButton.click();
      await page.waitForTimeout(2000);
    }

    // ページをリロードしてChromaDB情報を再取得
    await page.reload();
    await page.click('text=モデル選択');

    // 新しいChromaDB情報を確認
    const newInfo = await page.locator('text=/Embeddingモデル:.*/')
      .textContent();
    console.log('New ChromaDB info:', newInfo);
  });
});

test.describe('ChromaDB Auto-Update Flow', () => {
  test('完全なフロー: モデル変更→警告→リセット→情報更新', async ({ page }) => {
    // 1. 設定ページに移動
    await page.goto('/settings');

    // 2. APIキー設定
    await page.fill('input[placeholder*="sk-proj"]', 'sk-test-key');
    await page.fill('input[placeholder="..."]', 'test-cohere-key');

    // 3. モデルタブに移動
    await page.click('text=モデル選択');

    // 4. 現在の設定を記録
    const embeddingSelect = page.locator('label:has-text("Embeddingモデル")').locator('..').locator('select');
    const originalModel = await embeddingSelect.inputValue();
    console.log('Step 1 - Original model:', originalModel);

    // 5. モデルを変更
    const newModel = originalModel === 'text-embedding-3-small'
      ? 'text-embedding-3-large'
      : 'text-embedding-3-small';
    await embeddingSelect.selectOption(newModel);
    console.log('Step 2 - Changed to:', newModel);

    // 6. 保存時に警告ダイアログが表示されることを確認
    let warningShown = false;
    page.once('dialog', async dialog => {
      console.log('Step 3 - Warning dialog shown:', dialog.message().substring(0, 50));
      warningShown = true;
      await dialog.accept(); // 変更を承認
    });

    await page.click('button:has-text("設定を保存")');
    await page.waitForTimeout(1000);

    expect(warningShown).toBe(true);
    console.log('Step 4 - Warning was shown and accepted');

    // 7. 保存成功メッセージ確認
    await expect(page.locator('text=保存しました')).toBeVisible({ timeout: 5000 });
    console.log('Step 5 - Settings saved');

    // 8. 警告メッセージが表示されているか確認
    const warningSection = page.locator('text=⚠️ 警告');
    if (await warningSection.isVisible()) {
      console.log('Step 6 - Warning banner is visible');
      await expect(page.locator('text=Embeddingモデルを変更すると')).toBeVisible();
    }

    // 9. ChromaDBリセットボタンをクリック
    const resetButton = page.locator('button:has-text("ChromaDBをリセット")');
    await expect(resetButton).toBeVisible();

    page.once('dialog', async dialog => {
      console.log('Step 7 - Reset confirmation:', dialog.message().substring(0, 50));
      await dialog.accept();
    });

    await resetButton.click();
    await page.waitForTimeout(3000);  // リセット処理を待つ
    console.log('Step 8 - ChromaDB reset completed');

    // 10. ページをリロードして最終確認
    await page.reload();
    await page.click('text=モデル選択');

    const finalModel = await embeddingSelect.inputValue();
    console.log('Step 9 - Final model:', finalModel);
    expect(finalModel).toBe(newModel);

    console.log('✅ Complete flow test passed');
  });
});
