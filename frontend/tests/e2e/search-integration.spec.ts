import { test, expect } from '@playwright/test';

/**
 * 検索統合テスト
 *
 * 実行前提条件:
 * - バックエンドが起動していること (http://localhost:8000)
 * - 環境変数に正しいAPIキーが設定されていること
 *   - OPENAI_API_KEY
 *   - COHERE_API_KEY
 * - ChromaDBにID1-2のノートがインジェストされていること
 */
test.describe('検索統合テスト', () => {
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';
  const COHERE_API_KEY = process.env.COHERE_API_KEY || '';

  test.skip(!OPENAI_API_KEY || !COHERE_API_KEY, 'APIキーが設定されていません');

  test.beforeEach(async ({ page }) => {
    // APIキーをlocalStorageに設定
    await page.goto('/');
    await page.evaluate(({ openaiKey, cohereKey }) => {
      localStorage.setItem('openai_api_key', openaiKey);
      localStorage.setItem('cohere_api_key', cohereKey);
      // デフォルト設定
      localStorage.setItem('embedding_model', 'text-embedding-3-small');
      localStorage.setItem('search_llm_model', 'gpt-4o-mini');
      localStorage.setItem('summary_llm_model', 'gpt-3.5-turbo');
      localStorage.setItem('search_mode', 'semantic');
      // v3.2.3: 3軸分離検索OFF（単一クエリ検索）で検証
      localStorage.setItem('multi_axis_enabled', 'false');
    }, { openaiKey: OPENAI_API_KEY, cohereKey: COHERE_API_KEY });
  });

  test('ID1-2の検索条件でID1-2が1番目にヒットする', async ({ page }) => {
    await page.goto('/search');

    // ID1-2ノートの検索条件（実際のノート内容に基づく）
    const purpose = 'HbA1cセンサーの感度最適化のため、抗体固定化量とブロッキング剤の組み合わせを検討する';
    const materials = `① HbA1c捕捉抗体溶液: 1.0 mg/mL
② ブロッキング剤（BSA）: 3% w/v
③ 緩衝液（PBS）: pH 7.4
④ 標準HbA1c試料: 5%, 10%, 15%
⑤ 金コロイド標識抗体`;
    const methods = `1. センサー基板の前処理（エタノール洗浄、UV照射30分）
2. 捕捉抗体の固定化（①を基板上にスポット、37℃で1時間インキュベート）
3. ブロッキング処理（②で30分処理後、③で3回洗浄）
4. 標準試料での検量線作成（④を各3点測定）
5. シグナル検出（⑤で標識後、蛍光測定）`;

    // 検索条件を入力
    await page.getByPlaceholder('実験の目的や背景を入力...').fill(purpose);
    await page.getByPlaceholder('使用する材料を入力...').fill(materials);
    await page.getByPlaceholder('実験の手順を入力...').fill(methods);

    // 検索実行
    const searchButton = page.getByRole('button', { name: '検索' });
    await searchButton.click();

    // 結果を待つ（タイムアウト60秒）
    await expect(page.locator('text=検索結果')).toBeVisible({ timeout: 60000 });

    // 最初の検索結果にID1-2が含まれることを確認
    const firstNote = page.locator('.border.border-gray-300.rounded-lg.p-4.mb-4').first();
    await expect(firstNote).toContainText('ID1-2', { timeout: 10000 });
  });

  test('3軸分離検索OFF（単一クエリ）で検索が正しく動作する', async ({ page }) => {
    // コンソールログを収集
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      consoleLogs.push(msg.text());
    });

    await page.goto('/search');

    // 3軸分離検索を無効に設定（localStorageはbeforeEachで設定済み）
    // UIのチェックボックスがOFFになっていることを確認
    const multiAxisCheckbox = page.locator('input[type="checkbox"]');
    await expect(multiAxisCheckbox).not.toBeChecked();

    // 簡単な検索条件
    await page.getByPlaceholder('実験の目的や背景を入力...').fill('HbA1cセンサーの検討');
    await page.getByPlaceholder('使用する材料を入力...').fill('HbA1c捕捉抗体');
    await page.getByPlaceholder('実験の手順を入力...').fill('抗体固定化');

    // 検索実行
    await page.getByRole('button', { name: '検索' }).click();

    // 結果を待つ
    await expect(page.locator('text=検索結果')).toBeVisible({ timeout: 60000 });

    // 検索結果が存在することを確認
    await expect(page.locator('.border.border-gray-300.rounded-lg.p-4.mb-4').first()).toBeVisible();
  });

});
