"""
LangGraph Agent for Experiment Notes Search
実験ノート検索用のLangGraphエージェント
プロンプトとモデルを動的に設定可能
"""
import operator
import json
import re
import time
from typing import TypedDict, List, Annotated, Optional

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, BaseMessage
import cohere

from config import config
from utils import load_master_dict, normalize_text
from prompts import get_default_prompt
from synonym_dictionary import get_synonym_dictionary
from chroma_sync import (
    get_chroma_vectorstore,
    get_team_chroma_vectorstore,
    get_team_multi_collection_vectorstores
)


# --- State定義 ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

    # 入力データ
    input_purpose: str
    input_materials: str
    input_methods: str

    # 処理データ
    normalized_materials: str
    user_focus_instruction: str
    search_query: str

    # 検索結果
    retrieved_docs: List[str]  # UI表示用の最終選抜（通常: Top 3、評価モード: Top 10）

    iteration: int
    evaluation_mode: bool  # 評価モードフラグ（True: 比較省略、Top10返却）

    # v3.0.1: 検索モード設定
    search_mode: str  # "semantic" | "keyword" | "hybrid"
    hybrid_alpha: float  # ハイブリッド検索のセマンティック重み（0.0-1.0）

    # v3.1.0: 3軸分離検索設定
    multi_axis_enabled: bool  # 3軸検索の有効/無効
    focus_classification: str  # 重点指示の分類結果 ("materials" | "methods" | "both" | "none")
    fusion_method: str  # スコア統合方式 ("rrf" | "linear")
    axis_weights: dict  # 各軸のウエイト {"material": 0.3, "method": 0.4, "combined": 0.3}
    rerank_position: str  # リランク位置 ("per_axis" | "after_fusion")
    rerank_enabled: bool  # リランキングの有効/無効

    # 3軸検索結果
    material_query: str  # 材料軸クエリ
    method_query: str  # 方法軸クエリ
    combined_query: str  # 総合軸クエリ
    material_axis_results: List[tuple]  # 材料軸の検索結果 [(doc, score), ...]
    method_axis_results: List[tuple]  # 方法軸の検索結果 [(doc, score), ...]
    combined_axis_results: List[tuple]  # 総合軸の検索結果 [(doc, score), ...]


class SearchAgent:
    """検索エージェント（プロンプト・モデルを動的設定可能）"""

    def __init__(
        self,
        openai_api_key: str,
        cohere_api_key: str,
        embedding_model: str = None,
        llm_model: str = None,  # 後方互換性のため維持
        search_llm_model: str = None,  # v3.0: 検索・判定用LLM
        summary_llm_model: str = None,  # v3.0: 要約生成用LLM
        search_mode: str = None,  # v3.0.1: 検索モード
        hybrid_alpha: float = None,  # v3.0.1: ハイブリッド検索の重み
        prompts: dict = None,
        team_id: str = None,  # v3.0: マルチテナント対応
        # v3.1.0: 3軸分離検索設定
        multi_axis_enabled: bool = None,
        fusion_method: str = None,
        axis_weights: dict = None,
        rerank_position: str = None,
        rerank_enabled: bool = None
    ):
        """
        Args:
            openai_api_key: OpenAI APIキー
            cohere_api_key: Cohere APIキー
            embedding_model: Embeddingモデル名
            llm_model: LLMモデル名（後方互換性、非推奨）
            search_llm_model: 検索・判定用LLMモデル名（v3.0）
            summary_llm_model: 要約生成用LLMモデル名（v3.0）
            search_mode: 検索モード（v3.0.1）"semantic" | "keyword" | "hybrid"
            hybrid_alpha: ハイブリッド検索のセマンティック重み（v3.0.1）0.0-1.0
            prompts: カスタムプロンプト辞書
            team_id: チームID（v3.0）
            multi_axis_enabled: 3軸検索の有効/無効（v3.1.0）
            fusion_method: スコア統合方式（v3.1.0）"rrf" | "linear"
            axis_weights: 各軸のウエイト（v3.1.0）{"material": 0.3, "method": 0.4, "combined": 0.3}
            rerank_position: リランク位置（v3.1.0）"per_axis" | "after_fusion"
            rerank_enabled: リランキングの有効/無効（v3.1.0）
        """
        self.openai_api_key = openai_api_key
        self.cohere_api_key = cohere_api_key
        self.team_id = team_id

        # モデル設定（v3.0: 2段階選択対応）
        self.embedding_model = embedding_model or config.DEFAULT_EMBEDDING_MODEL
        # 後方互換性: llm_modelが指定されていればそれを使用
        self.search_llm_model = search_llm_model or llm_model or config.DEFAULT_SEARCH_LLM_MODEL
        self.summary_llm_model = summary_llm_model or llm_model or config.DEFAULT_SUMMARY_LLM_MODEL

        # 検索モード設定（v3.0.1）
        self.search_mode = search_mode or config.DEFAULT_SEARCH_MODE
        self.hybrid_alpha = hybrid_alpha if hybrid_alpha is not None else config.DEFAULT_HYBRID_ALPHA

        # 3軸分離検索設定（v3.1.0）
        self.multi_axis_enabled = multi_axis_enabled if multi_axis_enabled is not None else config.MULTI_AXIS_ENABLED
        self.fusion_method = fusion_method or config.FUSION_METHOD
        self.axis_weights = axis_weights or config.AXIS_WEIGHTS
        self.rerank_position = rerank_position or config.RERANK_POSITION
        self.rerank_enabled = rerank_enabled if rerank_enabled is not None else config.RERANK_ENABLED

        # プロンプト設定（カスタムまたはデフォルト）
        self.prompts = prompts or {}

        # Cohere クライアント
        self.cohere_client = cohere.Client(cohere_api_key)

        # 正規化辞書
        self.norm_map, _ = load_master_dict()

        # 同義語辞書（v3.2.1: クエリ展開用）
        self.synonym_dict = get_synonym_dictionary(team_id)

        # Embedding関数
        self.embedding_function = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=self.openai_api_key
        )

        # Vector Store（v3.2.0: 2コレクション対応に変更、v3.2.2: 常に2コレクション取得に変更）
        if team_id:
            # チームモード: 常に2コレクションを取得（3軸検索の有効/無効に関わらず）
            # これにより、3軸検索が無効でもcombinedコレクションで検索可能
            self.vectorstores = get_team_multi_collection_vectorstores(
                team_id=team_id,
                embeddings=self.embedding_function,
                embedding_model=self.embedding_model
            )
            # vectorstoreはcombinedを参照（単一クエリ検索時に使用）
            self.vectorstore = self.vectorstores["combined"]
            if self.multi_axis_enabled:
                print(f"2コレクションモード（3軸検索有効）: materials_methods, combined vectorstores初期化完了")
            else:
                print(f"2コレクションモード（単一クエリ検索）: combinedコレクションを使用")
        else:
            # 後方互換性: team_idがない場合はグローバルを使用
            self.vectorstores = None
            self.vectorstore = get_chroma_vectorstore(
                self.embedding_function,
                embedding_model=self.embedding_model
            )

        # LLM（v3.0: 2段階選択対応）
        # temperatureをサポートしないモデルの判定
        def supports_temperature(model_name: str) -> bool:
            """temperatureパラメータをサポートするモデルかどうか判定"""
            no_temp_models = ['o1', 'o1-mini', 'o1-preview', 'o3-mini', 'gpt-5-mini', 'gpt-5-nano']
            return not any(m in model_name for m in no_temp_models)

        # 検索・判定用LLM（正規化、クエリ生成に使用）
        search_llm_kwargs = {
            "model": self.search_llm_model,
            "api_key": self.openai_api_key,
            "seed": 42  # v3.2.4: 再現性のためseedを固定
        }
        if supports_temperature(self.search_llm_model):
            search_llm_kwargs["temperature"] = 0
        self.search_llm = ChatOpenAI(**search_llm_kwargs)

        # 要約生成用LLM（比較ノードに使用）
        summary_llm_kwargs = {
            "model": self.summary_llm_model,
            "api_key": self.openai_api_key,
            "seed": 42  # v3.2.4: 再現性のためseedを固定
        }
        if supports_temperature(self.summary_llm_model):
            summary_llm_kwargs["temperature"] = 0
        self.summary_llm = ChatOpenAI(**summary_llm_kwargs)
        # 後方互換性: self.llmはsearch_llmを参照
        self.llm = self.search_llm

        # グラフを構築
        self.graph = self._build_graph()

    def _get_prompt(self, prompt_type: str) -> str:
        """プロンプトを取得（カスタムまたはデフォルト）

        カスタムプロンプトが空文字の場合はデフォルトを使用する
        """
        custom = self.prompts.get(prompt_type)
        # カスタムプロンプトが存在し、空文字でない場合のみ使用
        if custom and custom.strip():
            return custom
        return get_default_prompt(prompt_type)

    def _normalize_node(self, state: AgentState):
        """正規化ノード"""
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)

        if evaluation_mode:
            print("\n" + "="*80)
            print("🔬 [評価モード] 性能評価実行中")
            print("="*80)
            print("\n--- 🚀 [1/3] 正規化 & JSON解析 ---")
        else:
            print("\n--- 🚀 [1/4] 正規化 & JSON解析 ---")

        updates = {}
        messages = state.get("messages", [])

        # JSON解析
        if messages:
            last_msg = messages[-1]
            content = ""
            if hasattr(last_msg, "content"):
                content = last_msg.content
            elif isinstance(last_msg, dict):
                content = last_msg.get("content", "")
            else:
                content = str(last_msg)

            if content.strip().startswith("{"):
                try:
                    data = json.loads(content)

                    if data.get("type") == "initial_search":
                        updates["input_purpose"] = data.get("purpose", "")
                        updates["input_materials"] = data.get("materials", "")
                        updates["input_methods"] = data.get("methods", "")

                        # v3.2.4: ユーザーが重点指示を入力していればそれを使用、
                        # 空の場合のみデフォルト指示を適用
                        user_instruction = data.get("instruction", "").strip()
                        if user_instruction:
                            updates["user_focus_instruction"] = user_instruction
                            print(f"  📌 重点指示（ユーザー指定）: {user_instruction[:50]}...")
                        else:
                            updates["user_focus_instruction"] = (
                                "使用されている材料(化学物質、容量）と、方法（化学物質、容量、手順）の記述が"
                                "類似している実験ノートを最優先して検索してください。"
                            )
                            print(f"  📌 重点指示（デフォルト適用）")

                    elif data.get("type") == "refinement":
                        updates["user_focus_instruction"] = data.get("instruction", "")
                        updates["input_purpose"] = data.get("purpose", "")
                        updates["input_materials"] = data.get("materials", "")
                        updates["input_methods"] = data.get("methods", "")

                except json.JSONDecodeError:
                    print("  > ⚠️ JSON Decode Error")

        # 正規化処理
        raw_materials = updates.get("input_materials", state.get("input_materials", ""))
        normalized_parts = []

        if raw_materials:
            lines = raw_materials.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = re.split(r'[:：]', line, 1)

                if len(parts) == 2:
                    left_part = parts[0]
                    amount_part = parts[1]
                    raw_name = re.sub(r'^[-・\s]*[①-⑨0-9.]*\s*', '', left_part).strip()
                    norm_name = normalize_text(raw_name, self.norm_map)
                    normalized_parts.append(f"- {norm_name}: {amount_part.strip()}")
                else:
                    clean_line = re.sub(r'^[-・\s]*[①-⑨0-9.]*\s*', '', line).strip()
                    norm_name = normalize_text(clean_line, self.norm_map)
                    normalized_parts.append(norm_name)

        normalized_str = "\n".join(normalized_parts) if normalized_parts else raw_materials
        updates["normalized_materials"] = normalized_str

        # 正規化完了をサマリ表示（検索/評価モード共通）
        material_count = len(normalized_parts) if normalized_parts else 0
        print(f"  📝 正規化完了: {material_count}材料")

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")
        return updates

    def _generate_query_node(self, state: AgentState):
        """クエリ生成ノード（単一クエリ検索時）

        v3.2.3: combined_query_generationプロンプトを使用するように変更
        3軸分離検索と同じ「総合軸クエリ生成」プロンプトを使うことで、
        保存済みのカスタムプロンプトが有効になる
        """
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)

        if evaluation_mode:
            print("\n--- 🧠 [2/3] 総合軸クエリ生成（単一クエリモード）---")
        else:
            print("--- 🧠 [2/4] 総合軸クエリ生成（単一クエリモード）---")

        instruction = state.get('user_focus_instruction', '特になし')

        # v3.2.3: combined_query_generationプロンプトを使用
        # これにより、3軸分離検索と同じ「総合軸クエリ生成」のカスタムプロンプトが適用される
        prompt_template = self._get_prompt("combined_query_generation")

        # プロンプトに変数を埋め込む（Noneの場合は空文字列にフォールバック）
        prompt = prompt_template.format(
            input_purpose=state.get('input_purpose') or '',
            normalized_materials=state.get('normalized_materials') or '',
            input_methods=state.get('input_methods') or '',
            user_focus_instruction=instruction
        )

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        # JSONを抽出（マークダウンブロック、余計なテキストに対応）
        def extract_json(text: str) -> str:
            """テキストからJSON部分を抽出"""
            import re
            # ```json ... ``` ブロックを探す
            json_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if json_block:
                return json_block.group(1).strip()
            # { ... } を探す
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json_match.group(0)
            return text

        content = extract_json(content)

        try:
            data = json.loads(content)
            queries = data.get("queries", [])
            if not queries:
                raise ValueError("Empty queries")

            combined_query = " ".join(queries)

            # クエリ全体を表示（検索/評価モード共通）
            print(f"\n  🔍 [生成されたクエリ] ({len(queries)}個)")
            for i, q in enumerate(queries, 1):
                print(f"    {i}. {q}")
            print(f"\n  📎 [統合検索クエリ]\n    {combined_query}")

        except Exception as e:
            print(f"  > ⚠️ Query Parse Error: {e}")
            print(f"  > Raw response: {response.content[:200]}...")
            # フォールバック: 入力をそのままクエリとして使用
            combined_query = f"{state.get('input_purpose') or ''} {state.get('normalized_materials') or ''} {instruction}"
            print(f"  > Fallback query: {combined_query[:100]}...")

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")
        return {"search_query": combined_query}

    def _expand_query_with_synonyms(self, query: str) -> List[str]:
        """同義語辞書を使ってクエリを展開（v3.2.1）

        Args:
            query: 元のクエリ

        Returns:
            展開されたクエリのリスト（元のクエリを含む）
        """
        return self.synonym_dict.expand_query(query)

    def _search_with_synonym_expansion(
        self,
        vectorstore,
        query: str,
        search_mode: str,
        hybrid_alpha: float,
        k: int = 30
    ) -> List[tuple]:
        """同義語展開を適用した検索（v3.2.1）

        複数のクエリで検索し、結果をマージする。

        Args:
            vectorstore: 検索対象のvectorstore
            query: 検索クエリ
            search_mode: 検索モード
            hybrid_alpha: ハイブリッド検索の重み
            k: 返却する上位件数

        Returns:
            List of (doc, score) tuples
        """
        # クエリを同義語展開
        expanded_queries = self._expand_query_with_synonyms(query)

        if len(expanded_queries) > 1:
            print(f"    > 同義語展開: {len(expanded_queries)}クエリに展開")

        # 各クエリで検索し、結果をマージ
        all_results = {}  # {note_id: (doc, max_score)}

        for eq in expanded_queries:
            # 検索モードに応じた検索実行
            if search_mode == "keyword":
                results = self._keyword_search_on_vectorstore(vectorstore, eq, k=k)
            elif search_mode == "hybrid":
                results = self._hybrid_search_on_vectorstore(vectorstore, eq, alpha=hybrid_alpha, k=k)
            else:
                # セマンティック検索
                docs = vectorstore.similarity_search_with_relevance_scores(eq, k=k)
                results = [(doc, score) for doc, score in docs]

            # 結果をマージ（同じノートは最高スコアを採用）
            for doc, score in results:
                note_id = doc.metadata.get('note_id', doc.metadata.get('source', doc.page_content[:50]))
                if note_id not in all_results or score > all_results[note_id][1]:
                    all_results[note_id] = (doc, score)

        # スコア降順でソート
        merged_results = list(all_results.values())
        merged_results.sort(key=lambda x: x[1], reverse=True)
        return merged_results[:k]

    def _keyword_search(self, query: str, k: int = 30) -> List[tuple]:
        """キーワード検索（BM25ベース）

        Args:
            query: 検索クエリ
            k: 返却する上位件数

        Returns:
            List of (doc, score) tuples sorted by score descending
        """
        import math
        from collections import Counter

        # ChromaDBから全ドキュメントを取得
        collection = self.vectorstore._collection
        all_docs = collection.get(include=["documents", "metadatas"])

        if not all_docs["documents"]:
            return []

        documents = all_docs["documents"]
        metadatas = all_docs["metadatas"]

        # クエリをトークン化（簡易的な日本語対応）
        query_tokens = self._tokenize(query)

        # BM25パラメータ
        k1 = 1.5
        b = 0.75

        # 文書長の平均を計算
        doc_lengths = [len(self._tokenize(doc)) for doc in documents]
        avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1

        # IDF計算
        N = len(documents)
        idf = {}
        for token in query_tokens:
            df = sum(1 for doc in documents if token in doc.lower())
            idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)

        # BM25スコア計算
        scores = []
        for i, doc in enumerate(documents):
            doc_tokens = self._tokenize(doc)
            doc_len = len(doc_tokens)
            term_freq = Counter(doc_tokens)

            score = 0
            for token in query_tokens:
                if token in term_freq:
                    tf = term_freq[token]
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * doc_len / avgdl)
                    score += idf.get(token, 0) * numerator / denominator

            # Document objectを作成
            from langchain_core.documents import Document
            doc_obj = Document(
                page_content=doc,
                metadata=metadatas[i] if metadatas else {}
            )
            scores.append((doc_obj, score))

        # スコア降順でソート
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def _tokenize(self, text: str) -> List[str]:
        """テキストをトークン化（簡易的な日本語対応）

        Args:
            text: 入力テキスト

        Returns:
            トークンのリスト
        """
        # 小文字化
        text = text.lower()

        # 日本語と英語を分離してトークン化
        # 簡易的に空白、句読点、特殊文字で分割
        import re
        # 日本語の場合は文字単位で2-gramを生成
        tokens = []

        # 英数字の単語を抽出
        words = re.findall(r'[a-z0-9]+', text)
        tokens.extend(words)

        # 日本語部分を抽出（ひらがな、カタカナ、漢字）
        japanese_text = re.sub(r'[a-z0-9\s\.,!?:;()\[\]{}\-_]+', '', text)
        # 2-gramで分割（より精度の高いマッチングのため）
        for i in range(len(japanese_text) - 1):
            tokens.append(japanese_text[i:i+2])
        # 1-gramも追加
        tokens.extend(list(japanese_text))

        return tokens

    def _hybrid_search(self, query: str, alpha: float, k: int = 30) -> List[tuple]:
        """ハイブリッド検索（セマンティック + キーワード）

        Args:
            query: 検索クエリ
            alpha: セマンティック検索の重み（0.0-1.0）
            k: 返却する上位件数

        Returns:
            List of (doc, score) tuples sorted by combined score descending
        """
        # セマンティック検索
        semantic_results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

        # キーワード検索
        keyword_results = self._keyword_search(query, k=k)

        # スコアの正規化と統合
        doc_scores = {}

        # セマンティック検索結果をスコア付け
        if semantic_results:
            max_semantic = max(score for _, score in semantic_results)
            min_semantic = min(score for _, score in semantic_results)
            range_semantic = max_semantic - min_semantic if max_semantic != min_semantic else 1

            for doc, score in semantic_results:
                # 0-1に正規化
                normalized_score = (score - min_semantic) / range_semantic if range_semantic > 0 else 0.5
                doc_id = doc.metadata.get('source', doc.page_content[:50])
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'semantic': 0, 'keyword': 0}
                doc_scores[doc_id]['semantic'] = normalized_score

        # キーワード検索結果をスコア付け
        if keyword_results:
            max_keyword = max(score for _, score in keyword_results)
            min_keyword = min(score for _, score in keyword_results)
            range_keyword = max_keyword - min_keyword if max_keyword != min_keyword else 1

            for doc, score in keyword_results:
                # 0-1に正規化
                normalized_score = (score - min_keyword) / range_keyword if range_keyword > 0 else 0.5
                doc_id = doc.metadata.get('source', doc.page_content[:50])
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'semantic': 0, 'keyword': 0}
                doc_scores[doc_id]['keyword'] = normalized_score

        # 統合スコア計算
        combined_results = []
        for doc_id, scores in doc_scores.items():
            combined_score = alpha * scores['semantic'] + (1 - alpha) * scores['keyword']
            combined_results.append((scores['doc'], combined_score))

        # スコア降順でソート
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results[:k]

    def _search_node(self, state: AgentState):
        """検索 & Cohereリランキングノード（v3.0.1: 検索モード対応）"""
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)

        # 検索モードを取得（stateから、またはインスタンス変数から）
        search_mode = state.get("search_mode", self.search_mode)
        hybrid_alpha = state.get("hybrid_alpha", self.hybrid_alpha)

        mode_label = {
            "semantic": "セマンティック",
            "keyword": "キーワード（BM25）",
            "hybrid": f"ハイブリッド（α={hybrid_alpha:.2f}）"
        }.get(search_mode, "セマンティック")

        if evaluation_mode:
            print(f"--- 🔍 [3/3] {mode_label}検索 & Cohereリランキング実行（評価モード）---")
        else:
            print(f"--- 🔍 [3/4] {mode_label}検索 & Cohereリランキング実行 ---")

        query = state["search_query"]

        try:
            # ChromaDBのドキュメント数を確認
            collection = self.vectorstore._collection
            doc_count = collection.count()
            print(f"  > ChromaDB Collection: {doc_count} documents")
            print(f"  > Search Mode: {search_mode}")

            # v3.2.1: 同義語展開を適用した検索
            search_results = self._search_with_synonym_expansion(
                vectorstore=self.vectorstore,
                query=query,
                search_mode=search_mode,
                hybrid_alpha=hybrid_alpha,
                k=config.VECTOR_SEARCH_K
            )
            candidates = [doc for doc, score in search_results]
            print(f"  > Retrieved {len(candidates)} candidates (with synonym expansion).")

            if not candidates:
                print("  > No candidates found.")
                print(f"  ⏱️ Execution Time: {time.time() - start_time:.4f} sec")
                return {"retrieved_docs": [], "iteration": state.get("iteration", 0) + 1}

            # Cohere Rerank
            documents_content = [doc.page_content for doc in candidates]

            rerank_results = self.cohere_client.rerank(
                model=config.DEFAULT_RERANK_MODEL,
                query=query,
                documents=documents_content,
                top_n=config.RERANK_TOP_N
            )

            if evaluation_mode:
                print(f"\n  📊 [リランキング結果] Top {config.RERANK_TOP_N} 件")
                print(f"  " + "="*76)
            else:
                print(f"\n  📊 [Console Log] Top {config.RERANK_TOP_N} Cohere Rerank Results:")
                print(f"  --------------------------------------------------")

            docs_for_ui = []
            seen_source_ids = set()  # 重複除去用

            # 評価モードなら全件（Top10）、通常モードなら上位3件のみ
            display_limit = config.RERANK_TOP_N if evaluation_mode else config.UI_DISPLAY_TOP_N

            rank_counter = 0  # 重複除去後のランク
            for i, result in enumerate(rerank_results.results):
                original_doc = candidates[result.index]
                source_id = original_doc.metadata.get('source', 'unknown')
                score = result.relevance_score
                snippet = original_doc.page_content[:50].replace('\n', ' ')

                # 重複チェック: 既に追加済みのノートIDはスキップ
                if source_id in seen_source_ids:
                    continue
                seen_source_ids.add(source_id)
                rank_counter += 1

                if evaluation_mode:
                    print(f"  Rank {rank_counter:2d} | Score: {score:.6f} | ノートID: {source_id}")
                else:
                    print(f"  Rank {rank_counter:2d} | Score: {score:.4f} | ID: {source_id} | {snippet}...")

                # 評価モードなら全件、通常モードなら上位3件のみ保存
                if rank_counter <= display_limit:
                    docs_for_ui.append(f"【実験ノートID: {source_id}】\n{original_doc.page_content}")

            if evaluation_mode:
                print(f"  " + "="*76)
                print(f"  ✅ 評価用に上位 {len(docs_for_ui)} 件を返却します。")
            else:
                print(f"  --------------------------------------------------")
                print(f"  > UI向けに上位 {len(docs_for_ui)} 件を選択しました。")

        except Exception as e:
            print(f"  > ⚠️ Search/Rerank Error: {e}")
            docs_for_ui = []

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")

        # 評価モード時は終了メッセージを表示
        if evaluation_mode:
            print("\n" + "="*80)
            print("✅ 評価モード終了 - 比較ノードをスキップして結果を返却します")
            print("="*80 + "\n")

        return {
            "retrieved_docs": docs_for_ui,
            "iteration": state.get("iteration", 0) + 1
        }

    # ===========================================
    # v3.1.0: 3軸分離検索用ノード
    # ===========================================

    def _extract_json_from_response(self, text: str) -> str:
        """LLMレスポンスからJSON部分を抽出するヘルパー"""
        # ```json ... ``` ブロックを探す
        json_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_block:
            return json_block.group(1).strip()
        # { ... } を探す
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)
        return text

    def _classify_focus_node(self, state: AgentState):
        """重点指示分類ノード（v3.1.0）

        重点指示をLLMで解析し、材料/方法/両方/なしを判定する
        """
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)

        if evaluation_mode:
            print("\n--- 🏷️ [2/6] 重点指示分類 ---")
        else:
            print("--- 🏷️ [2/7] 重点指示分類 ---")

        instruction = state.get('user_focus_instruction', '')

        # 重点指示が空の場合は"none"
        if not instruction or instruction.strip() in ['', '特になし', 'なし']:
            print(f"  > 重点指示が空のため、分類をスキップ: none")
            elapsed_time = time.time() - start_time
            print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")
            return {"focus_classification": "none"}

        # LLMで分類
        prompt_template = self._get_prompt("focus_classification")
        prompt = prompt_template.format(user_focus_instruction=instruction)

        try:
            response = self.search_llm.invoke(prompt)
            content = self._extract_json_from_response(response.content.strip())
            data = json.loads(content)
            classification = data.get("classification", "both")
            reason = data.get("reason", "")

            # 有効な値かチェック
            if classification not in ["materials", "methods", "both", "none"]:
                classification = "both"

            print(f"  > 分類結果: {classification}")
            print(f"  > 理由: {reason}")

        except Exception as e:
            print(f"  > ⚠️ 分類エラー: {e}")
            print(f"  > フォールバック: both")
            classification = "both"

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")
        return {"focus_classification": classification}

    def _generate_multi_axis_queries_node(self, state: AgentState):
        """3軸クエリ生成ノード（v3.1.0）

        材料軸、方法軸、総合軸のクエリを生成する
        """
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)

        if evaluation_mode:
            print("\n--- 🧠 [3/6] 3軸クエリ生成 ---")
        else:
            print("--- 🧠 [3/7] 3軸クエリ生成 ---")

        focus_class = state.get('focus_classification', 'none')
        instruction = state.get('user_focus_instruction', '')

        # 材料軸に重点指示を適用するかどうか
        apply_focus_to_material = focus_class in ["materials", "both"]
        # 方法軸に重点指示を適用するかどうか
        apply_focus_to_method = focus_class in ["methods", "both"]

        material_instruction = instruction if apply_focus_to_material else ""
        method_instruction = instruction if apply_focus_to_method else ""

        queries = {}

        # 材料軸クエリ生成
        try:
            print("  📦 材料軸クエリを生成中...")
            material_prompt = self._get_prompt("material_query_generation").format(
                normalized_materials=state.get('normalized_materials', ''),
                user_focus_instruction=material_instruction or "特になし"
            )
            response = self.search_llm.invoke(material_prompt)
            content = self._extract_json_from_response(response.content.strip())
            data = json.loads(content)
            queries["material"] = data.get("query", state.get('normalized_materials', ''))
            print(f"    > {queries['material'][:80]}...")
        except Exception as e:
            print(f"    > ⚠️ 材料軸クエリ生成エラー: {e}")
            queries["material"] = state.get('normalized_materials', '')

        # 方法軸クエリ生成
        try:
            print("  🔧 方法軸クエリを生成中...")
            # v3.2.0: デバッグログ追加
            materials_for_method = state.get('normalized_materials', '')
            methods_input = state.get('input_methods', '')
            print(f"    [DEBUG] 材料情報: {materials_for_method[:100]}..." if materials_for_method else "    [DEBUG] 材料情報: なし")
            print(f"    [DEBUG] 方法入力: {methods_input[:100]}..." if methods_input else "    [DEBUG] 方法入力: なし")

            method_prompt = self._get_prompt("method_query_generation").format(
                normalized_materials=materials_for_method,  # v3.2.0: 材料情報を追加
                input_methods=methods_input,
                user_focus_instruction=method_instruction or "特になし"
            )
            print(f"    [DEBUG] プロンプト長: {len(method_prompt)}文字")

            response = self.search_llm.invoke(method_prompt)
            content = self._extract_json_from_response(response.content.strip())
            print(f"    [DEBUG] LLM応答: {content[:200]}...")
            data = json.loads(content)
            queries["method"] = data.get("query", state.get('input_methods', ''))
            print(f"    > {queries['method'][:80]}...")
        except Exception as e:
            print(f"    > ⚠️ 方法軸クエリ生成エラー: {e}")
            import traceback
            traceback.print_exc()
            queries["method"] = state.get('input_methods', '')

        # 総合軸クエリ生成
        try:
            print("  🎯 総合軸クエリを生成中...")
            combined_prompt = self._get_prompt("combined_query_generation").format(
                input_purpose=state.get('input_purpose', ''),
                normalized_materials=state.get('normalized_materials', ''),
                input_methods=state.get('input_methods', ''),
                user_focus_instruction=instruction or "特になし"
            )
            response = self.search_llm.invoke(combined_prompt)
            content = self._extract_json_from_response(response.content.strip())
            data = json.loads(content)
            combined_queries = data.get("queries", [])
            queries["combined"] = " ".join(combined_queries) if combined_queries else f"{state.get('input_purpose', '')} {state.get('normalized_materials', '')} {state.get('input_methods', '')}"
            print(f"    > {queries['combined'][:80]}...")
        except Exception as e:
            print(f"    > ⚠️ 総合軸クエリ生成エラー: {e}")
            queries["combined"] = f"{state.get('input_purpose', '')} {state.get('normalized_materials', '')} {state.get('input_methods', '')}"

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")

        return {
            "material_query": queries["material"],
            "method_query": queries["method"],
            "combined_query": queries["combined"]
        }

    def _multi_axis_search_node(self, state: AgentState):
        """3軸検索実行ノード（v3.2.0: 2コレクション + 軸別検索方式対応）

        各軸で独立して検索を実行する
        - 材料軸: materials_methods_collectionをBM25キーワード検索
        - 方法軸: materials_methods_collectionをセマンティック検索
        - 総合軸: combined_collectionをセマンティック検索
        """
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)
        rerank_position = state.get("rerank_position", self.rerank_position)
        rerank_enabled = state.get("rerank_enabled", self.rerank_enabled)

        if evaluation_mode:
            print("\n--- 🔍 [4/6] 3軸検索実行（2コレクション + 軸別検索方式）---")
        else:
            print("--- 🔍 [4/7] 3軸検索実行（2コレクション + 軸別検索方式）---")

        hybrid_alpha = state.get("hybrid_alpha", self.hybrid_alpha)

        results = {}

        # v3.2.0: 2コレクション構成
        # 材料軸と方法軸は同じmaterials_methodsコレクションを使用
        axis_vectorstores = {
            "material": self.vectorstores["materials_methods"] if self.vectorstores else self.vectorstore,
            "method": self.vectorstores["materials_methods"] if self.vectorstores else self.vectorstore,
            "combined": self.vectorstores["combined"] if self.vectorstores else self.vectorstore
        }

        # v3.2.0: 軸別検索方式（config.AXIS_SEARCH_MODESから取得）
        axis_search_modes = {
            "material": config.AXIS_SEARCH_MODES.get("material", "keyword"),   # BM25キーワード検索
            "method": config.AXIS_SEARCH_MODES.get("method", "semantic"),      # セマンティック検索
            "combined": config.AXIS_SEARCH_MODES.get("combined", "semantic")   # セマンティック検索
        }

        # 各軸で検索を実行
        for axis, query in [
            ("material", state.get("material_query", "")),
            ("method", state.get("method_query", "")),
            ("combined", state.get("combined_query", ""))
        ]:
            axis_label = {"material": "材料", "method": "方法", "combined": "総合"}[axis]
            target_vectorstore = axis_vectorstores[axis]
            search_mode = axis_search_modes[axis]

            # v3.2.0: コレクション名と検索方式を表示
            collection_name = target_vectorstore._collection.name if hasattr(target_vectorstore, '_collection') else "unknown"
            mode_label = {"keyword": "BM25キーワード", "semantic": "セマンティック", "hybrid": "ハイブリッド"}.get(search_mode, search_mode)
            print(f"\n  {'='*70}")
            print(f"  📊 {axis_label}軸検索 (コレクション: {collection_name}, 方式: {mode_label})")
            print(f"  {'='*70}")

            # v3.1.2: 検索クエリを省略せずに表示
            print(f"  🔍 検索クエリ:")
            print(f"     {query}")

            if not query:
                print(f"    > クエリが空のためスキップ")
                results[axis] = []
                continue

            try:
                # v3.2.0: 軸別検索方式を適用した検索
                search_results = self._search_with_synonym_expansion(
                    vectorstore=target_vectorstore,
                    query=query,
                    search_mode=search_mode,  # 軸別の検索方式を使用
                    hybrid_alpha=hybrid_alpha,
                    k=config.VECTOR_SEARCH_K
                )

                print(f"  📋 候補数: {len(search_results)}件")

                # per_axisモードの場合、各軸でリランク
                if rerank_position == "per_axis" and rerank_enabled and search_results:
                    print(f"  🔄 リランキング実行中...")
                    docs_content = [doc.page_content for doc, _ in search_results]
                    rerank_results = self.cohere_client.rerank(
                        model=config.DEFAULT_RERANK_MODEL,
                        query=query,
                        documents=docs_content,
                        top_n=min(config.RERANK_TOP_N, len(docs_content))
                    )
                    # リランク結果で並び替え
                    reranked = []
                    for r in rerank_results.results:
                        original_doc = search_results[r.index][0]
                        reranked.append((original_doc, r.relevance_score))
                    results[axis] = reranked
                else:
                    results[axis] = search_results

                # v3.1.2: 上位10件の詳細を表示
                final_results = results[axis]
                print(f"\n  📊 {axis_label}軸 上位10件:")
                print(f"  {'-'*60}")
                seen_ids = set()
                rank_counter = 0
                for doc, score in final_results:
                    note_id = doc.metadata.get('note_id', doc.metadata.get('source', 'unknown'))
                    if note_id in seen_ids:
                        continue
                    seen_ids.add(note_id)
                    rank_counter += 1
                    print(f"  Rank {rank_counter:2d} | Score: {score:.6f} | ノートID: {note_id}")
                    if rank_counter >= 10:
                        break
                print(f"  {'-'*60}")

            except Exception as e:
                print(f"    > ⚠️ {axis_label}軸検索エラー: {e}")
                results[axis] = []

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")

        return {
            "material_axis_results": results.get("material", []),
            "method_axis_results": results.get("method", []),
            "combined_axis_results": results.get("combined", [])
        }

    def _keyword_search_on_vectorstore(self, vectorstore, query: str, k: int = 30) -> List[tuple]:
        """指定されたvectorstoreでキーワード検索（v3.1.1追加）"""
        import math
        from collections import Counter
        from langchain_core.documents import Document

        collection = vectorstore._collection
        all_docs = collection.get(include=["documents", "metadatas"])

        if not all_docs["documents"]:
            return []

        documents = all_docs["documents"]
        metadatas = all_docs["metadatas"]

        query_tokens = self._tokenize(query)

        k1 = 1.5
        b = 0.75

        doc_lengths = [len(self._tokenize(doc)) for doc in documents]
        avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1

        N = len(documents)
        idf = {}
        for token in query_tokens:
            df = sum(1 for doc in documents if token in doc.lower())
            idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)

        scores = []
        for i, doc in enumerate(documents):
            doc_tokens = self._tokenize(doc)
            doc_len = len(doc_tokens)
            term_freq = Counter(doc_tokens)

            score = 0
            for token in query_tokens:
                if token in term_freq:
                    tf = term_freq[token]
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * doc_len / avgdl)
                    score += idf.get(token, 0) * numerator / denominator

            doc_obj = Document(
                page_content=doc,
                metadata=metadatas[i] if metadatas else {}
            )
            scores.append((doc_obj, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def _hybrid_search_on_vectorstore(self, vectorstore, query: str, alpha: float, k: int = 30) -> List[tuple]:
        """指定されたvectorstoreでハイブリッド検索（v3.1.1追加）"""
        semantic_results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
        keyword_results = self._keyword_search_on_vectorstore(vectorstore, query, k=k)

        doc_scores = {}

        if semantic_results:
            max_semantic = max(score for _, score in semantic_results)
            min_semantic = min(score for _, score in semantic_results)
            range_semantic = max_semantic - min_semantic if max_semantic != min_semantic else 1

            for doc, score in semantic_results:
                normalized_score = (score - min_semantic) / range_semantic if range_semantic > 0 else 0.5
                doc_id = doc.metadata.get('source', doc.metadata.get('note_id', doc.page_content[:50]))
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'semantic': 0, 'keyword': 0}
                doc_scores[doc_id]['semantic'] = normalized_score

        if keyword_results:
            max_keyword = max(score for _, score in keyword_results)
            min_keyword = min(score for _, score in keyword_results)
            range_keyword = max_keyword - min_keyword if max_keyword != min_keyword else 1

            for doc, score in keyword_results:
                normalized_score = (score - min_keyword) / range_keyword if range_keyword > 0 else 0.5
                doc_id = doc.metadata.get('source', doc.metadata.get('note_id', doc.page_content[:50]))
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {'doc': doc, 'semantic': 0, 'keyword': 0}
                doc_scores[doc_id]['keyword'] = normalized_score

        combined_results = []
        for doc_id, scores in doc_scores.items():
            combined_score = alpha * scores['semantic'] + (1 - alpha) * scores['keyword']
            combined_results.append((scores['doc'], combined_score))

        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results[:k]

    def _score_fusion_node(self, state: AgentState):
        """スコア統合ノード（v3.1.1: note_idでの結果マージ対応）

        各軸の検索結果を統合して最終ランキングを生成する
        - 各コレクションの検索結果をnote_idでマージ
        - 同じノートが複数軸でヒットした場合、各軸のスコアを統合
        """
        start_time = time.time()
        evaluation_mode = state.get("evaluation_mode", False)
        fusion_method = state.get("fusion_method", self.fusion_method)
        axis_weights = state.get("axis_weights", self.axis_weights)
        rerank_position = state.get("rerank_position", self.rerank_position)
        rerank_enabled = state.get("rerank_enabled", self.rerank_enabled)

        if evaluation_mode:
            print("\n--- 🔀 [5/6] スコア統合（note_idでマージ）---")
        else:
            print("--- 🔀 [5/7] スコア統合（note_idでマージ）---")

        print(f"  > 統合方式: {fusion_method}")
        print(f"  > ウエイト: 材料={axis_weights.get('material', 0.3)}, 方法={axis_weights.get('method', 0.4)}, 総合={axis_weights.get('combined', 0.3)}")

        # 各軸の結果を取得
        material_results = state.get("material_axis_results", [])
        method_results = state.get("method_axis_results", [])
        combined_results = state.get("combined_axis_results", [])

        # v3.1.1: note_idでマージするためのディクショナリ
        # {note_id: {"docs": {axis: doc}, "scores": {axis: score}, "ranks": {axis: rank}}}
        doc_scores = {}

        for axis, results in [
            ("material", material_results),
            ("method", method_results),
            ("combined", combined_results)
        ]:
            for rank, (doc, score) in enumerate(results):
                # v3.1.1: note_idを優先的に使用（セクション別コレクションで統一されたID）
                note_id = doc.metadata.get('note_id', doc.metadata.get('source', doc.page_content[:50]))
                if note_id not in doc_scores:
                    doc_scores[note_id] = {
                        "docs": {"material": None, "method": None, "combined": None},
                        "scores": {"material": None, "method": None, "combined": None},
                        "ranks": {"material": None, "method": None, "combined": None}
                    }
                # 各軸のdocを保存（combined優先で最終的なdocを決定）
                doc_scores[note_id]["docs"][axis] = doc
                doc_scores[note_id]["scores"][axis] = score
                doc_scores[note_id]["ranks"][axis] = rank + 1  # 1-indexed

        # スコア統合
        final_scores = []
        rrf_k = config.RRF_K

        for note_id, data in doc_scores.items():
            if fusion_method == "rrf":
                # RRF (Reciprocal Rank Fusion)
                score = 0
                for axis in ["material", "method", "combined"]:
                    rank = data["ranks"][axis]
                    weight = axis_weights.get(axis, 0.33)
                    if rank is not None:
                        score += weight / (rrf_k + rank)
            else:
                # 線形結合
                score = 0
                for axis in ["material", "method", "combined"]:
                    axis_score = data["scores"][axis]
                    weight = axis_weights.get(axis, 0.33)
                    if axis_score is not None:
                        # スコアを0-1に正規化（すでに正規化されている前提）
                        score += weight * axis_score

            # v3.1.1: 最終的なdocはcombinedを優先、なければ他の軸から取得
            final_doc = data["docs"]["combined"] or data["docs"]["method"] or data["docs"]["material"]
            if final_doc:
                final_scores.append((final_doc, score, note_id))

        # スコア降順でソート
        final_scores.sort(key=lambda x: x[1], reverse=True)

        # after_fusionモードの場合、統合後にリランク
        if rerank_position == "after_fusion" and rerank_enabled and final_scores:
            print(f"  > 統合後リランキング実行中...")
            # 上位候補に対してリランク
            top_candidates = final_scores[:config.RERANK_TOP_N * 2]  # 余裕を持って取得
            if top_candidates:
                # クエリは総合クエリを使用
                combined_query = state.get("combined_query", "")
                docs_content = [doc.page_content for doc, _, _ in top_candidates]

                try:
                    rerank_results = self.cohere_client.rerank(
                        model=config.DEFAULT_RERANK_MODEL,
                        query=combined_query,
                        documents=docs_content,
                        top_n=min(config.RERANK_TOP_N, len(docs_content))
                    )
                    # リランク結果で並び替え
                    reranked = []
                    for r in rerank_results.results:
                        doc, _, source_id = top_candidates[r.index]
                        reranked.append((doc, r.relevance_score, source_id))
                    final_scores = reranked
                    print(f"  > リランク後: {len(final_scores)}件")
                except Exception as e:
                    print(f"  > ⚠️ リランクエラー: {e}")

        # 重複除去してUI用の結果を作成
        docs_for_ui = []
        seen_source_ids = set()
        display_limit = config.RERANK_TOP_N if evaluation_mode else config.UI_DISPLAY_TOP_N

        print(f"\n  📊 [最終ランキング]")
        print(f"  " + "="*60)

        rank_counter = 0
        for doc, score, source_id in final_scores:
            if source_id in seen_source_ids:
                continue
            seen_source_ids.add(source_id)
            rank_counter += 1

            if evaluation_mode:
                print(f"  Rank {rank_counter:2d} | Score: {score:.6f} | ノートID: {source_id}")
            else:
                snippet = doc.page_content[:50].replace('\n', ' ')
                print(f"  Rank {rank_counter:2d} | Score: {score:.4f} | ID: {source_id} | {snippet}...")

            if rank_counter <= display_limit:
                docs_for_ui.append(f"【実験ノートID: {source_id}】\n{doc.page_content}")

            if rank_counter >= config.RERANK_TOP_N:
                break

        print(f"  " + "="*60)

        if evaluation_mode:
            print(f"  ✅ 評価用に上位 {len(docs_for_ui)} 件を返却します。")
        else:
            print(f"  > UI向けに上位 {len(docs_for_ui)} 件を選択しました。")

        # 評価モード時は終了メッセージを表示
        if evaluation_mode:
            print("\n" + "="*80)
            print("✅ 評価モード終了 - 比較ノードをスキップして結果を返却します")
            print("="*80 + "\n")

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec")

        return {
            "retrieved_docs": docs_for_ui,
            "iteration": state.get("iteration", 0) + 1
        }

    # ===========================================
    # 共通ノード
    # ===========================================

    def _compare_node(self, state: AgentState):
        """比較・要約生成ノード"""
        start_time = time.time()
        print("--- 📝 [4/4] 比較・要約生成 (Deep Analysis) ---")

        input_purpose = state.get('input_purpose')
        input_materials = state.get('normalized_materials')
        input_methods = state.get('input_methods')
        instruction = state.get('user_focus_instruction', '')

        docs_str = "\n\n".join(state.get("retrieved_docs", []))

        if not docs_str:
            print(f"  ⏱️ Execution Time: {time.time() - start_time:.4f} sec")
            return {"messages": [HumanMessage(content="該当するノートが見つかりませんでした。")]}

        # カスタムプロンプトまたはデフォルトプロンプトを取得
        prompt_template = self._get_prompt("compare")

        # プロンプトに変数を埋め込む
        prompt = prompt_template.format(
            input_purpose=input_purpose,
            normalized_materials=input_materials,
            input_methods=input_methods,
            user_focus_instruction=instruction,
            retrieved_docs=docs_str
        )

        # v3.0: 要約生成用LLMを使用
        response = self.summary_llm.invoke(prompt)

        elapsed_time = time.time() - start_time
        print(f"  ⏱️ Execution Time: {elapsed_time:.4f} sec (using {self.summary_llm_model})")
        return {"messages": [response]}

    def _should_compare(self, state: AgentState):
        """compareノードに進むべきかを判定"""
        evaluation_mode = state.get("evaluation_mode", False)
        if evaluation_mode:
            return END
        else:
            return "compare"

    def _should_use_multi_axis(self, state: AgentState):
        """3軸検索を使用するかどうかを判定"""
        multi_axis_enabled = state.get("multi_axis_enabled", self.multi_axis_enabled)
        if multi_axis_enabled:
            return "classify_focus"
        else:
            return "generate_query"

    def _should_compare_multi_axis(self, state: AgentState):
        """3軸検索後にcompareノードに進むべきかを判定"""
        evaluation_mode = state.get("evaluation_mode", False)
        if evaluation_mode:
            return END
        else:
            return "compare"

    def _build_graph(self):
        """グラフを構築（v3.1.0: 3軸分離検索対応）"""
        workflow = StateGraph(AgentState)

        # 共通ノード
        workflow.add_node("normalize", self._normalize_node)
        workflow.add_node("compare", self._compare_node)

        # 従来の単一クエリ検索ノード
        workflow.add_node("generate_query", self._generate_query_node)
        workflow.add_node("search", self._search_node)

        # 3軸分離検索ノード（v3.1.0）
        workflow.add_node("classify_focus", self._classify_focus_node)
        workflow.add_node("generate_multi_axis_queries", self._generate_multi_axis_queries_node)
        workflow.add_node("multi_axis_search", self._multi_axis_search_node)
        workflow.add_node("score_fusion", self._score_fusion_node)

        # エントリーポイント
        workflow.set_entry_point("normalize")

        # normalize後に3軸検索か従来検索かを分岐
        workflow.add_conditional_edges(
            "normalize",
            self._should_use_multi_axis,
            {
                "classify_focus": "classify_focus",
                "generate_query": "generate_query"
            }
        )

        # 従来の検索フロー
        workflow.add_edge("generate_query", "search")
        workflow.add_conditional_edges(
            "search",
            self._should_compare,
            {
                "compare": "compare",
                END: END
            }
        )

        # 3軸分離検索フロー
        workflow.add_edge("classify_focus", "generate_multi_axis_queries")
        workflow.add_edge("generate_multi_axis_queries", "multi_axis_search")
        workflow.add_edge("multi_axis_search", "score_fusion")
        workflow.add_conditional_edges(
            "score_fusion",
            self._should_compare_multi_axis,
            {
                "compare": "compare",
                END: END
            }
        )

        # 比較ノードから終了
        workflow.add_edge("compare", END)

        return workflow.compile()

    def run(self, input_data: dict, evaluation_mode: bool = False):
        """エージェントを実行

        Args:
            input_data: 検索条件（purpose, materials, methods等）
            evaluation_mode: 評価モード（True: 比較省略、Top10返却、False: 通常動作）
        """
        initial_state = {
            "messages": [HumanMessage(content=json.dumps(input_data, ensure_ascii=False))],
            "input_purpose": "",
            "input_materials": "",
            "input_methods": "",
            "normalized_materials": "",
            "user_focus_instruction": "",
            "search_query": "",
            "retrieved_docs": [],
            "iteration": 0,
            "evaluation_mode": evaluation_mode,
            # v3.0.1: 検索モード設定
            "search_mode": self.search_mode,
            "hybrid_alpha": self.hybrid_alpha,
            # v3.1.0: 3軸分離検索設定
            "multi_axis_enabled": self.multi_axis_enabled,
            "focus_classification": "",
            "fusion_method": self.fusion_method,
            "axis_weights": self.axis_weights,
            "rerank_position": self.rerank_position,
            "rerank_enabled": self.rerank_enabled,
            # 3軸検索結果
            "material_query": "",
            "method_query": "",
            "combined_query": "",
            "material_axis_results": [],
            "method_axis_results": [],
            "combined_axis_results": []
        }

        result = self.graph.invoke(initial_state)
        return result
