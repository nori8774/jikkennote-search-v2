"""
認証ミドルウェア

全APIエンドポイントでFirebase ID Tokenを検証します。
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from auth import verify_firebase_token


# 認証をスキップするエンドポイント
SKIP_AUTH_PATHS = [
    "/health",
    "/auth/verify",
    "/docs",
    "/openapi.json",
    "/prompts",  # デフォルトプロンプト取得（GET /prompts）のみ認証不要
    "/chroma",  # ChromaDB情報・管理は認証不要
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Firebase ID Token検証ミドルウェア

    全リクエストのAuthorizationヘッダーからFirebase ID Tokenを取得し、
    検証に成功した場合はrequest.state.userに認証情報を設定します。
    """

    async def dispatch(self, request: Request, call_next):
        # /prompts のみexact matchでスキップ（デフォルトプロンプト取得のみ認証不要）
        if request.url.path == "/prompts" and request.method == "GET":
            print(f"✅ AuthMiddleware: Skipping auth for path: {request.url.path}")
            return await call_next(request)

        # その他のSKIP_AUTH_PATHSはprefix matchでスキップ
        skip_paths_without_prompts = [p for p in SKIP_AUTH_PATHS if p != "/prompts"]
        if any(request.url.path.startswith(path) for path in skip_paths_without_prompts):
            print(f"✅ AuthMiddleware: Skipping auth for path: {request.url.path}")
            return await call_next(request)

        # CORS プリフライトリクエスト（OPTIONS）をスキップ
        if request.method == "OPTIONS":
            return await call_next(request)

        print(f"🔒 AuthMiddleware: Checking auth for path: {request.url.path}")

        # Authorizationヘッダーの取得
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            print(f"❌ AuthMiddleware: Missing Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"}
            )

        if not auth_header.startswith("Bearer "):
            print(f"❌ AuthMiddleware: Invalid Authorization header format for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format. Expected: Bearer <token>"}
            )

        # トークン抽出
        id_token = auth_header.split("Bearer ")[1]

        # トークン検証
        try:
            decoded_token = await verify_firebase_token(id_token)
            # 認証情報をrequest.stateに設定
            request.state.user = decoded_token
            print(f"✅ AuthMiddleware: Token verified for user: {decoded_token.get('uid')}")
        except HTTPException as e:
            print(f"❌ AuthMiddleware: Token verification failed: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            print(f"❌ AuthMiddleware: Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": f"Authentication error: {str(e)}"}
            )

        # 次の処理へ
        return await call_next(request)


class TeamMiddleware(BaseHTTPMiddleware):
    """
    チームID検証ミドルウェア

    X-Team-IDヘッダーの存在を確認し、
    ユーザーがチームのメンバーか検証します。

    注意: チーム管理系のエンドポイント（/teams/*）はスキップします。
    """

    async def dispatch(self, request: Request, call_next):
        # /prompts のみexact matchでスキップ（デフォルトプロンプト取得のみチーム不要）
        if request.url.path == "/prompts" and request.method == "GET":
            print(f"✅ TeamMiddleware: Skipping team check for path: {request.url.path}")
            return await call_next(request)

        # その他のskip pathsはprefix matchでスキップ
        skip_paths = [p for p in SKIP_AUTH_PATHS if p != "/prompts"] + ["/teams"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            print(f"✅ TeamMiddleware: Skipping team check for path: {request.url.path}")
            return await call_next(request)

        # CORS プリフライトリクエスト（OPTIONS）をスキップ
        if request.method == "OPTIONS":
            return await call_next(request)

        print(f"🔒 TeamMiddleware: Checking team for path: {request.url.path}")

        # X-Team-IDヘッダーの取得
        team_id = request.headers.get("X-Team-ID")

        if not team_id:
            print(f"❌ TeamMiddleware: Missing X-Team-ID header for {request.url.path}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing X-Team-ID header"}
            )

        # ユーザーがチームのメンバーか確認
        try:
            from teams import is_team_member
            user_id = request.state.user.get("uid")

            if not is_team_member(user_id, team_id):
                print(f"❌ TeamMiddleware: User {user_id} is not a member of team {team_id}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "User is not a member of this team"}
                )
            print(f"✅ TeamMiddleware: User {user_id} is a member of team {team_id}")
        except AttributeError:
            # request.state.user が未設定の場合（認証ミドルウェアが未実行）
            print(f"❌ TeamMiddleware: request.state.user not set (auth middleware not run)")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        except Exception as e:
            print(f"❌ TeamMiddleware: Team verification error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Team verification error: {str(e)}"}
            )

        # チームIDをrequest.stateに設定
        request.state.team_id = team_id

        # 次の処理へ
        return await call_next(request)
