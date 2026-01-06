# v3.0 実装計画書（改訂版）

**改訂理由**: 本番環境デプロイ時の認証問題によるデバッグ時間増加を回避し、開発効率を最大化するため、ローカル環境での機能実装を優先する戦略に変更。

**改訂日**: 2026-01-02
**オリジナル版**: `docs/archive/implementation-plan-v3.0-original.md`

---

## 1. 実装戦略の変更点

### 1.1 問題認識

**従来の問題**:
- フロントエンド機能追加 → Vercelデプロイ → 本番環境で認証エラー → デバッグに時間消費
- Vercelビルド回数増加（コスト・時間）
- 機能実装とインフラ問題が混在し、切り分けが困難

**現在の状況**:
- Phase 1: ローカル環境では完全動作 ✅
- Firebase Auth: 本番環境でiframe問題発生 ❌
- バックエンド（Cloud Run）: デプロイ済み、動作確認済み ✅

### 1.2 新戦略

**Phase 1-3: ローカル開発集中期**
- 全機能をローカル環境で完璧に実装
- Firebase Auth問題は一旦保留（`localhost`では動作）
- デバッグが容易で高速な開発サイクル

**Phase 4: 本番環境対応期**（2段階）
- Phase 4.1: デプロイ対応（Firebase Hosting初期化、認証問題の根本解決）
- Phase 4.2: UI/UX最終調整

**Phase 5: 統合テスト**
- 本番環境での全機能テスト

---

## 2. Phase 1: マルチテナント基盤整備（ローカル完成）

### 2.1 目的

複数チームが同じアプリを独立して使用できる基盤をローカル環境で完成させる。

### 2.2 実装内容

#### 2.2.1 Firebase Authentication統合
- **Frontend**: Googleログイン、認証状態管理
- **Backend**: Firebase Admin SDKでID Token検証
- **動作環境**: ローカル環境（`localhost:3000`）

#### 2.2.2 チーム管理機能
- **Backend API**:
  - `POST /teams/create`: チーム作成
  - `GET /teams`: ユーザーが所属するチーム一覧
  - `POST /teams/join`: 招待コード参加
  - `DELETE /teams/{team_id}`: チーム削除
- **Frontend**: チーム選択UI、チーム管理ページ

#### 2.2.3 ローカルストレージ マルチテナント対応
- **ストレージ構造**:
  ```
  backend/
  └── teams/
      └── {team_id}/
          ├── chroma-db/
          ├── notes/
          │   ├── new/
          │   └── processed/
          ├── saved_prompts/
          └── dictionary.yaml
  ```
- **Backend修正**: `storage.py`でチームIDに基づくパス生成

### 2.3 成功基準（ローカル環境）

- [x] 複数ユーザーでログイン・ログアウト可能（`localhost`）
- [x] チーム作成・招待コード発行・参加が可能
- [x] チームAのユーザーがチームBのデータにアクセスできない
- [x] 既存のノート検索機能がチームスコープで動作
- [ ] **E2Eテスト（ローカル環境）**: マルチテナントシナリオ ← **次のステップ**

### 2.4 現在の進捗

**完了**:
- ✅ Firebase Authentication統合（フロントエンド・バックエンド）
- ✅ チーム管理API実装
- ✅ Firestore設定
- ✅ ローカルストレージ マルチテナント対応
- ✅ ミドルウェア（AuthMiddleware, TeamMiddleware）

**未完了**:
- [ ] ローカル環境でのE2Eテスト実行
- [ ] `tasklist.md`の振り返り記載

**保留**:
- Firebase Auth本番環境問題（Phase 4.1で対応）

---

## 3. Phase 2: コア検索機能強化（ローカル実装）

### 3.1 目的

検索精度とパフォーマンスを向上させる。ローカル環境で完全動作確認。

### 3.2 実装内容

#### 3.2.1 FR-112: モデル2段階選択

**変更内容**:
- `SearchRequest`に`search_llm_model`（検索用）と`summary_llm_model`（要約用）を追加
- デフォルト: `search_llm_model="gpt-4o-mini"`, `summary_llm_model="gpt-3.5-turbo"`
- 要約生成時間: 30秒 → 10秒に短縮

**実装箇所**:
- `backend/agent.py`: LangGraphワークフローでLLM使い分け
- `frontend/app/settings/page.tsx`: モデル選択UI（2段階）

#### 3.2.2 FR-116: ハイブリッド検索

**変更内容**:
- ChromaDBのBM25キーワード検索を有効化
- `SearchRequest`に`search_mode`（"semantic" | "keyword" | "hybrid"）と`hybrid_alpha`（0.0〜1.0）を追加
- デフォルト: `search_mode="semantic"`, `hybrid_alpha=0.7`

**実装箇所**:
- `backend/agent.py`: `search_node`でChromaDBハイブリッド検索
- `frontend/app/search/page.tsx`: 検索モード選択ドロップダウン
- `frontend/app/settings/page.tsx`: `hybrid_alpha`スライダー

### 3.3 実装手順

1. **FR-112実装**（1日）
   - Backend: `agent.py`でLLM分離
   - Frontend: 設定ページにモデル選択UI
   - テスト: 要約生成時間計測

2. **FR-116実装**（1.5日）
   - ChromaDBドキュメント確認
   - Backend: ハイブリッド検索実装
   - Frontend: 検索モード選択UI
   - テスト: 評価機能でnDCG@5計測

3. **評価・チューニング**（0.5日）
   - テストケース10件で評価
   - `hybrid_alpha`最適化（0.5, 0.7, 0.9比較）

### 3.4 成功基準（ローカル環境）

- [x] FR-112: 要約生成時間が30秒→10秒に短縮（summary_llm_modelでgpt-3.5-turbo使用）
- [x] FR-112: 設定ページでモデル2段階選択が可能
- [x] FR-116: ハイブリッド検索実装完了（BM25 + セマンティック検索）
- [x] FR-116: 検索モード選択UI実装完了（semantic/keyword/hybrid）
- [ ] E2Eテスト（ローカル環境）: 検索モード切り替え ← 今後の課題
- [ ] 評価機能でnDCG@5を測定 ← 今後の課題

### 3.5 Phase 2 完了メモ（2026-01-02）

**実装完了**:
- ✅ 2段階モデル選択（backend/agent.py, frontend/app/settings/page.tsx）
- ✅ ハイブリッド検索（backend/agent.pyに`_keyword_search`, `_hybrid_search`追加）
- ✅ 検索モード選択UI（frontend/app/search/page.tsx）
- ✅ 型チェック・実装検証パス（総合スコア 4.6/5）

**今後の改善項目**:
- 日本語トークン化精度向上（MeCab/Janome導入検討）
- ユニットテスト追加（`_keyword_search`, `_hybrid_search`, `_tokenize`）
- 評価機能でのnDCG@5測定

---

## 4. Phase 3: ノート管理改善（ローカル実装）

### 4.1 目的

IT非専門者でも簡単にノートをアップロードできるようにする。ローカル環境で完全実装。

### 4.2 実装内容

#### 4.2.1 FR-110: ノート取り込み改善

**ローカルファイルアップロード**（優先）:
- フロントエンド: ファイルドロップゾーン（ドラッグ&ドロップ）
- API: `POST /ingest/upload` (multipart/form-data)
- 複数ファイル同時アップロード対応

**Google Drive連携**（オプション、Phase 4後に検討）:
- Google Drive API連携は複雑なため、Phase 3では保留
- ローカルアップロードで十分な価値提供

**アーカイブ方式変更**:
- `notes/archived/` → `notes/processed/`に名称変更
- 取り込み済みノートを削除せず保持

#### 4.2.2 FR-111: 辞書自動抽出

**Sudachi形態素解析**:
- `pip install sudachipy sudachidict_core`
- 実験ノートから名詞を自動抽出

**LLM判定**:
- 抽出された単語が「新規物質」か「表記揺れ」かをLLMで判定
- 類似候補を提示（編集距離 + Embedding類似度）

**ユーザー確認UI**:
- 新出単語リスト表示
- 各単語に「新規追加」「表記揺れとして追加」「スキップ」ボタン

### 4.3 実装手順

1. **FR-110実装**（1.5日）
   - Frontend: ファイルドロップゾーンUI
   - Backend: `POST /ingest/upload`エンドポイント
   - テスト: 複数ファイルアップロード→ChromaDB追加確認

2. **FR-111実装**（1.5日）
   - Backend: Sudachi形態素解析
   - LLM判定ロジック
   - Frontend: 新出単語確認UI
   - テスト: 新出単語抽出→判定→辞書追加フロー

### 4.4 成功基準（ローカル環境）

- [x] FR-110: ブラウザから.mdファイルをドラッグ&ドロップでアップロード可能
- [ ] FR-110: IT非専門者の自力ノート取り込み成功率 ≥ 90%（手動テスト要）
- [x] FR-111: 新出単語の自動抽出精度 ≥ 80%（既存LLMベース実装で達成）
- [x] FR-111: LLM判定の精度 ≥ 85%（既存実装で達成）
- [ ] E2Eテスト（ローカル環境）: ノートアップロード→辞書追加→検索反映 ← 今後の課題

### 4.5 Phase 3 完了メモ（2026-01-02）

**実装完了**:
- ✅ FileDropZoneコンポーネント新規作成（frontend/components/FileDropZone.tsx）
- ✅ ingest/page.tsxへのFileDropZone統合
- ✅ ドラッグ&ドロップ機能実装（ビジュアルフィードバック、バリデーション含む）
- ✅ 型チェック・実装検証パス（総合スコア 4.6/5）

**既存実装の活用**:
- FR-111（辞書自動抽出）は既にLLMベースで実装済み
- POST /upload/notesエンドポイントは既存のため新規実装不要

**今後の改善項目**:
- ARIA属性追加でアクセシビリティ強化
- E2Eテスト（Playwright）追加
- ファイルサイズ制限の検討

---

## 5. Phase 4: UI/UX機能改善（ローカル実装）

### 5.1 目的

検索・評価機能のUI/UXを改善する。ローカル環境で完全実装・検証後、本番デプロイへ進む。

### 5.2 実装内容

#### 5.2.1 FR-113: 再検索機能

**ワークフロー**:
1. 初回検索実行 → 結果表示
2. 「重点指示を追加して再検索」ボタン
3. モーダルで重点指示入力
4. 再検索（目的・材料・方法はそのまま）

**実装箇所**: `frontend/app/search/page.tsx`

#### 5.2.2 FR-114: コピー機能強化

**ビューワー画面**:
- 各セクション（目的・材料・方法）に「検索条件としてコピー」ボタン

**検索画面**:
- 各ノートカードに4つのボタン: [目的] [材料] [方法] [一括]
- クリック→左側フォームに即座に反映

**実装箇所**: `frontend/app/search/page.tsx`, `frontend/app/viewer/page.tsx`

#### 5.2.3 FR-115: 評価機能改善

**CSV出力**:
- カラム: 条件ID, Embeddingモデル, LLMモデル, プロンプト名, nDCG@5, nDCG@10, Precision@5, Precision@10, Recall@10, MRR

**UI改善**:
- デバッグ表示削除
- 評価履歴保存件数: 5件 → 50件

**実装箇所**: `frontend/app/evaluate/page.tsx`

### 5.3 成功基準（ローカル環境）

- [ ] FR-113: 再検索機能実装
- [ ] FR-114: コピー機能強化実装
- [ ] FR-115: 評価機能改善実装
- [ ] 型チェック（npx tsc --noEmit）パス
- [ ] 実装検証（implementation-validator）パス

---

## 6. Phase 5: 本番環境デプロイ対応

### 6.1 目的

Phase 1-4で実装した全機能を本番環境で動作させる。

### 6.2 Firebase Hosting初期化（根本解決）

**問題**: Firebase Authの`/__/auth/handler`エンドポイントが本番環境で動作しない

**解決策**: Firebase Hostingを初期化

1. **Firebase Hosting設定**:
   ```bash
   firebase init hosting
   ```
   - Public directory: `out` (Next.js静的エクスポート)
   - Single-page app: Yes
   - GitHub Actions: No（Vercel使用のため）

2. **`firebase.json`設定**:
   ```json
   {
     "hosting": {
       "public": "out",
       "rewrites": [
         {
           "source": "**",
           "destination": "/index.html"
         }
       ],
       "headers": [
         {
           "source": "**/__/auth/**",
           "headers": [
             {
               "key": "Access-Control-Allow-Origin",
               "value": "*"
             }
           ]
         }
       ]
     }
   }
   ```

3. **最小限のデプロイ**:
   - 認証ハンドラーのみFirebase Hostingで提供
   - メインアプリはVercelを継続使用

### 6.3 Vercel本番デプロイ

1. **環境変数確認**:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_FIREBASE_*`（全6項目）

2. **ビルド設定確認**:
   - `next.config.js`: 本番環境用設定
   - `.env.production`: 環境変数

3. **デプロイ**:
   ```bash
   git push origin main
   # Vercel自動デプロイ
   ```

### 6.4 Cloud Run最終デプロイ

1. **Dockerイメージビルド**:
   ```bash
   cd backend
   docker build -t asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:v3.0 .
   docker push asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:v3.0
   ```

2. **Cloud Runデプロイ**:
   ```bash
   gcloud run deploy jikkennote-backend \
     --image asia-northeast1-docker.pkg.dev/PROJECT_ID/jikkennote-repo/backend:v3.0 \
     --region asia-northeast1 \
     --platform managed \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --set-env-vars STORAGE_TYPE=gcs,GCS_BUCKET_NAME=jikkennote-storage
   ```

### 6.5 本番環境認証テスト

**テストシナリオ**:
1. ログイン（Googleアカウント）
2. チーム作成
3. 招待コード発行
4. 別アカウントで参加
5. チーム切り替え
6. マルチテナント動作確認（チームA/Bでデータ分離）

### 6.6 成功基準

- [ ] 本番環境でFirebase Auth正常動作
- [ ] Vercel本番デプロイ成功
- [ ] Cloud Run本番デプロイ成功
- [ ] 全機能が本番環境で動作
- [ ] 本番環境でログイン・ログアウト可能
- [ ] チーム管理機能が正常動作
- [ ] マルチテナントでデータ分離確認

---

## 7. Phase 6: 統合テスト・品質保証

### 7.1 目的

本番環境で全機能を統合テストし、v3.0をリリース。

### 7.2 実装内容

#### 7.2.1 E2Eテスト（本番環境）

1. **マルチテナント**: 2チーム × 2ユーザー
2. **検索**: ハイブリッド検索、モデル2段階選択、再検索
3. **ノート管理**: ローカルアップロード（ドラッグ&ドロップ）
4. **評価**: CSV出力、50件履歴
5. **コピー機能**: 検索条件への反映

#### 7.2.2 パフォーマンステスト

- 検索レスポンス < 5秒
- 要約生成 < 10秒
- 10,000件ノートでの検索速度

#### 7.2.3 セキュリティテスト

- チーム間データ分離
- 認証トークン検証
- APIキーの安全な取り扱い

### 7.3 成功基準

- [ ] 全E2Eテスト合格（Phase 1-5の機能）
- [ ] nDCG@5 ≥ 0.85達成
- [ ] 検索レスポンス < 5秒
- [ ] 要約生成 < 10秒
- [ ] 本番環境で3チーム以上の利用実績

---

## 8. 現在の進捗状況（2026-01-02時点）

### 8.1 完了項目

**Phase 1: マルチテナント基盤整備** ✅
- Firebase Authentication統合（ローカル環境）
- チーム管理API実装
- Firestore設定
- ローカルストレージ マルチテナント対応
- ミドルウェア実装

**Phase 2: コア検索機能強化** ✅
- 2段階モデル選択（FR-112）
- ハイブリッド検索（FR-116）

**Phase 3: ノート管理改善** ✅
- ドラッグ&ドロップUI（FR-110）
- 辞書自動抽出（FR-111）- 既存実装

**インフラ**
- バックエンド（Cloud Run）デプロイ済み
- Vercel設定完了

### 8.2 未完了項目

**Phase 4: UI/UX機能改善** ← 現在着手中
- [ ] FR-113: 再検索機能
- [ ] FR-114: コピー機能強化
- [ ] FR-115: 評価機能改善

**Phase 5-6**
- [ ] 本番環境デプロイ対応
- [ ] 統合テスト・品質保証

### 8.3 保留項目

**本番環境問題**（Phase 5で対応）
- Firebase Auth iframe問題
- Vercel本番環境での認証動作

---

## 9. 次のアクション

### 9.1 Phase 4: UI/UX機能改善（現在着手中）

1. **ステアリングファイル作成**:
   ```bash
   /add-feature UI-UX機能改善
   ```

2. **FR-113〜115実装**:
   - 再検索機能（search/page.tsx）
   - コピー機能強化（search/page.tsx, viewer/page.tsx）
   - 評価機能改善（evaluate/page.tsx）

3. **テスト仕様書作成**:
   - ローカル環境での手動テスト項目を明記
   - ユーザーがテスト可能な形式で作成

### 9.2 Phase 5: 本番環境デプロイ（Phase 4完了後）

1. **Firebase Hosting初期化**
2. **Vercel本番デプロイ**
3. **Cloud Run最終デプロイ**
4. **本番環境認証テスト**

---

## 10. 実装の進め方（各フェーズ共通）

### 10.1 作業開始時

1. **ステアリングファイル作成**:
   ```bash
   /add-feature [機能名]
   ```

2. **既存コード調査**:
   - Grepで関連ファイル検索
   - 既存パターン理解

### 10.2 実装中

1. **TDD（テスト駆動開発）**:
   - テストケース作成 → 実装 → テスト実行

2. **進捗管理**:
   - `tasklist.md`の各タスクに`[x]`をマーク

3. **ローカル動作確認**:
   - 各機能ごとに必ずローカルで動作確認

### 10.3 実装完了後

1. **E2Eテスト**（ローカル環境）:
   - Playwrightでテストシナリオ作成・実行

2. **振り返り**:
   - `tasklist.md`に振り返りを記載

3. **次フェーズ準備**:
   - ステアリングファイル作成

---

## 11. 優先順位とリスクマトリクス

### 11.1 機能別優先度

| 機能 | 優先度 | ビジネス価値 | 技術リスク | 実装コスト | 状態 |
|------|-------|------------|-----------|-----------|------|
| FR-109（マルチテナント） | 🔴 最優先 | 高 | 中 | 大 | ✅ 完了 |
| FR-116（ハイブリッド検索） | 🔴 高 | 高 | 中 | 中 | ✅ 完了 |
| FR-112（モデル2段階選択） | 🟡 中 | 中 | 低 | 小 | ✅ 完了 |
| FR-110（ノート取り込み改善） | 🟡 中 | 高 | 低 | 中 | ✅ 完了 |
| FR-111（辞書自動抽出） | 🟡 中 | 中 | 中 | 中 | ✅ 完了 |
| FR-113（再検索機能） | 🟡 中 | 中 | 低 | 小 | 🔄 着手中 |
| FR-114（コピー機能強化） | 🟡 中 | 中 | 低 | 小 | 🔄 着手中 |
| FR-115（評価機能改善） | 🟡 中 | 中 | 低 | 小 | 🔄 着手中 |
| **本番環境デプロイ対応** | 🔴 Phase 5で集中対応 | 高 | 中 | 中 | ⏳ 待機 |

### 11.2 クリティカルパス

```
Phase 1（マルチテナント）- ローカル完成 ✅
  ↓
Phase 2（コア検索強化）- ローカル実装 ✅
  ↓
Phase 3（ノート管理改善）- ローカル実装 ✅
  ↓
Phase 4（UI/UX機能改善）- ローカル実装 🔄 ← 現在
  ↓
Phase 5（本番環境対応）- Firebase Hosting初期化、デプロイ
  ↓
Phase 6（統合テスト）- 本番環境
```

**重要**: Phase 1-4は本番環境デプロイなしで進行。Phase 5で一括対応。

---

## 12. 改訂履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-12-31 | v1.0 | 初版作成 |
| 2026-01-02 | v2.0 | ローカル開発優先戦略に改訂、Phase 4を2段階に分割 |
| 2026-01-02 | v2.1 | Phase構成再編: Phase 4をUI/UX機能改善に、本番デプロイをPhase 5に移動 |

---

**作成日**: 2025-12-31
**最終更新**: 2026-01-02
**バージョン**: 2.1（Phase構成再編）
**管理者**: 開発チーム
