/**
 * プロンプト保存・レストア機能の型定義
 */

export interface SavedPrompt {
  id: string;
  name: string;
  description?: string;
  prompts: {
    query_generation: string;
    compare: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface PromptStorage {
  savedPrompts: SavedPrompt[];
  maxPrompts: number;
}

/**
 * 評価履歴の型定義（プロンプト名を含む）
 */
export interface EvaluationHistory {
  id: string;
  testCaseId: string;
  testCaseName: string;
  timestamp: string;
  promptName?: string; // 使用したプロンプトの名前
  query: {
    purpose: string;
    materials: string;
    methods: string;
    instruction?: string;
  };
  metrics: {
    ndcg_10: number;
    precision_3: number;
    precision_5: number;
    precision_10: number;
    recall_10: number;
    mrr: number;
  };
  ranking: {
    noteId: string;
    rank: number;
    score: number;
  }[];
}
