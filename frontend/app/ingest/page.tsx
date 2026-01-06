'use client';

import { useState } from 'react';
import Button from '@/components/Button';
import FileDropZone from '@/components/FileDropZone';
import { api, DictionaryUpdateRequest } from '@/lib/api';
import { storage } from '@/lib/storage';
import { useAuth } from '@/lib/auth-context';

interface NewTerm {
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
  user_decision?: 'new' | 'variant' | 'skip';
  user_canonical?: string;
  user_category?: string;
}

export default function IngestPage() {
  const { idToken, currentTeamId } = useAuth();
  const [sourceFolder, setSourceFolder] = useState('');
  const [postAction, setPostAction] = useState<'delete' | 'archive' | 'keep' | 'move_to_processed'>('move_to_processed');
  const [archiveFolder, setArchiveFolder] = useState('');
  const [loading, setLoading] = useState(false);
  const [rebuildLoading, setRebuildLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [ingestResult, setIngestResult] = useState<{
    new_notes: string[];
    skipped_notes: string[];
  } | null>(null);
  const [newTerms, setNewTerms] = useState<NewTerm[]>([]);
  const [showTermsModal, setShowTermsModal] = useState(false);

  const handleIngest = async () => {
    setError('');
    setSuccess('');
    setLoading(true);
    setIngestResult(null);

    try {
      const openaiApiKey = storage.getOpenAIApiKey();
      if (!openaiApiKey) {
        throw new Error('OpenAI APIキーが設定されていません');
      }

      const embeddingModel = storage.getEmbeddingModel();

      const response = await api.ingest({
        openai_api_key: openaiApiKey,
        source_folder: sourceFolder || undefined,
        post_action: postAction,
        archive_folder: archiveFolder || undefined,
        embedding_model: embeddingModel || undefined,
      }, idToken, currentTeamId);

      if (response.success) {
        setIngestResult({
          new_notes: response.new_notes,
          skipped_notes: response.skipped_notes,
        });
        setSuccess(response.message);

        // 新出単語分析を提案
        if (response.new_notes.length > 0) {
          const analyzeNow = confirm(
            `${response.new_notes.length}件の新規ノートが取り込まれました。\n新出単語の分析を実行しますか？`
          );
          if (analyzeNow) {
            await handleAnalyze(response.new_notes);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'ノートの取り込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRebuild = async () => {
    setError('');
    setSuccess('');
    setRebuildLoading(true);
    setIngestResult(null);

    try {
      const openaiApiKey = storage.getOpenAIApiKey();
      if (!openaiApiKey) {
        throw new Error('OpenAI APIキーが設定されていません');
      }

      const embeddingModel = storage.getEmbeddingModel();

      // rebuild_mode=trueで実行
      const response = await api.ingest({
        openai_api_key: openaiApiKey,
        source_folder: undefined, // processedフォルダから読み込む
        post_action: 'keep', // 再構築時はファイルを移動しない
        archive_folder: undefined,
        embedding_model: embeddingModel || undefined,
        rebuild_mode: true,
      }, idToken, currentTeamId);

      if (response.success) {
        setIngestResult({
          new_notes: response.new_notes,
          skipped_notes: response.skipped_notes,
        });
        setSuccess(response.message);
      }
    } catch (err: any) {
      setError(err.message || 'ChromaDBの再構築に失敗しました');
    } finally {
      setRebuildLoading(false);
    }
  };

  const handleUpload = async (files: FileList) => {
    if (!files || files.length === 0) {
      return;
    }

    setUploadError('');
    setUploadSuccess('');
    setUploadLoading(true);

    try {
      const response = await api.uploadNotes(files, idToken, currentTeamId);

      if (response.success) {
        setUploadSuccess(`${response.uploaded_files.length}件のファイルをアップロードしました: ${response.uploaded_files.join(', ')}`);
      }
    } catch (err: any) {
      setUploadError(err.message || 'ファイルのアップロードに失敗しました');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleAnalyze = async (noteIds: string[]) => {
    setError('');
    setAnalyzing(true);

    try {
      const openaiApiKey = storage.getOpenAIApiKey();
      if (!openaiApiKey) {
        throw new Error('OpenAI APIキーが設定されていません');
      }

      // バックエンドがnote_idsから自動的にファイルを読み込むため、空配列を送信
      // （バックエンドのserver.py lines 756-772参照）
      const response = await api.analyzeNewTerms({
        note_ids: noteIds,
        note_contents: [],  // 空配列 → バックエンドが実ファイルから読み込む
        openai_api_key: openaiApiKey,
      }, idToken, currentTeamId);

      if (response.success) {
        // 重複を除去：同じtermを持つエントリーを1つにまとめる
        const uniqueTermsMap = new Map<string, typeof response.new_terms[0]>();

        for (const term of response.new_terms) {
          if (!uniqueTermsMap.has(term.term)) {
            uniqueTermsMap.set(term.term, term);
          }
        }

        const uniqueTerms = Array.from(uniqueTermsMap.values());

        setNewTerms(uniqueTerms.map(term => ({
          ...term,
          user_decision: term.llm_suggestion.decision, // LLMの提案をデフォルト値に
          user_canonical: term.llm_suggestion.suggested_canonical,
          user_category: undefined,
        })));
        setShowTermsModal(true);
      }
    } catch (err: any) {
      setError(err.message || '新出単語の分析に失敗しました');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleUpdateDecision = (index: number, field: keyof NewTerm, value: any) => {
    const updated = [...newTerms];
    updated[index] = { ...updated[index], [field]: value };
    setNewTerms(updated);
  };

  const handleSaveTerms = async () => {
    setError('');
    setLoading(true);

    try {
      const updates = newTerms
        .filter(term => term.user_decision !== 'skip')
        .map(term => ({
          term: term.term,
          decision: term.user_decision! as 'variant' | 'new',
          canonical: term.user_canonical,
          category: term.user_category,
          note: term.llm_suggestion.reason,
        }));

      if (updates.length === 0) {
        setSuccess('更新する用語がありません');
        setShowTermsModal(false);
        return;
      }

      const response = await api.updateDictionary({ updates }, idToken, currentTeamId);

      if (response.success) {
        setSuccess(`${response.updated_entries}件の用語を辞書に追加しました`);
        setShowTermsModal(false);
        setNewTerms([]);
      }
    } catch (err: any) {
      setError(err.message || '辞書の更新に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-4">ノート取り込み</h1>

        {/* 本番環境の説明 */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8">
          <h3 className="font-bold mb-2 text-green-900">📦 本番環境のストレージ設定</h3>
          <p className="text-sm text-green-800 mb-2">
            バックエンドは <strong>Google Cloud Storage (GCS)</strong> を使用しています。
          </p>
          <div className="text-xs font-mono text-green-900 bg-white p-3 rounded border border-green-200">
            バケット: jikkennote-storage<br />
            新規ノート: gs://jikkennote-storage/notes/new/<br />
            処理済み: gs://jikkennote-storage/notes/processed/<br />
            アーカイブ: gs://jikkennote-storage/notes/archived/
          </div>
          <p className="text-xs text-green-700 mt-2">
            ※ フォルダパスはバックエンドで固定されており、変更できません。
          </p>
        </div>

        {/* ChromaDB再構築セクション */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-2 text-blue-900">ChromaDB再構築</h2>
          <p className="text-sm text-blue-700 mb-4">
            Embeddingモデルを変更した後は、既存のノート（processedフォルダ）からChromaDBを再構築してください。
          </p>
          <Button onClick={handleRebuild} disabled={rebuildLoading || loading || analyzing}>
            {rebuildLoading ? '再構築中...' : 'ChromaDBを再構築'}
          </Button>
        </div>

        {/* ファイルアップロードセクション */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">📤 ファイルアップロード</h2>
          <p className="text-sm text-gray-700 mb-4">
            Markdownファイル(.md)をドラッグ&ドロップ、またはクリックしてアップロードしてください。
            アップロードされたファイルは自動的にnotes/newフォルダに保存されます。
          </p>

          <FileDropZone
            onFilesSelected={handleUpload}
            accept=".md"
            multiple={true}
            disabled={loading || analyzing}
            loading={uploadLoading}
          />

          {uploadError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
              {uploadError}
            </div>
          )}
          {uploadSuccess && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mt-4">
              {uploadSuccess}
            </div>
          )}
        </div>

        {/* 設定フォーム */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">新規ノート取り込み</h2>

          <div className="space-y-4">
            {/* ソースフォルダ */}
            <div>
              <label className="block text-sm font-medium mb-2">
                ソースフォルダ
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md p-3 bg-gray-100 cursor-not-allowed"
                value="notes/new (GCS: gs://jikkennote-storage/notes/new/)"
                readOnly
                disabled
              />
              <p className="text-sm text-text-secondary mt-1">
                ※ 本番環境ではバックエンドで固定されています。変更できません。
              </p>
            </div>

            {/* 取り込み後のアクション */}
            <div>
              <label className="block text-sm font-medium mb-2">取り込み後のアクション</label>
              <select
                className="w-full border border-gray-300 rounded-md p-3"
                value={postAction}
                onChange={(e) => setPostAction(e.target.value as any)}
              >
                <option value="move_to_processed">processedフォルダへ移動（推奨）</option>
                <option value="keep">ファイルを残す</option>
                <option value="archive">アーカイブフォルダへ移動</option>
                <option value="delete">ファイルを削除</option>
              </select>
              <p className="text-sm text-text-secondary mt-1">
                推奨: processedフォルダへ移動。ChromaDB再構築時にこのフォルダから読み込みます。
              </p>
            </div>

            {/* アーカイブフォルダ */}
            {postAction === 'archive' && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  アーカイブフォルダ（空欄の場合はデフォルト）
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded-md p-3"
                  value={archiveFolder}
                  onChange={(e) => setArchiveFolder(e.target.value)}
                  placeholder="./notes/archived"
                />
              </div>
            )}

            {/* 実行ボタン */}
            <div>
              <Button onClick={handleIngest} disabled={loading || analyzing}>
                {loading ? '取り込み中...' : '取り込み実行'}
              </Button>
            </div>
          </div>

          {/* 通知 */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mt-4">
              {success}
            </div>
          )}
        </div>

        {/* 取り込み結果 */}
        {ingestResult && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">取り込み結果</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 新規ノート */}
              <div className="border border-gray-300 rounded-lg p-4">
                <h3 className="font-bold mb-2">
                  新規取り込み ({ingestResult.new_notes.length}件)
                </h3>
                {ingestResult.new_notes.length === 0 ? (
                  <p className="text-text-secondary">なし</p>
                ) : (
                  <ul className="space-y-1">
                    {ingestResult.new_notes.map((noteId, index) => (
                      <li key={index} className="text-sm">
                        {noteId}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* スキップしたノート */}
              <div className="border border-gray-300 rounded-lg p-4">
                <h3 className="font-bold mb-2">
                  スキップ ({ingestResult.skipped_notes.length}件)
                </h3>
                {ingestResult.skipped_notes.length === 0 ? (
                  <p className="text-text-secondary">なし</p>
                ) : (
                  <ul className="space-y-1">
                    {ingestResult.skipped_notes.map((noteId, index) => (
                      <li key={index} className="text-sm text-text-secondary">
                        {noteId}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 新出単語判定モーダル */}
        {showTermsModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto p-6">
              <h2 className="text-2xl font-bold mb-4">新出単語の判定</h2>

              <div className="space-y-4 mb-6">
                {newTerms.map((term, index) => (
                  <div key={index} className="border border-gray-300 rounded-lg p-4">
                    {/* 用語名 */}
                    <div className="font-bold text-lg mb-2">{term.term}</div>

                    {/* LLM提案 */}
                    <div className="bg-blue-50 p-3 rounded mb-3">
                      <div className="text-sm font-medium mb-1">AI提案</div>
                      <div className="text-sm">
                        判定: {term.llm_suggestion.decision === 'new' ? '新規物質' : '表記揺れ'}
                      </div>
                      <div className="text-sm">理由: {term.llm_suggestion.reason}</div>
                      {term.llm_suggestion.suggested_canonical && (
                        <div className="text-sm">
                          紐付け先: {term.llm_suggestion.suggested_canonical}
                        </div>
                      )}
                    </div>

                    {/* 類似候補 */}
                    {term.similar_candidates.length > 0 && (
                      <div className="mb-3">
                        <div className="text-sm font-medium mb-1">類似候補</div>
                        <div className="flex flex-wrap gap-2">
                          {term.similar_candidates.slice(0, 3).map((cand, cIndex) => (
                            <span
                              key={cIndex}
                              className="bg-gray-100 px-2 py-1 rounded text-sm"
                            >
                              {cand.term} (正規化: {cand.canonical}, 類似度:{' '}
                              {cand.combined_score.toFixed(2)})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* ユーザー判定 */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">判定</label>
                        <select
                          className="w-full border border-gray-300 rounded p-2 text-sm"
                          value={term.user_decision}
                          onChange={(e) =>
                            handleUpdateDecision(index, 'user_decision', e.target.value)
                          }
                        >
                          <option value="new">新規物質</option>
                          <option value="variant">表記揺れ</option>
                          <option value="skip">スキップ</option>
                        </select>
                      </div>

                      {term.user_decision === 'variant' && (
                        <div>
                          <label className="block text-sm font-medium mb-1">正規化名</label>
                          <input
                            type="text"
                            className="w-full border border-gray-300 rounded p-2 text-sm"
                            value={term.user_canonical || ''}
                            onChange={(e) =>
                              handleUpdateDecision(index, 'user_canonical', e.target.value)
                            }
                            placeholder="紐付ける正規化名"
                          />
                        </div>
                      )}

                      {term.user_decision === 'new' && (
                        <div>
                          <label className="block text-sm font-medium mb-1">カテゴリ</label>
                          <input
                            type="text"
                            className="w-full border border-gray-300 rounded p-2 text-sm"
                            value={term.user_category || ''}
                            onChange={(e) =>
                              handleUpdateDecision(index, 'user_category', e.target.value)
                            }
                            placeholder="試薬、溶媒など"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* アクションボタン */}
              <div className="flex gap-4">
                <Button onClick={handleSaveTerms} disabled={loading}>
                  {loading ? '保存中...' : '辞書を更新'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setShowTermsModal(false)}
                  disabled={loading}
                >
                  キャンセル
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
