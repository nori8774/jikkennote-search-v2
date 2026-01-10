"""
Ingest notes into vector database
実験ノートをベクトルデータベースに取り込む
増分更新対応（既存ノートはスキップ）
"""
import os
import re
import time
from typing import Dict, List, Tuple
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from config import config
from utils import load_master_dict, normalize_text
from storage import storage
from synonym_dictionary import get_synonym_dictionary, normalize_text_with_synonyms
from chroma_sync import (
    get_chroma_vectorstore,
    get_team_chroma_vectorstore,
    get_team_multi_collection_vectorstores,
    sync_chroma_to_gcs
)
# v3.2.0: 省略形展開処理を廃止（検索時にLLMが文脈から解釈）
# from experimenter_profile import (
#     extract_shortcuts_from_materials,
#     expand_shortcuts_in_text,
#     apply_suffix_mapping,
#     ExperimenterProfileManager
# )


def extract_sections(content: str) -> Dict[str, str]:
    """
    マークダウンノートから材料・方法セクションを抽出する（v3.2.0変更: 2コレクション対応）

    Args:
        content: ノート全体のMarkdownテキスト

    Returns:
        dict: {
            "materials_methods": 材料+方法セクションを結合したテキスト（v3.2.0新規）,
            "combined": ノート全体のテキスト
        }

    Note:
        v3.2.0: 3コレクション→2コレクション構成に変更
        - 旧: materials, methods, combined（個別コレクション）
        - 新: materials_methods（結合）, combined（2コレクション）
    """
    materials = ""
    methods = ""

    # 材料セクションの抽出（## 材料 または ## Materials）
    # 次のセクション（## で始まる行）までを抽出
    materials_patterns = [
        r'## 材料\s*\n(.*?)(?=\n## |\Z)',
        r'## Materials\s*\n(.*?)(?=\n## |\Z)',
        r'## material\s*\n(.*?)(?=\n## |\Z)',
    ]
    for pattern in materials_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            materials = match.group(1).strip()
            break

    # 方法セクションの抽出（## 方法 または ## Methods）
    methods_patterns = [
        r'## 方法\s*\n(.*?)(?=\n## |\Z)',
        r'## Methods\s*\n(.*?)(?=\n## |\Z)',
        r'## method\s*\n(.*?)(?=\n## |\Z)',
        r'## 手順\s*\n(.*?)(?=\n## |\Z)',
        r'## Procedure\s*\n(.*?)(?=\n## |\Z)',
        r'## 実験手順\s*\n(.*?)(?=\n## |\Z)',
    ]
    for pattern in methods_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            methods = match.group(1).strip()
            break

    # v3.2.0: 材料+方法を結合（LLMが番号と材料名の対応を文脈で理解できるように）
    materials_methods = ""
    if materials or methods:
        parts = []
        if materials:
            parts.append(f"## 材料\n{materials}")
        if methods:
            parts.append(f"## 方法\n{methods}")
        materials_methods = "\n\n".join(parts)

    return {
        "materials_methods": materials_methods,
        "combined": content
    }


def parse_markdown_note(file_path: str, norm_map: dict) -> Dict:
    """マークダウンノートをパースして構造化データを返す"""
    content = storage.read_file(file_path)

    # パスから最後の部分を取得してノートIDに
    note_id = file_path.split('/')[-1].replace('.md', '')

    # 材料セクションから検索用キーワードを抽出して正規化
    materials_match = re.search(r'## 材料\n(.*?)\n##', content, re.DOTALL)
    materials_text = materials_match.group(1).strip() if materials_match else ""

    normalized_keywords = []
    if materials_text:
        lines = materials_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 簡易パース
            clean_line = re.sub(r'^[-・*]*\s*', '', line)
            parts = re.split(r'[:：]', clean_line, 1)
            raw_term = parts[0].strip()

            # 正規化
            norm_term = normalize_text(raw_term, norm_map)
            if norm_term:
                normalized_keywords.append(norm_term)

    return {
        "id": note_id,
        "full_content": content,
        "search_keywords": list(set(normalized_keywords))  # 重複排除
    }


def get_existing_ids(vectorstore) -> List[str]:
    """ChromaDBに既に登録されているドキュメントのソースID一覧を取得"""
    try:
        data = vectorstore.get()
        existing_ids = []
        if data and data['metadatas']:
            for meta in data['metadatas']:
                if meta and 'source' in meta:
                    existing_ids.append(meta['source'])
        return list(set(existing_ids))
    except Exception:
        return []


def ingest_notes(
    api_key: str,
    source_folder: str = None,
    post_action: str = 'move_to_processed',
    archive_folder: str = None,
    embedding_model: str = None,
    rebuild_mode: bool = False,
    team_id: str = None,  # v3.0: マルチテナント対応
    multi_collection: bool = True,  # v3.2.0: 2コレクション対応（デフォルト: True）
    use_synonym_normalization: bool = True,  # v3.2.1: 同義語正規化（デフォルト: True）
) -> Tuple[List[str], List[str]]:
    """
    ノートをデータベースに取り込む（増分更新）（v3.2.0簡素化版）

    Args:
        api_key: OpenAI APIキー
        source_folder: 新規ノートフォルダパス（デフォルト: notes/new）
        post_action: 取り込み後のアクション ('move_to_processed', 'delete', 'archive', 'keep')
        archive_folder: アーカイブ先フォルダパス（後方互換性のため残す）
        embedding_model: 使用するEmbeddingモデル
        rebuild_mode: ChromaDBリセット後の再構築モード（デフォルト: False）
        team_id: チームID（v3.0）
        multi_collection: 2コレクションモード（v3.2.0変更）
            - True: materials_methods（材料+方法結合）とcombined（全体）の2コレクションに登録
            - False: 従来の単一コレクション（ノート全体のみ）
        use_synonym_normalization: 同義語辞書による正規化（v3.2.1追加）
            - True: 取り込み時に同義語辞書を使って表記を統一（例: 精製水→純水）
            - False: 同義語正規化を行わない（検索時の展開に依存）

    Returns:
        (new_notes, skipped_notes): 取り込んだノートIDと既存のノートID

    Note:
        v3.2.0: 省略形展開処理を廃止。検索時にLLMが文脈から材料名と番号の対応を解釈する方式に変更。
    """
    # パラメータのデフォルト値設定（v3.0: チーム対応）
    if team_id:
        # マルチテナントモード: チーム専用パスを使用
        if rebuild_mode:
            source_folder = source_folder or storage.get_team_path(team_id, 'notes_processed')
            post_action = 'keep'
        else:
            source_folder = source_folder or storage.get_team_path(team_id, 'notes_new')
            post_action = post_action or 'move_to_processed'

        archive_folder = archive_folder or f"{storage.get_team_path(team_id, 'notes_new')}/archive"
        processed_folder = storage.get_team_path(team_id, 'notes_processed')
    else:
        # 後方互換性: グローバルパスを使用
        if rebuild_mode:
            source_folder = source_folder or config.NOTES_PROCESSED_FOLDER
            post_action = 'keep'
        else:
            source_folder = source_folder or config.NOTES_NEW_FOLDER
            post_action = post_action or 'move_to_processed'

        archive_folder = archive_folder or config.NOTES_ARCHIVE_FOLDER
        processed_folder = config.NOTES_PROCESSED_FOLDER

    embedding_model = embedding_model or config.DEFAULT_EMBEDDING_MODEL

    # 処理時間計測開始
    total_start_time = time.time()
    timing_stats = {
        "dictionary_load": 0.0,
        "synonym_load": 0.0,
        "file_scan": 0.0,
        "normalization_total": 0.0,
        "embedding_total": 0.0,
        "file_move": 0.0,
        "total": 0.0
    }

    # フォルダ確認（ストレージ抽象化に対応）
    storage.mkdir(source_folder)

    # 正規化辞書のロード
    dict_start = time.time()
    norm_map, _ = load_master_dict()
    timing_stats["dictionary_load"] = time.time() - dict_start
    print(f"正規化辞書ロード: {len(norm_map)} エントリ ({timing_stats['dictionary_load']:.2f}秒)")

    # 同義語辞書のロード（v3.2.1: 取り込み時正規化用）
    synonym_dict = None
    if use_synonym_normalization:
        synonym_start = time.time()
        synonym_dict = get_synonym_dictionary(team_id=team_id)
        timing_stats["synonym_load"] = time.time() - synonym_start
        print(f"同義語辞書ロード: {len(synonym_dict.groups)} グループ ({timing_stats['synonym_load']:.2f}秒)")
    else:
        print("同義語正規化: 無効（検索時の展開に依存）")

    # v3.2.0: 省略形展開処理を廃止（LLM初期化、プロファイルマネージャー不要）

    # ChromaDBの初期化（v3.2.0: 2コレクション対応）
    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)

    if team_id and multi_collection:
        # v3.2.0: 2コレクションモード
        vectorstores = get_team_multi_collection_vectorstores(
            team_id=team_id,
            embeddings=embeddings,
            embedding_model=embedding_model
        )
        # 既存IDチェックはcombinedコレクションを使用
        primary_vectorstore = vectorstores["combined"]
        print("2コレクションモード: materials_methods, combinedに登録します")
    elif team_id:
        vectorstores = None
        primary_vectorstore = get_team_chroma_vectorstore(
            team_id=team_id,
            embeddings=embeddings,
            embedding_model=embedding_model
        )
    else:
        vectorstores = None
        primary_vectorstore = get_chroma_vectorstore(embeddings, embedding_model=embedding_model)

    # 既存データの確認（増分更新のため）
    if rebuild_mode:
        # 再構築モード：既存IDのチェックをスキップ（全て取り込む）
        existing_ids = []
        print("再構築モード: 全てのノートを取り込みます")
    else:
        existing_ids = get_existing_ids(primary_vectorstore)
        print(f"既存の登録ノート数: {len(existing_ids)}")

    # ファイルスキャンと新規判定
    file_scan_start = time.time()
    files = storage.list_files(prefix=source_folder, pattern="*.md")
    timing_stats["file_scan"] = time.time() - file_scan_start
    print(f"ファイルスキャン: {len(files)} ファイル ({timing_stats['file_scan']:.2f}秒)")

    # v3.2.0: 2コレクション用のドキュメントリスト
    materials_methods_docs = []
    combined_docs = []
    skipped_ids = []
    new_ids = []
    normalization_times = []

    for file in files:
        note_id = file.split('/')[-1].replace('.md', '')

        # 既にDBにあるIDならスキップ（再構築モードではスキップしない）
        if not rebuild_mode and note_id in existing_ids:
            print(f"Skip: {note_id} (既に存在します)")
            skipped_ids.append(note_id)
            continue

        # 新規ファイルのパース
        data = parse_markdown_note(file, norm_map)
        content = data["full_content"]

        # v3.2.0: セクション抽出（材料+方法結合版）
        sections = extract_sections(content)

        # v3.2.1: 同義語辞書による正規化（取り込み時に表記統一）+ 時間計測
        norm_start = time.time()

        # Step 1: 基本正規化（master_dictionary）
        materials_methods_normalized = normalize_text(sections["materials_methods"], norm_map) if sections["materials_methods"] else ""
        combined_normalized = normalize_text(sections["combined"], norm_map) if sections["combined"] else ""

        # Step 2: 同義語辞書による正規化（バリアント→canonical）
        if use_synonym_normalization and synonym_dict and synonym_dict.groups:
            materials_methods_normalized = normalize_text_with_synonyms(materials_methods_normalized, synonym_dict)
            combined_normalized = normalize_text_with_synonyms(combined_normalized, synonym_dict)

        norm_time = time.time() - norm_start
        normalization_times.append(norm_time)

        base_metadata = {
            "source": data["id"],
            "note_id": data["id"],
            "materials": ", ".join(data["search_keywords"])
        }

        print(f"Processing New File: {data['id']} -> Keywords: {base_metadata['materials']}")

        if multi_collection and vectorstores:
            # v3.2.0: 2コレクションモード
            # 材料+方法セクション（空でない場合のみ）
            if materials_methods_normalized:
                materials_methods_docs.append(Document(
                    page_content=materials_methods_normalized,
                    metadata={**base_metadata, "section_type": "materials_methods"}
                ))
            else:
                print(f"  警告: {data['id']} - 材料・方法セクションが見つかりません")

            # 総合（ノート全体）
            combined_docs.append(Document(
                page_content=combined_normalized,
                metadata={**base_metadata, "section_type": "combined"}
            ))
        else:
            # 従来モード: ノート全体のみ
            combined_docs.append(Document(
                page_content=normalize_text(content, norm_map),
                metadata=base_metadata
            ))

        new_ids.append(note_id)

    # 正規化時間の集計
    if normalization_times:
        timing_stats["normalization_total"] = sum(normalization_times)
        avg_norm_time = timing_stats["normalization_total"] / len(normalization_times)
        print(f"正規化処理: 合計 {timing_stats['normalization_total']:.2f}秒, 平均 {avg_norm_time*1000:.1f}ms/ノート")

    # DBへの追加登録（バッチ処理）
    embedding_start = time.time()
    if new_ids:
        print(f"{len(new_ids)} 件の新規ノートをデータベースに追加しています...")

        # バッチサイズ（トークン制限を考慮して50件ずつ処理）
        BATCH_SIZE = 50

        if multi_collection and vectorstores:
            # v3.2.0: 2コレクションに登録
            for collection_name, docs, vectorstore in [
                ("materials_methods", materials_methods_docs, vectorstores["materials_methods"]),
                ("combined", combined_docs, vectorstores["combined"])
            ]:
                if not docs:
                    print(f"  {collection_name}: 登録するドキュメントなし")
                    continue

                print(f"\n  {collection_name}コレクション: {len(docs)}件を登録中...")
                total_batches = (len(docs) + BATCH_SIZE - 1) // BATCH_SIZE

                for i in range(0, len(docs), BATCH_SIZE):
                    batch = docs[i:i + BATCH_SIZE]
                    batch_num = (i // BATCH_SIZE) + 1
                    print(f"    バッチ {batch_num}/{total_batches}: {len(batch)}件を処理中...")

                    try:
                        vectorstore.add_documents(documents=batch)
                        print(f"    バッチ {batch_num}/{total_batches}: 完了")
                    except Exception as e:
                        print(f"    バッチ {batch_num}/{total_batches}: エラー - {str(e)}")
                        continue

        else:
            # 従来モード: 単一コレクションに登録
            total_batches = (len(combined_docs) + BATCH_SIZE - 1) // BATCH_SIZE

            for i in range(0, len(combined_docs), BATCH_SIZE):
                batch = combined_docs[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                print(f"  バッチ {batch_num}/{total_batches}: {len(batch)}件を処理中...")

                try:
                    primary_vectorstore.add_documents(documents=batch)
                    print(f"  バッチ {batch_num}/{total_batches}: 完了")
                except Exception as e:
                    print(f"  バッチ {batch_num}/{total_batches}: エラー - {str(e)}")
                    continue

        timing_stats["embedding_total"] = time.time() - embedding_start
        print(f"\n登録完了。(Embedding生成+DB追加: {timing_stats['embedding_total']:.2f}秒)")

        # GCSに同期（本番環境のみ）
        sync_chroma_to_gcs()

        # ファイル処理（post_action に応じて）
        file_move_start = time.time()
        for note_id in new_ids:
            file_path = f"{source_folder}/{note_id}.md"

            if post_action == 'move_to_processed':
                # processedフォルダに移動（デフォルト動作）
                storage.mkdir(processed_folder)
                dest_path = f"{processed_folder}/{note_id}.md"
                storage.move_file(file_path, dest_path)
                print(f"  Moved to processed: {file_path} -> {dest_path}")

            elif post_action == 'delete':
                storage.delete_file(file_path)
                print(f"  Deleted: {file_path}")

            elif post_action == 'archive':
                # アーカイブフォルダ作成（後方互換性のため残す）
                storage.mkdir(archive_folder)
                dest_path = f"{archive_folder}/{note_id}.md"
                storage.move_file(file_path, dest_path)
                print(f"  Archived: {file_path} -> {dest_path}")

            elif post_action == 'keep':
                print(f"  Kept: {file_path}")

        timing_stats["file_move"] = time.time() - file_move_start

    else:
        print("新規に追加すべきノートはありませんでした。")

    # 処理時間の最終集計
    timing_stats["total"] = time.time() - total_start_time

    print("\n" + "=" * 50)
    print("処理時間サマリー")
    print("=" * 50)
    print(f"  辞書ロード（正規化）: {timing_stats['dictionary_load']:.2f}秒")
    print(f"  辞書ロード（同義語）: {timing_stats['synonym_load']:.2f}秒")
    print(f"  ファイルスキャン: {timing_stats['file_scan']:.2f}秒")
    print(f"  正規化処理: {timing_stats['normalization_total']:.2f}秒")
    print(f"  Embedding生成+DB追加: {timing_stats['embedding_total']:.2f}秒")
    print(f"  ファイル移動: {timing_stats['file_move']:.2f}秒")
    print("-" * 50)
    print(f"  合計: {timing_stats['total']:.2f}秒")
    if new_ids:
        print(f"  1ノートあたり平均: {timing_stats['total']/len(new_ids):.2f}秒")
    print("=" * 50)

    return new_ids, skipped_ids


def ingest_notes_with_auto_dictionary(
    api_key: str,
    source_folder: str = None,
    post_action: str = 'move_to_processed',
    archive_folder: str = None,
    embedding_model: str = None,
    rebuild_mode: bool = False,
    auto_update_dictionary: bool = True
) -> Tuple[List[str], List[str], Dict]:
    """
    ノートを取り込み、自動的に辞書を更新する（拡張版）

    Args:
        api_key: OpenAI APIキー
        source_folder: 新規ノートフォルダパス
        post_action: 取り込み後のアクション
        archive_folder: アーカイブ先フォルダパス
        embedding_model: Embeddingモデル
        rebuild_mode: 再構築モード
        auto_update_dictionary: 辞書の自動更新を有効にするか

    Returns:
        (new_notes, skipped_notes, dictionary_update_result)
    """
    # 通常のingestを実行
    new_ids, skipped_ids = ingest_notes(
        api_key=api_key,
        source_folder=source_folder,
        post_action=post_action,
        archive_folder=archive_folder,
        embedding_model=embedding_model,
        rebuild_mode=rebuild_mode
    )

    dictionary_result = {
        'patterns_added': 0,
        'variants_detected': 0,
        'auto_updated': False
    }

    return new_ids, skipped_ids, dictionary_result
