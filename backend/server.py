"""
FastAPI Server for Experiment Notes Search System
実験ノート検索システムのメインAPIサーバー
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import json
import re

from config import config
from agent import SearchAgent
from prompts import get_all_default_prompts
from ingest import ingest_notes
from history import get_history_manager
from evaluation import get_evaluator
from storage import storage
from prompt_manager import PromptManager
from middleware import AuthMiddleware, TeamMiddleware
from auth import verify_firebase_token
from experimenter_profile import get_experimenter_profile_manager
from synonym_dictionary import get_synonym_dictionary
import teams

app = FastAPI(
    title="実験ノート検索システム API",
    version="3.0.0",
    description="LangChainを活用した高精度な実験ノート検索システム（マルチテナント対応）"
)

# 認証ミドルウェア（v3.0: Firebase ID Token検証）
# 注意: ミドルウェアは逆順で実行されるため、CORSミドルウェアを最後に追加
app.add_middleware(TeamMiddleware)
app.add_middleware(AuthMiddleware)

# CORS設定（最後に追加することで、OPTIONSリクエストが最初に処理される）
# 環境変数からCORS originsを取得（カンマ区切り）
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Request/Response Models ===

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    config: dict


class FolderPathsRequest(BaseModel):
    notes_new: Optional[str] = None
    notes_processed: Optional[str] = None
    notes_archive: Optional[str] = None
    chroma_db: Optional[str] = None


class FolderPathsResponse(BaseModel):
    success: bool
    message: str
    paths: dict


class SearchRequest(BaseModel):
    purpose: str
    materials: str
    methods: str
    type: str = "initial_search"
    instruction: Optional[str] = ""
    openai_api_key: str
    cohere_api_key: str
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None  # 後方互換性のため維持（非推奨）
    search_llm_model: Optional[str] = None  # v3.0: 検索・判定用LLM
    summary_llm_model: Optional[str] = None  # v3.0: 要約生成用LLM
    search_mode: Optional[str] = None  # v3.0.1: "semantic" | "keyword" | "hybrid"
    hybrid_alpha: Optional[float] = None  # v3.0.1: ハイブリッド検索のセマンティック重み（0.0-1.0）
    custom_prompts: Optional[Dict[str, str]] = None
    prompt_name: Optional[str] = None  # v3.2.4: プロンプト名（ログ表示用）
    evaluation_mode: bool = False  # 評価モード（True: 比較省略、Top10返却）
    # v3.1.0: 3軸分離検索設定
    multi_axis_enabled: Optional[bool] = None  # 3軸検索の有効/無効
    fusion_method: Optional[str] = None  # "rrf" | "linear"
    axis_weights: Optional[Dict[str, float]] = None  # {"material": 0.3, "method": 0.4, "combined": 0.3}
    rerank_position: Optional[str] = None  # "per_axis" | "after_fusion"
    rerank_enabled: Optional[bool] = None  # リランキングの有効/無効


class SearchResponse(BaseModel):
    success: bool
    message: str
    retrieved_docs: List[str]
    normalized_materials: Optional[str] = None
    search_query: Optional[str] = None


class PromptsResponse(BaseModel):
    success: bool
    prompts: Dict[str, dict]


class IngestRequest(BaseModel):
    openai_api_key: str
    source_folder: Optional[str] = None
    post_action: str = 'move_to_processed'  # 'delete', 'archive', 'keep', 'move_to_processed'
    archive_folder: Optional[str] = None
    embedding_model: Optional[str] = None
    rebuild_mode: bool = False  # ChromaDBリセット後の再構築モード
    use_synonym_normalization: bool = True  # v3.2.1: 同義語辞書による正規化（デフォルト: True）


class IngestResponse(BaseModel):
    success: bool
    message: str
    new_notes: List[str]
    skipped_notes: List[str]


class UploadNotesResponse(BaseModel):
    success: bool
    message: str
    uploaded_files: List[str]


class NoteResponse(BaseModel):
    success: bool
    note: Optional[Dict] = None
    error: Optional[str] = None


# ============================================
# 実験者プロファイル管理 Request/Response Models（v3.2.0）
# ============================================

class ExperimenterProfileResponse(BaseModel):
    success: bool
    profiles: List[Dict]
    id_pattern: str


class ExperimenterProfileDetailResponse(BaseModel):
    success: bool
    profile: Optional[Dict] = None
    error: Optional[str] = None


class CreateExperimenterProfileRequest(BaseModel):
    experimenter_id: str
    name: str
    material_shortcuts: Optional[Dict[str, str]] = None
    suffix_conventions: Optional[List[List[str]]] = None


class UpdateExperimenterProfileRequest(BaseModel):
    name: Optional[str] = None
    material_shortcuts: Optional[Dict[str, str]] = None
    suffix_conventions: Optional[List[List[str]]] = None


class UpdateIdPatternRequest(BaseModel):
    pattern: str


class ExperimenterProfileMutationResponse(BaseModel):
    success: bool
    message: str


class HistoryRequest(BaseModel):
    query: Dict[str, str]
    results: List[Dict]
    normalized_materials: Optional[str] = None
    search_query: Optional[str] = None


class HistoryResponse(BaseModel):
    success: bool
    history_id: str


class HistoryListResponse(BaseModel):
    success: bool
    histories: List[Dict]
    total: int


class TestCaseImportRequest(BaseModel):
    file_type: str  # 'csv' or 'excel'


class TestCaseResponse(BaseModel):
    success: bool
    test_cases: List[Dict]


class EvaluateRequest(BaseModel):
    test_case_id: str
    openai_api_key: str
    cohere_api_key: str
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    search_llm_model: Optional[str] = None  # v3.0: 検索・判定用LLM
    summary_llm_model: Optional[str] = None  # v3.0: 要約生成用LLM
    search_mode: Optional[str] = None  # v3.0.1: "semantic" | "keyword" | "hybrid"
    hybrid_alpha: Optional[float] = None  # v3.0.1: ハイブリッド検索の重み
    custom_prompts: Optional[Dict[str, str]] = None  # カスタムプロンプト
    # v3.1.0: 3軸分離検索設定
    multi_axis_enabled: Optional[bool] = None  # 3軸検索の有効/無効
    fusion_method: Optional[str] = None  # "rrf" | "linear"
    axis_weights: Optional[Dict[str, float]] = None  # {"material": 0.3, "method": 0.4, "combined": 0.3}
    rerank_position: Optional[str] = None  # "per_axis" | "after_fusion"
    rerank_enabled: Optional[bool] = None  # リランキングの有効/無効


class EvaluateResponse(BaseModel):
    success: bool
    metrics: Dict
    ranking: List[Dict]
    comparison: List[Dict]


class BatchEvaluateRequest(BaseModel):
    test_case_ids: List[str]
    openai_api_key: str
    cohere_api_key: str
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    search_llm_model: Optional[str] = None  # v3.0: 検索・判定用LLM
    summary_llm_model: Optional[str] = None  # v3.0: 要約生成用LLM
    search_mode: Optional[str] = None  # v3.0.1: "semantic" | "keyword" | "hybrid"
    hybrid_alpha: Optional[float] = None  # v3.0.1: ハイブリッド検索の重み
    custom_prompts: Optional[Dict[str, str]] = None  # カスタムプロンプト
    # v3.1.0: 3軸分離検索設定
    multi_axis_enabled: Optional[bool] = None  # 3軸検索の有効/無効
    fusion_method: Optional[str] = None  # "rrf" | "linear"
    axis_weights: Optional[Dict[str, float]] = None  # {"material": 0.3, "method": 0.4, "combined": 0.3}
    rerank_position: Optional[str] = None  # "per_axis" | "after_fusion"
    rerank_enabled: Optional[bool] = None  # リランキングの有効/無効


class BatchEvaluateResponse(BaseModel):
    success: bool
    average_metrics: Dict
    individual_results: List[Dict]


# === チーム管理 Request/Response Models（v3.0新規） ===

class CreateTeamRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CreateTeamResponse(BaseModel):
    success: bool
    team: Dict
    message: str


class JoinTeamRequest(BaseModel):
    inviteCode: str


class JoinTeamResponse(BaseModel):
    success: bool
    teamId: str
    message: str


class LeaveTeamResponse(BaseModel):
    success: bool
    message: str


class DeleteTeamResponse(BaseModel):
    success: bool
    message: str


class TeamsListResponse(BaseModel):
    success: bool
    teams: List[Dict]


# === Endpoints ===

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "実験ノート検索システム API",
        "version": "3.0.0",
        "status": "Phase 1: マルチテナント基盤整備中",
        "endpoints": {
            "health": "/health - ヘルスチェック",
            "auth": "/auth/verify - Firebase ID Token検証（内部用）",
            "teams": "/teams - チーム管理",
            "config": "/config/folders - フォルダパス設定",
            "search": "/search - 実験ノート検索",
            "prompts": "/prompts - デフォルトプロンプト取得",
            "ingest": "/ingest - ノート取り込み",
        }
    }


# === 認証API（v3.0新規） ===

class AuthVerifyRequest(BaseModel):
    id_token: str


class AuthVerifyResponse(BaseModel):
    success: bool
    uid: str
    email: str
    displayName: Optional[str] = None


@app.post("/auth/verify", response_model=AuthVerifyResponse)
async def verify_token(request: AuthVerifyRequest):
    """
    Firebase ID Tokenを検証する（内部用エンドポイント）

    クライアントから送られたFirebase ID Tokenを検証し、
    ユーザー情報を返します。
    """
    try:
        decoded_token = await verify_firebase_token(request.id_token)

        return AuthVerifyResponse(
            success=True,
            uid=decoded_token.get("uid", ""),
            email=decoded_token.get("email", ""),
            displayName=decoded_token.get("name")
        )
    except HTTPException as e:
        raise e


# === チーム管理API（v3.0新規） ===

@app.get("/teams", response_model=TeamsListResponse)
async def get_user_teams(request: Request):
    """
    ユーザーが所属するチーム一覧を取得

    認証ミドルウェアで設定された request.state.user を使用
    """
    try:
        user_id = request.state.user.get("uid")
        user_teams = teams.get_user_teams(user_id)

        return TeamsListResponse(
            success=True,
            teams=user_teams
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/teams/create", response_model=CreateTeamResponse)
async def create_team(request: Request, req: CreateTeamRequest):
    """
    新しいチームを作成

    Args:
        req: チーム作成リクエスト（name, description）

    Returns:
        作成されたチーム情報（招待コード含む）
    """
    try:
        user = request.state.user
        user_id = user.get("uid")
        user_email = user.get("email")
        user_display_name = user.get("name")

        team = teams.create_team(
            user_id=user_id,
            user_email=user_email,
            user_display_name=user_display_name,
            name=req.name,
            description=req.description
        )

        return CreateTeamResponse(
            success=True,
            team=team,
            message=f"Team '{req.name}' created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/teams/join", response_model=JoinTeamResponse)
async def join_team(request: Request, req: JoinTeamRequest):
    """
    招待コードでチームに参加

    Args:
        req: 招待コード

    Returns:
        参加したチーム情報
    """
    try:
        user = request.state.user
        user_id = user.get("uid")
        user_email = user.get("email")
        user_display_name = user.get("name")

        result = teams.join_team(
            user_id=user_id,
            user_email=user_email,
            user_display_name=user_display_name,
            invite_code=req.inviteCode
        )

        return JoinTeamResponse(
            success=True,
            teamId=result['id'],
            message=result['message']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/teams/{team_id}/leave", response_model=LeaveTeamResponse)
async def leave_team(request: Request, team_id: str):
    """
    チームから脱退

    Args:
        team_id: 脱退するチームID

    Returns:
        脱退結果
    """
    try:
        user_id = request.state.user.get("uid")
        result = teams.leave_team(user_id, team_id)

        return LeaveTeamResponse(
            success=result['success'],
            message=result['message']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/teams/{team_id}", response_model=DeleteTeamResponse)
async def delete_team(request: Request, team_id: str):
    """
    チームを削除

    Args:
        team_id: 削除するチームID

    Returns:
        削除結果

    Note:
        - Firestoreからチーム情報を削除
        - GCSからチームフォルダを削除
        - ChromaDBコレクションを削除
    """
    try:
        result = teams.delete_team(team_id)

        return DeleteTeamResponse(
            success=result['success'],
            message=result['message']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    config.ensure_folders()

    return HealthResponse(
        status="healthy",
        message="Server is running",
        version="2.0.0",
        config={
            "notes_new": config.NOTES_NEW_FOLDER,
            "notes_processed": config.NOTES_PROCESSED_FOLDER,
            "notes_archive": config.NOTES_ARCHIVE_FOLDER,
            "chroma_db": config.CHROMA_DB_FOLDER,
            "master_dict": config.MASTER_DICTIONARY_PATH,
        }
    )


@app.post("/config/folders", response_model=FolderPathsResponse)
async def update_folder_paths(request: FolderPathsRequest):
    """フォルダパス設定を更新"""
    try:
        config.update_folder_paths(
            notes_new=request.notes_new,
            notes_processed=request.notes_processed,
            notes_archive=request.notes_archive,
            chroma_db=request.chroma_db
        )

        return FolderPathsResponse(
            success=True,
            message="フォルダパス設定を更新しました",
            paths={
                "notes_new": config.NOTES_NEW_FOLDER,
                "notes_processed": config.NOTES_PROCESSED_FOLDER,
                "notes_archive": config.NOTES_ARCHIVE_FOLDER,
                "chroma_db": config.CHROMA_DB_FOLDER,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"フォルダパス更新エラー: {str(e)}"
        )


@app.get("/config/folders")
async def get_folder_paths():
    """現在のフォルダパス設定を取得"""
    return {
        "success": True,
        "paths": {
            "notes_new": config.NOTES_NEW_FOLDER,
            "notes_processed": config.NOTES_PROCESSED_FOLDER,
            "notes_archive": config.NOTES_ARCHIVE_FOLDER,
            "chroma_db": config.CHROMA_DB_FOLDER,
            "master_dict": config.MASTER_DICTIONARY_PATH,
        }
    }


@app.post("/search", response_model=SearchResponse)
async def search_experiments(req_obj: Request, request: SearchRequest):
    """実験ノート検索（v3.0: マルチテナント対応、v3.1.0: 3軸分離検索対応）"""
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        # デバッグログ: リクエストパラメータを出力（簡潔版）
        prompt_display = request.prompt_name or ("カスタム" if request.custom_prompts else "デフォルト")
        mode_str = "評価" if request.evaluation_mode else "検索"
        axis_str = "3軸" if request.multi_axis_enabled else "単一"
        print(f"\n📝 [/search] {mode_str}モード | プロンプト: {prompt_display} | {axis_str}検索 | {request.search_mode or 'semantic'}")

        # エージェント初期化（v3.1.0: 3軸分離検索対応）
        agent = SearchAgent(
            openai_api_key=request.openai_api_key,
            cohere_api_key=request.cohere_api_key,
            embedding_model=request.embedding_model,
            llm_model=request.llm_model,  # 後方互換性
            search_llm_model=request.search_llm_model,  # v3.0: 検索・判定用LLM
            summary_llm_model=request.summary_llm_model,  # v3.0: 要約生成用LLM
            search_mode=request.search_mode,  # v3.0.1: 検索モード
            hybrid_alpha=request.hybrid_alpha,  # v3.0.1: ハイブリッド検索の重み
            prompts=request.custom_prompts,
            team_id=team_id,  # v3.0: チームID指定
            # v3.1.0: 3軸分離検索設定
            multi_axis_enabled=request.multi_axis_enabled,
            fusion_method=request.fusion_method,
            axis_weights=request.axis_weights,
            rerank_position=request.rerank_position,
            rerank_enabled=request.rerank_enabled
        )

        # 検索実行
        input_data = {
            "type": request.type,
            "purpose": request.purpose,
            "materials": request.materials,
            "methods": request.methods,
            "instruction": request.instruction
        }

        result = agent.run(input_data, evaluation_mode=request.evaluation_mode)

        # 結果から最後のメッセージを取得
        final_message = ""
        if result.get("messages"):
            last_msg = result["messages"][-1]
            if hasattr(last_msg, "content"):
                final_message = last_msg.content
            else:
                final_message = str(last_msg)

        return SearchResponse(
            success=True,
            message=final_message,
            retrieved_docs=result.get("retrieved_docs", []),
            normalized_materials=result.get("normalized_materials", ""),
            search_query=result.get("search_query", "")
        )

    except Exception as e:
        import traceback
        error_str = str(e)
        print(f"Error in search: {error_str}")
        print(f"Stack trace:\n{traceback.format_exc()}")

        # OpenAI APIキーエラーを検出
        if "401" in error_str or "invalid_api_key" in error_str or "Incorrect API key" in error_str:
            raise HTTPException(status_code=401, detail="OpenAI APIキーが無効です。設定ページで正しいAPIキー（sk-proj-で始まる）を入力してください。")

        raise HTTPException(status_code=500, detail=f"検索エラー: {error_str}")


@app.get("/prompts", response_model=PromptsResponse)
async def get_default_prompts():
    """デフォルトプロンプトを取得"""
    try:
        prompts = get_all_default_prompts()
        return PromptsResponse(
            success=True,
            prompts=prompts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト取得エラー: {str(e)}")


@app.post("/upload/notes", response_model=UploadNotesResponse)
async def upload_notes(
    req_obj: Request,
    files: List[UploadFile] = File(...)
):
    """
    ノートファイルのアップロード（v3.0: マルチテナント対応）

    アップロードされたMarkdownファイルをチーム専用の notes/new フォルダに保存します。
    """
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        # 保存先フォルダを決定
        if team_id:
            upload_folder = storage.get_team_path(team_id, 'notes_new')
        else:
            # 後方互換性: グローバルパス
            upload_folder = config.NOTES_NEW_FOLDER

        # フォルダが存在しない場合は作成
        from pathlib import Path
        Path(upload_folder).mkdir(parents=True, exist_ok=True)

        uploaded_files = []

        for file in files:
            # ファイル名の検証
            if not file.filename.endswith('.md'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Markdownファイル(.md)のみアップロード可能です: {file.filename}"
                )

            # ファイル内容を読み込み
            content = await file.read()

            # ファイルを保存
            file_path = f"{upload_folder}/{file.filename}"
            storage.write_file(file_path, content.decode('utf-8'))

            uploaded_files.append(file.filename)

        return UploadNotesResponse(
            success=True,
            message=f"{len(uploaded_files)}件のファイルをアップロードしました",
            uploaded_files=uploaded_files
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in upload_notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ファイルアップロードエラー: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_notes_endpoint(req_obj: Request, request: IngestRequest):
    """ノート取り込み（増分更新 or ChromaDB再構築、v3.0: マルチテナント対応）"""
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        new_notes, skipped_notes = ingest_notes(
            api_key=request.openai_api_key,
            source_folder=request.source_folder,
            post_action=request.post_action,
            archive_folder=request.archive_folder,
            embedding_model=request.embedding_model,
            rebuild_mode=request.rebuild_mode,
            team_id=team_id,  # v3.0: チームID指定
            use_synonym_normalization=request.use_synonym_normalization  # v3.2.1: 同義語正規化
        )

        if request.rebuild_mode:
            message = f"ChromaDB再構築完了: {len(new_notes)}件のノートを取り込みました。"
        else:
            message = f"{len(new_notes)}件の新規ノートを追加しました。{len(skipped_notes)}件はスキップされました。"

        return IngestResponse(
            success=True,
            message=message,
            new_notes=new_notes,
            skipped_notes=skipped_notes
        )

    except Exception as e:
        print(f"Error in ingest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ノート取り込みエラー: {str(e)}")


@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(req_obj: Request, note_id: str):
    """実験ノートを取得（v3.0: マルチテナント対応）"""
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        # ノートファイルを検索（v3.0: チーム対応）
        note_file = None
        if team_id:
            # マルチテナントモード: チーム専用パスから検索
            folders = [
                storage.get_team_path(team_id, 'notes_new'),
                storage.get_team_path(team_id, 'notes_processed'),
                f"{storage.get_team_path(team_id, 'notes_new')}/archive"
            ]
        else:
            # 後方互換性: グローバルパスから検索
            folders = [
                config.NOTES_NEW_FOLDER,
                config.NOTES_PROCESSED_FOLDER,
                config.NOTES_ARCHIVE_FOLDER
            ]

        for folder in folders:
            potential_file = f"{folder}/{note_id}.md"
            try:
                # storage抽象化レイヤーを使用してファイルの存在確認
                storage.read_file(potential_file)
                note_file = potential_file
                break
            except:
                continue

        if not note_file:
            return NoteResponse(
                success=False,
                error=f"ノートが見つかりません: {note_id}"
            )

        # ファイルを読み込み（storage抽象化レイヤーを使用）
        content = storage.read_file(note_file)

        # セクションを抽出
        def extract_section(pattern: str, text: str) -> Optional[str]:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else None

        sections = {
            # v3.2.2: より柔軟なパターンに修正
            # "## 目的", "## 目的・背景", "## 背景" などに対応
            'purpose': extract_section(r'##\s*(?:目的|背景)(?:[・･/\s]*(?:目的|背景))?\s*\n(.*?)(?=\n##|\Z)', content),
            # "## 材料", "## 材料・試薬" などに対応
            'materials': extract_section(r'##\s*材料(?:[・･/\s]*試薬)?\s*\n(.*?)(?=\n##|\Z)', content),
            # "## 方法", "## 実験手順", "## 手順", "## 操作" などに対応
            'methods': extract_section(r'##\s*(?:方法|実験手順|手順|操作)\s*\n(.*?)(?=\n##|\Z)', content),
            # "## 結果", "## 結果・考察" などに対応
            'results': extract_section(r'##\s*結果(?:[・･/\s]*考察)?\s*\n(.*?)(?=\n##|\Z)', content),
        }

        return NoteResponse(
            success=True,
            note={
                'id': note_id,
                'content': content,
                'sections': sections
            }
        )

    except Exception as e:
        print(f"Error in get_note: {str(e)}")
        return NoteResponse(
            success=False,
            error=f"ノート読み込みエラー: {str(e)}"
        )


# ============================================
# 実験者プロファイル管理エンドポイント（v3.2.0）
# ============================================

@app.get("/experimenter-profiles", response_model=ExperimenterProfileResponse)
async def get_experimenter_profiles(request: Request):
    """実験者プロファイル一覧を取得（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)
        profiles = profile_manager.get_all_profiles()

        return ExperimenterProfileResponse(
            success=True,
            profiles=profiles,
            id_pattern=profile_manager.get_id_pattern()
        )

    except Exception as e:
        print(f"Error in get_experimenter_profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロファイル取得エラー: {str(e)}")


@app.get("/experimenter-profiles/{experimenter_id}", response_model=ExperimenterProfileDetailResponse)
async def get_experimenter_profile(request: Request, experimenter_id: str):
    """実験者プロファイル詳細を取得（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)
        profile = profile_manager.get_profile(experimenter_id)

        if not profile:
            return ExperimenterProfileDetailResponse(
                success=False,
                error=f"プロファイルが見つかりません: {experimenter_id}"
            )

        return ExperimenterProfileDetailResponse(
            success=True,
            profile=profile.to_dict()
        )

    except Exception as e:
        print(f"Error in get_experimenter_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロファイル取得エラー: {str(e)}")


@app.post("/experimenter-profiles", response_model=ExperimenterProfileMutationResponse)
async def create_experimenter_profile(request: Request, req: CreateExperimenterProfileRequest):
    """実験者プロファイルを作成（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)

        # 既存チェック
        if profile_manager.get_profile(req.experimenter_id):
            raise HTTPException(
                status_code=400,
                detail=f"プロファイルが既に存在します: {req.experimenter_id}"
            )

        success = profile_manager.create_profile(
            experimenter_id=req.experimenter_id,
            name=req.name,
            material_shortcuts=req.material_shortcuts,
            suffix_conventions=req.suffix_conventions
        )

        if not success:
            raise HTTPException(status_code=500, detail="プロファイルの作成に失敗しました")

        return ExperimenterProfileMutationResponse(
            success=True,
            message=f"プロファイルを作成しました: {req.experimenter_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_experimenter_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロファイル作成エラー: {str(e)}")


@app.put("/experimenter-profiles/{experimenter_id}", response_model=ExperimenterProfileMutationResponse)
async def update_experimenter_profile(
    request: Request,
    experimenter_id: str,
    req: UpdateExperimenterProfileRequest
):
    """実験者プロファイルを更新（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)

        # 存在チェック
        if not profile_manager.get_profile(experimenter_id):
            raise HTTPException(
                status_code=404,
                detail=f"プロファイルが見つかりません: {experimenter_id}"
            )

        success = profile_manager.update_profile(
            experimenter_id=experimenter_id,
            name=req.name,
            material_shortcuts=req.material_shortcuts,
            suffix_conventions=req.suffix_conventions
        )

        if not success:
            raise HTTPException(status_code=500, detail="プロファイルの更新に失敗しました")

        return ExperimenterProfileMutationResponse(
            success=True,
            message=f"プロファイルを更新しました: {experimenter_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_experimenter_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロファイル更新エラー: {str(e)}")


@app.delete("/experimenter-profiles/{experimenter_id}", response_model=ExperimenterProfileMutationResponse)
async def delete_experimenter_profile(request: Request, experimenter_id: str):
    """実験者プロファイルを削除（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)

        # 存在チェック
        if not profile_manager.get_profile(experimenter_id):
            raise HTTPException(
                status_code=404,
                detail=f"プロファイルが見つかりません: {experimenter_id}"
            )

        success = profile_manager.delete_profile(experimenter_id)

        if not success:
            raise HTTPException(status_code=500, detail="プロファイルの削除に失敗しました")

        return ExperimenterProfileMutationResponse(
            success=True,
            message=f"プロファイルを削除しました: {experimenter_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_experimenter_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロファイル削除エラー: {str(e)}")


@app.put("/experimenter-profiles/id-pattern", response_model=ExperimenterProfileMutationResponse)
async def update_id_pattern(request: Request, req: UpdateIdPatternRequest):
    """IDパターンを更新（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        profile_manager = get_experimenter_profile_manager(team_id=team_id)
        success = profile_manager.set_id_pattern(req.pattern)

        if not success:
            raise HTTPException(status_code=400, detail="無効な正規表現パターンです")

        return ExperimenterProfileMutationResponse(
            success=True,
            message=f"IDパターンを更新しました: {req.pattern}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_id_pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=f"IDパターン更新エラー: {str(e)}")


# ============================================
# 同義語辞書管理エンドポイント（v3.2.1）
# ============================================

class SynonymGroupRequest(BaseModel):
    canonical: str
    variants: List[str]


class SynonymGroupUpdateRequest(BaseModel):
    new_canonical: Optional[str] = None
    variants: Optional[List[str]] = None


class SynonymVariantRequest(BaseModel):
    variant: str


class SynonymDictionaryResponse(BaseModel):
    success: bool
    groups: Optional[List[Dict]] = None
    message: Optional[str] = None


class SynonymGroupDetailResponse(BaseModel):
    success: bool
    group: Optional[Dict] = None
    message: Optional[str] = None


@app.get("/synonyms", response_model=SynonymDictionaryResponse)
async def get_synonym_groups(request: Request):
    """同義語辞書の全グループを取得（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)
        groups = dictionary.get_all_groups()

        return SynonymDictionaryResponse(
            success=True,
            groups=groups
        )

    except Exception as e:
        print(f"Error in get_synonym_groups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同義語辞書取得エラー: {str(e)}")


@app.get("/synonyms/export/yaml")
async def export_synonyms_yaml(request: Request):
    """同義語辞書をYAMLファイルとしてエクスポート（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        yaml_content = dictionary.export_yaml()

        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": "attachment; filename=synonym_dictionary.yaml"
            }
        )

    except Exception as e:
        print(f"Error in export_synonyms_yaml: {str(e)}")
        raise HTTPException(status_code=500, detail=f"YAMLエクスポートエラー: {str(e)}")


@app.get("/synonyms/{canonical}", response_model=SynonymGroupDetailResponse)
async def get_synonym_group(canonical: str, request: Request):
    """特定の同義語グループを取得（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)
        group = dictionary.get_group(canonical)

        if not group:
            raise HTTPException(status_code=404, detail=f"グループが見つかりません: {canonical}")

        return SynonymGroupDetailResponse(
            success=True,
            group=group.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_synonym_group: {str(e)}")
        raise HTTPException(status_code=500, detail=f"グループ取得エラー: {str(e)}")


@app.post("/synonyms", response_model=SynonymDictionaryResponse)
async def add_synonym_group(req: SynonymGroupRequest, request: Request):
    """同義語グループを追加（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        success = dictionary.add_group(
            canonical=req.canonical,
            variants=req.variants
        )

        if not success:
            raise HTTPException(status_code=400, detail=f"グループが既に存在します: {req.canonical}")

        return SynonymDictionaryResponse(
            success=True,
            groups=dictionary.get_all_groups(),
            message=f"グループを追加しました: {req.canonical}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in add_synonym_group: {str(e)}")
        raise HTTPException(status_code=500, detail=f"グループ追加エラー: {str(e)}")


@app.put("/synonyms/{canonical}", response_model=SynonymDictionaryResponse)
async def update_synonym_group(canonical: str, req: SynonymGroupUpdateRequest, request: Request):
    """同義語グループを更新（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        success = dictionary.update_group(
            canonical=canonical,
            new_canonical=req.new_canonical,
            variants=req.variants
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"グループが見つかりません: {canonical}")

        return SynonymDictionaryResponse(
            success=True,
            groups=dictionary.get_all_groups(),
            message=f"グループを更新しました: {canonical}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_synonym_group: {str(e)}")
        raise HTTPException(status_code=500, detail=f"グループ更新エラー: {str(e)}")


@app.delete("/synonyms/{canonical}", response_model=SynonymDictionaryResponse)
async def delete_synonym_group(canonical: str, request: Request):
    """同義語グループを削除（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        success = dictionary.delete_group(canonical)

        if not success:
            raise HTTPException(status_code=404, detail=f"グループが見つかりません: {canonical}")

        return SynonymDictionaryResponse(
            success=True,
            groups=dictionary.get_all_groups(),
            message=f"グループを削除しました: {canonical}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_synonym_group: {str(e)}")
        raise HTTPException(status_code=500, detail=f"グループ削除エラー: {str(e)}")


@app.post("/synonyms/{canonical}/variants", response_model=SynonymDictionaryResponse)
async def add_synonym_variant(canonical: str, req: SynonymVariantRequest, request: Request):
    """同義語グループにバリアントを追加（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        success = dictionary.add_variant(canonical, req.variant)

        if not success:
            raise HTTPException(status_code=404, detail=f"グループが見つかりません: {canonical}")

        return SynonymDictionaryResponse(
            success=True,
            groups=dictionary.get_all_groups(),
            message=f"バリアントを追加しました: {req.variant} → {canonical}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in add_synonym_variant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"バリアント追加エラー: {str(e)}")


@app.delete("/synonyms/{canonical}/variants/{variant}", response_model=SynonymDictionaryResponse)
async def delete_synonym_variant(canonical: str, variant: str, request: Request):
    """同義語グループからバリアントを削除（チーム専用）"""
    try:
        team_id = request.headers.get("X-Team-ID")
        dictionary = get_synonym_dictionary(team_id=team_id)

        success = dictionary.remove_variant(canonical, variant)

        if not success:
            raise HTTPException(status_code=404, detail=f"グループが見つかりません: {canonical}")

        return SynonymDictionaryResponse(
            success=True,
            groups=dictionary.get_all_groups(),
            message=f"バリアントを削除しました: {variant}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_synonym_variant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"バリアント削除エラー: {str(e)}")


@app.post("/history", response_model=HistoryResponse)
async def add_search_history(request: HistoryRequest):
    """検索履歴を追加"""
    try:
        history_manager = get_history_manager()

        history_id = history_manager.add_history(
            query=request.query,
            results=request.results,
            normalized_materials=request.normalized_materials,
            search_query=request.search_query
        )

        return HistoryResponse(
            success=True,
            history_id=history_id
        )

    except Exception as e:
        print(f"Error in add_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"履歴追加エラー: {str(e)}")


@app.get("/history", response_model=HistoryListResponse)
async def get_search_histories(limit: int = 50, offset: int = 0, keyword: Optional[str] = None):
    """検索履歴を取得"""
    try:
        history_manager = get_history_manager()

        if keyword:
            histories = history_manager.search_histories(keyword=keyword)
        else:
            histories = history_manager.get_all_histories(limit=limit, offset=offset)

        stats = history_manager.get_statistics()

        return HistoryListResponse(
            success=True,
            histories=histories,
            total=stats['total_count']
        )

    except Exception as e:
        print(f"Error in get_histories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"履歴取得エラー: {str(e)}")


@app.get("/history/{history_id}")
async def get_search_history(history_id: str):
    """特定の検索履歴を取得"""
    try:
        history_manager = get_history_manager()
        history = history_manager.get_history(history_id)

        if not history:
            raise HTTPException(status_code=404, detail="履歴が見つかりません")

        from dataclasses import asdict
        return {
            "success": True,
            "history": asdict(history)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"履歴取得エラー: {str(e)}")


@app.delete("/history/{history_id}")
async def delete_search_history(history_id: str):
    """検索履歴を削除"""
    try:
        history_manager = get_history_manager()
        success = history_manager.delete_history(history_id)

        if not success:
            raise HTTPException(status_code=404, detail="履歴が見つかりません")

        return {"success": True, "message": "履歴を削除しました"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"履歴削除エラー: {str(e)}")


@app.get("/evaluate/cases", response_model=TestCaseResponse)
async def get_test_cases():
    """評価用テストケースを取得"""
    try:
        evaluator = get_evaluator()
        test_cases = evaluator.get_all_test_cases()

        return TestCaseResponse(
            success=True,
            test_cases=test_cases
        )

    except Exception as e:
        print(f"Error in get_test_cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"テストケース取得エラー: {str(e)}")


@app.post("/evaluate/import")
async def import_test_cases(file: UploadFile = File(...)):
    """テストケースをインポート（CSV/Excel）"""
    try:
        evaluator = get_evaluator()
        content = await file.read()

        filename = file.filename.lower()
        if filename.endswith('.csv'):
            content_str = content.decode('utf-8')
            count = evaluator.import_from_csv(content_str)
        elif filename.endswith(('.xlsx', '.xls')):
            # 一時ファイルに保存してインポート
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            count = evaluator.import_from_excel(tmp_path)
            os.unlink(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="サポートされていないファイル形式です")

        return {
            "success": True,
            "message": f"{count}件のテストケースをインポートしました",
            "imported_count": count
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in import_test_cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"テストケースインポートエラー: {str(e)}")


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_rag(req_obj: Request, request: EvaluateRequest):
    """RAG性能を評価（v3.0: マルチテナント対応、v3.1.0: 3軸分離検索対応）"""
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        evaluator = get_evaluator()

        # テストケースを取得
        test_case = evaluator.get_test_case(request.test_case_id)
        if not test_case:
            raise HTTPException(status_code=404, detail="テストケースが見つかりません")

        # 検索を実行（v3.1.0: 3軸分離検索対応）
        agent = SearchAgent(
            openai_api_key=request.openai_api_key,
            cohere_api_key=request.cohere_api_key,
            embedding_model=request.embedding_model,
            llm_model=request.llm_model,
            search_llm_model=request.search_llm_model,
            summary_llm_model=request.summary_llm_model,
            search_mode=request.search_mode,
            hybrid_alpha=request.hybrid_alpha,
            prompts=request.custom_prompts,
            team_id=team_id,  # v3.0: チームID指定
            # v3.1.0: 3軸分離検索設定
            multi_axis_enabled=request.multi_axis_enabled,
            fusion_method=request.fusion_method,
            axis_weights=request.axis_weights,
            rerank_position=request.rerank_position,
            rerank_enabled=request.rerank_enabled
        )

        input_data = {
            "type": "initial_search",
            "purpose": test_case.query.get('purpose', ''),
            "materials": test_case.query.get('materials', ''),
            "methods": test_case.query.get('methods', ''),
            "instruction": ""
        }

        result = agent.run(input_data)

        # 検索結果を整形
        retrieved_docs = result.get("retrieved_docs", [])
        retrieved_results = []

        for i, doc in enumerate(retrieved_docs[:10]):
            # ノートIDを抽出（例: "# 実験ノート ID3-14" から "ID3-14" を抽出）
            note_id_match = re.search(r'ID[\d-]+', doc)
            note_id = note_id_match.group(0) if note_id_match else f"unknown_{i+1}"

            retrieved_results.append({
                'note_id': note_id,
                'score': 1.0 - (i * 0.05),  # スコアは仮の値
                'rank': i + 1
            })

        # 評価
        eval_result = evaluator.evaluate(test_case, retrieved_results)

        from dataclasses import asdict
        return EvaluateResponse(
            success=True,
            metrics=asdict(eval_result.metrics),
            ranking=eval_result.ranking,
            comparison=eval_result.comparison
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in evaluate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"評価エラー: {str(e)}")


@app.post("/evaluate/batch", response_model=BatchEvaluateResponse)
async def batch_evaluate_rag(req_obj: Request, request: BatchEvaluateRequest):
    """バッチ評価（v3.0: マルチテナント対応、v3.1.0: 3軸分離検索対応）"""
    try:
        # チームIDを取得（v3.0）
        team_id = getattr(req_obj.state, 'team_id', None)

        evaluator = get_evaluator()
        results = []

        for test_case_id in request.test_case_ids:
            # テストケースを取得
            test_case = evaluator.get_test_case(test_case_id)
            if not test_case:
                print(f"テストケースが見つかりません: {test_case_id}")
                continue

            # 検索を実行（v3.1.0: 3軸分離検索対応）
            agent = SearchAgent(
                openai_api_key=request.openai_api_key,
                cohere_api_key=request.cohere_api_key,
                embedding_model=request.embedding_model,
                llm_model=request.llm_model,
                search_llm_model=request.search_llm_model,
                summary_llm_model=request.summary_llm_model,
                search_mode=request.search_mode,
                hybrid_alpha=request.hybrid_alpha,
                prompts=request.custom_prompts,
                team_id=team_id,  # v3.0: チームID指定
                # v3.1.0: 3軸分離検索設定
                multi_axis_enabled=request.multi_axis_enabled,
                fusion_method=request.fusion_method,
                axis_weights=request.axis_weights,
                rerank_position=request.rerank_position,
                rerank_enabled=request.rerank_enabled
            )

            input_data = {
                "type": "initial_search",
                "purpose": test_case.query.get('purpose', ''),
                "materials": test_case.query.get('materials', ''),
                "methods": test_case.query.get('methods', ''),
                "instruction": ""
            }

            result = agent.run(input_data)

            # 検索結果を整形
            retrieved_docs = result.get("retrieved_docs", [])
            retrieved_results = []

            for i, doc in enumerate(retrieved_docs[:10]):
                note_id_match = re.search(r'ID[\d-]+', doc)
                note_id = note_id_match.group(0) if note_id_match else f"unknown_{i+1}"

                retrieved_results.append({
                    'note_id': note_id,
                    'score': 1.0 - (i * 0.05),
                    'rank': i + 1
                })

            results.append((test_case, retrieved_results))

        # バッチ評価
        batch_result = evaluator.batch_evaluate(results)

        return BatchEvaluateResponse(
            success=True,
            average_metrics=batch_result['average_metrics'],
            individual_results=batch_result['individual_results']
        )

    except Exception as e:
        print(f"Error in batch_evaluate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"バッチ評価エラー: {str(e)}")


# === Prompt Management Endpoints ===

# PromptManagerは各エンドポイントでチームIDを使って初期化します（マルチテナント対応）


class SavePromptRequest(BaseModel):
    name: str
    prompts: Dict[str, str]
    description: Optional[str] = ""


class UpdatePromptRequest(BaseModel):
    name: str
    prompts: Optional[Dict[str, str]] = None
    description: Optional[str] = None


@app.get("/prompts/list")
async def list_prompts(request: Request):
    """保存されているプロンプトの一覧を取得（チーム専用）"""
    try:
        # チームIDの取得と検証（ミドルウェアで検証済み）
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        prompt_manager = PromptManager(team_id=team_id)
        prompts = prompt_manager.list_prompts()
        return {
            "success": True,
            "prompts": prompts,
            "count": len(prompts)
        }
    except Exception as e:
        print(f"Error in list_prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロンプト一覧取得エラー: {str(e)}")


@app.post("/prompts/save")
async def save_prompt(http_request: Request, request: SavePromptRequest):
    """プロンプトをYAMLファイルとして保存（チーム専用）"""
    try:
        # チームIDの取得と検証（ミドルウェアで検証済み）
        team_id = http_request.headers.get("X-Team-ID")
        user_id = http_request.state.user["uid"]

        prompt_manager = PromptManager(team_id=team_id)
        result = prompt_manager.save_prompt(
            name=request.name,
            prompts=request.prompts,
            description=request.description
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "保存に失敗しました"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in save_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロンプト保存エラー: {str(e)}")


@app.get("/prompts/load/{name}")
async def load_prompt(request: Request, name: str):
    """プロンプトをYAMLファイルから読み込み（チーム専用）"""
    try:
        # チームIDの取得と検証（ミドルウェアで検証済み）
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        prompt_manager = PromptManager(team_id=team_id)
        data = prompt_manager.load_prompt(name)

        if not data:
            raise HTTPException(status_code=404, detail="プロンプトが見つかりません")

        return {
            "success": True,
            "prompt": data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in load_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロンプト読み込みエラー: {str(e)}")


@app.delete("/prompts/delete/{name}")
async def delete_prompt(request: Request, name: str):
    """プロンプトを削除（チーム専用）"""
    try:
        # チームIDの取得と検証（ミドルウェアで検証済み）
        team_id = request.headers.get("X-Team-ID")
        user_id = request.state.user["uid"]

        prompt_manager = PromptManager(team_id=team_id)
        result = prompt_manager.delete_prompt(name)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "削除に失敗しました"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロンプト削除エラー: {str(e)}")


@app.put("/prompts/update")
async def update_prompt(http_request: Request, request: UpdatePromptRequest):
    """プロンプトを更新（チーム専用）"""
    try:
        # チームIDの取得と検証（ミドルウェアで検証済み）
        team_id = http_request.headers.get("X-Team-ID")
        user_id = http_request.state.user["uid"]

        prompt_manager = PromptManager(team_id=team_id)
        result = prompt_manager.update_prompt(
            name=request.name,
            prompts=request.prompts,
            description=request.description
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "更新に失敗しました"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"プロンプト更新エラー: {str(e)}")


# === ChromaDB Management Endpoints ===

class ChromaDBInfoResponse(BaseModel):
    success: bool
    current_embedding_model: Optional[str]
    created_at: Optional[str]
    last_updated: Optional[str]


class ChromaDBResetResponse(BaseModel):
    success: bool
    message: str


@app.get("/chroma/info", response_model=ChromaDBInfoResponse)
async def get_chroma_info():
    """ChromaDBの現在のembeddingモデル情報を取得"""
    try:
        from chroma_sync import get_current_embedding_model, get_chroma_config_path
        import json

        current_model = get_current_embedding_model()
        config_path = get_chroma_config_path()

        created_at = None
        last_updated = None

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                created_at = config_data.get('created_at')
                last_updated = config_data.get('last_updated')

        return ChromaDBInfoResponse(
            success=True,
            current_embedding_model=current_model,
            created_at=created_at,
            last_updated=last_updated
        )

    except Exception as e:
        print(f"Error in get_chroma_info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ChromaDB情報取得エラー: {str(e)}")


@app.post("/chroma/reset", response_model=ChromaDBResetResponse)
async def reset_chroma_db_endpoint(
    authorization: Optional[str] = Header(None),
    x_team_id: Optional[str] = Header(None, alias="X-Team-ID")
):
    """ChromaDBを完全にリセット（v3.1.1: 3コレクション対応）

    チームIDが指定されている場合:
    - materials_collection, methods_collection, combined_collection をすべて削除
    - 旧形式のコレクション（notes_{team_id}）も削除

    チームIDが指定されていない場合:
    - 従来通りグローバルChromaDBをリセット
    """
    try:
        from chroma_sync import reset_chroma_db, reset_team_collections

        # チームIDを取得
        team_id = x_team_id

        if team_id:
            # v3.1.1: チームの3コレクションをリセット
            print(f"チーム {team_id} のコレクションをリセット中...")
            success = reset_team_collections(team_id)
            message = f"チーム {team_id} のコレクション（materials, methods, combined）をリセットしました。「ChromaDBを再構築」ボタンをクリックして、既存ノートからデータベースを再構築してください。"
        else:
            # 従来のグローバルリセット
            success = reset_chroma_db()
            message = "ChromaDBをリセットしました。「ChromaDBを再構築」ボタンをクリックして、既存ノートからデータベースを再構築してください。"

        if success:
            return ChromaDBResetResponse(
                success=True,
                message=message
            )
        else:
            raise HTTPException(status_code=500, detail="ChromaDBのリセットに失敗しました")

    except Exception as e:
        print(f"Error in reset_chroma_db: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ChromaDBリセットエラー: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Cloud Run環境ではPORT環境変数を使用、ローカルではデフォルトで8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print("🚀 実験ノート検索システム API サーバー起動中...")
    print(f"📍 Server: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print("🔧 Phase 4: 履歴・評価機能実装中\n")

    # 必要なフォルダを作成
    config.ensure_folders()

    uvicorn.run(app, host=host, port=port)
