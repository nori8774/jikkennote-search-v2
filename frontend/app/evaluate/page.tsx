'use client';

import { useState, useEffect } from 'react';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { storage } from '@/lib/storage';
import { useAuth } from '@/lib/auth-context';
import * as XLSX from 'xlsx';

interface TestCondition {
  条件: number;
  目的: string;
  材料: string;
  実験手順: string;
  重点指示?: string;  // 新規: 重点指示フィールド
  [key: string]: any; // ranking_1, ranking_2, etc.
}

interface EvaluationResult {
  condition_id: number;
  condition_details: {
    目的: string;
    材料: string;
    実験手順: string;
    重点指示?: string;
  };
  metrics: {
    ndcg_10: number;
    precision_10: number;
    recall_10: number;
    mrr: number;
  };
  candidates: { noteId: string; rank: number; score: number }[]; // 検索結果（リランキング後）
  ground_truth: { noteId: string; rank: number }[]; // 正解データ (10件)
}

// v3.1.0: 3軸分離検索設定
interface MultiAxisSettings {
  enabled: boolean;
  fusionMethod: 'rrf' | 'linear';
  axisWeights: { material: number; method: number; combined: number };
  rerankPosition: 'per_axis' | 'after_fusion';
  rerankEnabled: boolean;
}

interface EvaluationHistory {
  id: string;
  timestamp: Date;
  promptName?: string;  // プロンプト名
  embedding_model: string;
  llm_model: string;
  custom_prompts: Record<string, string>;
  results: EvaluationResult[];
  average_metrics: {
    ndcg_10: number;
    precision_10: number;
    recall_10: number;
    mrr: number;
  };
  // v3.1.0: 3軸分離検索設定
  multi_axis_settings?: MultiAxisSettings;
}

export default function EvaluatePage() {
  const { idToken, currentTeamId } = useAuth();
  const [testConditions, setTestConditions] = useState<TestCondition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [currentCondition, setCurrentCondition] = useState<number | null>(null);

  // 評価履歴（最新5件）
  const [evaluationHistories, setEvaluationHistories] = useState<EvaluationHistory[]>([]);
  const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);

  // プロンプト設定
  const [embeddingModel, setEmbeddingModel] = useState('text-embedding-3-small');
  const [llmModel, setLlmModel] = useState('gpt-4o-mini');
  const [defaultPrompts, setDefaultPrompts] = useState<any>(null);
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  const [showPromptEditor, setShowPromptEditor] = useState(false);

  // プロンプト名管理
  const [promptName, setPromptName] = useState('デフォルト');
  const [savedPromptsList, setSavedPromptsList] = useState<any[]>([]);

  // v3.1.0: 3軸分離検索設定
  const [multiAxisEnabled, setMultiAxisEnabled] = useState(true);
  const [fusionMethod, setFusionMethod] = useState<'rrf' | 'linear'>('rrf');
  const [axisWeights, setAxisWeights] = useState({ material: 0.3, method: 0.4, combined: 0.3 });
  const [rerankPosition, setRerankPosition] = useState<'per_axis' | 'after_fusion'>('after_fusion');
  const [rerankEnabled, setRerankEnabled] = useState(true);

  // 評価用シートのデータを読み込む
  useEffect(() => {
    loadEvaluationData();
    loadEvaluationHistories();
    loadDefaultPrompts();

    // 現在の設定を読み込む
    setEmbeddingModel(storage.getEmbeddingModel() || 'text-embedding-3-small');
    setLlmModel(storage.getLLMModel() || 'gpt-4o-mini');
    setCustomPrompts(storage.getCustomPrompts() || {});
  }, []);

  // 保存済みプロンプト一覧をバックエンドから読み込む（認証後）
  useEffect(() => {
    if (!idToken || !currentTeamId) return;

    api.listSavedPrompts(idToken, currentTeamId).then((res) => {
      if (res.success) {
        setSavedPromptsList(res.prompts || []);
        console.log('保存済みプロンプト一覧を読み込みました:', res.prompts?.length || 0, '件');
      }
    }).catch(console.error);
  }, [idToken, currentTeamId]);

  const loadEvaluationData = async () => {
    try {
      const response = await fetch('/evaluation_data.json');
      const data = await response.json();
      setTestConditions(data);
    } catch (err) {
      console.error('評価データの読み込みに失敗:', err);
      setError('評価データの読み込みに失敗しました');
    }
  };

  // Excel ファイルを読み込む
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);

        // データを TestCondition 形式に変換
        const conditions: TestCondition[] = jsonData.map((row: any) => {
          // ranking カラムのノートIDに "ID" プレフィックスを追加（必要な場合）
          const processedRow = { ...row };
          for (let i = 1; i <= 16; i++) {
            const key = `ranking_${i}`;
            if (processedRow[key] && typeof processedRow[key] === 'string') {
              // "ID" プレフィックスがない場合は追加
              if (!processedRow[key].startsWith('ID')) {
                processedRow[key] = `ID${processedRow[key]}`;
              }
            }
          }
          return processedRow as TestCondition;
        });

        setTestConditions(conditions);
        setError('');
        console.log(`Excel ファイルから ${conditions.length} 件の評価条件を読み込みました`);
      } catch (err) {
        console.error('Excel ファイルの解析に失敗:', err);
        setError('Excel ファイルの解析に失敗しました');
      }
    };

    reader.readAsArrayBuffer(file);
  };

  const loadDefaultPrompts = async () => {
    try {
      const response = await api.getDefaultPrompts();
      setDefaultPrompts(response.prompts);
    } catch (err) {
      console.error('デフォルトプロンプトの取得に失敗:', err);
    }
  };

  const loadEvaluationHistories = () => {
    const stored = localStorage.getItem('evaluation_histories');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        console.log('📊 評価履歴を読み込みました:', parsed.length, '件');
        const histories = parsed.map((h: any) => {
          console.log('履歴データ:', {
            id: h.id,
            timestamp: h.timestamp,
            hasResults: !!h.results,
            resultsCount: h.results?.length || 0,
            firstResult: h.results?.[0] || null
          });
          return {
            ...h,
            timestamp: new Date(h.timestamp),
          };
        });
        setEvaluationHistories(histories);
      } catch (error) {
        console.error('評価履歴の読み込みに失敗:', error);
      }
    } else {
      console.log('📊 評価履歴が見つかりません（localStorage）');
    }
  };

  const saveEvaluationHistory = (results: EvaluationResult[], avgMetrics: any) => {
    console.log('💾 評価履歴を保存します');
    console.log('結果数:', results.length);
    console.log('最初の結果:', results[0]);

    const newHistory: EvaluationHistory = {
      id: Date.now().toString(),
      timestamp: new Date(),
      promptName: promptName || 'デフォルト',  // プロンプト名を記録
      embedding_model: embeddingModel,
      llm_model: llmModel,
      custom_prompts: customPrompts,
      results,
      average_metrics: avgMetrics,
      // v3.1.0: 3軸分離検索設定を記録
      multi_axis_settings: {
        enabled: multiAxisEnabled,
        fusionMethod,
        axisWeights,
        rerankPosition,
        rerankEnabled,
      },
    };

    console.log('保存する履歴データ:', newHistory);

    const updated = [newHistory, ...evaluationHistories].slice(0, 50); // FR-115: 最新50件のみ保持
    setEvaluationHistories(updated);
    localStorage.setItem('evaluation_histories', JSON.stringify(updated));

    console.log('✅ 評価履歴を保存しました（全', updated.length, '件）');
  };

  // 全条件について評価を実行
  const handleEvaluateAll = async () => {
    setLoading(true);
    setError('');
    setProgress({ current: 0, total: testConditions.length });
    const results: EvaluationResult[] = [];
    const errors: string[] = [];

    try {
      // APIキーを取得（事前チェック）
      const openaiKey = storage.getOpenAIApiKey();
      const cohereKey = storage.getCohereApiKey();

      if (!openaiKey || !cohereKey) {
        throw new Error('APIキーが設定されていません');
      }

      for (let i = 0; i < testConditions.length; i++) {
        const condition = testConditions[i];
        setCurrentCondition(condition.条件);
        setProgress({ current: i + 1, total: testConditions.length });

        try {
          console.log(`条件 ${condition.条件} を評価中...`);

          // 検索実行（評価モード: 比較省略、Top10返却、v3.1.0: 3軸分離検索対応）
          const searchResponse = await api.search({
            purpose: condition.目的 || '',
            materials: condition.材料 || '',
            methods: condition.実験手順 || '',
            instruction: condition.重点指示 || '', // 重点指示フィールドを使用
            openai_api_key: openaiKey,
            cohere_api_key: cohereKey,
            embedding_model: embeddingModel,
            llm_model: llmModel,
            custom_prompts: customPrompts,
            evaluation_mode: true,  // 評価モードを有効化
            // v3.1.0: 3軸分離検索設定
            multi_axis_enabled: multiAxisEnabled,
            fusion_method: fusionMethod,
            axis_weights: axisWeights,
            rerank_position: rerankPosition,
            rerank_enabled: rerankEnabled,
          }, idToken, currentTeamId);

          // デバッグログ: 検索レスポンスを確認
          console.log(`条件 ${condition.条件} の検索レスポンス:`, {
            success: searchResponse.success,
            retrieved_docs_count: searchResponse.retrieved_docs?.length || 0,
            first_doc_preview: searchResponse.retrieved_docs?.[0]?.substring(0, 200) || 'なし'
          });

          // 検索結果からノートIDとスコアを抽出（リランキング後の上位10件、重複除去）
          const candidates: { noteId: string; rank: number; score: number }[] = [];
          const seenNoteIds = new Set<string>(); // 重複チェック用
          if (searchResponse.retrieved_docs && searchResponse.retrieved_docs.length > 0) {
            for (let j = 0; j < searchResponse.retrieved_docs.length; j++) {
              // 上位10件（重複除去後）に達したら終了
              if (candidates.length >= 10) break;

              const doc = searchResponse.retrieved_docs[j];
              // ノートIDを抽出（バックエンドから返されるフォーマット: 【実験ノートID: ID3-14】）
              const idMatch = doc.match(/【実験ノートID:\s*([ID\d-]+)】/) ||  // 【実験ノートID: ID3-14】
                             doc.match(/実験ノートID:\s*([ID\d-]+)/) ||       // 実験ノートID: ID3-14
                             doc.match(/^#\s+([ID\d-]+)/m) ||                  // # ID3-14
                             doc.match(/\b(ID\d+-\d+)\b/);                     // ID3-14

              if (idMatch) {
                const noteId = idMatch[1];
                // 重複チェック: 同じノートIDが既に追加されている場合はスキップ
                if (seenNoteIds.has(noteId)) {
                  console.log(`条件 ${condition.条件}: 重複ノートID「${noteId}」をスキップ（元順位 ${j+1}）`);
                  continue;
                }
                seenNoteIds.add(noteId);

                // スコアは重複除去後のランクに基づいて設定
                const rank = candidates.length + 1;
                const score = 1.0 - ((rank - 1) * 0.05); // 1位=1.0, 2位=0.95, ...
                candidates.push({
                  noteId: noteId,
                  rank: rank,
                  score: score,
                });
              } else {
                console.warn(`条件 ${condition.条件}: ノートID抽出失敗（順位 ${j+1}）`, doc.substring(0, 100));
              }
            }
          }

          // 正解データを取得（ranking_1からranking_10まで）
          const groundTruth: { noteId: string; rank: number }[] = [];
          for (let j = 1; j <= 10; j++) {
            const rankingKey = `ranking_${j}`;
            if (condition[rankingKey]) {
              // ノートIDをそのまま使用（形式を統一）
              const noteId = condition[rankingKey];
              groundTruth.push({
                noteId: noteId,
                rank: j,
              });
            }
          }

          // 評価指標を計算
          const metrics = calculateMetrics(candidates, groundTruth);

          results.push({
            condition_id: condition.条件,
            condition_details: {
              目的: condition.目的 || '',
              材料: condition.材料 || '',
              実験手順: condition.実験手順 || '',
              重点指示: condition.重点指示 || '',
            },
            metrics,
            candidates,
            ground_truth: groundTruth,
          });

          console.log(`条件 ${condition.条件} 完了`);

          // 少し待機してブラウザのリソースを解放
          await new Promise(resolve => setTimeout(resolve, 500));

        } catch (conditionErr: any) {
          console.error(`条件 ${condition.条件} でエラー:`, conditionErr);
          errors.push(`条件${condition.条件}: ${conditionErr.message || 'エラーが発生しました'}`);
          // エラーが発生しても次の条件に進む
        }
      }

      // 平均スコアを計算（成功した結果のみ）
      if (results.length > 0) {
        const avgMetrics = calculateAverageMetrics(results);
        // 履歴に保存
        saveEvaluationHistory(results, avgMetrics);
      }

      // エラーがあった場合は表示
      if (errors.length > 0) {
        setError(`一部の条件で評価に失敗しました:\n${errors.join('\n')}`);
      } else if (results.length === 0) {
        setError('全ての条件で評価に失敗しました');
      }

    } catch (err: any) {
      console.error('評価エラー:', err);
      setError(err.message || '評価の実行に失敗しました');
    } finally {
      setLoading(false);
      setCurrentCondition(null);
      setProgress({ current: 0, total: 0 });
    }
  };

  // 評価指標の計算
  const calculateMetrics = (
    candidates: { noteId: string; rank: number; score?: number }[],
    groundTruth: { noteId: string; rank: number }[]
  ) => {
    const k = 10;

    // 正解ノートIDのリスト
    const gtIds = groundTruth.map(gt => gt.noteId);

    // nDCG@10の計算
    let dcg = 0;
    let idcg = 0;

    for (let i = 0; i < k; i++) {
      // DCG: 検索結果の順位での計算
      if (i < candidates.length) {
        const candidateId = candidates[i].noteId;
        const gtIndex = gtIds.indexOf(candidateId);
        if (gtIndex !== -1) {
          // 正解データでの順位に基づいてrelevanceを計算（上位ほど高い）
          const relevance = k - gtIndex;
          dcg += relevance / Math.log2(i + 2);
        }
      }

      // IDCG: 理想的なランキング（正解データの順序）
      if (i < groundTruth.length) {
        const relevance = k - i;
        idcg += relevance / Math.log2(i + 2);
      }
    }

    const ndcg_10 = idcg > 0 ? dcg / idcg : 0;

    // Precision@10の計算
    let hits = 0;
    for (let i = 0; i < Math.min(k, candidates.length); i++) {
      if (gtIds.includes(candidates[i].noteId)) {
        hits++;
      }
    }
    const precision_10 = candidates.length > 0 ? hits / Math.min(k, candidates.length) : 0;

    // Recall@10の計算
    const recall_10 = groundTruth.length > 0 ? hits / Math.min(k, groundTruth.length) : 0;

    // MRR（Mean Reciprocal Rank）の計算
    let mrr = 0;
    for (let i = 0; i < candidates.length; i++) {
      if (gtIds.includes(candidates[i].noteId)) {
        mrr = 1 / (i + 1);
        break;
      }
    }

    return {
      ndcg_10,
      precision_10,
      recall_10,
      mrr,
    };
  };

  // 平均スコアを計算
  const calculateAverageMetrics = (results: EvaluationResult[]) => {
    if (results.length === 0) return null;

    const sum = results.reduce(
      (acc, result) => ({
        ndcg_10: acc.ndcg_10 + result.metrics.ndcg_10,
        precision_10: acc.precision_10 + result.metrics.precision_10,
        recall_10: acc.recall_10 + result.metrics.recall_10,
        mrr: acc.mrr + result.metrics.mrr,
      }),
      { ndcg_10: 0, precision_10: 0, recall_10: 0, mrr: 0 }
    );

    const count = results.length;
    return {
      ndcg_10: sum.ndcg_10 / count,
      precision_10: sum.precision_10 / count,
      recall_10: sum.recall_10 / count,
      mrr: sum.mrr / count,
    };
  };

  const handleResetPrompt = (promptType: string) => {
    if (defaultPrompts && defaultPrompts[promptType]) {
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

  // FR-115: CSV出力関数（v3.1.0: 3軸分離検索設定カラム追加）
  const exportToCSV = () => {
    try {
      if (evaluationHistories.length === 0) {
        setError('エクスポートする評価履歴がありません');
        return;
      }

      const headers = [
        '条件ID',
        'Embeddingモデル',
        'LLMモデル',
        'プロンプト名',
        'nDCG@10',
        'Precision@10',
        'Recall@10',
        'MRR',
        // v3.1.0: 3軸分離検索設定カラム
        '3軸検索',
        '統合方式',
        '材料ウエイト',
        '方法ウエイト',
        '総合ウエイト',
        'リランク位置',
        'リランク有効',
        '実行日時'
      ];

      const rows: string[][] = [];

      evaluationHistories.forEach((history) => {
        // v3.1.0: 3軸検索設定を取得（存在しない場合はデフォルト値）
        const mas = history.multi_axis_settings;
        const multiAxisStr = mas?.enabled ? '有効' : '無効';
        const fusionStr = mas?.fusionMethod === 'rrf' ? 'RRF' : (mas?.fusionMethod === 'linear' ? '線形結合' : '-');
        const materialWeight = mas?.axisWeights?.material?.toFixed(2) || '0.30';
        const methodWeight = mas?.axisWeights?.method?.toFixed(2) || '0.40';
        const combinedWeight = mas?.axisWeights?.combined?.toFixed(2) || '0.30';
        const rerankPosStr = mas?.rerankPosition === 'per_axis' ? '各軸後' : (mas?.rerankPosition === 'after_fusion' ? '統合後' : '-');
        const rerankEnabledStr = mas?.rerankEnabled ? '有効' : '無効';

        history.results.forEach((result) => {
          rows.push([
            result.condition_id.toString(),
            history.embedding_model,
            history.llm_model,
            history.promptName || 'デフォルト',
            result.metrics.ndcg_10.toFixed(4),
            result.metrics.precision_10.toFixed(4),
            result.metrics.recall_10.toFixed(4),
            result.metrics.mrr.toFixed(4),
            multiAxisStr,
            fusionStr,
            materialWeight,
            methodWeight,
            combinedWeight,
            rerankPosStr,
            rerankEnabledStr,
            history.timestamp.toISOString()
          ]);
        });
      });

      // BOM付きUTF-8でCSVを生成（Excelで文字化けを防ぐ）
      const BOM = '\uFEFF';
      const csv = BOM + [headers.join(','), ...rows.map(row => row.join(','))].join('\n');

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `evaluation_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      console.error('CSV出力エラー:', err);
      setError('CSVファイルの出力に失敗しました');
    }
  };

  // プロンプト名が変更されたときに保存済みプロンプトをロードする
  useEffect(() => {
    const loadSelectedPrompt = async () => {
      // デフォルトの場合はカスタムプロンプトをクリア
      if (promptName === 'デフォルト') {
        setCustomPrompts({});
        return;
      }

      // カスタムや空の場合はロードしない
      if (promptName === 'カスタム' || !promptName) {
        return;
      }

      // 認証情報がない場合はスキップ
      if (!idToken || !currentTeamId) {
        return;
      }

      // 保存済みプロンプトリストに存在するか確認
      const savedPrompt = savedPromptsList.find(p => p.name === promptName);
      if (!savedPrompt) {
        return;
      }

      try {
        // バックエンドからプロンプトをロード（認証情報を渡す）
        const result = await api.loadPrompt(savedPrompt.id, idToken, currentTeamId);
        if (result.success && result.prompts) {
          setCustomPrompts(result.prompts);
          console.log(`プロンプト「${promptName}」をロードしました`);
        }
      } catch (error) {
        console.error(`プロンプト「${promptName}」のロードに失敗:`, error);
      }
    };

    loadSelectedPrompt();
  }, [promptName, savedPromptsList, idToken, currentTeamId]);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">性能評価</h1>

        {/* 評価条件セクション */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">評価条件</h2>

          {/* Excel ファイルアップロードセクション */}
          <div className="border border-gray-300 rounded-md p-4 mb-6 bg-gray-50">
            <h3 className="font-semibold mb-2">評価データファイル</h3>
            <p className="text-sm text-gray-600 mb-3">
              Excel ファイル（.xlsx）をアップロードして評価データを読み込みます。
              <br />
              現在の評価条件数: {testConditions.length} 件
            </p>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-primary file:text-white
                  hover:file:bg-primary-dark
                  cursor-pointer"
              />
              <Button
                variant="secondary"
                onClick={loadEvaluationData}
                className="text-sm whitespace-nowrap"
              >
                JSONデータ読込
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              ※ Excel ファイルには「条件」「目的」「材料」「実験手順」「重点指示」「ranking_1〜16」のカラムが必要です
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2">Embedding モデル</label>
              <select
                value={embeddingModel}
                onChange={(e) => setEmbeddingModel(e.target.value)}
                className="w-full border border-gray-300 rounded-md p-2"
              >
                <option value="text-embedding-3-small">text-embedding-3-small</option>
                <option value="text-embedding-3-large">text-embedding-3-large</option>
                <option value="text-embedding-ada-002">text-embedding-ada-002</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">LLM モデル</label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="w-full border border-gray-300 rounded-md p-2"
              >
                <optgroup label="GPT-5 シリーズ（最新）">
                  <option value="gpt-5.2">gpt-5.2（高精度）</option>
                  <option value="gpt-5.2-pro">gpt-5.2-pro（最高精度）</option>
                  <option value="gpt-5-mini">gpt-5-mini（コスト効率）</option>
                  <option value="gpt-5-nano">gpt-5-nano（高速）</option>
                </optgroup>
                <optgroup label="GPT-4 シリーズ">
                  <option value="gpt-4o-mini">gpt-4o-mini（推奨）</option>
                  <option value="gpt-4o">gpt-4o</option>
                  <option value="gpt-4-turbo">gpt-4-turbo</option>
                </optgroup>
                <optgroup label="GPT-3.5">
                  <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                </optgroup>
              </select>
            </div>
          </div>

          {/* v3.1.0: 3軸分離検索設定 */}
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold">3軸分離検索設定</h3>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={multiAxisEnabled}
                  onChange={(e) => setMultiAxisEnabled(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">{multiAxisEnabled ? '有効' : '無効'}</span>
              </label>
            </div>

            {multiAxisEnabled && (
              <div className="space-y-4 bg-gray-50 rounded-lg p-4">
                {/* 統合方式 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">スコア統合方式</label>
                    <select
                      value={fusionMethod}
                      onChange={(e) => setFusionMethod(e.target.value as 'rrf' | 'linear')}
                      className="w-full border border-gray-300 rounded-md p-2"
                    >
                      <option value="rrf">RRF (Reciprocal Rank Fusion)</option>
                      <option value="linear">線形結合</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {fusionMethod === 'rrf'
                        ? 'ランク位置に基づくスコア統合（推奨）'
                        : '各軸のスコアを重み付け合計'}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">リランク位置</label>
                    <select
                      value={rerankPosition}
                      onChange={(e) => setRerankPosition(e.target.value as 'per_axis' | 'after_fusion')}
                      className="w-full border border-gray-300 rounded-md p-2"
                      disabled={!rerankEnabled}
                    >
                      <option value="after_fusion">統合後にリランク（推奨）</option>
                      <option value="per_axis">各軸でリランク後に統合</option>
                    </select>
                    <div className="flex items-center gap-2 mt-2">
                      <input
                        type="checkbox"
                        id="rerankEnabled"
                        checked={rerankEnabled}
                        onChange={(e) => setRerankEnabled(e.target.checked)}
                        className="w-4 h-4"
                      />
                      <label htmlFor="rerankEnabled" className="text-xs text-gray-600">
                        Cohereリランキングを使用
                      </label>
                    </div>
                  </div>
                </div>

                {/* 軸ウエイト */}
                <div>
                  <label className="block text-sm font-medium mb-2">軸ウエイト設定</label>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        材料軸: {axisWeights.material.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={axisWeights.material}
                        onChange={(e) => {
                          const newMaterial = Math.round(parseFloat(e.target.value) * 100) / 100;
                          const remaining = Math.round((1 - newMaterial) * 100) / 100;
                          const ratio = axisWeights.method + axisWeights.combined > 0
                            ? axisWeights.method / (axisWeights.method + axisWeights.combined)
                            : 0.5;
                          const newMethod = Math.round(remaining * ratio * 100) / 100;
                          const newCombined = Math.round((remaining - newMethod) * 100) / 100;
                          setAxisWeights({
                            material: newMaterial,
                            method: newMethod,
                            combined: newCombined,
                          });
                        }}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        方法軸: {axisWeights.method.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={axisWeights.method}
                        onChange={(e) => {
                          const newMethod = Math.round(parseFloat(e.target.value) * 100) / 100;
                          const remaining = Math.round((1 - newMethod) * 100) / 100;
                          const ratio = axisWeights.material + axisWeights.combined > 0
                            ? axisWeights.material / (axisWeights.material + axisWeights.combined)
                            : 0.5;
                          const newMaterial = Math.round(remaining * ratio * 100) / 100;
                          const newCombined = Math.round((remaining - newMaterial) * 100) / 100;
                          setAxisWeights({
                            material: newMaterial,
                            method: newMethod,
                            combined: newCombined,
                          });
                        }}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        総合軸: {axisWeights.combined.toFixed(2)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={axisWeights.combined}
                        onChange={(e) => {
                          const newCombined = Math.round(parseFloat(e.target.value) * 100) / 100;
                          const remaining = Math.round((1 - newCombined) * 100) / 100;
                          const ratio = axisWeights.material + axisWeights.method > 0
                            ? axisWeights.material / (axisWeights.material + axisWeights.method)
                            : 0.5;
                          const newMaterial = Math.round(remaining * ratio * 100) / 100;
                          const newMethod = Math.round((remaining - newMaterial) * 100) / 100;
                          setAxisWeights({
                            material: newMaterial,
                            method: newMethod,
                            combined: newCombined,
                          });
                        }}
                        className="w-full"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    合計: {(axisWeights.material + axisWeights.method + axisWeights.combined).toFixed(2)}
                    （自動調整で1.0になります）
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* プロンプト編集セクション */}
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex justify-between items-center mb-2">
              <div>
                <h3 className="font-semibold">プロンプト設定</h3>
                <p className="text-sm text-gray-600">
                  {Object.keys(customPrompts).length > 0
                    ? `カスタマイズ済み (${Object.keys(customPrompts).length}件)`
                    : 'デフォルト'}
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => setShowPromptEditor(!showPromptEditor)}
                className="text-sm"
              >
                {showPromptEditor ? 'プロンプト編集を閉じる' : 'プロンプトを編集'}
              </Button>
            </div>

            {showPromptEditor && defaultPrompts && (
              <div className="mt-4 space-y-4">
                <div className="flex justify-end">
                  <Button variant="danger" onClick={handleResetAllPrompts} className="text-sm">
                    全て初期設定にリセット
                  </Button>
                </div>

                {Object.entries(defaultPrompts).map(([key, value]: [string, any]) => (
                  <div key={key} className="border border-gray-300 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="font-bold">{value.name}</h4>
                        <p className="text-xs text-gray-600">{value.description}</p>
                      </div>
                      <Button
                        variant="secondary"
                        onClick={() => handleResetPrompt(key)}
                        className="text-xs py-1 px-2"
                      >
                        リセット
                      </Button>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* デフォルト */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="block text-xs font-medium text-gray-700">
                            デフォルト
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
                          className="w-full border border-gray-200 bg-gray-50 rounded-md p-2 h-32 font-mono text-xs"
                          value={value.prompt}
                          readOnly
                        />
                      </div>

                      {/* カスタム */}
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-2">
                          カスタム
                          {customPrompts[key] && customPrompts[key] !== value.prompt && (
                            <span className="ml-2 text-xs text-warning">⚠️ 変更済み</span>
                          )}
                        </label>
                        <textarea
                          className="w-full border border-gray-300 rounded-md p-2 h-32 font-mono text-xs"
                          value={customPrompts[key] || value.prompt}
                          onChange={(e) =>
                            setCustomPrompts({ ...customPrompts, [key]: e.target.value })
                          }
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* プロンプト名の設定 */}
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 mt-6">
            <h3 className="font-bold mb-3">プロンプト名</h3>
            <p className="text-sm text-gray-600 mb-3">
              評価履歴に記録するプロンプト名を選択または入力してください。
            </p>

            <div className="flex gap-3 items-center">
              <select
                className="flex-1 border border-gray-300 rounded-md p-2"
                value={promptName}
                onChange={(e) => setPromptName(e.target.value)}
              >
                <option value="デフォルト">デフォルト</option>
                <option value="カスタム">カスタム（手動入力）</option>
                {savedPromptsList.map((prompt) => (
                  <option key={prompt.id} value={prompt.name}>
                    {prompt.name}
                  </option>
                ))}
              </select>

              {promptName === 'カスタム' && (
                <input
                  type="text"
                  className="flex-1 border border-gray-300 rounded-md p-2"
                  placeholder="プロンプト名を入力"
                  onChange={(e) => setPromptName(e.target.value || 'カスタム')}
                />
              )}
            </div>
          </div>

          {/* 評価実行ボタン */}
          <div className="mt-6">
            <Button
              onClick={handleEvaluateAll}
              disabled={loading || testConditions.length === 0}
              className="w-full md:w-auto"
            >
              {loading
                ? currentCondition
                  ? `条件 ${currentCondition} を評価中... (${progress.current}/${progress.total})`
                  : `評価実行中... (${testConditions.length}条件)`
                : '全条件を評価'}
            </Button>
            {loading && (
              <p className="text-sm text-blue-600 mt-2">
                評価実行中です。ネットワークエラーが発生しても処理は継続されます...
              </p>
            )}
            {!loading && (
              <p className="text-sm text-gray-600 mt-2">
                {testConditions.length}件の条件について検索・評価を実行します
              </p>
            )}
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
              <div className="whitespace-pre-wrap">{error}</div>
            </div>
          )}
        </div>

        {/* 評価履歴セクション */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">評価履歴（最新50件）</h2>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={exportToCSV}
                disabled={evaluationHistories.length === 0}
                className="text-sm"
              >
                CSV出力
              </Button>
              <button
                onClick={() => {
                  if (confirm('評価履歴を全て削除しますか？')) {
                    localStorage.removeItem('evaluation_histories');
                    setEvaluationHistories([]);
                    alert('評価履歴を削除しました');
                  }
                }}
                className="text-xs px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200"
              >
                履歴削除
              </button>
            </div>
          </div>

          {evaluationHistories.length === 0 ? (
            <div className="p-6 bg-gray-50 border border-gray-300 rounded text-center">
              <p className="text-gray-600 mb-2">評価履歴がありません</p>
              <p className="text-sm text-gray-500">
                「全条件を評価」ボタンをクリックして評価を実行すると、ここに履歴が表示されます。
              </p>
            </div>
          ) : (

            <div className="space-y-4">
              {evaluationHistories.map((history) => (
                <div key={history.id} className="border border-gray-200 rounded-lg">
                  {/* ヘッダー部分 */}
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => {
                      console.log('クリック:', history.id, '現在の展開ID:', expandedHistoryId);
                      console.log('履歴データ:', history);
                      setExpandedHistoryId(expandedHistoryId === history.id ? null : history.id);
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium">
                            {history.timestamp.toLocaleString('ja-JP')}
                          </span>
                          {history.promptName && (
                            <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded font-semibold">
                              📌 {history.promptName}
                            </span>
                          )}
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            {history.embedding_model}
                          </span>
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                            {history.llm_model}
                          </span>
                          {Object.keys(history.custom_prompts).length > 0 && (
                            <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                              カスタムプロンプト
                            </span>
                          )}
                        </div>

                        {/* 平均スコア */}
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">nDCG@10: </span>
                            <span className="font-bold">
                              {history.average_metrics.ndcg_10.toFixed(3)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Precision@10: </span>
                            <span className="font-bold">
                              {history.average_metrics.precision_10.toFixed(3)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Recall@10: </span>
                            <span className="font-bold">
                              {history.average_metrics.recall_10.toFixed(3)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">MRR: </span>
                            <span className="font-bold">
                              {history.average_metrics.mrr.toFixed(3)}
                            </span>
                          </div>
                        </div>
                      </div>

                      <button className="ml-4 text-gray-400 hover:text-gray-600">
                        {expandedHistoryId === history.id ? '▲' : '▼'}
                      </button>
                    </div>
                  </div>

                  {/* 展開部分 */}
                  {expandedHistoryId === history.id && (
                    <div className="border-t border-gray-200 p-4 bg-gray-50">
                      <div className="space-y-4">
                        {history.results && history.results.length > 0 ? (
                          history.results.map((result) => (
                            <div
                              key={result.condition_id}
                              className="border border-gray-200 rounded-lg p-4 bg-white"
                            >
                              <h4 className="font-bold text-sm mb-3">条件 {result.condition_id}</h4>

                            {/* 指標 */}
                            <div className="grid grid-cols-4 gap-2 text-xs mb-3">
                              <div>
                                <span className="text-gray-600">nDCG@10:</span>
                                <span className="ml-1 font-bold">
                                  {result.metrics.ndcg_10.toFixed(3)}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-600">Precision@10:</span>
                                <span className="ml-1 font-bold">
                                  {result.metrics.precision_10.toFixed(3)}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-600">Recall@10:</span>
                                <span className="ml-1 font-bold">
                                  {result.metrics.recall_10.toFixed(3)}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-600">MRR:</span>
                                <span className="ml-1 font-bold">
                                  {result.metrics.mrr.toFixed(3)}
                                </span>
                              </div>
                            </div>

                            {/* 検索結果（リランキング後） */}
                            {result.candidates && result.candidates.length > 0 ? (
                              <div className="mb-3">
                                <h5 className="font-semibold text-xs mb-2">
                                  検索結果（リランキング後、Top 10）
                                </h5>
                                <div className="overflow-x-auto">
                                  <table className="min-w-full text-xs border border-gray-300">
                                    <thead className="bg-gray-100">
                                      <tr>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">ランク</th>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">ノートID</th>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">スコア</th>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">正解</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {result.candidates.map((candidate) => {
                                        const isCorrect = result.ground_truth?.some(
                                          (gt) => gt.noteId === candidate.noteId
                                        ) || false;
                                        return (
                                          <tr
                                            key={candidate.rank}
                                            className={isCorrect ? 'bg-green-50' : ''}
                                          >
                                            <td className="px-2 py-1 border-b border-gray-200">{candidate.rank}</td>
                                            <td className="px-2 py-1 border-b border-gray-200 font-mono">
                                              {candidate.noteId}
                                            </td>
                                            <td className="px-2 py-1 border-b border-gray-200">
                                              {candidate.score?.toFixed(3) || 'N/A'}
                                            </td>
                                            <td className="px-2 py-1 border-b border-gray-200">
                                              {isCorrect ? (
                                                <span className="text-green-600 font-bold">✓</span>
                                              ) : (
                                                <span className="text-gray-400">-</span>
                                              )}
                                            </td>
                                          </tr>
                                        );
                                      })}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            ) : (
                              <div className="mb-3 p-3 bg-gray-50 border border-gray-300 rounded">
                                <p className="text-xs text-gray-600">検索結果がありません</p>
                              </div>
                            )}

                            {/* 正解データ */}
                            {result.ground_truth && result.ground_truth.length > 0 ? (
                              <div>
                                <h5 className="font-semibold text-xs mb-2">
                                  正解データ (Ground Truth、Top 10)
                                </h5>
                                <div className="overflow-x-auto">
                                  <table className="min-w-full text-xs border border-gray-300">
                                    <thead className="bg-gray-100">
                                      <tr>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">正解順位</th>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">ノートID</th>
                                        <th className="px-2 py-1 border-b border-gray-300 text-left">検出</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {result.ground_truth.map((gt) => {
                                        const wasFound = result.candidates?.some(
                                          (c) => c.noteId === gt.noteId
                                        ) || false;
                                        const foundRank = result.candidates?.find(
                                          (c) => c.noteId === gt.noteId
                                        )?.rank;
                                        return (
                                          <tr key={gt.rank} className={wasFound ? 'bg-green-50' : 'bg-red-50'}>
                                            <td className="px-2 py-1 border-b border-gray-200">{gt.rank}</td>
                                            <td className="px-2 py-1 border-b border-gray-200 font-mono">
                                              {gt.noteId}
                                            </td>
                                            <td className="px-2 py-1 border-b border-gray-200">
                                              {wasFound ? (
                                                <span className="text-green-600 font-bold">
                                                  ✓ (ランク {foundRank})
                                                </span>
                                              ) : (
                                                <span className="text-red-600">✗ 未検出</span>
                                              )}
                                            </td>
                                          </tr>
                                        );
                                      })}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            ) : (
                              <div className="p-3 bg-gray-50 border border-gray-300 rounded">
                                <p className="text-xs text-gray-600">正解データがありません</p>
                              </div>
                            )}
                          </div>
                        ))
                        ) : (
                          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
                            <p className="text-sm text-yellow-800">
                              評価結果がありません。評価を実行してください。
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
