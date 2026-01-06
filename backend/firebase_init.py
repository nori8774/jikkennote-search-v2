"""
Firebase Admin SDK 初期化モジュール

このモジュールは Firebase Admin SDK を初期化し、
認証とFirestoreの機能を提供します。

セットアップ手順:
1. Firebase Console でサービスアカウントの秘密鍵を生成
2. ダウンロードしたJSONファイルを `backend/firebase-adminsdk.json` に配置
3. このモジュールをインポートすると自動的に初期化されます

参考: .steering/20251231-multitenancy/FIREBASE_SETUP_GUIDE.md
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
from pathlib import Path

# Firebase Admin SDK の初期化（シングルトン）
_initialized = False
_db = None

def initialize_firebase():
    """Firebase Admin SDK を初期化する"""
    global _initialized, _db

    if _initialized:
        return _db

    # サービスアカウント鍵のパス
    cred_path = Path(__file__).parent / "firebase-adminsdk.json"

    if not cred_path.exists():
        raise FileNotFoundError(
            f"Firebase Admin SDK の秘密鍵が見つかりません: {cred_path}\n"
            "セットアップ手順に従って firebase-adminsdk.json を配置してください。\n"
            "参考: .steering/20251231-multitenancy/FIREBASE_SETUP_GUIDE.md"
        )

    # 認証情報の読み込み
    cred = credentials.Certificate(str(cred_path))

    # Firebase Admin SDK 初期化
    firebase_admin.initialize_app(cred)

    # Firestore クライアント取得
    _db = firestore.client()

    _initialized = True
    print(f"✅ Firebase Admin SDK initialized successfully")

    return _db


def get_firestore_client():
    """Firestoreクライアントを取得する"""
    global _db
    if not _initialized:
        initialize_firebase()
    return _db


def verify_id_token(id_token: str) -> dict:
    """
    Firebase ID Token を検証する

    Args:
        id_token: クライアントから送られたFirebase ID Token

    Returns:
        デコードされたトークン情報（uid, email, displayNameなど）

    Raises:
        firebase_admin.auth.InvalidIdTokenError: トークンが無効
        firebase_admin.auth.ExpiredIdTokenError: トークンが期限切れ
    """
    if not _initialized:
        initialize_firebase()

    decoded_token = auth.verify_id_token(id_token)
    return decoded_token


# モジュールインポート時に自動初期化を試みる（オプション）
# 本番環境では、エラーハンドリングのため明示的に initialize_firebase() を呼ぶことを推奨
try:
    if os.getenv("AUTO_INIT_FIREBASE", "false").lower() == "true":
        initialize_firebase()
except FileNotFoundError:
    # 開発中はファイルが未配置の場合がある
    pass
