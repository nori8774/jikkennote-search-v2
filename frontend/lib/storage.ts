/**
 * Local Storage Management
 * ブラウザのlocalStorageを使った設定管理
 */

const STORAGE_KEYS = {
  OPENAI_API_KEY: 'openai_api_key',
  COHERE_API_KEY: 'cohere_api_key',
  EMBEDDING_MODEL: 'embedding_model',
  LLM_MODEL: 'llm_model',  // 後方互換性のため維持
  SEARCH_LLM_MODEL: 'search_llm_model',  // v3.0: 検索・判定用LLM
  SUMMARY_LLM_MODEL: 'summary_llm_model',  // v3.0: 要約生成用LLM
  SEARCH_MODE: 'search_mode',  // v3.0.1: 検索モード
  HYBRID_ALPHA: 'hybrid_alpha',  // v3.0.1: ハイブリッド検索の重み
  CUSTOM_PROMPTS: 'custom_prompts',
  FOLDER_PATHS: 'folder_paths',
  STORAGE_TYPE: 'storage_type',
  GOOGLE_DRIVE_FOLDER_ID: 'google_drive_folder_id',
  GOOGLE_DRIVE_CREDENTIALS_PATH: 'google_drive_credentials_path',
};

export const storage = {
  // APIキー
  setOpenAIApiKey(key: string) {
    localStorage.setItem(STORAGE_KEYS.OPENAI_API_KEY, key);
  },

  getOpenAIApiKey(): string | null {
    return localStorage.getItem(STORAGE_KEYS.OPENAI_API_KEY);
  },

  setCohereApiKey(key: string) {
    localStorage.setItem(STORAGE_KEYS.COHERE_API_KEY, key);
  },

  getCohereApiKey(): string | null {
    return localStorage.getItem(STORAGE_KEYS.COHERE_API_KEY);
  },

  // モデル設定
  setEmbeddingModel(model: string) {
    localStorage.setItem(STORAGE_KEYS.EMBEDDING_MODEL, model);
  },

  getEmbeddingModel(): string | null {
    return localStorage.getItem(STORAGE_KEYS.EMBEDDING_MODEL);
  },

  setLLMModel(model: string) {
    localStorage.setItem(STORAGE_KEYS.LLM_MODEL, model);
  },

  getLLMModel(): string | null {
    return localStorage.getItem(STORAGE_KEYS.LLM_MODEL);
  },

  // v3.0: 検索・判定用LLMモデル
  setSearchLLMModel(model: string) {
    localStorage.setItem(STORAGE_KEYS.SEARCH_LLM_MODEL, model);
  },

  getSearchLLMModel(): string | null {
    return localStorage.getItem(STORAGE_KEYS.SEARCH_LLM_MODEL);
  },

  // v3.0: 要約生成用LLMモデル
  setSummaryLLMModel(model: string) {
    localStorage.setItem(STORAGE_KEYS.SUMMARY_LLM_MODEL, model);
  },

  getSummaryLLMModel(): string | null {
    return localStorage.getItem(STORAGE_KEYS.SUMMARY_LLM_MODEL);
  },

  // v3.0.1: 検索モード
  setSearchMode(mode: 'semantic' | 'keyword' | 'hybrid') {
    localStorage.setItem(STORAGE_KEYS.SEARCH_MODE, mode);
  },

  getSearchMode(): 'semantic' | 'keyword' | 'hybrid' | null {
    return localStorage.getItem(STORAGE_KEYS.SEARCH_MODE) as 'semantic' | 'keyword' | 'hybrid' | null;
  },

  // v3.0.1: ハイブリッド検索の重み
  setHybridAlpha(alpha: number) {
    localStorage.setItem(STORAGE_KEYS.HYBRID_ALPHA, alpha.toString());
  },

  getHybridAlpha(): number | null {
    const value = localStorage.getItem(STORAGE_KEYS.HYBRID_ALPHA);
    return value ? parseFloat(value) : null;
  },

  // カスタムプロンプト
  setCustomPrompts(prompts: Record<string, string>) {
    localStorage.setItem(STORAGE_KEYS.CUSTOM_PROMPTS, JSON.stringify(prompts));
  },

  getCustomPrompts(): Record<string, string> | null {
    const data = localStorage.getItem(STORAGE_KEYS.CUSTOM_PROMPTS);
    return data ? JSON.parse(data) : null;
  },

  // フォルダパス
  setFolderPaths(paths: Record<string, string>) {
    localStorage.setItem(STORAGE_KEYS.FOLDER_PATHS, JSON.stringify(paths));
  },

  getFolderPaths(): Record<string, string> | null {
    const data = localStorage.getItem(STORAGE_KEYS.FOLDER_PATHS);
    return data ? JSON.parse(data) : null;
  },

  // ストレージタイプ
  setStorageType(type: 'local' | 'gcs' | 'google_drive') {
    localStorage.setItem(STORAGE_KEYS.STORAGE_TYPE, type);
  },

  getStorageType(): 'local' | 'gcs' | 'google_drive' | null {
    return localStorage.getItem(STORAGE_KEYS.STORAGE_TYPE) as any;
  },

  // Google Drive設定
  setGoogleDriveFolderId(id: string) {
    localStorage.setItem(STORAGE_KEYS.GOOGLE_DRIVE_FOLDER_ID, id);
  },

  getGoogleDriveFolderId(): string | null {
    return localStorage.getItem(STORAGE_KEYS.GOOGLE_DRIVE_FOLDER_ID);
  },

  setGoogleDriveCredentialsPath(path: string) {
    localStorage.setItem(STORAGE_KEYS.GOOGLE_DRIVE_CREDENTIALS_PATH, path);
  },

  getGoogleDriveCredentialsPath(): string | null {
    return localStorage.getItem(STORAGE_KEYS.GOOGLE_DRIVE_CREDENTIALS_PATH);
  },

  // 全削除
  clearAll() {
    Object.values(STORAGE_KEYS).forEach((key) => {
      localStorage.removeItem(key);
    });
  },
};
