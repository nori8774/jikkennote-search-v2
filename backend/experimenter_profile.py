"""
実験者プロファイル管理モジュール

機能:
- 実験者ごとのプロファイル管理（CRUD）
- ノートIDから実験者IDの抽出
- LLMによる省略形の自動学習
- 方法セクションの省略形展開
"""

import re
import yaml
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field

from storage import storage


@dataclass
class ExperimenterProfile:
    """実験者プロファイル"""
    experimenter_id: str  # 実験者ID（例: "1", "2"）
    name: str  # 表示名（例: "実験者1"）
    suffix_conventions: List[List[str]] = field(default_factory=list)  # サフィックス規則
    material_shortcuts: Dict[str, str] = field(default_factory=dict)  # 省略形マッピング
    learned_from: Optional[str] = None  # 学習元ノートID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        result = {
            'experimenter_id': self.experimenter_id,
            'name': self.name,
        }
        if self.suffix_conventions:
            result['suffix_conventions'] = self.suffix_conventions
        if self.material_shortcuts:
            result['material_shortcuts'] = self.material_shortcuts
        if self.learned_from:
            result['learned_from'] = self.learned_from
        if self.created_at:
            result['created_at'] = self.created_at
        if self.updated_at:
            result['updated_at'] = self.updated_at
        return result

    @classmethod
    def from_dict(cls, experimenter_id: str, data: Dict) -> 'ExperimenterProfile':
        """辞書からインスタンスを生成"""
        return cls(
            experimenter_id=experimenter_id,
            name=data.get('name', f'実験者{experimenter_id}'),
            suffix_conventions=data.get('suffix_conventions', []),
            material_shortcuts=data.get('material_shortcuts', {}),
            learned_from=data.get('learned_from'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class ExperimenterProfileManager:
    """実験者プロファイルマネージャー"""

    # デフォルトのIDパターン（キャプチャグループ1が実験者ID）
    DEFAULT_ID_PATTERN = r'^ID(\d+)-'

    def __init__(self, team_id: Optional[str] = None, profile_path: Optional[str] = None):
        """
        Args:
            team_id: チームID（マルチテナント対応）
            profile_path: プロファイルファイルのパス
        """
        if profile_path:
            self.profile_path = profile_path
        elif team_id:
            self.profile_path = f"teams/{team_id}/experimenter_profiles.yaml"
        else:
            self.profile_path = "experimenter_profiles.yaml"

        self.team_id = team_id
        self.id_pattern: str = self.DEFAULT_ID_PATTERN
        self.experimenters: Dict[str, ExperimenterProfile] = {}
        self.load()

    def load(self) -> None:
        """YAMLからプロファイルを読み込む"""
        if not storage.exists(self.profile_path):
            print(f"プロファイルファイルが見つかりません: {self.profile_path}")
            return

        try:
            content = storage.read_file(self.profile_path)
            data = yaml.safe_load(content) or {}

            # IDパターンの読み込み
            self.id_pattern = data.get('id_pattern', self.DEFAULT_ID_PATTERN)

            # 実験者プロファイルの読み込み
            experimenters_data = data.get('experimenters', {})
            self.experimenters = {}

            for exp_id, exp_data in experimenters_data.items():
                self.experimenters[str(exp_id)] = ExperimenterProfile.from_dict(
                    str(exp_id), exp_data
                )

            print(f"プロファイルを読み込みました: {len(self.experimenters)}件")

        except Exception as e:
            print(f"プロファイルの読み込みに失敗: {e}")
            self.experimenters = {}

    def save(self) -> bool:
        """YAMLにプロファイルを保存"""
        try:
            # バックアップ作成
            if storage.exists(self.profile_path):
                backup_path = f"{self.profile_path}.backup"
                content = storage.read_file(self.profile_path)
                storage.write_file(backup_path, content)

            # データ構造の作成
            data = {
                'id_pattern': self.id_pattern,
                'experimenters': {}
            }

            for exp_id, profile in self.experimenters.items():
                data['experimenters'][exp_id] = profile.to_dict()

            # YAML形式で保存
            yaml_content = yaml.dump(
                data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )
            storage.write_file(self.profile_path, yaml_content)

            print(f"プロファイルを保存しました: {len(self.experimenters)}件")
            return True

        except Exception as e:
            print(f"プロファイルの保存に失敗: {e}")
            return False

    def get_experimenter_id(self, note_id: str) -> Optional[str]:
        """
        ノートIDから実験者IDを抽出

        Args:
            note_id: ノートID（例: "ID2-5"）

        Returns:
            実験者ID（例: "2"）、抽出できない場合はNone
        """
        try:
            match = re.search(self.id_pattern, note_id)
            if match and match.group(1):
                return match.group(1)
        except Exception as e:
            print(f"実験者ID抽出エラー: {e}")
        return None

    def get_profile(self, experimenter_id: str) -> Optional[ExperimenterProfile]:
        """実験者プロファイルを取得"""
        return self.experimenters.get(str(experimenter_id))

    def get_all_profiles(self) -> List[Dict]:
        """全プロファイルを取得"""
        return [profile.to_dict() for profile in self.experimenters.values()]

    def create_profile(
        self,
        experimenter_id: str,
        name: str,
        material_shortcuts: Optional[Dict[str, str]] = None,
        suffix_conventions: Optional[List[List[str]]] = None,
        learned_from: Optional[str] = None
    ) -> bool:
        """
        新規プロファイルを作成

        Args:
            experimenter_id: 実験者ID
            name: 表示名
            material_shortcuts: 省略形マッピング
            suffix_conventions: サフィックス規則
            learned_from: 学習元ノートID

        Returns:
            成功したかどうか
        """
        exp_id = str(experimenter_id)

        if exp_id in self.experimenters:
            print(f"プロファイルが既に存在します: {exp_id}")
            return False

        now = datetime.now().isoformat()
        profile = ExperimenterProfile(
            experimenter_id=exp_id,
            name=name,
            suffix_conventions=suffix_conventions or [],
            material_shortcuts=material_shortcuts or {},
            learned_from=learned_from,
            created_at=now,
            updated_at=now
        )

        self.experimenters[exp_id] = profile
        return self.save()

    def update_profile(
        self,
        experimenter_id: str,
        name: Optional[str] = None,
        material_shortcuts: Optional[Dict[str, str]] = None,
        suffix_conventions: Optional[List[List[str]]] = None,
        learned_from: Optional[str] = None
    ) -> bool:
        """
        プロファイルを更新

        Args:
            experimenter_id: 実験者ID
            name: 新しい表示名（Noneの場合は変更なし）
            material_shortcuts: 新しい省略形マッピング（Noneの場合は変更なし）
            suffix_conventions: 新しいサフィックス規則（Noneの場合は変更なし）
            learned_from: 新しい学習元ノートID（Noneの場合は変更なし）

        Returns:
            成功したかどうか
        """
        exp_id = str(experimenter_id)
        profile = self.experimenters.get(exp_id)

        if not profile:
            print(f"プロファイルが見つかりません: {exp_id}")
            return False

        if name is not None:
            profile.name = name
        if material_shortcuts is not None:
            profile.material_shortcuts = material_shortcuts
        if suffix_conventions is not None:
            profile.suffix_conventions = suffix_conventions
        if learned_from is not None:
            profile.learned_from = learned_from

        profile.updated_at = datetime.now().isoformat()
        return self.save()

    def delete_profile(self, experimenter_id: str) -> bool:
        """
        プロファイルを削除

        Args:
            experimenter_id: 実験者ID

        Returns:
            成功したかどうか
        """
        exp_id = str(experimenter_id)

        if exp_id not in self.experimenters:
            print(f"プロファイルが見つかりません: {exp_id}")
            return False

        del self.experimenters[exp_id]
        return self.save()

    def set_id_pattern(self, pattern: str) -> bool:
        """
        IDパターンを設定

        Args:
            pattern: 正規表現パターン（キャプチャグループ1が実験者ID）

        Returns:
            成功したかどうか
        """
        # パターンの検証
        try:
            re.compile(pattern)
        except re.error as e:
            print(f"無効な正規表現パターン: {e}")
            return False

        self.id_pattern = pattern
        return self.save()

    def get_id_pattern(self) -> str:
        """現在のIDパターンを取得"""
        return self.id_pattern

    # ============================================
    # LLM学習機能（フェーズ2）
    # ============================================

    def learn_shortcuts_from_materials(
        self,
        materials_text: str,
        llm,
        experimenter_id: str
    ) -> Dict[str, str]:
        """
        LLMを使って材料セクションから省略形を学習

        Args:
            materials_text: 材料セクションのテキスト
            llm: LangChainのLLMインスタンス
            experimenter_id: 実験者ID

        Returns:
            省略形マッピング {"①": "材料名: 容量", ...}
        """
        if not materials_text.strip():
            return {}

        # プロンプトの構築
        prompt = f"""あなたは実験ノートの解析専門家です。
以下の材料リストを読み、番号や記号（①②③、(1)(2)(3)、1.2.3.など）と
それが指す材料名・容量の対応を抽出してください。

# 材料リスト
{materials_text}

# 出力形式（JSON）
{{
  "shortcuts": {{
    "①": "材料名: 容量",
    "②": "材料名: 容量"
  }}
}}

番号や記号がない場合は空のオブジェクトを返してください。
必ずJSON形式で出力してください。"""

        try:
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # JSONを抽出
            shortcuts = self._parse_shortcuts_response(response_text)
            print(f"実験者{experimenter_id}の省略形を学習しました: {len(shortcuts)}件")
            return shortcuts

        except Exception as e:
            print(f"省略形学習エラー: {e}")
            return {}

    def _parse_shortcuts_response(self, response_text: str) -> Dict[str, str]:
        """
        LLMレスポンスから省略形マッピングをパース

        Args:
            response_text: LLMのレスポンステキスト

        Returns:
            省略形マッピング
        """
        try:
            # JSON部分を抽出（コードブロック内の場合もあり）
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                return {}

            json_str = json_match.group(0)
            data = json.loads(json_str)

            # "shortcuts"キーがある場合はその中身を返す
            if 'shortcuts' in data:
                return data['shortcuts']

            # そうでなければ全体を返す（省略形マッピングとして解釈）
            return data

        except json.JSONDecodeError as e:
            print(f"JSONパースエラー: {e}")
            return {}

    def expand_shortcuts(self, text: str, experimenter_id: str) -> str:
        """
        テキスト内の省略形を展開

        Args:
            text: 展開対象のテキスト
            experimenter_id: 実験者ID

        Returns:
            省略形を展開したテキスト
        """
        profile = self.get_profile(experimenter_id)
        if not profile or not profile.material_shortcuts:
            return text

        expanded_text = text

        # 省略形を長い順にソート（部分一致を避けるため）
        sorted_shortcuts = sorted(
            profile.material_shortcuts.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for shortcut, material in sorted_shortcuts:
            # 省略形を材料名に置換
            # 様々な形式に対応: ①、(1)、1.、A. など
            expanded_text = expanded_text.replace(shortcut, material)

        return expanded_text

    def add_shortcut(
        self,
        experimenter_id: str,
        shortcut: str,
        material: str
    ) -> bool:
        """
        省略形を追加

        Args:
            experimenter_id: 実験者ID
            shortcut: 省略形（例: "①"）
            material: 材料名（例: "HbA1c捕捉抗体1: 1mL"）

        Returns:
            成功したかどうか
        """
        profile = self.get_profile(experimenter_id)
        if not profile:
            print(f"プロファイルが見つかりません: {experimenter_id}")
            return False

        profile.material_shortcuts[shortcut] = material
        profile.updated_at = datetime.now().isoformat()
        return self.save()

    def remove_shortcut(self, experimenter_id: str, shortcut: str) -> bool:
        """
        省略形を削除

        Args:
            experimenter_id: 実験者ID
            shortcut: 省略形（例: "①"）

        Returns:
            成功したかどうか
        """
        profile = self.get_profile(experimenter_id)
        if not profile:
            print(f"プロファイルが見つかりません: {experimenter_id}")
            return False

        if shortcut in profile.material_shortcuts:
            del profile.material_shortcuts[shortcut]
            profile.updated_at = datetime.now().isoformat()
            return self.save()

        return False


def get_experimenter_profile_manager(
    team_id: Optional[str] = None
) -> ExperimenterProfileManager:
    """
    実験者プロファイルマネージャーのインスタンスを取得

    Args:
        team_id: チームID（マルチテナント対応）

    Returns:
        ExperimenterProfileManagerインスタンス
    """
    return ExperimenterProfileManager(team_id=team_id)


# ============================================
# ノート単位の省略形解析機能（v3.2.0）
# ============================================

def extract_shortcuts_from_materials(materials_text: str, llm) -> Dict[str, str]:
    """
    LLMを使って材料セクションから省略形を動的に抽出（ノート単位）

    Args:
        materials_text: 材料セクションのテキスト
        llm: LangChainのLLMインスタンス

    Returns:
        省略形マッピング {"①": "材料名: 容量", ...}
    """
    if not materials_text.strip():
        return {}

    # プロンプトの構築
    prompt = f"""あなたは実験ノートの解析専門家です。
以下の材料リストを読み、番号や記号（①②③、(1)(2)(3)、1.2.3.など）と
それが指す材料名・容量の対応を抽出してください。

# 材料リスト
{materials_text}

# 出力形式（JSON）
{{
  "shortcuts": {{
    "①": "材料名: 容量",
    "②": "材料名: 容量"
  }}
}}

番号や記号がない場合は空のオブジェクトを返してください。
必ずJSON形式で出力してください。"""

    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # JSONを抽出
        return _parse_shortcuts_response(response_text)

    except Exception as e:
        print(f"省略形抽出エラー: {e}")
        return {}


def _parse_shortcuts_response(response_text: str) -> Dict[str, str]:
    """
    LLMレスポンスから省略形マッピングをパース

    Args:
        response_text: LLMのレスポンステキスト

    Returns:
        省略形マッピング
    """
    try:
        # JSON部分を抽出（コードブロック内の場合もあり）
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            return {}

        json_str = json_match.group(0)
        data = json.loads(json_str)

        # "shortcuts"キーがある場合はその中身を返す
        if 'shortcuts' in data:
            return data['shortcuts']

        # そうでなければ全体を返す（省略形マッピングとして解釈）
        return data

    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}")
        return {}


def _circled_to_int(char: str) -> Optional[int]:
    """
    丸数字を整数に変換

    Args:
        char: 丸数字（①〜㊿）

    Returns:
        整数値（1〜50）、変換できない場合はNone
    """
    code = ord(char)

    # ① (U+2460) 〜 ⑳ (U+2473) → 1〜20
    if 0x2460 <= code <= 0x2473:
        return code - 0x2460 + 1

    # ㉑ (U+3251) 〜 ㉟ (U+325F) → 21〜35
    if 0x3251 <= code <= 0x325F:
        return code - 0x3251 + 21

    # ㊱ (U+32B1) 〜 ㊿ (U+32BF) → 36〜50
    if 0x32B1 <= code <= 0x32BF:
        return code - 0x32B1 + 36

    return None


def _int_to_circled(num: int) -> Optional[str]:
    """
    整数を丸数字に変換

    Args:
        num: 整数値（1〜50）

    Returns:
        丸数字、変換できない場合はNone
    """
    if 1 <= num <= 20:
        return chr(0x2460 + num - 1)
    elif 21 <= num <= 35:
        return chr(0x3251 + num - 21)
    elif 36 <= num <= 50:
        return chr(0x32B1 + num - 36)
    return None


def expand_circled_number_ranges(text: str) -> str:
    """
    丸数字の範囲表記を展開（v3.2.2）

    例: "①〜③" → "①②③", "④～⑥" → "④⑤⑥"

    Args:
        text: 展開対象のテキスト

    Returns:
        範囲表記を展開したテキスト
    """
    # 範囲表記のパターン: ①〜③, ①～③, ①-③, ①―③
    # 丸数字 + 範囲記号 + 丸数字
    range_pattern = r'([①-⑳㉑-㉟㊱-㊿])([〜～\-―])([①-⑳㉑-㉟㊱-㊿])'

    def expand_range(match):
        start_char = match.group(1)
        range_symbol = match.group(2)
        end_char = match.group(3)

        start_num = _circled_to_int(start_char)
        end_num = _circled_to_int(end_char)

        if start_num is None or end_num is None:
            return match.group(0)  # 変換できない場合はそのまま

        if start_num > end_num:
            return match.group(0)  # 逆順の場合はそのまま

        # 範囲内のすべての丸数字を生成
        expanded = []
        for num in range(start_num, end_num + 1):
            circled = _int_to_circled(num)
            if circled:
                expanded.append(circled)

        return ''.join(expanded)

    return re.sub(range_pattern, expand_range, text)


def expand_shortcuts_in_text(text: str, shortcuts: Dict[str, str]) -> str:
    """
    テキスト内の省略形を展開

    v3.2.2: 範囲表記（①〜③など）を先に展開してから省略形置換

    Args:
        text: 展開対象のテキスト
        shortcuts: 省略形マッピング {"①": "材料名", ...}

    Returns:
        省略形を展開したテキスト
    """
    if not shortcuts:
        return text

    # v3.2.2: まず範囲表記を展開
    expanded_text = expand_circled_number_ranges(text)

    # 省略形を長い順にソート（部分一致を避けるため）
    sorted_shortcuts = sorted(
        shortcuts.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for shortcut, material in sorted_shortcuts:
        # 省略形を材料名に置換
        expanded_text = expanded_text.replace(shortcut, material)

    return expanded_text


def apply_suffix_mapping(text: str, suffix_conventions: List[List[str]]) -> str:
    """
    サフィックスマッピングを適用してテキスト内の表記を正規化（v3.2.0）

    例: suffix_conventions = [["A", "1"], ["B", "2"]] の場合
    "HbA1c捕捉抗体A" → "HbA1c捕捉抗体1"
    "HbA1c検出抗体B" → "HbA1c検出抗体2"

    Args:
        text: 変換対象のテキスト
        suffix_conventions: サフィックスマッピング [["元", "先"], ...]

    Returns:
        サフィックスを正規化したテキスト
    """
    if not suffix_conventions:
        return text

    result = text

    for mapping in suffix_conventions:
        if len(mapping) >= 2:
            from_suffix = mapping[0]
            to_suffix = mapping[1]

            # 材料名の末尾のサフィックスを置換
            # 例: "抗体A" → "抗体1", "抗体A（" → "抗体1（"
            # 単語境界を考慮したパターン
            patterns = [
                # 末尾パターン: "抗体A" → "抗体1"
                (rf'({from_suffix})(\s|$|[,，、。）\)])', rf'{to_suffix}\2'),
                # 括弧前パターン: "抗体A(" → "抗体1("
                (rf'({from_suffix})([（(])', rf'{to_suffix}\2'),
                # コロン前パターン: "抗体A:" → "抗体1:"
                (rf'({from_suffix})([:：])', rf'{to_suffix}\2'),
            ]

            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result)

    return result


def get_suffix_mapping_for_experimenter(
    experimenter_id: str,
    team_id: Optional[str] = None
) -> List[List[str]]:
    """
    実験者IDに基づいてサフィックスマッピングを取得（v3.2.0）

    Args:
        experimenter_id: 実験者ID
        team_id: チームID

    Returns:
        サフィックスマッピング [["A", "1"], ...]
    """
    manager = ExperimenterProfileManager(team_id=team_id)
    profile = manager.get_profile(experimenter_id)

    if profile and profile.suffix_conventions:
        return profile.suffix_conventions

    return []
