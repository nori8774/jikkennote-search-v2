'use client';

import { useState, useEffect, useRef } from 'react';
import { api, ExperimenterProfile, SynonymGroup } from '@/lib/api';
import { storage } from '@/lib/storage';
import Button from '@/components/Button';
import { useAuth } from '@/lib/auth-context';

interface SavedPrompt {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export default function SettingsPage() {
  const { idToken, currentTeamId, loading } = useAuth();
  const [openaiKey, setOpenaiKey] = useState('');
  const [cohereKey, setCohereKey] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('text-embedding-3-small');
  const [llmModel, setLlmModel] = useState('gpt-4o-mini');  // 後方互換性のため維持
  const [searchLlmModel, setSearchLlmModel] = useState('gpt-4o-mini');  // v3.0: 検索・判定用
  const [summaryLlmModel, setSummaryLlmModel] = useState('gpt-3.5-turbo');  // v3.0: 要約生成用（デフォルト: 高速）
  const [searchMode, setSearchMode] = useState<'semantic' | 'keyword' | 'hybrid'>('semantic');  // v3.0.1
  const [hybridAlpha, setHybridAlpha] = useState(0.7);  // v3.0.1
  const [defaultPrompts, setDefaultPrompts] = useState<any>(null);
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<'api' | 'models' | 'prompts' | 'notes' | 'profiles' | 'synonyms'>('api');
  const [saved, setSaved] = useState(false);

  // プロンプト保存機能用のステート
  const [savedPromptsList, setSavedPromptsList] = useState<SavedPrompt[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [savePromptName, setSavePromptName] = useState('');
  const [savePromptDescription, setSavePromptDescription] = useState('');
  const [saveError, setSaveError] = useState('');

  // ChromaDB管理用のステート
  const [chromaDBInfo, setChromaDBInfo] = useState<{
    current_embedding_model: string | null;
    created_at: string | null;
    last_updated: string | null;
  } | null>(null);
  const [originalEmbeddingModel, setOriginalEmbeddingModel] = useState<string>('');

  // 保存ボタンクリック時のEmbeddingモデルの値を保持（キャンセル時の復元用）
  const embeddingModelBeforeSave = useRef<string>('');

  // ノート管理用のステート
  const [storageType, setStorageType] = useState<'local' | 'gcs' | 'google_drive'>('local');
  const [googleDriveFolderId, setGoogleDriveFolderId] = useState('');
  const [googleDriveCredentialsPath, setGoogleDriveCredentialsPath] = useState('');

  // 実験者プロファイル管理用のステート（v3.2.0）
  const [experimenterProfiles, setExperimenterProfiles] = useState<ExperimenterProfile[]>([]);
  const [idPattern, setIdPattern] = useState('^ID(\\d+)-');
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [editingProfile, setEditingProfile] = useState<ExperimenterProfile | null>(null);
  const [profileFormData, setProfileFormData] = useState({
    experimenter_id: '',
    name: '',
    material_shortcuts: {} as Record<string, string>,
    shortcutInput: { key: '', value: '' }
  });
  const [profileError, setProfileError] = useState('');

  // 同義語辞書管理用のステート（v3.2.1）
  const [synonymGroups, setSynonymGroups] = useState<SynonymGroup[]>([]);
  const [showSynonymDialog, setShowSynonymDialog] = useState(false);
  const [editingSynonym, setEditingSynonym] = useState<SynonymGroup | null>(null);
  const [synonymFormData, setSynonymFormData] = useState({
    canonical: '',
    variants: [] as string[],
    variantInput: ''
  });
  const [synonymError, setSynonymError] = useState('');

  // ローカルストレージと認証不要APIの読み込み（初回のみ）
  useEffect(() => {
    // localStorageから設定を読み込む
    setOpenaiKey(storage.getOpenAIApiKey() || '');
    setCohereKey(storage.getCohereApiKey() || '');
    const storedEmbeddingModel = storage.getEmbeddingModel() || 'text-embedding-3-small';
    setEmbeddingModel(storedEmbeddingModel);
    setOriginalEmbeddingModel(storedEmbeddingModel);
    setLlmModel(storage.getLLMModel() || 'gpt-4o-mini');
    // v3.0: 2段階モデル選択
    setSearchLlmModel(storage.getSearchLLMModel() || storage.getLLMModel() || 'gpt-4o-mini');
    setSummaryLlmModel(storage.getSummaryLLMModel() || 'gpt-3.5-turbo');  // デフォルト: 高速モデル
    // v3.0.1: ハイブリッド検索
    setSearchMode(storage.getSearchMode() || 'semantic');
    setHybridAlpha(storage.getHybridAlpha() ?? 0.7);
    setCustomPrompts(storage.getCustomPrompts() || {});

    // Google Drive設定を読み込む
    setStorageType(storage.getStorageType() || 'local');
    setGoogleDriveFolderId(storage.getGoogleDriveFolderId() || '');
    setGoogleDriveCredentialsPath(storage.getGoogleDriveCredentialsPath() || '');

    // デフォルトプロンプトを取得（認証不要）
    api.getDefaultPrompts().then((res) => {
      setDefaultPrompts(res.prompts);
    }).catch(console.error);

    // ChromaDB情報を取得（認証不要）
    api.getChromaInfo().then((res) => {
      if (res.success) {
        setChromaDBInfo({
          current_embedding_model: res.current_embedding_model,
          created_at: res.created_at,
          last_updated: res.last_updated
        });
      }
    }).catch(console.error);
  }, []);

  // 認証情報が揃ったらプロンプトリストと実験者プロファイルを取得
  useEffect(() => {
    if (!loading && idToken && currentTeamId) {
      api.listSavedPrompts(idToken, currentTeamId).then((res) => {
        if (res.success) {
          setSavedPromptsList(res.prompts || []);
        }
      }).catch(console.error);

      // v3.2.0: 実験者プロファイルを取得
      api.getExperimenterProfiles(idToken, currentTeamId).then((res) => {
        if (res.success) {
          setExperimenterProfiles(res.profiles || []);
          setIdPattern(res.id_pattern || '^ID(\\d+)-');
        }
      }).catch(console.error);

      // v3.2.1: 同義語辞書を取得
      api.getSynonymGroups(idToken, currentTeamId).then((res) => {
        if (res.success) {
          setSynonymGroups(res.groups || []);
        }
      }).catch(console.error);
    }
  }, [loading, idToken, currentTeamId]);

  const handleSave = () => {
    // 保存前のEmbeddingモデルの値を保存（localStorageから取得）
    const savedEmbeddingModel = storage.getEmbeddingModel();
    embeddingModelBeforeSave.current = savedEmbeddingModel || embeddingModel;

    // Embeddingモデルが変更されているかチェック
    // 優先順位: 1) ChromaDBの現在のモデル、2) localStorageの値
    const currentModel = chromaDBInfo?.current_embedding_model || savedEmbeddingModel;
    const isModelChanged = currentModel && embeddingModel !== currentModel;

    // Embeddingモデルが変更されている場合、警告を表示
    if (isModelChanged) {
      const confirmMessage = `⚠️ 警告: Embeddingモデルを変更しようとしています\n\n` +
        `現在のモデル: ${currentModel}\n` +
        `変更後: ${embeddingModel}\n\n` +
        `Embeddingモデルを変更すると、既存のベクトルDBとの互換性がなくなります。\n` +
        `検索が正しく動作しなくなるため、ChromaDBをリセットして全ノートを再取り込みする必要があります。\n\n` +
        `本当に変更しますか？`;

      if (!confirm(confirmMessage)) {
        // キャンセルされた場合、保存前の値に戻す
        setEmbeddingModel(embeddingModelBeforeSave.current);
        return;
      }
    }

    storage.setOpenAIApiKey(openaiKey);
    storage.setCohereApiKey(cohereKey);
    storage.setEmbeddingModel(embeddingModel);
    storage.setLLMModel(llmModel);  // 後方互換性のため維持
    // v3.0: 2段階モデル選択
    storage.setSearchLLMModel(searchLlmModel);
    storage.setSummaryLLMModel(summaryLlmModel);
    // v3.0.1: ハイブリッド検索
    storage.setSearchMode(searchMode);
    storage.setHybridAlpha(hybridAlpha);
    storage.setCustomPrompts(customPrompts);

    // Google Drive設定を保存
    storage.setStorageType(storageType);
    storage.setGoogleDriveFolderId(googleDriveFolderId);
    storage.setGoogleDriveCredentialsPath(googleDriveCredentialsPath);

    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleResetChromaDB = async () => {
    const confirmMessage = `⚠️ 危険な操作: ChromaDBを完全にリセットします\n\n` +
      `この操作により、以下のデータが削除されます：\n` +
      `- 全ての実験ノートのベクトルデータ\n` +
      `- 検索インデックス\n\n` +
      `リセット後は、全ての実験ノートを再度取り込む必要があります。\n\n` +
      `本当にリセットしますか？`;

    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      const result = await api.resetChromaDB();
      if (result.success) {
        alert(`✅ ${result.message}`);
        // ChromaDB情報を再読み込み
        const info = await api.getChromaInfo();
        if (info.success) {
          setChromaDBInfo({
            current_embedding_model: info.current_embedding_model,
            created_at: info.created_at,
            last_updated: info.last_updated
          });
        }
      }
    } catch (error) {
      alert(`❌ ChromaDBリセットエラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleResetPrompt = (promptType: string) => {
    if (confirm(`${promptType}のプロンプトを初期設定に戻しますか？`)) {
      const newCustomPrompts = { ...customPrompts };
      delete newCustomPrompts[promptType];
      setCustomPrompts(newCustomPrompts);
    }
  };

  const handleResetAllPrompts = () => {
    if (confirm('全てのプロンプトを初期設定に戻しますか？')) {
      setCustomPrompts({});
    }
  };

  // プロンプト保存機能
  const handleOpenSaveDialog = () => {
    setSavePromptName('');
    setSavePromptDescription('');
    setSaveError('');
    setShowSaveDialog(true);
  };

  const handleSavePromptSet = async () => {
    if (!savePromptName.trim()) {
      setSaveError('プロンプト名を入力してください。');
      return;
    }

    // 認証情報の確認
    if (!idToken || !currentTeamId) {
      setSaveError('認証情報が取得できていません。ページを再読み込みしてください。');
      return;
    }

    try {
      // v3.1.0: 3軸分離検索用の5つのプロンプトを保存
      const promptsToSave: Record<string, string> = {};
      const promptKeys = [
        'focus_classification',
        'material_query_generation',
        'method_query_generation',
        'combined_query_generation',
        'compare'
      ];

      for (const key of promptKeys) {
        // カスタム値があればそれを保存、なければnull（復元時にデフォルト使用）
        if (customPrompts[key] && customPrompts[key] !== defaultPrompts?.[key]?.prompt) {
          promptsToSave[key] = customPrompts[key];
        } else {
          promptsToSave[key] = ''; // 空文字＝デフォルトを使用
        }
      }

      const result = await api.savePrompt(savePromptName, promptsToSave, savePromptDescription, idToken, currentTeamId);

      if (!result.success) {
        setSaveError(result.error || '保存に失敗しました。');
        return;
      }

      // 保存成功 - リストを再読み込み
      const listRes = await api.listSavedPrompts(idToken, currentTeamId);
      if (listRes.success) {
        setSavedPromptsList(listRes.prompts || []);
      }
      setShowSaveDialog(false);
      alert(`プロンプト「${savePromptName}」を保存しました。`);
    } catch (error) {
      setSaveError(`保存エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleRestorePrompt = async (id: string) => {
    try {
      const result = await api.loadPrompt(id, idToken, currentTeamId);
      console.log('🔍 Load prompt result:', result);

      if (!result.success || !result.prompt) {
        console.error('❌ Prompt not found or invalid response');
        alert('プロンプトが見つかりません。');
        return;
      }

      console.log('✅ Prompt data:', result.prompt);
      console.log('📝 Prompts field:', result.prompt.prompts);

      if (confirm(`プロンプト「${result.prompt.name}」を復元しますか？現在の編集内容は上書きされます。`)) {
        // v3.1.0: 3軸分離検索用の5つのプロンプトを復元（後方互換性対応）
        const savedPrompts = result.prompt.prompts || {};
        const newPrompts: Record<string, string> = {};
        const promptKeys = [
          'focus_classification',
          'material_query_generation',
          'method_query_generation',
          'combined_query_generation',
          'compare'
        ];

        for (const key of promptKeys) {
          // 保存されている値があればそれを使用
          if (savedPrompts[key]) {
            newPrompts[key] = savedPrompts[key];
          }
          // 後方互換性: query_generation を combined_query_generation として使用
          else if (key === 'combined_query_generation' && savedPrompts['query_generation']) {
            newPrompts[key] = savedPrompts['query_generation'];
          }
          // 値がない場合はデフォルトを使用（空文字列を設定しない）
        }

        console.log('🔄 Setting custom prompts:', newPrompts);
        setCustomPrompts(newPrompts);
        alert(`プロンプト「${result.prompt.name}」を復元しました。「設定を保存」ボタンをクリックして適用してください。`);
      }
    } catch (error) {
      console.error('❌ Restore error:', error);
      alert(`復元エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleDeleteSavedPrompt = async (id: string, name: string) => {
    if (confirm(`プロンプト「${name}」を削除しますか？この操作は元に戻せません。`)) {
      try {
        const result = await api.deletePrompt(id, idToken, currentTeamId);
        if (result.success) {
          // リストを再読み込み
          const listRes = await api.listSavedPrompts(idToken, currentTeamId);
          if (listRes.success) {
            setSavedPromptsList(listRes.prompts || []);
          }
          alert('削除しました。');
        } else {
          alert(result.error || '削除に失敗しました。');
        }
      } catch (error) {
        alert(`削除エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
      }
    }
  };

  // ============================================
  // 実験者プロファイル管理ハンドラー（v3.2.0）
  // ============================================

  const loadProfiles = async () => {
    try {
      const res = await api.getExperimenterProfiles(idToken, currentTeamId);
      if (res.success) {
        setExperimenterProfiles(res.profiles || []);
        setIdPattern(res.id_pattern || '^ID(\\d+)-');
      }
    } catch (error) {
      console.error('プロファイル取得エラー:', error);
    }
  };

  const handleOpenProfileDialog = (profile?: ExperimenterProfile) => {
    if (profile) {
      // 編集モード
      setEditingProfile(profile);
      setProfileFormData({
        experimenter_id: profile.experimenter_id,
        name: profile.name,
        material_shortcuts: profile.material_shortcuts || {},
        shortcutInput: { key: '', value: '' }
      });
    } else {
      // 新規作成モード
      setEditingProfile(null);
      setProfileFormData({
        experimenter_id: '',
        name: '',
        material_shortcuts: {},
        shortcutInput: { key: '', value: '' }
      });
    }
    setProfileError('');
    setShowProfileDialog(true);
  };

  const handleSaveProfile = async () => {
    if (!profileFormData.experimenter_id.trim() || !profileFormData.name.trim()) {
      setProfileError('実験者IDと名前は必須です');
      return;
    }

    try {
      if (editingProfile) {
        // 更新
        const result = await api.updateExperimenterProfile(
          editingProfile.experimenter_id,
          {
            name: profileFormData.name,
            material_shortcuts: profileFormData.material_shortcuts,
          },
          idToken,
          currentTeamId
        );
        if (!result.success) {
          setProfileError(result.message || '更新に失敗しました');
          return;
        }
      } else {
        // 新規作成
        const result = await api.createExperimenterProfile(
          {
            experimenter_id: profileFormData.experimenter_id,
            name: profileFormData.name,
            material_shortcuts: profileFormData.material_shortcuts,
          },
          idToken,
          currentTeamId
        );
        if (!result.success) {
          setProfileError(result.message || '作成に失敗しました');
          return;
        }
      }

      await loadProfiles();
      setShowProfileDialog(false);
    } catch (error) {
      setProfileError(`エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleDeleteProfile = async (experimenterId: string, name: string) => {
    if (!confirm(`プロファイル「${name}」を削除しますか？この操作は元に戻せません。`)) {
      return;
    }

    try {
      const result = await api.deleteExperimenterProfile(experimenterId, idToken, currentTeamId);
      if (result.success) {
        await loadProfiles();
      } else {
        alert(result.message || '削除に失敗しました');
      }
    } catch (error) {
      alert(`削除エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleUpdateIdPattern = async () => {
    try {
      // 正規表現として有効かチェック
      new RegExp(idPattern);
    } catch {
      alert('無効な正規表現パターンです');
      return;
    }

    try {
      const result = await api.updateIdPattern(idPattern, idToken, currentTeamId);
      if (result.success) {
        alert('IDパターンを更新しました');
      } else {
        alert(result.message || 'IDパターンの更新に失敗しました');
      }
    } catch (error) {
      alert(`エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleAddShortcut = () => {
    const { key, value } = profileFormData.shortcutInput;
    if (!key.trim() || !value.trim()) return;

    setProfileFormData({
      ...profileFormData,
      material_shortcuts: {
        ...profileFormData.material_shortcuts,
        [key]: value
      },
      shortcutInput: { key: '', value: '' }
    });
  };

  const handleRemoveShortcut = (key: string) => {
    const newShortcuts = { ...profileFormData.material_shortcuts };
    delete newShortcuts[key];
    setProfileFormData({
      ...profileFormData,
      material_shortcuts: newShortcuts
    });
  };

  // ============================================
  // 同義語辞書管理ハンドラー（v3.2.1）
  // ============================================

  const loadSynonyms = async () => {
    try {
      const res = await api.getSynonymGroups(idToken, currentTeamId);
      if (res.success) {
        setSynonymGroups(res.groups || []);
      }
    } catch (error) {
      console.error('同義語辞書取得エラー:', error);
    }
  };

  const handleOpenSynonymDialog = (group?: SynonymGroup) => {
    if (group) {
      // 編集モード
      setEditingSynonym(group);
      setSynonymFormData({
        canonical: group.canonical,
        variants: [...group.variants],
        variantInput: ''
      });
    } else {
      // 新規作成モード
      setEditingSynonym(null);
      setSynonymFormData({
        canonical: '',
        variants: [],
        variantInput: ''
      });
    }
    setSynonymError('');
    setShowSynonymDialog(true);
  };

  const handleSaveSynonym = async () => {
    if (!synonymFormData.canonical.trim()) {
      setSynonymError('正規形（代表表記）は必須です');
      return;
    }

    try {
      if (editingSynonym) {
        // 更新
        const result = await api.updateSynonymGroup(
          editingSynonym.canonical,
          {
            new_canonical: synonymFormData.canonical !== editingSynonym.canonical
              ? synonymFormData.canonical
              : undefined,
            variants: synonymFormData.variants,
          },
          idToken,
          currentTeamId
        );
        if (!result.success) {
          setSynonymError(result.message || '更新に失敗しました');
          return;
        }
      } else {
        // 新規作成
        const result = await api.addSynonymGroup(
          synonymFormData.canonical,
          synonymFormData.variants,
          idToken,
          currentTeamId
        );
        if (!result.success) {
          setSynonymError(result.message || '作成に失敗しました');
          return;
        }
      }

      await loadSynonyms();
      setShowSynonymDialog(false);
    } catch (error) {
      setSynonymError(`エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleDeleteSynonym = async (canonical: string) => {
    if (!confirm(`同義語グループ「${canonical}」を削除しますか？この操作は元に戻せません。`)) {
      return;
    }

    try {
      const result = await api.deleteSynonymGroup(canonical, idToken, currentTeamId);
      if (result.success) {
        await loadSynonyms();
      } else {
        alert(result.message || '削除に失敗しました');
      }
    } catch (error) {
      alert(`削除エラー: ${error instanceof Error ? error.message : '不明なエラー'}`);
    }
  };

  const handleAddVariant = () => {
    const variant = synonymFormData.variantInput.trim();
    if (!variant) return;

    if (synonymFormData.variants.includes(variant)) {
      setSynonymError('既に登録されているバリアントです');
      return;
    }

    setSynonymFormData({
      ...synonymFormData,
      variants: [...synonymFormData.variants, variant],
      variantInput: ''
    });
    setSynonymError('');
  };

  const handleRemoveVariant = (variant: string) => {
    setSynonymFormData({
      ...synonymFormData,
      variants: synonymFormData.variants.filter(v => v !== variant)
    });
  };

  const embeddingModels = [
    'text-embedding-3-small',
    'text-embedding-3-large',
    'text-embedding-ada-002',
  ];

  // 後方互換性のため維持
  const llmModels = [
    'gpt-5.2',
    'gpt-5.2-pro',
    'gpt-5-mini',
    'gpt-5-nano',
    'gpt-4o-mini',
    'gpt-4o',
    'gpt-4-turbo',
    'gpt-3.5-turbo',
  ];

  // v3.0: 検索・判定用LLMモデル（高精度モデル推奨）
  const searchLlmModels = [
    'gpt-5.2',        // 最新・高精度
    'gpt-5.2-pro',    // 最高精度
    'gpt-5-mini',     // コスト効率
    'gpt-4o-mini',
    'gpt-4o',
    'gpt-4-turbo',
  ];

  // v3.0: 要約生成用LLMモデル（高速モデル推奨）
  const summaryLlmModels = [
    'gpt-5-nano',     // 最新・高速
    'gpt-5-mini',     // コスト効率
    'gpt-3.5-turbo',  // 高速
    'gpt-4o-mini',
    'gpt-4o',
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">設定</h1>

        {/* タブ */}
        <div className="mb-6 border-b border-gray-300">
          <div className="flex space-x-8">
            {[
              { key: 'api', label: 'APIキー' },
              { key: 'models', label: 'モデル選択' },
              { key: 'prompts', label: 'プロンプト管理' },
              { key: 'notes', label: 'ノート管理' },
              { key: 'profiles', label: '実験者プロファイル' },
              { key: 'synonyms', label: '同義語辞書' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`pb-3 px-2 ${
                  activeTab === tab.key
                    ? 'border-b-2 border-primary font-semibold'
                    : 'text-gray-600'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* APIキータブ */}
          {activeTab === 'api' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">OpenAI API Key</label>
                <input
                  type="password"
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder="sk-..."
                />
                <p className="text-sm text-gray-600 mt-1">
                  ブラウザのlocalStorageに保存されます。「sk-」で始まるキーを入力してください。
                </p>
                {openaiKey && (
                  <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-300">
                    <p className="text-xs font-mono">
                      現在の値: {openaiKey.substring(0, 10)}...{openaiKey.substring(openaiKey.length - 4)}
                    </p>
                    <p className={`text-xs mt-1 ${openaiKey.startsWith('sk-') ? 'text-green-600' : 'text-red-600'}`}>
                      {openaiKey.startsWith('sk-') ? '✓ 形式が正しいです' : '✗ 「sk-」で始まっていません'}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Cohere API Key</label>
                <input
                  type="password"
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={cohereKey}
                  onChange={(e) => setCohereKey(e.target.value)}
                  placeholder="..."
                />
                <p className="text-sm text-gray-600 mt-1">
                  リランキングに使用されます。
                </p>
                {cohereKey && (
                  <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-300">
                    <p className="text-xs font-mono">
                      現在の値: {cohereKey.substring(0, 8)}...{cohereKey.substring(cohereKey.length - 4)}
                    </p>
                  </div>
                )}
              </div>

              {/* デバッグ情報 */}
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
                <h3 className="font-bold text-sm mb-2">保存状態の確認</h3>
                <button
                  onClick={() => {
                    const saved = localStorage.getItem('openai_api_key');
                    alert(`保存されているOpenAI APIキー:\n${saved ? saved.substring(0, 10) + '...' + saved.substring(saved.length - 4) : '未設定'}\n\nsk-で始まっている: ${saved?.startsWith('sk-') ? 'はい' : 'いいえ'}`);
                  }}
                  className="text-sm text-blue-600 underline"
                >
                  localStorageを確認
                </button>
              </div>
            </div>
          )}

          {/* モデル選択タブ */}
          {activeTab === 'models' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Embeddingモデル</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                >
                  {embeddingModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-600 mt-1">
                  ベクトル検索に使用されます。text-embedding-3-small が推奨です。
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">検索・判定用LLM</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={searchLlmModel}
                  onChange={(e) => setSearchLlmModel(e.target.value)}
                >
                  {searchLlmModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-600 mt-1">
                  クエリ生成、正規化に使用されます。gpt-4o-mini が推奨です。
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">要約生成用LLM</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={summaryLlmModel}
                  onChange={(e) => setSummaryLlmModel(e.target.value)}
                >
                  {summaryLlmModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-600 mt-1">
                  検索結果の比較・要約に使用されます。gpt-3.5-turbo が高速で推奨です。
                </p>
              </div>

              {/* 検索設定セクション（v3.0.1） */}
              <div className="border-t border-gray-300 pt-6 mt-6">
                <h3 className="text-lg font-bold mb-4">検索設定</h3>

                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">デフォルト検索モード</label>
                  <select
                    className="w-full border border-gray-300 rounded-md p-3"
                    value={searchMode}
                    onChange={(e) => setSearchMode(e.target.value as 'semantic' | 'keyword' | 'hybrid')}
                  >
                    <option value="semantic">セマンティック検索（意味的類似性）</option>
                    <option value="keyword">キーワード検索（固有名詞に強い）</option>
                    <option value="hybrid">ハイブリッド検索（推奨）</option>
                  </select>
                  <p className="text-sm text-gray-600 mt-1">
                    検索ページで使用するデフォルトの検索モードを設定します。
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    ハイブリッド検索の重み: {hybridAlpha.toFixed(1)}
                  </label>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500">キーワード</span>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={hybridAlpha}
                      onChange={(e) => setHybridAlpha(parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-xs text-gray-500">セマンティック</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    0.7（デフォルト）= セマンティック70%、キーワード30%の比率で検索します。
                  </p>
                </div>
              </div>

              {/* ChromaDB管理 */}
              <div className="border-t border-gray-300 pt-6 mt-6">
                <h3 className="text-lg font-bold mb-4">ChromaDB管理</h3>

                {/* ChromaDB情報 */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <h4 className="font-semibold text-sm mb-2">現在のChromaDB設定</h4>
                  {chromaDBInfo ? (
                    <div className="space-y-1 text-sm">
                      <p>
                        <span className="font-medium">Embeddingモデル:</span>{' '}
                        <span className="font-mono">
                          {chromaDBInfo.current_embedding_model || 'まだ設定されていません'}
                        </span>
                      </p>
                      {chromaDBInfo.created_at && (
                        <p>
                          <span className="font-medium">作成日時:</span>{' '}
                          {new Date(chromaDBInfo.created_at).toLocaleString('ja-JP')}
                        </p>
                      )}
                      {chromaDBInfo.last_updated && (
                        <p>
                          <span className="font-medium">最終更新:</span>{' '}
                          {new Date(chromaDBInfo.last_updated).toLocaleString('ja-JP')}
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600">読み込み中...</p>
                  )}
                </div>

                {/* Embedding変更警告 */}
                {(() => {
                  const currentModel = chromaDBInfo?.current_embedding_model || storage.getEmbeddingModel();
                  const isChanged = currentModel && embeddingModel !== currentModel;
                  return isChanged && (
                    <div className="bg-warning/10 border-2 border-warning rounded-lg p-4 mb-4">
                      <h4 className="font-bold text-warning mb-2">⚠️ 警告</h4>
                      <p className="text-sm mb-2">
                        Embeddingモデルを <span className="font-mono">{currentModel}</span> から{' '}
                        <span className="font-mono">{embeddingModel}</span> に変更しようとしています。
                      </p>
                      <p className="text-sm text-gray-700">
                        Embeddingモデルを変更すると、既存のベクトルDBとの互換性がなくなります。
                        変更後は、ChromaDBをリセットして全ての実験ノートを再度取り込む必要があります。
                      </p>
                    </div>
                  );
                })()}

                {/* ChromaDBリセットボタン */}
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="font-semibold text-sm text-red-800 mb-2">危険な操作</h4>
                  <p className="text-sm text-gray-700 mb-3">
                    ChromaDBをリセットすると、全てのベクトルデータが削除されます。
                    Embeddingモデルを変更した場合のみ実行してください。
                  </p>
                  <Button
                    variant="danger"
                    onClick={handleResetChromaDB}
                    className="text-sm"
                  >
                    ChromaDBをリセット
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* プロンプト管理タブ */}
          {activeTab === 'prompts' && defaultPrompts && (
            <div className="space-y-8">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">プロンプトのカスタマイズ</h2>
                <div className="flex gap-3">
                  <Button onClick={handleOpenSaveDialog}>
                    現在のプロンプトを保存
                  </Button>
                  <Button variant="danger" onClick={handleResetAllPrompts}>
                    全て初期設定にリセット
                  </Button>
                </div>
              </div>

              {/* 保存済みプロンプト一覧 */}
              <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                <h3 className="font-bold mb-3">
                  保存済みプロンプト ({savedPromptsList.length}/50)
                </h3>
                {savedPromptsList.length > 0 ? (
                  <>
                    <div className="space-y-2">
                      {savedPromptsList.map((prompt) => (
                        <div
                          key={prompt.id}
                          className="bg-white border border-gray-200 rounded p-3 flex justify-between items-start"
                        >
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm">{prompt.name}</h4>
                            {prompt.description && (
                              <p className="text-xs text-gray-600 mt-1">
                                {prompt.description}
                              </p>
                            )}
                            <p className="text-xs text-gray-500 mt-1">
                              更新日: {new Date(prompt.updated_at).toLocaleString('ja-JP')}
                            </p>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <button
                              onClick={() => handleRestorePrompt(prompt.id)}
                              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 border border-blue-600 rounded hover:bg-blue-50"
                              title="このプロンプトを復元して現在の設定に適用します"
                            >
                              復元
                            </button>
                            <button
                              onClick={() => handleDeleteSavedPrompt(prompt.id, prompt.name)}
                              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 border border-red-600 rounded hover:bg-red-50"
                              title="このプロンプトを削除します（元に戻せません）"
                            >
                              削除
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600 mt-3">
                      残り保存可能数: {50 - savedPromptsList.length}個
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-gray-600">
                    保存されているプロンプトはありません。<br />
                    「現在のプロンプトを保存」ボタンをクリックして、カスタマイズしたプロンプトを保存できます。
                  </p>
                )}
              </div>

              {Object.entries(defaultPrompts).map(([key, value]: [string, any]) => (
                <div key={key} className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold">{value.name}</h3>
                      <p className="text-sm text-gray-600">{value.description}</p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => handleResetPrompt(key)}
                      className="text-sm py-1 px-3"
                    >
                      初期設定にリセット
                    </Button>
                  </div>

                  {/* 左右2カラムレイアウト */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* 左側: デフォルトプロンプト（読み取り専用） */}
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <label className="block text-sm font-medium text-gray-700">
                          デフォルトプロンプト
                        </label>
                        <button
                          onClick={() => {
                            setCustomPrompts({ ...customPrompts, [key]: value.prompt });
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          右にコピー →
                        </button>
                      </div>
                      <textarea
                        className="w-full border border-gray-200 bg-gray-50 rounded-md p-3 h-64 font-mono text-sm"
                        value={value.prompt}
                        readOnly
                      />
                    </div>

                    {/* 右側: カスタムプロンプト（編集可能） */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        カスタムプロンプト
                        {customPrompts[key] && customPrompts[key] !== value.prompt && (
                          <span className="ml-2 text-xs text-warning">
                            ⚠️ カスタマイズ済み
                          </span>
                        )}
                      </label>
                      <textarea
                        className="w-full border border-gray-300 rounded-md p-3 h-64 font-mono text-sm"
                        value={customPrompts[key] || value.prompt}
                        onChange={(e) => setCustomPrompts({ ...customPrompts, [key]: e.target.value })}
                        placeholder={value.prompt}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ノート管理タブ */}
          {activeTab === 'notes' && (
            <div className="space-y-6">
              {/* 本番環境の警告 */}
              <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4 mb-6">
                <h3 className="font-bold mb-2 text-yellow-900">⚠️ 本番環境について</h3>
                <p className="text-sm text-yellow-800 mb-2">
                  現在、バックエンドは <strong>Google Cloud Storage (GCS)</strong> で動作しています。
                </p>
                <p className="text-sm text-yellow-800">
                  下記の設定はブラウザに保存されますが、<strong>バックエンドのストレージ設定には影響しません</strong>。
                  バックエンドのストレージタイプとフォルダパスは環境変数で管理されています。
                </p>
                <div className="mt-3 p-3 bg-white rounded border border-yellow-200">
                  <p className="text-xs font-mono text-gray-700">
                    <strong>バックエンド設定:</strong><br />
                    ストレージ: GCS (jikkennote-storage)<br />
                    新規ノート: notes/new<br />
                    処理済み: notes/processed<br />
                    アーカイブ: notes/archived
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-bold mb-2">ノートストレージの設定（参考）</h3>
                <p className="text-sm text-gray-700">
                  実験ノートの保存先を設定します。Google Driveを使用すると、チーム全体でノートを共有できます。
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  ※ 本番環境ではバックエンドの環境変数が優先されます。
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">ストレージタイプ</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={storageType}
                  onChange={(e) => setStorageType(e.target.value as any)}
                >
                  <option value="local">ローカルファイルシステム</option>
                  <option value="gcs">Google Cloud Storage</option>
                  <option value="google_drive">Google Drive</option>
                </select>
                <p className="text-sm text-gray-600 mt-1">
                  {storageType === 'local' && 'ローカルマシン上のフォルダに保存します。'}
                  {storageType === 'gcs' && 'Google Cloud Storageのバケットに保存します。'}
                  {storageType === 'google_drive' && 'Google Driveの共有フォルダに保存します（推奨）。'}
                </p>
              </div>

              {storageType === 'google_drive' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Google Drive フォルダID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      className="w-full border border-gray-300 rounded-md p-3"
                      value={googleDriveFolderId}
                      onChange={(e) => setGoogleDriveFolderId(e.target.value)}
                      placeholder="例: 1a2B3c4D5e6F7g8H9i0J"
                    />
                    <p className="text-sm text-gray-600 mt-1">
                      Google Driveの共有フォルダのIDを入力してください。
                      フォルダのURL「https://drive.google.com/drive/folders/<strong>フォルダID</strong>」から取得できます。
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      サービスアカウント認証情報のパス <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      className="w-full border border-gray-300 rounded-md p-3"
                      value={googleDriveCredentialsPath}
                      onChange={(e) => setGoogleDriveCredentialsPath(e.target.value)}
                      placeholder="例: /path/to/service-account-key.json"
                    />
                    <p className="text-sm text-gray-600 mt-1">
                      Google Cloud ConsoleでダウンロードしたサービスアカウントのJSONキーファイルのパスを入力してください。
                    </p>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-semibold text-sm mb-2">📘 Google Drive APIの設定方法</h4>
                    <ol className="text-sm space-y-2 list-decimal list-inside">
                      <li>Google Cloud Consoleでプロジェクトを作成</li>
                      <li>Google Drive APIを有効化</li>
                      <li>サービスアカウントを作成してJSONキーをダウンロード</li>
                      <li>共有フォルダにサービスアカウントのメールアドレスを編集者として追加</li>
                      <li>フォルダIDとJSONキーのパスを上記に入力</li>
                    </ol>
                    <p className="text-xs text-gray-600 mt-3">
                      詳しい手順は
                      <a
                        href="https://developers.google.com/drive/api/guides/about-sdk"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline ml-1"
                      >
                        Google Drive API ドキュメント
                      </a>
                      を参照してください。
                    </p>
                  </div>
                </>
              )}

              <div className="border-t border-gray-300 pt-6 mt-6">
                <h3 className="text-lg font-bold mb-4">フォルダ構成</h3>
                <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                  <p className="text-sm mb-3">
                    ノートは以下のフォルダ構成で管理されます：
                  </p>
                  <div className="font-mono text-sm space-y-1 bg-white border border-gray-200 rounded p-3">
                    <div>📁 {storageType === 'google_drive' ? '共有フォルダ（指定したフォルダID）' : 'ルートフォルダ'}</div>
                    <div className="ml-4">├── 📁 notes/</div>
                    <div className="ml-8">│   ├── 📁 new/ <span className="text-gray-600">← 新規ノート（取り込み前）</span></div>
                    <div className="ml-8">│   └── 📁 processed/ <span className="text-gray-600">← 取り込み済みノート</span></div>
                    <div className="ml-4">└── 📄 master_dictionary.yaml <span className="text-gray-600">← 正規化辞書</span></div>
                  </div>
                  <p className="text-xs text-gray-600 mt-3">
                    ※ 新規ノートを <code>notes/new/</code> フォルダに配置すると、取り込み処理で自動的に <code>notes/processed/</code> に移動されます。
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 実験者プロファイルタブ（v3.2.0） */}
          {activeTab === 'profiles' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-bold mb-2">実験者プロファイルとは</h3>
                <div className="text-sm text-gray-700 space-y-2">
                  <p>
                    <strong>1. 省略形（①②③）の展開</strong><br/>
                    ノート取り込み時に、材料セクションの内容からLLMが自動的に省略形を解析し、
                    方法セクションの省略表記を材料名に展開します。（設定不要・自動処理）
                  </p>
                  <p>
                    <strong>2. サフィックス（1/A/αなど）の表記揺れ</strong><br/>
                    実験者ごとに「HbA1c捕捉抗体<strong>1</strong>」「HbA1c捕捉抗体<strong>A</strong>」のような
                    サフィックスのクセがあります。下記プロファイルでカスタムマッピングを登録できます。
                  </p>
                </div>
              </div>

              {/* IDパターン設定 */}
              <div className="border border-gray-300 rounded-lg p-4">
                <h3 className="font-bold mb-3">ノートIDパターン設定</h3>
                <p className="text-sm text-gray-600 mb-3">
                  ノートIDから実験者IDを抽出する正規表現パターンです。
                  キャプチャグループ1が実験者IDとして使用されます。
                </p>
                <div className="flex gap-3">
                  <input
                    type="text"
                    className="flex-1 border border-gray-300 rounded-md p-2 font-mono text-sm"
                    value={idPattern}
                    onChange={(e) => setIdPattern(e.target.value)}
                    placeholder="^ID(\d+)-"
                  />
                  <Button onClick={handleUpdateIdPattern}>
                    パターンを更新
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  例: パターン「^ID(\d+)-」でノートID「ID2-5」から実験者ID「2」を抽出
                </p>
              </div>

              {/* プロファイル一覧 */}
              <div className="border border-gray-300 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold">登録済みプロファイル ({experimenterProfiles.length}件)</h3>
                  <Button onClick={() => handleOpenProfileDialog()}>
                    新規プロファイル作成
                  </Button>
                </div>

                {experimenterProfiles.length > 0 ? (
                  <div className="space-y-3">
                    {experimenterProfiles.map((profile) => (
                      <div
                        key={profile.experimenter_id}
                        className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold">
                              {profile.name}
                              <span className="ml-2 text-sm font-normal text-gray-600">
                                (ID: {profile.experimenter_id})
                              </span>
                            </h4>
                            {profile.material_shortcuts && Object.keys(profile.material_shortcuts).length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs text-gray-600 mb-1">サフィックスマッピング:</p>
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(profile.material_shortcuts).map(([key, value]) => (
                                    <span
                                      key={key}
                                      className="text-xs bg-white border border-gray-300 rounded px-2 py-0.5"
                                    >
                                      {key} → {value}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {profile.updated_at && (
                              <p className="text-xs text-gray-500 mt-2">
                                更新日: {new Date(profile.updated_at).toLocaleString('ja-JP')}
                              </p>
                            )}
                          </div>
                          <div className="flex gap-2 ml-4">
                            <button
                              onClick={() => handleOpenProfileDialog(profile)}
                              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 border border-blue-600 rounded hover:bg-blue-50"
                            >
                              編集
                            </button>
                            <button
                              onClick={() => handleDeleteProfile(profile.experimenter_id, profile.name)}
                              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 border border-red-600 rounded hover:bg-red-50"
                            >
                              削除
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    登録されているプロファイルはありません。<br />
                    「新規プロファイル作成」ボタンをクリックして、実験者ごとのサフィックス表記揺れを登録できます。<br />
                    <span className="text-xs text-gray-500">
                      ※ 省略形（①②③）の展開は自動で行われるため、登録不要です。
                    </span>
                  </p>
                )}
              </div>
            </div>
          )}

          {/* 同義語辞書タブ（v3.2.1） */}
          {activeTab === 'synonyms' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-bold mb-2">同義語辞書とは</h3>
                <div className="text-sm text-gray-700 space-y-2">
                  <p>
                    <strong>検索時のクエリ展開</strong>に使用されます。
                    例えば「純水」と「精製水」を同義語として登録しておくと、
                    「純水」で検索した際に「精製水」を含むノートもヒットするようになります。
                  </p>
                  <p className="text-xs text-gray-600">
                    ※ 正規化辞書（正規形と異表記）とは別に、検索時のクエリ展開専用の辞書です。
                    データベースを再構築する必要はありません。
                  </p>
                </div>
              </div>

              {/* 同義語グループ一覧 */}
              <div className="border border-gray-300 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold">登録済み同義語グループ ({synonymGroups.length}件)</h3>
                  <Button onClick={() => handleOpenSynonymDialog()}>
                    新規グループ作成
                  </Button>
                </div>

                {synonymGroups.length > 0 ? (
                  <div className="space-y-3">
                    {synonymGroups.map((group) => (
                      <div
                        key={group.canonical}
                        className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold text-lg">
                              {group.canonical}
                              <span className="ml-2 text-xs font-normal text-gray-500 bg-blue-100 px-2 py-0.5 rounded">
                                正規形
                              </span>
                            </h4>
                            {group.variants.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs text-gray-600 mb-1">同義語（バリアント）:</p>
                                <div className="flex flex-wrap gap-1">
                                  {group.variants.map((variant) => (
                                    <span
                                      key={variant}
                                      className="text-sm bg-white border border-gray-300 rounded px-2 py-0.5"
                                    >
                                      {variant}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {group.variants.length === 0 && (
                              <p className="text-xs text-gray-500 mt-1">
                                バリアントなし（追加してください）
                              </p>
                            )}
                            {group.updated_at && (
                              <p className="text-xs text-gray-500 mt-2">
                                更新日: {new Date(group.updated_at).toLocaleString('ja-JP')}
                              </p>
                            )}
                          </div>
                          <div className="flex gap-2 ml-4">
                            <button
                              onClick={() => handleOpenSynonymDialog(group)}
                              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 border border-blue-600 rounded hover:bg-blue-50"
                            >
                              編集
                            </button>
                            <button
                              onClick={() => handleDeleteSynonym(group.canonical)}
                              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 border border-red-600 rounded hover:bg-red-50"
                            >
                              削除
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    登録されている同義語グループはありません。<br />
                    「新規グループ作成」ボタンをクリックして、同義語グループを登録できます。<br />
                    <span className="text-xs text-gray-500">
                      例: 正規形「純水」にバリアント「精製水」「蒸留水」「超純水」を登録
                    </span>
                  </p>
                )}
              </div>

              {/* 使い方のヒント */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-semibold text-sm mb-2">使い方のヒント</h4>
                <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                  <li>正規形: 検索結果で表示される代表的な表記</li>
                  <li>バリアント: 正規形と同じ意味の異表記（複数登録可能）</li>
                  <li>検索時: クエリ内の用語が自動的に展開され、全バリアントで検索されます</li>
                  <li>例: 「純水」で検索 → 「精製水」「蒸留水」も同時に検索</li>
                </ul>
              </div>
            </div>
          )}

          {/* 保存ボタン */}
          <div className="mt-8 flex items-center gap-4">
            <Button onClick={handleSave} className="w-full md:w-auto">
              設定を保存
            </Button>
            {saved && (
              <span className="text-success font-medium">✓ 保存しました</span>
            )}
          </div>
        </div>

        {/* プロンプト保存ダイアログ */}
        {showSaveDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-bold mb-4">プロンプトを保存</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    プロンプト名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={savePromptName}
                    onChange={(e) => {
                      setSavePromptName(e.target.value);
                      setSaveError('');
                    }}
                    placeholder="例: 高精度検索用プロンプト"
                    maxLength={50}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    説明（任意）
                  </label>
                  <textarea
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={savePromptDescription}
                    onChange={(e) => setSavePromptDescription(e.target.value)}
                    placeholder="このプロンプトの特徴や用途を記載"
                    rows={3}
                    maxLength={200}
                  />
                </div>

                {saveError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    {saveError}
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleSavePromptSet}
                    className="flex-1"
                  >
                    保存
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowSaveDialog(false)}
                    className="flex-1"
                  >
                    キャンセル
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* プロファイル編集ダイアログ（v3.2.0） */}
        {showProfileDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
              <h3 className="text-xl font-bold mb-4">
                {editingProfile ? 'プロファイルを編集' : '新規プロファイル作成'}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    実験者ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className={`w-full border border-gray-300 rounded-md p-2 ${
                      editingProfile ? 'bg-gray-100' : ''
                    }`}
                    value={profileFormData.experimenter_id}
                    onChange={(e) => setProfileFormData({
                      ...profileFormData,
                      experimenter_id: e.target.value
                    })}
                    placeholder="例: 1, 2, 3..."
                    disabled={!!editingProfile}
                  />
                  {editingProfile && (
                    <p className="text-xs text-gray-500 mt-1">
                      ※ 実験者IDは変更できません
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    表示名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={profileFormData.name}
                    onChange={(e) => setProfileFormData({
                      ...profileFormData,
                      name: e.target.value
                    })}
                    placeholder="例: 田中さん, 実験者A..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    サフィックスマッピング（任意）
                  </label>
                  <p className="text-xs text-gray-600 mb-2">
                    この実験者特有のサフィックス表記揺れを登録します。
                    例: 「A」→「1」、「α」→「1」など
                  </p>

                  {/* 登録済み省略形 */}
                  {Object.keys(profileFormData.material_shortcuts).length > 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-3">
                      <div className="space-y-2">
                        {Object.entries(profileFormData.material_shortcuts).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-2">
                            <span className="font-mono bg-white border border-gray-300 rounded px-2 py-1 text-sm min-w-[40px] text-center">
                              {key}
                            </span>
                            <span className="text-gray-500">→</span>
                            <span className="flex-1 text-sm truncate">{value}</span>
                            <button
                              onClick={() => handleRemoveShortcut(key)}
                              className="text-red-600 hover:text-red-800 text-xs"
                            >
                              削除
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 新規追加フォーム */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="w-16 border border-gray-300 rounded-md p-2 text-center font-mono"
                      value={profileFormData.shortcutInput.key}
                      onChange={(e) => setProfileFormData({
                        ...profileFormData,
                        shortcutInput: {
                          ...profileFormData.shortcutInput,
                          key: e.target.value
                        }
                      })}
                      placeholder="①"
                    />
                    <span className="flex items-center text-gray-500">→</span>
                    <input
                      type="text"
                      className="flex-1 border border-gray-300 rounded-md p-2"
                      value={profileFormData.shortcutInput.value}
                      onChange={(e) => setProfileFormData({
                        ...profileFormData,
                        shortcutInput: {
                          ...profileFormData.shortcutInput,
                          value: e.target.value
                        }
                      })}
                      placeholder="材料名: 容量"
                    />
                    <button
                      onClick={handleAddShortcut}
                      className="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm"
                    >
                      追加
                    </button>
                  </div>
                </div>

                {profileError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    {profileError}
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button onClick={handleSaveProfile} className="flex-1">
                    {editingProfile ? '更新' : '作成'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowProfileDialog(false)}
                    className="flex-1"
                  >
                    キャンセル
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 同義語グループ編集ダイアログ（v3.2.1） */}
        {showSynonymDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
              <h3 className="text-xl font-bold mb-4">
                {editingSynonym ? '同義語グループを編集' : '新規同義語グループ作成'}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    正規形（代表表記） <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={synonymFormData.canonical}
                    onChange={(e) => setSynonymFormData({
                      ...synonymFormData,
                      canonical: e.target.value
                    })}
                    placeholder="例: 純水"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    検索結果で使用される代表的な表記です
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    同義語（バリアント）
                  </label>
                  <p className="text-xs text-gray-600 mb-2">
                    正規形と同じ意味の異表記を登録します。検索時に自動的に展開されます。
                  </p>

                  {/* 登録済みバリアント */}
                  {synonymFormData.variants.length > 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded p-3 mb-3">
                      <div className="flex flex-wrap gap-2">
                        {synonymFormData.variants.map((variant) => (
                          <span
                            key={variant}
                            className="inline-flex items-center gap-1 bg-white border border-gray-300 rounded px-2 py-1 text-sm"
                          >
                            {variant}
                            <button
                              onClick={() => handleRemoveVariant(variant)}
                              className="text-red-500 hover:text-red-700 ml-1"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 新規追加フォーム */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="flex-1 border border-gray-300 rounded-md p-2"
                      value={synonymFormData.variantInput}
                      onChange={(e) => setSynonymFormData({
                        ...synonymFormData,
                        variantInput: e.target.value
                      })}
                      placeholder="例: 精製水"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddVariant();
                        }
                      }}
                    />
                    <button
                      onClick={handleAddVariant}
                      className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm"
                    >
                      追加
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Enterキーでも追加できます
                  </p>
                </div>

                {synonymError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    {synonymError}
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button onClick={handleSaveSynonym} className="flex-1">
                    {editingSynonym ? '更新' : '作成'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowSynonymDialog(false)}
                    className="flex-1"
                  >
                    キャンセル
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
