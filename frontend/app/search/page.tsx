'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { storage } from '@/lib/storage';
import { useAuth } from '@/lib/auth-context';
import Button from '@/components/Button';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

function SearchContent() {
  const { idToken, currentTeamId } = useAuth();
  const searchParams = useSearchParams();
  const [purpose, setPurpose] = useState('');
  const [materials, setMaterials] = useState('');
  const [methods, setMethods] = useState('');
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [copySuccess, setCopySuccess] = useState('');
  // v3.0: 検索モード設定
  const [searchMode, setSearchMode] = useState<'semantic' | 'keyword' | 'hybrid'>(() => {
    if (typeof window !== 'undefined') {
      return storage.getSearchMode() || 'semantic';
    }
    return 'semantic';
  });
  // FR-113: 再検索モーダル
  const [showResearchModal, setShowResearchModal] = useState(false);
  const [researchInstruction, setResearchInstruction] = useState('');
  // FR-114: フォーム反映時のハイライト
  const [highlightField, setHighlightField] = useState<string | null>(null);

  // FR-114: URLパラメータから検索条件を読み込み
  useEffect(() => {
    const purposeParam = searchParams.get('purpose');
    const materialsParam = searchParams.get('materials');
    const methodsParam = searchParams.get('methods');

    if (purposeParam) {
      setPurpose(purposeParam);
      setHighlightField('purpose');
    }
    if (materialsParam) {
      setMaterials(materialsParam);
      setHighlightField('materials');
    }
    if (methodsParam) {
      setMethods(methodsParam);
      setHighlightField('methods');
    }

    // ハイライトを3秒後に解除
    if (purposeParam || materialsParam || methodsParam) {
      setTimeout(() => setHighlightField(null), 3000);
    }
  }, [searchParams]);

  const handleSearch = async () => {
    setError('');
    setLoading(true);

    try {
      // APIキーをlocalStorageから取得
      const openaiKey = storage.getOpenAIApiKey();
      const cohereKey = storage.getCohereApiKey();

      if (!openaiKey || !cohereKey) {
        throw new Error('APIキーが設定されていません。設定ページで入力してください。');
      }

      if (!openaiKey.startsWith('sk-')) {
        throw new Error('OpenAI APIキーの形式が正しくありません。「sk-」で始まるキーを設定してください。');
      }

      const response = await api.search({
        purpose,
        materials,
        methods,
        instruction,
        openai_api_key: openaiKey,
        cohere_api_key: cohereKey,
        embedding_model: storage.getEmbeddingModel() || undefined,
        llm_model: storage.getLLMModel() || undefined,
        // v3.0: 2段階モデル選択
        search_llm_model: storage.getSearchLLMModel() || undefined,
        summary_llm_model: storage.getSummaryLLMModel() || undefined,
        // v3.0.1: ハイブリッド検索
        search_mode: searchMode,
        hybrid_alpha: storage.getHybridAlpha() || undefined,
        custom_prompts: storage.getCustomPrompts() || undefined,
      }, idToken, currentTeamId);

      setResult(response);

      // 検索結果を履歴に保存
      saveToHistory(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveToHistory = (response: any) => {
    // 検索結果から上位10件のノートIDを抽出
    const results = response.retrieved_docs?.slice(0, 10).map((doc: string, index: number) => {
      // ノートIDを抽出（複数のパターンを試す）
      let noteId = null;

      // パターン1: 【実験ノートID: ID1-2】 形式（バックエンドの標準形式）
      let idMatch = doc.match(/【実験ノートID:\s*(ID[\d-]+)】/);
      if (idMatch) {
        noteId = idMatch[1];
      }

      // パターン2: # ID1-2 形式（Markdown見出し）
      if (!noteId) {
        idMatch = doc.match(/^#\s+(ID[\d-]+)/m);
        if (idMatch) {
          noteId = idMatch[1];
        }
      }

      // パターン3: ## ID1-2 形式
      if (!noteId) {
        idMatch = doc.match(/^##\s+(ID[\d-]+)/m);
        if (idMatch) {
          noteId = idMatch[1];
        }
      }

      // パターン4: 任意の位置の ID1-2 パターン
      if (!noteId) {
        idMatch = doc.match(/ID\d+-\d+/);
        if (idMatch) {
          noteId = idMatch[0];
        }
      }

      // デバッグ用
      if (!noteId) {
        console.log('ノートIDを抽出できませんでした:', doc.substring(0, 200));
        noteId = `note-${index + 1}`;
      } else {
        console.log(`ノート${index + 1}のID:`, noteId);
      }

      return {
        noteId,
        score: 1.0 - (index * 0.05), // 仮のスコア
        rank: index + 1,
      };
    }) || [];

    console.log('履歴に保存するノートID:', results.map((r: any) => r.noteId));

    const history = {
      id: Date.now().toString(),
      timestamp: new Date(),
      query: {
        purpose,
        materials,
        methods,
        instruction,
      },
      results,
    };

    // localStorageに保存
    const stored = localStorage.getItem('search_histories');
    const histories = stored ? JSON.parse(stored) : [];
    histories.unshift(history); // 最新を先頭に追加

    // 最大50件まで保存
    if (histories.length > 50) {
      histories.pop();
    }

    localStorage.setItem('search_histories', JSON.stringify(histories));
  };

  const handleCopyMaterials = (doc: string) => {
    // ノートから材料セクションを抽出してコピー
    const materialsMatch = doc.match(/## 材料\n(.*?)\n##/s);
    if (materialsMatch) {
      setMaterials(materialsMatch[1].trim());
      setCopySuccess('材料を検索条件にコピーしました');
      setTimeout(() => setCopySuccess(''), 3000);
    } else {
      setCopySuccess('材料セクションが見つかりませんでした');
      setTimeout(() => setCopySuccess(''), 3000);
    }
  };

  const handleCopyMethods = (doc: string) => {
    // ノートから方法セクションを抽出してコピー
    const methodsMatch = doc.match(/## 方法\n(.*?)(?:\n##|$)/s);
    if (methodsMatch) {
      setMethods(methodsMatch[1].trim());
      setCopySuccess('方法を検索条件にコピーしました');
      setTimeout(() => setCopySuccess(''), 3000);
    } else {
      setCopySuccess('方法セクションが見つかりませんでした');
      setTimeout(() => setCopySuccess(''), 3000);
    }
  };

  // FR-114: ノートから目的セクションを抽出してコピー
  const handleCopyPurpose = (doc: string) => {
    const purposeMatch = doc.match(/## 目的\n(.*?)(?:\n##|$)/s);
    if (purposeMatch) {
      setPurpose(purposeMatch[1].trim());
      setHighlightField('purpose');
      setCopySuccess('目的を検索条件にコピーしました');
      setTimeout(() => {
        setCopySuccess('');
        setHighlightField(null);
      }, 3000);
    } else {
      setCopySuccess('目的セクションが見つかりませんでした');
      setTimeout(() => setCopySuccess(''), 3000);
    }
  };

  // FR-114: ノートから全セクションを一括コピー
  const handleCopyAll = (doc: string) => {
    const purposeMatch = doc.match(/## 目的\n(.*?)(?:\n##|$)/s);
    const materialsMatch = doc.match(/## 材料\n(.*?)\n##/s);
    const methodsMatch = doc.match(/## 方法\n(.*?)(?:\n##|$)/s);

    let copied: string[] = [];
    if (purposeMatch) {
      setPurpose(purposeMatch[1].trim());
      copied.push('目的');
    }
    if (materialsMatch) {
      setMaterials(materialsMatch[1].trim());
      copied.push('材料');
    }
    if (methodsMatch) {
      setMethods(methodsMatch[1].trim());
      copied.push('方法');
    }

    if (copied.length > 0) {
      setHighlightField('all');
      setCopySuccess(`${copied.join('・')}を検索条件にコピーしました`);
      setTimeout(() => {
        setCopySuccess('');
        setHighlightField(null);
      }, 3000);
    } else {
      setCopySuccess('コピー可能なセクションが見つかりませんでした');
      setTimeout(() => setCopySuccess(''), 3000);
    }
  };

  // FR-113: 再検索実行
  const handleResearch = () => {
    setInstruction(researchInstruction);
    setShowResearchModal(false);
    setResearchInstruction(''); // モーダルの入力をクリア
    // 検索実行
    setTimeout(() => {
      handleSearch();
    }, 100);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">実験ノート検索</h1>

        {/* 2カラムレイアウト */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左側: 検索フォーム */}
          <div className="bg-white rounded-lg shadow-lg p-6 h-fit sticky top-8">
            <h2 className="text-xl font-bold mb-4">検索条件</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">目的・背景</label>
                <textarea
                  className={`w-full border rounded-md p-3 h-24 text-sm transition-all duration-300 ${
                    highlightField === 'purpose' || highlightField === 'all'
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-300'
                  }`}
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  placeholder="実験の目的や背景を入力..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">材料</label>
                <textarea
                  className={`w-full border rounded-md p-3 h-32 text-sm transition-all duration-300 ${
                    highlightField === 'materials' || highlightField === 'all'
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-300'
                  }`}
                  value={materials}
                  onChange={(e) => setMaterials(e.target.value)}
                  placeholder="使用する材料を入力..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">方法・手順</label>
                <textarea
                  className={`w-full border rounded-md p-3 h-32 text-sm transition-all duration-300 ${
                    highlightField === 'methods' || highlightField === 'all'
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-300'
                  }`}
                  value={methods}
                  onChange={(e) => setMethods(e.target.value)}
                  placeholder="実験の手順を入力..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">絞り込み指示（オプション）</label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded-md p-3 text-sm"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder="特定の条件で絞り込む場合は入力..."
                />
              </div>

              {/* v3.0.1: 検索モード選択 */}
              <div>
                <label className="block text-sm font-medium mb-2">検索モード</label>
                <select
                  className="w-full border border-gray-300 rounded-md p-3 text-sm bg-white"
                  value={searchMode}
                  onChange={(e) => setSearchMode(e.target.value as 'semantic' | 'keyword' | 'hybrid')}
                >
                  <option value="semantic">セマンティック検索（意味検索）</option>
                  <option value="keyword">キーワード検索（BM25）</option>
                  <option value="hybrid">ハイブリッド検索（併用）</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {searchMode === 'semantic' && 'ベクトル類似度で意味的に類似したノートを検索'}
                  {searchMode === 'keyword' && 'キーワードの出現頻度で検索（材料名等の完全一致に強い）'}
                  {searchMode === 'hybrid' && 'セマンティックとキーワードを組み合わせて検索'}
                </p>
              </div>

              <Button
                onClick={handleSearch}
                disabled={loading || !purpose || !materials || !methods}
                className="w-full"
              >
                {loading ? '検索中...' : '検索'}
              </Button>

              {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
                  {error}
                </div>
              )}

              {copySuccess && (
                <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded text-sm">
                  {copySuccess}
                </div>
              )}
            </div>
          </div>

          {/* 右側: 検索結果 */}
          <div>
            {!result && (
              <div className="bg-white rounded-lg shadow-lg p-8 text-center text-gray-500">
                <p>検索条件を入力して検索ボタンをクリックしてください</p>
              </div>
            )}

            {result && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold">検索結果</h2>
                  {/* FR-113: 再検索ボタン */}
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setResearchInstruction(instruction);
                      setShowResearchModal(true);
                    }}
                    className="text-sm"
                  >
                    重点指示を追加して再検索
                  </Button>
                </div>

                {/* 比較分析レポート */}
                <div className="mb-8 prose max-w-none">
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
                    {result.message}
                  </ReactMarkdown>
                </div>

                {/* 検索されたノート */}
                {result.retrieved_docs && result.retrieved_docs.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-xl font-bold mb-4">検索された実験ノート（上位3件）</h3>
                    {result.retrieved_docs.map((doc: string, index: number) => {
                      // ノートIDを抽出（複数のパターンを試す）
                      let noteId = null;

                      // パターン1: 【実験ノートID: ID1-2】 形式
                      let idMatch = doc.match(/【実験ノートID:\s*(ID[\d-]+)】/);
                      if (idMatch) {
                        noteId = idMatch[1];
                      }

                      // パターン2: # ID1-2 形式
                      if (!noteId) {
                        idMatch = doc.match(/^#\s+(ID[\d-]+)/m);
                        if (idMatch) {
                          noteId = idMatch[1];
                        }
                      }

                      // パターン3: ID1-2 パターン
                      if (!noteId) {
                        idMatch = doc.match(/ID\d+-\d+/);
                        if (idMatch) {
                          noteId = idMatch[0];
                        }
                      }

                      return (
                        <div key={index} className="border border-gray-300 rounded-lg p-4 mb-4">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-lg">ノート {index + 1}</h4>
                              {noteId && (
                                <a
                                  href={`/viewer?id=${noteId}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 text-sm underline"
                                  title="新しいタブで全文表示"
                                >
                                  {noteId} →
                                </a>
                              )}
                            </div>
                            {/* FR-114: コピーボタン群 */}
                            <div className="flex gap-1 flex-wrap">
                              <Button
                                variant="secondary"
                                onClick={() => handleCopyPurpose(doc)}
                                className="text-xs py-1 px-2"
                                title="目的を検索条件にコピー"
                              >
                                目的
                              </Button>
                              <Button
                                variant="secondary"
                                onClick={() => handleCopyMaterials(doc)}
                                className="text-xs py-1 px-2"
                                title="材料を検索条件にコピー"
                              >
                                材料
                              </Button>
                              <Button
                                variant="secondary"
                                onClick={() => handleCopyMethods(doc)}
                                className="text-xs py-1 px-2"
                                title="方法を検索条件にコピー"
                              >
                                方法
                              </Button>
                              <Button
                                variant="secondary"
                                onClick={() => handleCopyAll(doc)}
                                className="text-xs py-1 px-2 bg-blue-100"
                                title="目的・材料・方法を一括コピー"
                              >
                                一括
                              </Button>
                            </div>
                          </div>
                          <div className="prose max-w-none text-sm">
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
                              {doc}
                            </ReactMarkdown>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* FR-113: 再検索モーダル */}
        {showResearchModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
              <h2 className="text-xl font-bold mb-4">重点指示を追加して再検索</h2>

              {/* 現在の検索条件を表示 */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4 text-sm">
                <h3 className="font-medium mb-2">現在の検索条件</h3>
                <div className="space-y-1">
                  <p><span className="font-medium">目的:</span> {purpose.substring(0, 100)}{purpose.length > 100 ? '...' : ''}</p>
                  <p><span className="font-medium">材料:</span> {materials.substring(0, 100)}{materials.length > 100 ? '...' : ''}</p>
                  <p><span className="font-medium">方法:</span> {methods.substring(0, 100)}{methods.length > 100 ? '...' : ''}</p>
                </div>
              </div>

              {/* 重点指示入力 */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  重点指示（新しい絞り込み条件）
                </label>
                <textarea
                  className="w-full border border-gray-300 rounded-md p-3 h-32 text-sm"
                  value={researchInstruction}
                  onChange={(e) => setResearchInstruction(e.target.value)}
                  placeholder="例: 反応温度は60度以上で、攪拌時間は2時間以上のものに絞り込む"
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-1">
                  目的・材料・方法は維持されます。新しい絞り込み条件を入力してください。
                </p>
              </div>

              {/* ボタン */}
              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={() => setShowResearchModal(false)}
                >
                  キャンセル
                </Button>
                <Button
                  onClick={handleResearch}
                  disabled={loading}
                >
                  {loading ? '検索中...' : '再検索'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center">読み込み中...</div>}>
      <SearchContent />
    </Suspense>
  );
}
