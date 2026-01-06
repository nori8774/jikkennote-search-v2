/**
 * プロンプト保存・レストア機能のユーティリティ
 */

import { SavedPrompt } from './types';

const STORAGE_KEY = 'jikkennote_saved_prompts';
const MAX_PROMPTS = 50;

/**
 * 保存済みプロンプト一覧を取得
 */
export function getSavedPrompts(): SavedPrompt[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    const prompts: SavedPrompt[] = JSON.parse(stored);
    return prompts.sort((a, b) =>
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  } catch (error) {
    console.error('Failed to load saved prompts:', error);
    return [];
  }
}

/**
 * プロンプトを保存
 */
export function savePrompt(
  name: string,
  prompts: { query_generation: string; compare: string },
  description?: string
): { success: boolean; error?: string } {
  try {
    const existing = getSavedPrompts();

    // 最大数チェック
    if (existing.length >= MAX_PROMPTS) {
      return {
        success: false,
        error: `最大保存数（${MAX_PROMPTS}個）に達しています。既存のプロンプトを削除してください。`
      };
    }

    // 同名チェック
    if (existing.some(p => p.name === name)) {
      return {
        success: false,
        error: '同じ名前のプロンプトが既に存在します。'
      };
    }

    const newPrompt: SavedPrompt = {
      id: `prompt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      description,
      prompts,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const updated = [...existing, newPrompt];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    return { success: true };
  } catch (error) {
    console.error('Failed to save prompt:', error);
    return {
      success: false,
      error: 'プロンプトの保存に失敗しました。'
    };
  }
}

/**
 * プロンプトを更新
 */
export function updatePrompt(
  id: string,
  updates: Partial<Omit<SavedPrompt, 'id' | 'createdAt'>>
): { success: boolean; error?: string } {
  try {
    const existing = getSavedPrompts();
    const index = existing.findIndex(p => p.id === id);

    if (index === -1) {
      return {
        success: false,
        error: 'プロンプトが見つかりません。'
      };
    }

    // 名前変更時の重複チェック
    if (updates.name && updates.name !== existing[index].name) {
      if (existing.some(p => p.id !== id && p.name === updates.name)) {
        return {
          success: false,
          error: '同じ名前のプロンプトが既に存在します。'
        };
      }
    }

    existing[index] = {
      ...existing[index],
      ...updates,
      updatedAt: new Date().toISOString()
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));

    return { success: true };
  } catch (error) {
    console.error('Failed to update prompt:', error);
    return {
      success: false,
      error: 'プロンプトの更新に失敗しました。'
    };
  }
}

/**
 * プロンプトを削除
 */
export function deletePrompt(id: string): { success: boolean; error?: string } {
  try {
    const existing = getSavedPrompts();
    const filtered = existing.filter(p => p.id !== id);

    if (filtered.length === existing.length) {
      return {
        success: false,
        error: 'プロンプトが見つかりません。'
      };
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));

    return { success: true };
  } catch (error) {
    console.error('Failed to delete prompt:', error);
    return {
      success: false,
      error: 'プロンプトの削除に失敗しました。'
    };
  }
}

/**
 * プロンプトをIDで取得
 */
export function getPromptById(id: string): SavedPrompt | null {
  const prompts = getSavedPrompts();
  return prompts.find(p => p.id === id) || null;
}

/**
 * プロンプトを名前で取得
 */
export function getPromptByName(name: string): SavedPrompt | null {
  const prompts = getSavedPrompts();
  return prompts.find(p => p.name === name) || null;
}

/**
 * 保存可能な残り数を取得
 */
export function getRemainingSlots(): number {
  const existing = getSavedPrompts();
  return Math.max(0, MAX_PROMPTS - existing.length);
}
