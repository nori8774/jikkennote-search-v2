"""
チーム管理モジュール

Firestoreを使用したチーム管理機能を提供します。
"""

import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from firebase_init import get_firestore_client
from google.cloud.firestore_v1 import FieldFilter
from storage import storage


def generate_invite_code() -> str:
    """
    招待コードを生成する

    形式: ABC-XYZ-123（3文字-3文字-3桁の数字）

    Returns:
        招待コード
    """
    part1 = ''.join(random.choices(string.ascii_uppercase, k=3))
    part2 = ''.join(random.choices(string.ascii_uppercase, k=3))
    part3 = ''.join(random.choices(string.digits, k=3))
    return f"{part1}-{part2}-{part3}"


def create_team_folders_in_gcs(team_id: str) -> None:
    """
    GCSにチーム用フォルダを作成する

    Args:
        team_id: チームID

    Note:
        以下のフォルダ構造を作成:
        - teams/{team_id}/chroma-db/
        - teams/{team_id}/notes/new/
        - teams/{team_id}/notes/processed/
        - teams/{team_id}/saved_prompts/
        - teams/{team_id}/dictionary.yaml
    """
    # GCSモードの場合のみフォルダ作成
    if storage.storage_type != 'gcs':
        return

    # 各フォルダに .gitkeep を配置してフォルダを作成
    folders = [
        f"teams/{team_id}/chroma-db/.gitkeep",
        f"teams/{team_id}/notes/new/.gitkeep",
        f"teams/{team_id}/notes/processed/.gitkeep",
        f"teams/{team_id}/saved_prompts/.gitkeep",
    ]

    for folder_path in folders:
        try:
            storage.bucket.blob(folder_path).upload_from_string('')
        except Exception as e:
            print(f"Warning: Failed to create folder {folder_path}: {e}")

    # 空の辞書ファイルを作成
    try:
        dictionary_content = "# Team Dictionary\n# Format: canonical: [variant1, variant2, ...]\n"
        storage.bucket.blob(f"teams/{team_id}/dictionary.yaml").upload_from_string(dictionary_content)
    except Exception as e:
        print(f"Warning: Failed to create dictionary file: {e}")


def create_team(
    user_id: str,
    user_email: str,
    user_display_name: Optional[str],
    name: str,
    description: Optional[str] = None
) -> Dict:
    """
    新しいチームを作成する

    Args:
        user_id: 作成者のFirebase UID
        user_email: 作成者のメールアドレス
        user_display_name: 作成者の表示名
        name: チーム名
        description: チーム説明（オプション）

    Returns:
        作成されたチーム情報（id, name, inviteCodeを含む）
    """
    db = get_firestore_client()

    # 招待コード生成
    invite_code = generate_invite_code()

    # チーム作成
    team_ref = db.collection('teams').document()
    team_data = {
        'name': name,
        'description': description or '',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now(),
        'inviteCode': invite_code,
        'inviteCodeExpiresAt': datetime.now() + timedelta(days=7)
    }
    team_ref.set(team_data)

    # 作成者をメンバーに追加
    member_ref = team_ref.collection('members').document(user_id)
    member_data = {
        'userId': user_id,
        'email': user_email,
        'displayName': user_display_name or '',
        'joinedAt': datetime.now(),
        'role': 'member'
    }
    member_ref.set(member_data)

    # GCSにチームフォルダ作成
    create_team_folders_in_gcs(team_ref.id)

    return {
        'id': team_ref.id,
        'name': name,
        'description': description or '',
        'inviteCode': invite_code,
        'createdAt': team_data['createdAt'].isoformat()
    }


def get_user_teams(user_id: str) -> List[Dict]:
    """
    ユーザーが所属する全チームを取得する

    Args:
        user_id: Firebase UID

    Returns:
        チーム一覧（id, name, role, createdAtを含む）
    """
    db = get_firestore_client()

    # 全チームを取得し、ユーザーがメンバーかチェック
    teams_ref = db.collection('teams')
    all_teams = teams_ref.stream()

    user_teams = []
    for team_doc in all_teams:
        team_id = team_doc.id
        team_data = team_doc.to_dict()

        # メンバーシップチェック
        member_ref = team_doc.reference.collection('members').document(user_id)
        member_doc = member_ref.get()

        if member_doc.exists:
            member_data = member_doc.to_dict()
            user_teams.append({
                'id': team_id,
                'name': team_data.get('name', ''),
                'role': member_data.get('role', 'member'),
                'createdAt': team_data.get('createdAt').isoformat() if team_data.get('createdAt') else None
            })

    return user_teams


def join_team(
    user_id: str,
    user_email: str,
    user_display_name: Optional[str],
    invite_code: str
) -> Dict:
    """
    招待コードでチームに参加する

    Args:
        user_id: Firebase UID
        user_email: メールアドレス
        user_display_name: 表示名
        invite_code: 招待コード

    Returns:
        参加したチーム情報

    Raises:
        ValueError: 招待コードが無効または期限切れ
    """
    try:
        db = get_firestore_client()
        print(f"[join_team] Searching for invite code: {invite_code}")

        # 招待コードでチーム検索
        teams_ref = db.collection('teams')
        query = teams_ref.where(filter=FieldFilter('inviteCode', '==', invite_code))
        results = list(query.stream())
        print(f"[join_team] Query results count: {len(results)}")

        if not results:
            raise ValueError("Invalid invite code")

        team_doc = results[0]
        team_data = team_doc.to_dict()
        print(f"[join_team] Found team: {team_data.get('name')}")

        # 有効期限チェック
        expires_at = team_data.get('inviteCodeExpiresAt')
        print(f"[join_team] Expires at: {expires_at}, type: {type(expires_at)}")

        # Firestoreのタイムスタンプ型の場合、datetimeに変換
        if expires_at:
            # タイムゾーン非対応のdatetimeに変換
            if hasattr(expires_at, 'timestamp'):
                from datetime import datetime as dt
                expires_datetime = dt.fromtimestamp(expires_at.timestamp())
                if expires_datetime < datetime.now():
                    raise ValueError("Invite code expired")
            elif expires_at < datetime.now():
                raise ValueError("Invite code expired")
        # 既にメンバーかチェック
        member_ref = team_doc.reference.collection('members').document(user_id)
        if member_ref.get().exists:
            # 既にメンバーの場合はそのまま返す
            print(f"[join_team] User already a member")
            return {
                'id': team_doc.id,
                'name': team_data.get('name', ''),
                'message': 'Already a member of this team'
            }

        # メンバーに追加
        member_data = {
            'userId': user_id,
            'email': user_email,
            'displayName': user_display_name or '',
            'joinedAt': datetime.now(),
            'role': 'member'
        }
        member_ref.set(member_data)
        print(f"[join_team] Successfully added user to team")

        return {
            'id': team_doc.id,
            'name': team_data.get('name', ''),
            'message': f'Successfully joined team: {team_data.get("name", "")}'
        }
    except ValueError as e:
        print(f"[join_team] ValueError: {e}")
        raise
    except Exception as e:
        print(f"[join_team] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def leave_team(user_id: str, team_id: str) -> Dict:
    """
    チームから脱退する

    Args:
        user_id: Firebase UID
        team_id: チームID

    Returns:
        脱退結果

    Raises:
        ValueError: 最後のチームから脱退しようとした場合
    """
    # ユーザーが所属するチーム数を確認
    user_teams = get_user_teams(user_id)
    if len(user_teams) <= 1:
        raise ValueError("Cannot leave the last team. Please join another team first.")

    db = get_firestore_client()

    # チームからメンバーを削除
    team_ref = db.collection('teams').document(team_id)
    member_ref = team_ref.collection('members').document(user_id)

    if not member_ref.get().exists:
        raise ValueError("User is not a member of this team")

    member_ref.delete()

    return {
        'success': True,
        'message': 'Successfully left the team'
    }


def delete_team(team_id: str) -> Dict:
    """
    チームを削除する

    Args:
        team_id: チームID

    Returns:
        削除結果

    Note:
        - Firestoreからチーム情報とメンバー情報を削除
        - GCSからチームフォルダを削除
        - ChromaDBコレクションを削除（将来実装）
    """
    db = get_firestore_client()

    team_ref = db.collection('teams').document(team_id)
    team_doc = team_ref.get()

    if not team_doc.exists:
        raise ValueError("Team not found")

    # メンバーサブコレクションを削除
    members_ref = team_ref.collection('members')
    for member_doc in members_ref.stream():
        member_doc.reference.delete()

    # チームドキュメントを削除
    team_ref.delete()

    # GCSからチームフォルダを削除
    if storage.storage_type == 'gcs':
        try:
            prefix = f"teams/{team_id}/"
            blobs = storage.bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blob.delete()
        except Exception as e:
            print(f"Warning: Failed to delete GCS folder: {e}")

    # TODO: ChromaDBコレクションを削除（Step 4で実装）

    return {
        'success': True,
        'message': 'Team deleted successfully'
    }


def is_team_member(user_id: str, team_id: str) -> bool:
    """
    ユーザーがチームのメンバーか確認する

    Args:
        user_id: Firebase UID
        team_id: チームID

    Returns:
        メンバーの場合True、それ以外False
    """
    db = get_firestore_client()

    team_ref = db.collection('teams').document(team_id)
    member_ref = team_ref.collection('members').document(user_id)

    return member_ref.get().exists
