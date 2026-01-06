"""
同義語辞書モジュール（v3.2.1）

検索時のクエリ展開に使用する同義語グループを管理

辞書形式:
```yaml
groups:
  - canonical: 純水
    variants: [精製水, 水, 蒸留水]
  - canonical: 抗体1
    variants: [抗体A, 抗体α]
```
"""

import yaml
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from storage import storage


@dataclass
class SynonymGroup:
    """同義語グループ"""
    canonical: str  # 正規形（代表表記）
    variants: List[str] = field(default_factory=list)  # バリアント（異表記）
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'canonical': self.canonical,
            'variants': self.variants,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SynonymGroup':
        return cls(
            canonical=data.get('canonical', ''),
            variants=data.get('variants', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def get_all_terms(self) -> Set[str]:
        """canonical + variants の全用語を取得"""
        terms = {self.canonical}
        terms.update(self.variants)
        return terms


class SynonymDictionary:
    """同義語辞書マネージャー"""

    def __init__(self, team_id: Optional[str] = None, dict_path: Optional[str] = None):
        """
        Args:
            team_id: チームID（マルチテナント対応）
            dict_path: 辞書ファイルのパス（指定しない場合は自動設定）
        """
        if dict_path:
            self.dict_path = dict_path
        elif team_id:
            self.dict_path = f"teams/{team_id}/synonym_dictionary.yaml"
        else:
            self.dict_path = "synonym_dictionary.yaml"

        self.team_id = team_id
        self.groups: List[SynonymGroup] = []
        self._term_to_group: Dict[str, SynonymGroup] = {}  # 用語→グループの逆引き
        self.load()

    def load(self) -> None:
        """YAMLから辞書を読み込む"""
        if not storage.exists(self.dict_path):
            print(f"同義語辞書が見つかりません: {self.dict_path}")
            self._create_default_dictionary()
            return

        try:
            content = storage.read_file(self.dict_path)
            data = yaml.safe_load(content) or {}

            self.groups = []
            for group_data in data.get('groups', []):
                group = SynonymGroup.from_dict(group_data)
                self.groups.append(group)

            self._rebuild_index()
            print(f"同義語辞書を読み込みました: {len(self.groups)}グループ")

        except Exception as e:
            print(f"同義語辞書の読み込みに失敗: {e}")
            self.groups = []
            self._term_to_group = {}

    def _create_default_dictionary(self) -> None:
        """デフォルトの同義語辞書を作成"""
        now = datetime.now().isoformat()
        self.groups = [
            SynonymGroup(
                canonical="純水",
                variants=["精製水", "蒸留水", "超純水"],
                created_at=now,
                updated_at=now
            ),
        ]
        self.save()
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """用語→グループの逆引きインデックスを再構築"""
        self._term_to_group = {}
        for group in self.groups:
            for term in group.get_all_terms():
                self._term_to_group[term] = group

    def save(self) -> bool:
        """YAMLに辞書を保存"""
        try:
            # バックアップ作成
            if storage.exists(self.dict_path):
                backup_path = f"{self.dict_path}.backup"
                content = storage.read_file(self.dict_path)
                storage.write_file(backup_path, content)

            # データ構造の作成
            data = {
                'groups': [group.to_dict() for group in self.groups]
            }

            # YAML形式で保存
            yaml_content = yaml.dump(
                data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )
            storage.write_file(self.dict_path, yaml_content)

            print(f"同義語辞書を保存しました: {len(self.groups)}グループ")
            return True

        except Exception as e:
            print(f"同義語辞書の保存に失敗: {e}")
            return False

    def get_all_groups(self) -> List[Dict]:
        """全グループを取得"""
        return [group.to_dict() for group in self.groups]

    def get_group(self, canonical: str) -> Optional[SynonymGroup]:
        """正規形でグループを取得"""
        for group in self.groups:
            if group.canonical == canonical:
                return group
        return None

    def add_group(
        self,
        canonical: str,
        variants: List[str]
    ) -> bool:
        """
        新規グループを追加

        Args:
            canonical: 正規形
            variants: バリアントリスト

        Returns:
            成功したかどうか
        """
        # 既存チェック
        if self.get_group(canonical):
            print(f"グループが既に存在します: {canonical}")
            return False

        now = datetime.now().isoformat()
        group = SynonymGroup(
            canonical=canonical,
            variants=variants,
            created_at=now,
            updated_at=now
        )

        self.groups.append(group)
        self._rebuild_index()
        return self.save()

    def update_group(
        self,
        canonical: str,
        new_canonical: Optional[str] = None,
        variants: Optional[List[str]] = None
    ) -> bool:
        """
        グループを更新

        Args:
            canonical: 現在の正規形
            new_canonical: 新しい正規形（変更する場合）
            variants: 新しいバリアントリスト（変更する場合）

        Returns:
            成功したかどうか
        """
        group = self.get_group(canonical)
        if not group:
            print(f"グループが見つかりません: {canonical}")
            return False

        if new_canonical is not None:
            group.canonical = new_canonical
        if variants is not None:
            group.variants = variants

        group.updated_at = datetime.now().isoformat()
        self._rebuild_index()
        return self.save()

    def delete_group(self, canonical: str) -> bool:
        """
        グループを削除

        Args:
            canonical: 正規形

        Returns:
            成功したかどうか
        """
        group = self.get_group(canonical)
        if not group:
            print(f"グループが見つかりません: {canonical}")
            return False

        self.groups.remove(group)
        self._rebuild_index()
        return self.save()

    def add_variant(self, canonical: str, variant: str) -> bool:
        """
        既存グループにバリアントを追加

        Args:
            canonical: 正規形
            variant: 追加するバリアント

        Returns:
            成功したかどうか
        """
        group = self.get_group(canonical)
        if not group:
            print(f"グループが見つかりません: {canonical}")
            return False

        if variant not in group.variants:
            group.variants.append(variant)
            group.updated_at = datetime.now().isoformat()
            self._rebuild_index()
            return self.save()

        return True  # 既に存在する場合も成功扱い

    def remove_variant(self, canonical: str, variant: str) -> bool:
        """
        グループからバリアントを削除

        Args:
            canonical: 正規形
            variant: 削除するバリアント

        Returns:
            成功したかどうか
        """
        group = self.get_group(canonical)
        if not group:
            print(f"グループが見つかりません: {canonical}")
            return False

        if variant in group.variants:
            group.variants.remove(variant)
            group.updated_at = datetime.now().isoformat()
            self._rebuild_index()
            return self.save()

        return True

    # ============================================
    # 検索時のクエリ展開機能
    # ============================================

    def find_group_for_term(self, term: str) -> Optional[SynonymGroup]:
        """
        用語が属するグループを検索

        Args:
            term: 検索する用語

        Returns:
            該当するグループ（なければNone）
        """
        return self._term_to_group.get(term)

    def expand_term(self, term: str) -> List[str]:
        """
        用語を同義語に展開

        Args:
            term: 展開する用語

        Returns:
            同義語リスト（グループに属さない場合は元の用語のみ）
        """
        group = self.find_group_for_term(term)
        if group:
            return list(group.get_all_terms())
        return [term]

    def expand_query(self, query: str) -> List[str]:
        """
        クエリ文字列内の用語を同義語に展開

        改良版（v3.2.2）: 長い用語から優先的にマッチし、
        部分文字列の誤置換を防止

        Args:
            query: 検索クエリ文字列

        Returns:
            展開されたクエリのリスト
        """
        expanded_queries = [query]

        # 全用語を収集（グループ情報付き）
        all_terms_with_groups: List[tuple] = []
        for group in self.groups:
            for term in group.get_all_terms():
                all_terms_with_groups.append((term, group))

        # 長い用語から優先してマッチ（より具体的な用語を先に処理）
        all_terms_with_groups.sort(key=lambda x: len(x[0]), reverse=True)

        # マッチした範囲を記録（重複マッチを防ぐ）
        used_ranges: List[tuple] = []  # (start, end)

        # マッチしたグループと対応する用語を記録（canonical名をキーに使用）
        matched_terms: Dict[str, tuple] = {}  # canonical -> (group, matched_term)

        for term, group in all_terms_with_groups:
            # クエリ内での出現位置を検索
            pos = query.find(term)
            if pos == -1:
                continue

            end = pos + len(term)

            # 既にマッチした範囲と重複していないかチェック
            overlaps = False
            for used_start, used_end in used_ranges:
                # 範囲が重複している場合
                if not (end <= used_start or pos >= used_end):
                    overlaps = True
                    break

            if not overlaps:
                # この範囲を使用済みとしてマーク
                used_ranges.append((pos, end))
                # このグループでまだマッチしていなければ記録
                if group.canonical not in matched_terms:
                    matched_terms[group.canonical] = (group, term)

        # マッチした各グループの同義語で展開クエリを生成
        for canonical, (group, matched_term) in matched_terms.items():
            all_terms = group.get_all_terms()

            # 他のバリアントでクエリを生成
            for variant in all_terms:
                if variant != matched_term:
                    variant_query = query.replace(matched_term, variant)
                    if variant_query not in expanded_queries:
                        expanded_queries.append(variant_query)

        return expanded_queries

    def get_canonical(self, term: str) -> str:
        """
        用語の正規形を取得

        Args:
            term: 用語

        Returns:
            正規形（グループに属さない場合は元の用語）
        """
        group = self.find_group_for_term(term)
        if group:
            return group.canonical
        return term


def get_synonym_dictionary(team_id: Optional[str] = None) -> SynonymDictionary:
    """
    同義語辞書のインスタンスを取得

    Args:
        team_id: チームID

    Returns:
        SynonymDictionaryインスタンス
    """
    return SynonymDictionary(team_id=team_id)
