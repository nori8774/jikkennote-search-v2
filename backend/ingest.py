"""
Ingest notes into vector database
実験ノートをベクトルデータベースに取り込む
増分更新対応（既存ノートはスキップ）
"""
import os
import re
from typing import Dict, List, Tuple
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from config import config
from utils import load_master_dict, normalize_text
from storage import storage
from chroma_sync import (
    get_chroma_vectorstore,
    get_team_chroma_vectorstore,
    get_team_multi_collection_vectorstores,
    sync_chroma_to_gcs
)
from experimenter_profile import (
    extract_shortcuts_from_materials,
    expand_shortcuts_in_text,
    apply_suffix_mapping,
    ExperimenterProfileManager
)


def extract_sections(content: str) -> Dict[str, str]:
    """
    マークダウンノートから材料・方法セクションを抽出する（v3.1.1新規）

    Args:
        content: ノート全体のMarkdownテキスト

    Returns:
        dict: {
            "materials": 材料セクションのテキスト（見つからない場合は空文字列）,
            "methods": 方法セクションのテキスト（見つからない場合は空文字列）,
            "combined": ノート全体のテキスト
        }
    """
    sections = {
        "materials": "",
        "methods": "",
        "combined": content
    }

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
            sections["materials"] = match.group(1).strip()
            break

    # 方法セクションの抽出（## 方法 または ## Methods）
    methods_patterns = [
        r'## 方法\s*\n(.*?)(?=\n## |\Z)',
        r'## Methods\s*\n(.*?)(?=\n## |\Z)',
        r'## method\s*\n(.*?)(?=\n## |\Z)',
        r'## 手順\s*\n(.*?)(?=\n## |\Z)',
        r'## Procedure\s*\n(.*?)(?=\n## |\Z)',
        r'## 実験手順\s*\n(.*?)(?=\n## |\Z)',  # v3.2.0: 「実験手順」パターン追加
    ]
    for pattern in methods_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            sections["methods"] = match.group(1).strip()
            break

    return sections


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
    multi_collection: bool = True,  # v3.1.1: 3コレクション対応（デフォルト: True）
    expand_shortcuts: bool = True  # v3.2.0: 省略形展開機能（デフォルト: True）
) -> Tuple[List[str], List[str]]:
    """
    ノートをデータベースに取り込む（増分更新）

    Args:
        api_key: OpenAI APIキー
        source_folder: 新規ノートフォルダパス（デフォルト: notes/new）
        post_action: 取り込み後のアクション ('move_to_processed', 'delete', 'archive', 'keep')
        archive_folder: アーカイブ先フォルダパス（後方互換性のため残す）
        embedding_model: 使用するEmbeddingモデル
        rebuild_mode: ChromaDBリセット後の再構築モード（デフォルト: False）
        team_id: チームID（v3.0）
        multi_collection: 3コレクションモード（v3.1.1）
            - True: 材料/方法/総合の3コレクションに登録
            - False: 従来の単一コレクション（ノート全体のみ）
        expand_shortcuts: 省略形展開機能（v3.2.0）
            - True: 方法セクションの省略形（①②③等）を材料名に展開
            - False: 展開せずにそのまま登録

    Returns:
        (new_notes, skipped_notes): 取り込んだノートIDと既存のノートID
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

    # フォルダ確認（ストレージ抽象化に対応）
    storage.mkdir(source_folder)

    # 正規化辞書のロード
    norm_map, _ = load_master_dict()
    print(f"正規化辞書ロード: {len(norm_map)} エントリ")

    # v3.2.0: 実験者プロファイルマネージャーの初期化（サフィックスマッピング用）
    profile_manager = None
    if team_id:
        try:
            profile_manager = ExperimenterProfileManager(team_id=team_id)
            print(f"実験者プロファイルをロード: {len(profile_manager.experimenters)}件")
        except Exception as e:
            print(f"プロファイルロードエラー: {e}")
            profile_manager = None

    # v3.2.0: 省略形展開用のLLMを初期化（expand_shortcutsが有効な場合）
    shortcut_llm = None
    if expand_shortcuts:
        try:
            from langchain_openai import ChatOpenAI
            shortcut_llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)
            print("省略形展開: LLMを初期化しました")
        except Exception as e:
            print(f"省略形展開LLM初期化エラー: {e}")
            shortcut_llm = None

    # ChromaDBの初期化（v3.1.1: 3コレクション対応）
    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)

    if team_id and multi_collection:
        # v3.1.1: 3コレクションモード
        vectorstores = get_team_multi_collection_vectorstores(
            team_id=team_id,
            embeddings=embeddings,
            embedding_model=embedding_model
        )
        # 既存IDチェックはcombinedコレクションを使用
        primary_vectorstore = vectorstores["combined"]
        print("3コレクションモード: materials, methods, combinedに登録します")
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
    files = storage.list_files(prefix=source_folder, pattern="*.md")

    # 3コレクション用のドキュメントリスト
    materials_docs = []
    methods_docs = []
    combined_docs = []
    skipped_ids = []
    new_ids = []

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

        # v3.1.1: セクション抽出
        sections = extract_sections(content)

        # v3.2.1: 辞書による名寄せ（材料・方法セクションを正規化）
        materials_normalized = normalize_text(sections["materials"], norm_map) if sections["materials"] else ""
        methods_normalized = normalize_text(sections["methods"], norm_map) if sections["methods"] else ""
        combined_normalized = normalize_text(sections["combined"], norm_map) if sections["combined"] else ""

        # v3.2.0: サフィックスマッピングの適用（実験者プロファイルに基づく）
        materials_text_for_embedding = materials_normalized
        suffix_conventions = []
        if profile_manager:
            experimenter_id = profile_manager.get_experimenter_id(note_id)
            if experimenter_id:
                profile = profile_manager.get_profile(experimenter_id)
                if profile and profile.suffix_conventions:
                    suffix_conventions = profile.suffix_conventions
                    # 材料セクションにサフィックスマッピングを適用
                    materials_text_for_embedding = apply_suffix_mapping(
                        sections["materials"],
                        suffix_conventions
                    )
                    if materials_text_for_embedding != sections["materials"]:
                        print(f"  サフィックス正規化: {note_id} (実験者{experimenter_id})")

        # v3.2.0: 省略形展開処理（ノートごとに材料セクションから動的解析）
        methods_text_for_embedding = methods_normalized
        if expand_shortcuts and shortcut_llm and sections["materials"] and sections["methods"]:
            try:
                # 材料セクションから省略形マッピングを動的に抽出
                shortcuts = extract_shortcuts_from_materials(sections["materials"], shortcut_llm)

                if shortcuts:
                    # 抽出した省略形で方法セクションを展開
                    methods_text_for_embedding = expand_shortcuts_in_text(
                        sections["methods"],
                        shortcuts
                    )
                    if methods_text_for_embedding != sections["methods"]:
                        print(f"  省略形展開: {note_id} ({len(shortcuts)}件のマッピング)")
            except Exception as e:
                print(f"  省略形展開エラー ({note_id}): {e}")

        # v3.2.0: 方法セクションにもサフィックスマッピングを適用
        if suffix_conventions and methods_text_for_embedding:
            methods_text_for_embedding = apply_suffix_mapping(
                methods_text_for_embedding,
                suffix_conventions
            )

        base_metadata = {
            "source": data["id"],
            "note_id": data["id"],  # v3.1.1: note_idでマージするため追加
            "materials": ", ".join(data["search_keywords"])
        }

        print(f"Processing New File: {data['id']} -> Keywords: {base_metadata['materials']}")

        if multi_collection and vectorstores:
            # 3コレクションモード: 各セクションを別々のドキュメントとして追加
            # 材料セクション（空でない場合のみ）
            # v3.2.0: サフィックス正規化済みのテキストを使用
            if materials_text_for_embedding:
                materials_docs.append(Document(
                    page_content=materials_text_for_embedding,
                    metadata={**base_metadata, "section_type": "materials"}
                ))
            else:
                print(f"  警告: {data['id']} - 材料セクションが見つかりません")

            # 方法セクション（空でない場合のみ）
            # v3.2.0: 省略形展開済みのテキストを使用
            if methods_text_for_embedding:
                methods_docs.append(Document(
                    page_content=methods_text_for_embedding,
                    metadata={**base_metadata, "section_type": "methods"}
                ))
            else:
                print(f"  警告: {data['id']} - 方法セクションが見つかりません")

            # 総合（ノート全体）
            # v3.2.1: 辞書正規化済みのテキストを使用
            combined_docs.append(Document(
                page_content=combined_normalized,
                metadata={**base_metadata, "section_type": "combined"}
            ))
        else:
            # 従来モード: ノート全体のみ
            # v3.2.1: 辞書正規化済みのテキストを使用
            combined_docs.append(Document(
                page_content=normalize_text(content, norm_map),
                metadata=base_metadata
            ))

        new_ids.append(note_id)

    # DBへの追加登録（バッチ処理）
    if new_ids:
        print(f"{len(new_ids)} 件の新規ノートをデータベースに追加しています...")

        # バッチサイズ（トークン制限を考慮して50件ずつ処理）
        BATCH_SIZE = 50

        if multi_collection and vectorstores:
            # v3.1.1: 3コレクションに登録
            for collection_name, docs, vectorstore in [
                ("materials", materials_docs, vectorstores["materials"]),
                ("methods", methods_docs, vectorstores["methods"]),
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

        print("\n登録完了。")

        # GCSに同期（本番環境のみ）
        sync_chroma_to_gcs()

        # ファイル処理（post_action に応じて）
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

    else:
        print("新規に追加すべきノートはありませんでした。")

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
