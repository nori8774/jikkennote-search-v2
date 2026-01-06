'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Button from '@/components/Button';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

function ViewerContent() {
  const { idToken, currentTeamId } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [noteId, setNoteId] = useState('');
  const [noteContent, setNoteContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copySuccess, setCopySuccess] = useState('');
  const [sections, setSections] = useState<{
    purpose?: string;
    materials?: string;
    methods?: string;
    results?: string;
  }>({});
  // v3.2.2: 現在表示中のノートIDを追跡
  const [displayedNoteId, setDisplayedNoteId] = useState('');

  // v3.2.2: URLパラメータからの初期ID取得用の状態を追加
  const [initialId, setInitialId] = useState<string | null>(null);

  // URLパラメータからIDを取得して自動表示
  useEffect(() => {
    const id = searchParams.get('id');
    if (id && id !== initialId) {
      setInitialId(id);
      setNoteId(id);
      handleLoadById(id);
    }
  }, [searchParams, initialId]);

  const handleLoadById = async (id: string) => {
    setError('');
    setLoading(true);

    try {
      const response = await api.getNote(id, idToken, currentTeamId);

      if (!response.success || !response.note) {
        setError(response.error || 'ノートの読み込みに失敗しました');
        return;
      }

      setNoteContent(response.note.content);
      setSections(response.note.sections);
      setDisplayedNoteId(id);  // v3.2.2: 表示中のIDを更新

    } catch (err: any) {
      setError(err.message || 'ノートの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleLoad = async () => {
    setError('');
    setLoading(true);

    try {
      const response = await api.getNote(noteId, idToken, currentTeamId);

      if (!response.success || !response.note) {
        setError(response.error || 'ノートの読み込みに失敗しました');
        return;
      }

      setNoteContent(response.note.content);
      setSections(response.note.sections);
      setDisplayedNoteId(noteId);  // v3.2.2: 表示中のIDを更新

    } catch (err: any) {
      setError(err.message || 'ノートの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // FR-114: クリップボードにコピー
  const handleCopyToClipboard = (sectionName: string, content?: string) => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopySuccess(`${sectionName}をクリップボードにコピーしました`);
    setTimeout(() => setCopySuccess(''), 3000);
  };

  // FR-114: 検索ページに遷移してフォームに反映（v3.2.2: 新しいタブで開く）
  const copyToSearch = (field: 'purpose' | 'materials' | 'methods' | 'all') => {
    const params = new URLSearchParams();

    if ((field === 'all' || field === 'purpose') && sections.purpose) {
      params.set('purpose', sections.purpose);
    }
    if ((field === 'all' || field === 'materials') && sections.materials) {
      params.set('materials', sections.materials);
    }
    if ((field === 'all' || field === 'methods') && sections.methods) {
      params.set('methods', sections.methods);
    }

    // v3.2.2: 新しいタブで検索ページを開く
    window.open(`/search?${params.toString()}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">実験ノートビューワー</h1>

        {/* 入力フォーム */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">実験ノートID</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md p-3"
                value={noteId}
                onChange={(e) => setNoteId(e.target.value)}
                placeholder="例: ID3-14"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleLoad}
                disabled={loading || !noteId}
              >
                {loading ? '読み込み中...' : '表示'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
              {error}
            </div>
          )}

          {copySuccess && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mt-4">
              {copySuccess}
            </div>
          )}
        </div>

        {/* ノート表示 */}
        {noteContent && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            {/* v3.2.2: 入力中のIDと表示中のIDが異なる場合に警告表示 */}
            {noteId !== displayedNoteId && noteId && (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-2 rounded mb-4 text-sm">
                入力中のID「{noteId}」と表示中のノート「{displayedNoteId}」が異なります。
                「表示」ボタンをクリックして読み込んでください。
              </div>
            )}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">実験ノート {displayedNoteId}</h2>
              {/* FR-114: 一括コピーボタン */}
              <Button
                onClick={() => copyToSearch('all')}
                className="text-sm"
                disabled={!sections.purpose && !sections.materials && !sections.methods}
              >
                目的・材料・方法を検索条件にコピー
              </Button>
            </div>

            {/* セクション別コピーボタン付き表示 */}
            <div className="space-y-6">
              {sections.purpose && (
                <div className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-bold">目的・背景</h3>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => copyToSearch('purpose')}
                        className="text-sm py-1 px-3"
                        title="検索ページに移動して目的を設定"
                      >
                        検索条件にコピー
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleCopyToClipboard('目的・背景', sections.purpose)}
                        className="text-sm py-1 px-3"
                        title="クリップボードにコピー"
                      >
                        📋
                      </Button>
                    </div>
                  </div>
                  <div className="prose max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                    >
                      {sections.purpose}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {sections.materials && (
                <div className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-bold">材料</h3>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => copyToSearch('materials')}
                        className="text-sm py-1 px-3"
                        title="検索ページに移動して材料を設定"
                      >
                        検索条件にコピー
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleCopyToClipboard('材料', sections.materials)}
                        className="text-sm py-1 px-3"
                        title="クリップボードにコピー"
                      >
                        📋
                      </Button>
                    </div>
                  </div>
                  <div className="prose max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                    >
                      {sections.materials}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {sections.methods && (
                <div className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-bold">方法</h3>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => copyToSearch('methods')}
                        className="text-sm py-1 px-3"
                        title="検索ページに移動して方法を設定"
                      >
                        検索条件にコピー
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleCopyToClipboard('方法', sections.methods)}
                        className="text-sm py-1 px-3"
                        title="クリップボードにコピー"
                      >
                        📋
                      </Button>
                    </div>
                  </div>
                  <div className="prose max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                    >
                      {sections.methods}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {sections.results && (
                <div className="border border-gray-300 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-bold">結果</h3>
                    <Button
                      variant="secondary"
                      onClick={() => handleCopyToClipboard('結果', sections.results)}
                      className="text-sm py-1 px-3"
                      title="クリップボードにコピー"
                    >
                      📋 コピー
                    </Button>
                  </div>
                  <div className="prose max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw]}
                    >
                      {sections.results}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>

            {/* 全文表示 */}
            <div className="mt-8 pt-8 border-t border-gray-300">
              <h3 className="text-lg font-bold mb-4">全文</h3>
              <div className="prose max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                  components={{
                    table: ({node, ...props}) => (
                      <table className="border-collapse border border-gray-300 w-full my-4" {...props} />
                    ),
                    thead: ({node, ...props}) => (
                      <thead className="bg-gray-100" {...props} />
                    ),
                    th: ({node, ...props}) => (
                      <th className="border border-gray-300 px-4 py-2 text-left font-semibold" {...props} />
                    ),
                    td: ({node, ...props}) => (
                      <td className="border border-gray-300 px-4 py-2" {...props} />
                    ),
                    p: ({node, ...props}) => (
                      <p className="whitespace-pre-wrap my-2" {...props} />
                    ),
                    br: ({node, ...props}) => (
                      <br {...props} />
                    ),
                  }}
                >
                  {noteContent}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ViewerPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center">読み込み中...</div>}>
      <ViewerContent />
    </Suspense>
  );
}
