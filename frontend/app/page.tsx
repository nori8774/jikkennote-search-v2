'use client';

import Link from 'next/link';
import Button from '@/components/Button';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h1 className="text-4xl font-bold mb-4">実験ノート検索システム v2.0</h1>
            <p className="text-lg text-text-secondary mb-6">
              LangChainを活用した高精度な実験ノート検索システム
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <Link href="/search">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">🔍 検索</h3>
                  <p className="text-text-secondary">
                    類似する実験ノートを検索し、比較分析レポートを生成
                  </p>
                </div>
              </Link>

              <Link href="/history">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">📜 履歴</h3>
                  <p className="text-text-secondary">
                    過去の検索履歴を閲覧・再利用
                  </p>
                </div>
              </Link>

              <Link href="/viewer">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">📄 ビューワー</h3>
                  <p className="text-text-secondary">
                    実験ノートIDを入力して直接閲覧
                  </p>
                </div>
              </Link>

              <Link href="/ingest">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">📥 ノート管理</h3>
                  <p className="text-text-secondary">
                    ノート取り込みと新出単語の判定
                  </p>
                </div>
              </Link>

              <Link href="/dictionary">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">📚 辞書管理</h3>
                  <p className="text-text-secondary">
                    正規化辞書の閲覧・編集・エクスポート
                  </p>
                </div>
              </Link>

              <Link href="/evaluate">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">📊 性能評価</h3>
                  <p className="text-text-secondary">
                    CSV取り込み・RAG性能評価
                  </p>
                </div>
              </Link>

              <Link href="/settings">
                <div className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <h3 className="text-xl font-bold mb-2">⚙️ 設定</h3>
                  <p className="text-text-secondary">
                    APIキー、モデル選択、プロンプト管理
                  </p>
                </div>
              </Link>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">新機能（Phase 2）</h2>
            <ul className="space-y-2 text-text-secondary">
              <li>✅ プロンプト管理画面（初期設定リセット機能）</li>
              <li>✅ 検索結果コピー機能</li>
              <li>✅ ノートビューワー（セクション別コピーボタン）</li>
              <li>✅ モデル選択UI</li>
              <li>✅ 増分DB更新（既存ノートスキップ）</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">新機能（Phase 3）</h2>
            <ul className="space-y-2 text-text-secondary">
              <li>✅ 新出単語抽出と正規化辞書管理</li>
              <li>✅ 取り込み後のファイルアクション（削除/移動/保持）</li>
              <li>✅ 正規化辞書管理UI</li>
              <li>✅ LLMによる表記揺れ判定機能</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">新機能（Phase 4）</h2>
            <ul className="space-y-2 text-text-secondary">
              <li>✅ 検索履歴管理（テーブル表示）</li>
              <li>✅ RAG性能評価機能</li>
              <li>✅ Excel/CSVインポート機能</li>
              <li>✅ nDCG等の評価指標実装</li>
              <li>✅ バッチ評価機能</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">新機能（Phase 5）</h2>
            <ul className="space-y-2 text-text-secondary">
              <li>✅ 共通コンポーネント（Loading, Toast）</li>
              <li>✅ UIデザインの統一性確認</li>
              <li>✅ レスポンシブ対応</li>
              <li>✅ エラーハンドリング強化</li>
              <li>✅ 詳細な使用方法ドキュメント</li>
              <li>✅ トラブルシューティングガイド</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">新機能（Phase 6）🎉</h2>
            <ul className="space-y-2 text-text-secondary">
              <li>✅ Vercelデプロイ設定</li>
              <li>✅ Railwayバックエンドデプロイ設定</li>
              <li>✅ CORS環境変数対応</li>
              <li>✅ デプロイ手順書（DEPLOYMENT.md）</li>
              <li>✅ ユーザーマニュアル（USER_MANUAL.md）</li>
              <li>✅ 本番環境テストチェックリスト</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
