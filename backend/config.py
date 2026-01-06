"""
Configuration management
環境変数とフォルダパス設定を管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """アプリケーション設定"""

    # フォルダパス設定（GCS環境では "notes/new" のようにパスを指定）
    NOTES_NEW_FOLDER = os.getenv("NOTES_NEW_FOLDER", "notes/new")
    NOTES_PROCESSED_FOLDER = os.getenv("NOTES_PROCESSED_FOLDER", "notes/processed")
    NOTES_ARCHIVE_FOLDER = os.getenv("NOTES_ARCHIVE_FOLDER", "notes/archived")  # 後方互換性のため残す
    CHROMA_DB_FOLDER = os.getenv("CHROMA_DB_FOLDER", "/tmp/chroma_db")
    MASTER_DICTIONARY_PATH = os.getenv("MASTER_DICTIONARY_PATH", "master_dictionary.yaml")

    # デフォルトモデル設定
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
    DEFAULT_LLM_MODEL = "gpt-4o-mini"  # 後方互換性のため維持
    DEFAULT_SEARCH_LLM_MODEL = "gpt-4o-mini"  # v3.0: 検索・判定用LLM
    DEFAULT_SUMMARY_LLM_MODEL = "gpt-3.5-turbo"  # v3.0: 要約生成用LLM
    DEFAULT_RERANK_MODEL = "rerank-multilingual-v3.0"

    # 検索モード設定（v3.0.1）
    DEFAULT_SEARCH_MODE = "semantic"  # "semantic" | "keyword" | "hybrid"
    DEFAULT_HYBRID_ALPHA = 0.7  # ハイブリッド検索のセマンティック重み（0.0-1.0）

    # 検索設定
    VECTOR_SEARCH_K = 30  # 初期検索候補数（重複除去を考慮して増加）
    RERANK_TOP_N = 20  # リランキング後の上位件数（重複除去後に10件確保するため）
    UI_DISPLAY_TOP_N = 3  # UI表示用の上位件数

    # 3軸分離検索設定（v3.1.0）
    MULTI_AXIS_ENABLED = True  # 3軸検索の有効/無効（デフォルト: True）
    FUSION_METHOD = "rrf"  # スコア統合方式: "rrf" | "linear"
    AXIS_WEIGHTS = {  # 各軸のウエイト（合計1.0）
        "material": 0.3,  # 材料軸
        "method": 0.4,    # 方法軸
        "combined": 0.3   # 総合軸
    }
    RERANK_POSITION = "after_fusion"  # リランク位置: "per_axis" | "after_fusion"
    RERANK_ENABLED = True  # リランキングの有効/無効
    RRF_K = 60  # RRF（Reciprocal Rank Fusion）のkパラメータ

    # セクション別Embeddingコレクション設定（v3.1.1）
    MATERIALS_COLLECTION_NAME = "materials_collection"  # 材料セクション用コレクション
    METHODS_COLLECTION_NAME = "methods_collection"      # 方法セクション用コレクション
    COMBINED_COLLECTION_NAME = "combined_collection"    # ノート全体用コレクション
    # 後方互換性のため、従来のCOLLECTION_NAMEはCOMBINED_COLLECTION_NAMEを参照
    COLLECTION_NAME = COMBINED_COLLECTION_NAME

    @classmethod
    def ensure_folders(cls):
        """必要なフォルダを作成"""
        Path(cls.NOTES_NEW_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(cls.NOTES_PROCESSED_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(cls.NOTES_ARCHIVE_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(cls.CHROMA_DB_FOLDER).mkdir(parents=True, exist_ok=True)

    @classmethod
    def update_folder_paths(cls, notes_new: str = None, notes_processed: str = None, notes_archive: str = None, chroma_db: str = None):
        """フォルダパスを動的に更新"""
        if notes_new:
            cls.NOTES_NEW_FOLDER = notes_new
        if notes_processed:
            cls.NOTES_PROCESSED_FOLDER = notes_processed
        if notes_archive:
            cls.NOTES_ARCHIVE_FOLDER = notes_archive
        if chroma_db:
            cls.CHROMA_DB_FOLDER = chroma_db
        cls.ensure_folders()

config = Config()
