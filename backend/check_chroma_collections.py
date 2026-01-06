#!/usr/bin/env python3
"""
ChromaDBコレクションの確認スクリプト

チーム別のコレクションとドキュメント数を表示します。
"""

import chromadb
from pathlib import Path
import os

def check_collections():
    """全てのChromaDBコレクションを確認"""

    # ローカルモードの場合
    local_collections = []

    # teams/配下のchroma-dbフォルダを探す
    teams_dir = Path("teams")
    if teams_dir.exists():
        for team_folder in teams_dir.iterdir():
            if team_folder.is_dir():
                team_id = team_folder.name
                chroma_path = team_folder / "chroma-db"

                if chroma_path.exists():
                    try:
                        client = chromadb.PersistentClient(path=str(chroma_path))
                        collections = client.list_collections()

                        for collection in collections:
                            count = collection.count()
                            local_collections.append({
                                'team_id': team_id,
                                'collection_name': collection.name,
                                'document_count': count,
                                'path': str(chroma_path)
                            })
                    except Exception as e:
                        print(f"Error reading {chroma_path}: {e}")

    # グローバルコレクション（後方互換性）
    global_chroma_path = Path("/tmp/chroma_db")
    if global_chroma_path.exists():
        try:
            client = chromadb.PersistentClient(path=str(global_chroma_path))
            collections = client.list_collections()

            for collection in collections:
                count = collection.count()
                local_collections.append({
                    'team_id': 'GLOBAL',
                    'collection_name': collection.name,
                    'document_count': count,
                    'path': str(global_chroma_path)
                })
        except Exception as e:
            print(f"Error reading global ChromaDB: {e}")

    return local_collections

def main():
    print("=" * 70)
    print("ChromaDB コレクション確認")
    print("=" * 70)

    collections = check_collections()

    if not collections:
        print("\n⚠️  ChromaDBコレクションが見つかりませんでした。")
        print("ノートを取り込んでからもう一度実行してください。")
        return

    print(f"\n見つかったコレクション数: {len(collections)}\n")

    for col in collections:
        print(f"チームID: {col['team_id']}")
        print(f"  コレクション名: {col['collection_name']}")
        print(f"  ドキュメント数: {col['document_count']}")
        print(f"  パス: {col['path']}")
        print()

    # チーム別サマリー
    team_summary = {}
    for col in collections:
        team_id = col['team_id']
        if team_id not in team_summary:
            team_summary[team_id] = 0
        team_summary[team_id] += col['document_count']

    print("-" * 70)
    print("チーム別ドキュメント数:")
    for team_id, count in team_summary.items():
        print(f"  {team_id}: {count}件")
    print("-" * 70)

if __name__ == "__main__":
    main()
