"""
認証ユーティリティ

Firebase ID Tokenの検証を行います。
"""

from firebase_init import verify_id_token as firebase_verify_token
from fastapi import HTTPException


async def verify_firebase_token(id_token: str) -> dict:
    """
    Firebase ID Tokenを検証する

    Args:
        id_token: クライアントから送られたFirebase ID Token

    Returns:
        デコードされたトークン情報（uid, email, displayNameなど）

    Raises:
        HTTPException: トークンが無効または期限切れ
    """
    try:
        decoded_token = firebase_verify_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired Firebase ID Token: {str(e)}"
        )
