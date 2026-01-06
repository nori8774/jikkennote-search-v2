"""
検索履歴管理モジュール

機能:
- 検索履歴の保存・取得・削除
- 検索クエリごとの履歴管理
- JSON形式での永続化
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from config import config


@dataclass
class SearchHistory:
    """検索履歴"""
    id: str
    timestamp: str
    query: Dict[str, str]  # {"purpose": "...", "materials": "...", "methods": "...", "instruction": "..."}
    results: List[Dict]  # [{"note_id": "...", "score": 0.9, "rank": 1}, ...]
    normalized_materials: Optional[str] = None
    search_query: Optional[str] = None


class HistoryManager:
    """検索履歴マネージャー"""

    def __init__(self, history_file: Optional[str] = None):
        """
        Args:
            history_file: 履歴を保存するJSONファイル
        """
        self.history_file = history_file or os.path.join(config.Config.CHROMA_DB_FOLDER, 'search_history.json')
        self.histories: List[SearchHistory] = []
        self.load()

    def load(self):
        """履歴を読み込み"""
        if not os.path.exists(self.history_file):
            self.histories = []
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.histories = [
                SearchHistory(
                    id=h['id'],
                    timestamp=h['timestamp'],
                    query=h['query'],
                    results=h['results'],
                    normalized_materials=h.get('normalized_materials'),
                    search_query=h.get('search_query')
                )
                for h in data
            ]

            # 日時順にソート（新しい順）
            self.histories.sort(key=lambda h: h.timestamp, reverse=True)

            print(f"検索履歴を読み込みました: {len(self.histories)}件")

        except Exception as e:
            print(f"検索履歴の読み込みに失敗: {e}")
            self.histories = []

    def save(self):
        """履歴を保存"""
        try:
            # フォルダが存在しない場合は作成
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

            data = [asdict(h) for h in self.histories]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"検索履歴を保存しました: {len(self.histories)}件")
            return True

        except Exception as e:
            print(f"検索履歴の保存に失敗: {e}")
            return False

    def add_history(
        self,
        query: Dict[str, str],
        results: List[Dict],
        normalized_materials: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> str:
        """
        検索履歴を追加

        Args:
            query: 検索クエリ
            results: 検索結果 (上位10件程度)
            normalized_materials: 正規化された材料
            search_query: 生成された検索クエリ

        Returns:
            履歴ID
        """
        history_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        history = SearchHistory(
            id=history_id,
            timestamp=timestamp,
            query=query,
            results=results,
            normalized_materials=normalized_materials,
            search_query=search_query
        )

        self.histories.insert(0, history)  # 先頭に追加（新しい順）

        # 履歴数の上限設定（例: 最新100件のみ保持）
        max_histories = 100
        if len(self.histories) > max_histories:
            self.histories = self.histories[:max_histories]

        self.save()
        return history_id

    def get_history(self, history_id: str) -> Optional[SearchHistory]:
        """履歴を取得"""
        for h in self.histories:
            if h.id == history_id:
                return h
        return None

    def get_all_histories(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        全履歴を取得

        Args:
            limit: 取得件数の上限
            offset: オフセット

        Returns:
            履歴のリスト
        """
        histories = self.histories[offset:]

        if limit is not None:
            histories = histories[:limit]

        return [asdict(h) for h in histories]

    def delete_history(self, history_id: str) -> bool:
        """履歴を削除"""
        original_len = len(self.histories)
        self.histories = [h for h in self.histories if h.id != history_id]

        if len(self.histories) < original_len:
            return self.save()
        return False

    def clear_all(self) -> bool:
        """全履歴を削除"""
        self.histories = []
        return self.save()

    def search_histories(
        self,
        keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        履歴を検索

        Args:
            keyword: クエリに含まれるキーワード
            start_date: 開始日時（ISO形式）
            end_date: 終了日時（ISO形式）

        Returns:
            検索結果
        """
        filtered = self.histories

        if keyword:
            keyword_lower = keyword.lower()
            filtered = [
                h for h in filtered
                if (keyword_lower in h.query.get('purpose', '').lower() or
                    keyword_lower in h.query.get('materials', '').lower() or
                    keyword_lower in h.query.get('methods', '').lower())
            ]

        if start_date:
            filtered = [h for h in filtered if h.timestamp >= start_date]

        if end_date:
            filtered = [h for h in filtered if h.timestamp <= end_date]

        return [asdict(h) for h in filtered]

    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        if not self.histories:
            return {
                'total_count': 0,
                'latest_search': None,
                'oldest_search': None
            }

        return {
            'total_count': len(self.histories),
            'latest_search': self.histories[0].timestamp if self.histories else None,
            'oldest_search': self.histories[-1].timestamp if self.histories else None
        }


# グローバルインスタンス
_history_manager = None


def get_history_manager() -> HistoryManager:
    """履歴マネージャーのシングルトンインスタンスを取得"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
