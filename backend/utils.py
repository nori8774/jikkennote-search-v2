"""
Utility functions for text normalization and term extraction
テキスト正規化と用語抽出のためのユーティリティ関数
"""
import yaml
import re
import unicodedata
import json
from typing import Dict, Set, List, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config import config
from storage import storage


def load_master_dict(path: str = None) -> Tuple[Dict[str, str], Set[str]]:
    """
    YAML辞書を読み込み、以下の2つを返します
    1. replace_map: 正規化用辞書 { "NaOH": "水酸化ナトリウム", ... }
    2. known_terms: 未知語チェック用セット { "水酸化ナトリウム", "NaOH", ... }
    """
    if path is None:
        path = config.MASTER_DICTIONARY_PATH

    try:
        content = storage.read_file(path)
        data = yaml.safe_load(content) or []
    except Exception:
        return {}, set()

    replace_map = {}
    known_terms = set()

    for entry in data:
        canonical = entry['canonical']
        variants = entry.get('variants', [])

        known_terms.add(canonical)
        replace_map[canonical] = canonical

        for v in variants:
            replace_map[v] = canonical
            known_terms.add(v)

    return replace_map, known_terms


def separate_number_and_unit(text: str) -> str:
    """100rpm -> 100 rpm のように数字と単位を分離"""
    pattern = r'(\d+)([a-zA-Z%℃°μΩ])'
    return re.sub(pattern, r'\1 \2', text)


def remove_redundant_parentheses(text: str) -> str:
    """TMP(TMP) -> TMP のように重複括弧を削除"""
    pattern = r'(?P<word>\S+)\s*[（(](?P=word)[）)]'
    return re.sub(pattern, r'\g<word>', text)


def normalize_text(text: str, replace_map: Dict[str, str]) -> str:
    """テキスト全体を正規化するメイン関数"""
    if not text:
        return ""

    text = unicodedata.normalize('NFKC', text)
    text = separate_number_and_unit(text)

    if replace_map:
        sorted_keys = sorted(replace_map.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in text:
                text = text.replace(key, replace_map[key])

    text = remove_redundant_parentheses(text)
    return text


def normalize_text_with_suffix(
    text: str,
    replace_map: Dict[str, str],
    suffix_maps: Dict[str, Dict[str, str]],
    canonicals: List[str]
) -> str:
    """
    サフィックス対応のテキスト正規化（v3.1.2）

    Args:
        text: 正規化するテキスト
        replace_map: 通常の正規化マップ（バリアント→canonical）
        suffix_maps: サフィックスマップ（{canonical: {suffix: representative}}）
        canonicals: 全ての正規化名リスト

    Returns:
        正規化されたテキスト
    """
    if not text:
        return ""

    # Step 1: Unicode正規化と単位分離
    text = unicodedata.normalize('NFKC', text)
    text = separate_number_and_unit(text)

    # Step 2: 通常のバリアント正規化
    if replace_map:
        sorted_keys = sorted(replace_map.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in text:
                text = text.replace(key, replace_map[key])

    # Step 3: サフィックス正規化
    if suffix_maps and canonicals:
        # 長い順にソート（最長一致）
        sorted_canonicals = sorted(canonicals, key=len, reverse=True)

        for canonical in sorted_canonicals:
            if canonical not in suffix_maps:
                continue

            suffix_map = suffix_maps[canonical]
            # テキスト内でcanonical + サフィックスのパターンを探す
            for suffix, representative in suffix_map.items():
                if suffix == representative:
                    continue  # 代表サフィックス自身はスキップ
                old_term = canonical + suffix
                new_term = canonical + representative
                if old_term in text:
                    text = text.replace(old_term, new_term)

    text = remove_redundant_parentheses(text)
    return text


def parse_json_garbage(text: str) -> any:
    """
    AIの返答から JSON 部分だけを無理やり抽出するヘルパー関数
    """
    text = text.strip()
    # Markdownのコードブロック削除
    text = re.sub(r'^```(json)?', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 単純パースで失敗した場合、正規表現で [ ] や { } を探す
        # リスト [...] を探す
        match_list = re.search(r'\[.*\]', text, re.DOTALL)
        if match_list:
            try:
                return json.loads(match_list.group(0))
            except:
                pass

        # 辞書 {...} を探す
        match_dict = re.search(r'\{.*\}', text, re.DOTALL)
        if match_dict:
            try:
                return json.loads(match_dict.group(0))
            except:
                pass

        # どうしてもダメならエラー
        raise ValueError("Could not parse JSON from LLM response")


def extract_unknown_terms(text: str, known_terms: Set[str], api_key: str, model: str = "gpt-4o") -> List[str]:
    """LLMを使用して未知語を抽出"""
    if not text or len(text) < 5:
        return []

    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)

    prompt = f"""
    あなたは化学・実験データの専門家です。
    以下の実験ノートのテキストから、辞書に登録すべき**「専門用語」「化学物質名」「試薬名」「実験器具名」「特殊な実験操作名」**を抽出してください。

    # 除外ルール（抽出してはいけないもの）:
    - 一般的な動詞や名詞（例：開始、終了、時間、結果、測定、確認、使用、ビーカー、実験）
    - 数値や単位のみ（例：100mL, 50g, 10分）
    - 既に知られている以下の単語: {list(known_terms)[:50]}... (省略)

    # 出力形式:
    必ず JSON形式のリスト `["単語1", "単語2"]` のみを出力してください。
    解説やMarkdownタグは一切不要です。

    # 対象テキスト:
    {text}
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # 強化したパース関数を通す
        extracted_terms = parse_json_garbage(response.content)

        unknowns = set()
        for term in extracted_terms:
            term = str(term).strip()
            if term not in known_terms and not term.replace('.', '').isnumeric():
                unknowns.add(term)

        return sorted(list(unknowns))

    except Exception as e:
        # エラー時は空リストを返して処理を止めない
        print(f"  ⚠️ Extraction Error: {e}")
        return []


def find_similar_terms(new_terms: List[str], existing_canonicals: List[str], api_key: str, model: str = "gpt-4o") -> Dict[str, Optional[str]]:
    """LLMを使用して類似語を判定"""
    if not new_terms or not existing_canonicals:
        return {term: None for term in new_terms}

    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)

    prompt = f"""
    タスク: 新しい専門用語が、既存の用語リストにある単語の「表記ゆれ」「略語」「同義語」であるかを判定してください。

    # 新しい用語リスト:
    {json.dumps(new_terms, ensure_ascii=False)}

    # 既存の正規化済み用語リスト(Canonical):
    {json.dumps(list(existing_canonicals)[:3000], ensure_ascii=False)}
    (※リストが長い場合は一部省略されています)

    # 指示:
    各「新しい用語」について、もし「既存の用語リスト」の中に同一の意味を持つと思われる単語があれば、その既存単語を返してください。
    該当するものがない場合は null を返してください。

    # 出力形式 (JSON):
    必ず JSONオブジェクト `{{ "新語A": "既存語X", "新語B": null }}` のみを出力してください。
    解説やMarkdownタグは一切不要です。
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # 強化したパース関数を通す
        result = parse_json_garbage(response.content)
        return result

    except Exception as e:
        # エラー時は全てNone（類似なし）として返す
        print(f"  ⚠️ Similarity Check Error: {e}")
        return {term: None for term in new_terms}
