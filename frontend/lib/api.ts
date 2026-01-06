/**
 * API Client
 * バックエンドAPIとの通信を行う
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * 認証ヘッダーを生成する
 *
 * @param idToken Firebase ID Token
 * @param teamId 現在のチームID
 * @returns 認証ヘッダー
 */
export function getAuthHeaders(idToken: string | null, teamId: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (idToken) {
    headers['Authorization'] = `Bearer ${idToken}`;
  }

  if (teamId) {
    headers['X-Team-ID'] = teamId;
  }

  return headers;
}

export interface SearchRequest {
  purpose: string;
  materials: string;
  methods: string;
  type?: string;
  instruction?: string;
  openai_api_key: string;
  cohere_api_key: string;
  embedding_model?: string;
  llm_model?: string;
  // v3.0: 2段階モデル選択
  search_llm_model?: string;  // 検索・判定用LLM
  summary_llm_model?: string;  // 要約生成用LLM
  // v3.0.1: ハイブリッド検索
  search_mode?: 'semantic' | 'keyword' | 'hybrid';  // 検索モード
  hybrid_alpha?: number;  // ハイブリッド検索のセマンティック重み（0.0-1.0）
  custom_prompts?: Record<string, string>;
  evaluation_mode?: boolean;  // 評価モード（True: 比較省略、Top10返却）
  // v3.1.0: 3軸分離検索設定
  multi_axis_enabled?: boolean;  // 3軸検索の有効/無効
  fusion_method?: 'rrf' | 'linear';  // スコア統合方式
  axis_weights?: { material: number; method: number; combined: number };  // 各軸のウエイト
  rerank_position?: 'per_axis' | 'after_fusion';  // リランク位置
  rerank_enabled?: boolean;  // リランキングの有効/無効
}

export interface SearchResponse {
  success: boolean;
  message: string;
  retrieved_docs: string[];
  normalized_materials?: string;
  search_query?: string;
}

export interface PromptsResponse {
  success: boolean;
  prompts: Record<string, {
    name: string;
    description: string;
    prompt: string;
  }>;
}

export interface IngestRequest {
  openai_api_key: string;
  source_folder?: string;
  post_action?: 'delete' | 'archive' | 'keep' | 'move_to_processed';
  archive_folder?: string;
  embedding_model?: string;
  rebuild_mode?: boolean;
}

export interface IngestResponse {
  success: boolean;
  message: string;
  new_notes: string[];
  skipped_notes: string[];
}

export interface NoteResponse {
  success: boolean;
  note?: {
    id: string;
    content: string;
    sections: {
      purpose?: string;
      materials?: string;
      methods?: string;
      results?: string;
    };
  };
  error?: string;
}

export interface AnalyzeRequest {
  note_ids: string[];
  note_contents: string[];
  openai_api_key: string;
}

export interface AnalyzeResponse {
  success: boolean;
  new_terms: Array<{
    term: string;
    similar_candidates: Array<{
      term: string;
      canonical: string;
      similarity: number;
      embedding_similarity: number;
      combined_score: number;
    }>;
    llm_suggestion: {
      decision: 'variant' | 'new';
      reason: string;
      suggested_canonical?: string;
    };
  }>;
}

export interface DictionaryEntry {
  canonical: string;
  variants: string[];
  category?: string;
  note?: string;
  suffix_equivalents?: string[][];  // サフィックス同等グループ（v3.1.2）
  created_at?: string;
  updated_at?: string;
}

export interface DictionaryResponse {
  success: boolean;
  entries: DictionaryEntry[];
}

export interface DictionaryUpdateRequest {
  updates: Array<{
    term: string;
    decision: 'new' | 'variant';
    canonical?: string;
    category?: string;
    note?: string;
  }>;
}

export interface DictionaryUpdateResponse {
  success: boolean;
  message: string;
  updated_entries: number;
}

// ============================================
// 実験者プロファイル（v3.2.0）
// ============================================

export interface ExperimenterProfile {
  experimenter_id: string;
  name: string;
  suffix_conventions?: string[][];
  material_shortcuts?: Record<string, string>;
  learned_from?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ExperimenterProfilesResponse {
  success: boolean;
  profiles: ExperimenterProfile[];
  id_pattern: string;
}

export interface ExperimenterProfileDetailResponse {
  success: boolean;
  profile?: ExperimenterProfile;
  error?: string;
}

export interface CreateExperimenterProfileRequest {
  experimenter_id: string;
  name: string;
  material_shortcuts?: Record<string, string>;
  suffix_conventions?: string[][];
}

export interface UpdateExperimenterProfileRequest {
  name?: string;
  material_shortcuts?: Record<string, string>;
  suffix_conventions?: string[][];
}

export interface ExperimenterProfileMutationResponse {
  success: boolean;
  message: string;
}

// ============================================
// 同義語辞書（v3.2.1）
// ============================================

export interface SynonymGroup {
  canonical: string;
  variants: string[];
  created_at?: string;
  updated_at?: string;
}

export interface SynonymGroupsResponse {
  success: boolean;
  groups: SynonymGroup[];
}

export interface SynonymGroupMutationResponse {
  success: boolean;
  message: string;
}

export const api = {
  async search(request: SearchRequest, idToken: string | null = null, teamId: string | null = null): Promise<SearchResponse> {
    const headers = getAuthHeaders(idToken, teamId);

    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('OpenAI APIキーが無効です。設定ページで正しいAPIキー（sk-で始まる）を入力してください。');
      }
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || response.statusText;
      throw new Error(`検索エラー: ${errorMessage}`);
    }

    return response.json();
  },

  async getDefaultPrompts(): Promise<PromptsResponse> {
    const response = await fetch(`${API_BASE_URL}/prompts`);

    if (!response.ok) {
      throw new Error(`Get prompts failed: ${response.statusText}`);
    }

    return response.json();
  },

  async uploadNotes(files: FileList, idToken: string | null = null, teamId: string | null = null): Promise<{ success: boolean; message: string; uploaded_files: string[] }> {
    const formData = new FormData();

    // Add all files to form data
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    const headers: Record<string, string> = {};
    if (idToken) {
      headers['Authorization'] = `Bearer ${idToken}`;
    }
    if (teamId) {
      headers['X-Team-ID'] = teamId;
    }

    const response = await fetch(`${API_BASE_URL}/upload/notes`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  },

  async ingest(request: IngestRequest, idToken: string | null = null, teamId: string | null = null): Promise<IngestResponse> {
    const headers = getAuthHeaders(idToken, teamId);

    const response = await fetch(`${API_BASE_URL}/ingest`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Ingest failed: ${response.statusText}`);
    }

    return response.json();
  },

  async health(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  async getNote(noteId: string, idToken: string | null = null, teamId: string | null = null): Promise<NoteResponse> {
    const headers = getAuthHeaders(idToken, teamId);

    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      headers,
    });

    if (!response.ok) {
      throw new Error(`Get note failed: ${response.statusText}`);
    }

    return response.json();
  },

  async analyzeNewTerms(request: AnalyzeRequest, idToken: string | null = null, teamId: string | null = null): Promise<AnalyzeResponse> {
    const headers = getAuthHeaders(idToken, teamId);

    const response = await fetch(`${API_BASE_URL}/ingest/analyze`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Analyze failed: ${response.statusText}`);
    }

    return response.json();
  },

  async getDictionary(idToken: string | null = null, teamId: string | null = null): Promise<DictionaryResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/dictionary`, { headers });

    if (!response.ok) {
      throw new Error(`Get dictionary failed: ${response.statusText}`);
    }

    return response.json();
  },

  async updateDictionary(request: DictionaryUpdateRequest, idToken: string | null = null, teamId: string | null = null): Promise<DictionaryUpdateResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/dictionary/update`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Update dictionary failed: ${response.statusText}`);
    }

    return response.json();
  },

  async exportDictionary(format: 'yaml' | 'json' | 'csv' = 'yaml', idToken: string | null = null, teamId: string | null = null): Promise<Blob> {
    const headers = getAuthHeaders(idToken, teamId);
    // FormDataの場合はContent-Typeを削除
    delete headers['Content-Type'];
    const response = await fetch(`${API_BASE_URL}/dictionary/export?format=${format}`, { headers });

    if (!response.ok) {
      throw new Error(`Export dictionary failed: ${response.statusText}`);
    }

    return response.blob();
  },

  async importDictionary(file: File, idToken: string | null = null, teamId: string | null = null): Promise<{ success: boolean; message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const headers = getAuthHeaders(idToken, teamId);
    // FormDataの場合はContent-Typeを削除（ブラウザが自動設定）
    delete headers['Content-Type'];

    const response = await fetch(`${API_BASE_URL}/dictionary/import`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Import dictionary failed: ${response.statusText}`);
    }

    return response.json();
  },

  async editDictionaryEntry(
    canonical: string,
    updates: {
      new_canonical?: string;
      variants?: string[];
      category?: string;
      note?: string;
    },
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<{ success: boolean; message: string }> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/dictionary/entry`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({
        canonical,
        ...updates,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `Edit dictionary entry failed: ${response.statusText}`);
    }

    return response.json();
  },

  async deleteDictionaryEntry(canonical: string, idToken: string | null = null, teamId: string | null = null): Promise<{ success: boolean; message: string }> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/dictionary/entry`, {
      method: 'DELETE',
      headers,
      body: JSON.stringify({ canonical }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `Delete dictionary entry failed: ${response.statusText}`);
    }

    return response.json();
  },

  // === Prompt Management APIs ===

  /**
   * 保存されているプロンプトの一覧を取得
   */
  async listSavedPrompts(idToken: string | null = null, teamId: string | null = null) {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/prompts/list`, { headers });

    if (!response.ok) {
      throw new Error(`List prompts failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * プロンプトをYAMLファイルとして保存
   */
  async savePrompt(name: string, prompts: Record<string, string>, description?: string, idToken: string | null = null, teamId: string | null = null) {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/prompts/save`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name,
        prompts,
        description: description || ''
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Save prompt failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * プロンプトをYAMLファイルから読み込み
   */
  async loadPrompt(name: string, idToken: string | null = null, teamId: string | null = null) {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/prompts/load/${encodeURIComponent(name)}`, { headers });

    if (!response.ok) {
      throw new Error(`Load prompt failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * プロンプトを削除
   */
  async deletePrompt(name: string, idToken: string | null = null, teamId: string | null = null) {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/prompts/delete/${encodeURIComponent(name)}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Delete prompt failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * プロンプトを更新
   */
  async updatePrompt(name: string, prompts?: Record<string, string>, description?: string, idToken: string | null = null, teamId: string | null = null) {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/prompts/update`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({
        name,
        prompts,
        description
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Update prompt failed: ${response.statusText}`);
    }

    return response.json();
  },

  // === ChromaDB Management APIs ===

  /**
   * ChromaDBの現在のembeddingモデル情報を取得
   */
  async getChromaInfo() {
    const response = await fetch(`${API_BASE_URL}/chroma/info`);

    if (!response.ok) {
      throw new Error(`Get ChromaDB info failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * ChromaDBを完全にリセット
   */
  async resetChromaDB() {
    const response = await fetch(`${API_BASE_URL}/chroma/reset`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Reset ChromaDB failed: ${response.statusText}`);
    }

    return response.json();
  },

  // === 実験者プロファイル管理 APIs（v3.2.0） ===

  /**
   * 実験者プロファイル一覧を取得
   */
  async getExperimenterProfiles(idToken: string | null = null, teamId: string | null = null): Promise<ExperimenterProfilesResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles`, { headers });

    if (!response.ok) {
      throw new Error(`Get experimenter profiles failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 実験者プロファイル詳細を取得
   */
  async getExperimenterProfile(experimenterId: string, idToken: string | null = null, teamId: string | null = null): Promise<ExperimenterProfileDetailResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles/${encodeURIComponent(experimenterId)}`, { headers });

    if (!response.ok) {
      throw new Error(`Get experimenter profile failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 実験者プロファイルを作成
   */
  async createExperimenterProfile(
    request: CreateExperimenterProfileRequest,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<ExperimenterProfileMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Create experimenter profile failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 実験者プロファイルを更新
   */
  async updateExperimenterProfile(
    experimenterId: string,
    request: UpdateExperimenterProfileRequest,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<ExperimenterProfileMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles/${encodeURIComponent(experimenterId)}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Update experimenter profile failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 実験者プロファイルを削除
   */
  async deleteExperimenterProfile(
    experimenterId: string,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<ExperimenterProfileMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles/${encodeURIComponent(experimenterId)}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Delete experimenter profile failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * IDパターンを更新
   */
  async updateIdPattern(
    pattern: string,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<ExperimenterProfileMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/experimenter-profiles/id-pattern`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ pattern }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Update ID pattern failed: ${response.statusText}`);
    }

    return response.json();
  },

  // === 同義語辞書管理 APIs（v3.2.1） ===

  /**
   * 同義語グループ一覧を取得
   */
  async getSynonymGroups(idToken: string | null = null, teamId: string | null = null): Promise<SynonymGroupsResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms`, { headers });

    if (!response.ok) {
      throw new Error(`Get synonym groups failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 同義語グループを追加
   */
  async addSynonymGroup(
    canonical: string,
    variants: string[],
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<SynonymGroupMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ canonical, variants }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Add synonym group failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 同義語グループを更新
   */
  async updateSynonymGroup(
    canonical: string,
    updates: { new_canonical?: string; variants?: string[] },
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<SynonymGroupMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms/${encodeURIComponent(canonical)}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Update synonym group failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 同義語グループを削除
   */
  async deleteSynonymGroup(
    canonical: string,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<SynonymGroupMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms/${encodeURIComponent(canonical)}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Delete synonym group failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 同義語グループにバリアントを追加
   */
  async addSynonymVariant(
    canonical: string,
    variant: string,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<SynonymGroupMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms/${encodeURIComponent(canonical)}/variants`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ variant }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Add variant failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 同義語グループからバリアントを削除
   */
  async removeSynonymVariant(
    canonical: string,
    variant: string,
    idToken: string | null = null,
    teamId: string | null = null
  ): Promise<SynonymGroupMutationResponse> {
    const headers = getAuthHeaders(idToken, teamId);
    const response = await fetch(`${API_BASE_URL}/synonyms/${encodeURIComponent(canonical)}/variants/${encodeURIComponent(variant)}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Remove variant failed: ${response.statusText}`);
    }

    return response.json();
  },
};
