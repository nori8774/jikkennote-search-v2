"""
Storage abstraction layer
ローカルファイルシステムとGoogle Cloud Storageを抽象化
"""
import os
from pathlib import Path
from typing import List, Optional
from abc import ABC, abstractmethod
import tempfile
import shutil


class StorageBackend(ABC):
    """ストレージバックエンドの抽象基底クラス"""

    @abstractmethod
    def read_file(self, path: str) -> str:
        """ファイルを読み込む"""
        pass

    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """ファイルに書き込む"""
        pass

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """バイナリファイルを読み込む"""
        pass

    @abstractmethod
    def write_bytes(self, path: str, content: bytes) -> None:
        """バイナリファイルに書き込む"""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "", pattern: str = "*") -> List[str]:
        """ファイル一覧を取得"""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """ファイルの存在確認"""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """ファイルを削除"""
        pass

    @abstractmethod
    def move_file(self, src: str, dst: str) -> None:
        """ファイルを移動"""
        pass

    @abstractmethod
    def mkdir(self, path: str) -> None:
        """ディレクトリを作成"""
        pass

    @abstractmethod
    def download_to_local(self, remote_path: str, local_path: str) -> None:
        """リモートからローカルにダウンロード（GCS用）"""
        pass

    @abstractmethod
    def upload_from_local(self, local_path: str, remote_path: str) -> None:
        """ローカルからリモートにアップロード（GCS用）"""
        pass


class LocalStorage(StorageBackend):
    """ローカルファイルシステムのストレージバックエンド"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)

    def _get_path(self, path: str) -> Path:
        """相対パスから絶対パスを生成"""
        return self.base_path / path

    def read_file(self, path: str) -> str:
        """ファイルを読み込む"""
        with open(self._get_path(path), 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, path: str, content: str) -> None:
        """ファイルに書き込む"""
        file_path = self._get_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def read_bytes(self, path: str) -> bytes:
        """バイナリファイルを読み込む"""
        with open(self._get_path(path), 'rb') as f:
            return f.read()

    def write_bytes(self, path: str, content: bytes) -> None:
        """バイナリファイルに書き込む"""
        file_path = self._get_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content)

    def list_files(self, prefix: str = "", pattern: str = "*") -> List[str]:
        """ファイル一覧を取得"""
        search_path = self._get_path(prefix) if prefix else self.base_path
        if not search_path.exists():
            return []

        files = []
        if search_path.is_dir():
            for item in search_path.rglob(pattern):
                if item.is_file():
                    # ベースパスからの相対パスを返す
                    rel_path = item.relative_to(self.base_path)
                    files.append(str(rel_path))
        return sorted(files)

    def exists(self, path: str) -> bool:
        """ファイルの存在確認"""
        return self._get_path(path).exists()

    def delete_file(self, path: str) -> None:
        """ファイルを削除"""
        file_path = self._get_path(path)
        if file_path.exists():
            file_path.unlink()

    def move_file(self, src: str, dst: str) -> None:
        """ファイルを移動"""
        src_path = self._get_path(src)
        dst_path = self._get_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))

    def mkdir(self, path: str) -> None:
        """ディレクトリを作成"""
        self._get_path(path).mkdir(parents=True, exist_ok=True)

    def download_to_local(self, remote_path: str, local_path: str) -> None:
        """ローカルストレージでは単純にコピー"""
        shutil.copy(str(self._get_path(remote_path)), local_path)

    def upload_from_local(self, local_path: str, remote_path: str) -> None:
        """ローカルストレージでは単純にコピー"""
        dst_path = self._get_path(remote_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(local_path, str(dst_path))


class GCSStorage(StorageBackend):
    """Google Cloud Storageのストレージバックエンド"""

    def __init__(self, bucket_name: str):
        from google.cloud import storage
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def _get_blob(self, path: str):
        """Blobオブジェクトを取得"""
        return self.bucket.blob(path)

    def read_file(self, path: str) -> str:
        """ファイルを読み込む"""
        blob = self._get_blob(path)
        return blob.download_as_text(encoding='utf-8')

    def write_file(self, path: str, content: str) -> None:
        """ファイルに書き込む"""
        blob = self._get_blob(path)
        blob.upload_from_string(content, content_type='text/plain')

    def read_bytes(self, path: str) -> bytes:
        """バイナリファイルを読み込む"""
        blob = self._get_blob(path)
        return blob.download_as_bytes()

    def write_bytes(self, path: str, content: bytes) -> None:
        """バイナリファイルに書き込む"""
        blob = self._get_blob(path)
        blob.upload_from_string(content, content_type='application/octet-stream')

    def list_files(self, prefix: str = "", pattern: str = "*") -> List[str]:
        """ファイル一覧を取得"""
        blobs = self.bucket.list_blobs(prefix=prefix)
        files = []

        # パターンマッチング（簡易実装）
        import fnmatch
        for blob in blobs:
            if pattern == "*" or fnmatch.fnmatch(blob.name, f"{prefix}{pattern}"):
                files.append(blob.name)

        return sorted(files)

    def exists(self, path: str) -> bool:
        """ファイルの存在確認"""
        blob = self._get_blob(path)
        return blob.exists()

    def delete_file(self, path: str) -> None:
        """ファイルを削除"""
        blob = self._get_blob(path)
        if blob.exists():
            blob.delete()

    def move_file(self, src: str, dst: str) -> None:
        """ファイルを移動（コピー後に元を削除）"""
        src_blob = self._get_blob(src)
        dst_blob = self.bucket.blob(dst)

        # コピー
        self.bucket.copy_blob(src_blob, self.bucket, dst)
        # 元を削除
        src_blob.delete()

    def mkdir(self, path: str) -> None:
        """GCSにはディレクトリの概念がないので何もしない"""
        pass

    def download_to_local(self, remote_path: str, local_path: str) -> None:
        """GCSからローカルにダウンロード"""
        blob = self._get_blob(remote_path)
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)

    def upload_from_local(self, local_path: str, remote_path: str) -> None:
        """ローカルからGCSにアップロード"""
        blob = self._get_blob(remote_path)
        blob.upload_from_filename(local_path)


class GoogleDriveStorage(StorageBackend):
    """Google Drive APIのストレージバックエンド"""

    def __init__(self, credentials_path: str, folder_id: str):
        """
        Google Drive Storage初期化

        Args:
            credentials_path: サービスアカウントのJSONキーファイルパス
            folder_id: 共有フォルダのID
        """
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
        from google.oauth2 import service_account
        import io

        self.credentials_path = credentials_path
        self.folder_id = folder_id

        # 認証情報の設定
        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )

        # Drive APIクライアントの構築
        self.service = build('drive', 'v3', credentials=credentials)
        self.io = io

    def _get_file_id(self, path: str) -> Optional[str]:
        """パスからGoogle DriveのファイルIDを取得"""
        # パスを分割（例: "notes/new/ID3-14.md" -> ["notes", "new", "ID3-14.md"]）
        parts = path.split('/')

        current_folder_id = self.folder_id

        # フォルダ階層を辿る
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)

            # 現在のフォルダ内でファイル/フォルダを検索
            query = f"name='{part}' and '{current_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id, name, mimeType)'
            ).execute()

            files = results.get('files', [])

            if not files:
                return None

            file_item = files[0]

            if is_last:
                return file_item['id']
            else:
                current_folder_id = file_item['id']

        return None

    def _create_folder_path(self, path: str) -> str:
        """フォルダパスを作成し、最終フォルダのIDを返す"""
        parts = path.split('/')
        current_folder_id = self.folder_id

        for part in parts:
            # フォルダが既に存在するか確認
            query = f"name='{part}' and '{current_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id)'
            ).execute()

            files = results.get('files', [])

            if files:
                current_folder_id = files[0]['id']
            else:
                # フォルダを作成
                file_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [current_folder_id]
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                current_folder_id = folder['id']

        return current_folder_id

    def read_file(self, path: str) -> str:
        """ファイルを読み込む"""
        from googleapiclient.http import MediaIoBaseDownload

        file_id = self._get_file_id(path)
        if not file_id:
            raise FileNotFoundError(f"File not found: {path}")

        request = self.service.files().get_media(fileId=file_id)
        fh = self.io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return fh.read().decode('utf-8')

    def write_file(self, path: str, content: str) -> None:
        """ファイルに書き込む"""
        from googleapiclient.http import MediaIoBaseUpload

        # パスを分割
        parts = path.split('/')
        filename = parts[-1]
        folder_path = '/'.join(parts[:-1]) if len(parts) > 1 else ''

        # 親フォルダのIDを取得または作成
        if folder_path:
            parent_folder_id = self._create_folder_path(folder_path)
        else:
            parent_folder_id = self.folder_id

        # 既存ファイルを確認
        existing_file_id = self._get_file_id(path)

        # メディアのアップロード準備
        media = MediaIoBaseUpload(
            self.io.BytesIO(content.encode('utf-8')),
            mimetype='text/plain',
            resumable=True
        )

        if existing_file_id:
            # 既存ファイルを更新
            self.service.files().update(
                fileId=existing_file_id,
                media_body=media
            ).execute()
        else:
            # 新規ファイルを作成
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

    def read_bytes(self, path: str) -> bytes:
        """バイナリファイルを読み込む"""
        from googleapiclient.http import MediaIoBaseDownload

        file_id = self._get_file_id(path)
        if not file_id:
            raise FileNotFoundError(f"File not found: {path}")

        request = self.service.files().get_media(fileId=file_id)
        fh = self.io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return fh.read()

    def write_bytes(self, path: str, content: bytes) -> None:
        """バイナリファイルに書き込む"""
        from googleapiclient.http import MediaIoBaseUpload

        parts = path.split('/')
        filename = parts[-1]
        folder_path = '/'.join(parts[:-1]) if len(parts) > 1 else ''

        if folder_path:
            parent_folder_id = self._create_folder_path(folder_path)
        else:
            parent_folder_id = self.folder_id

        existing_file_id = self._get_file_id(path)

        media = MediaIoBaseUpload(
            self.io.BytesIO(content),
            mimetype='application/octet-stream',
            resumable=True
        )

        if existing_file_id:
            self.service.files().update(
                fileId=existing_file_id,
                media_body=media
            ).execute()
        else:
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

    def list_files(self, prefix: str = "", pattern: str = "*") -> List[str]:
        """ファイル一覧を取得"""
        import fnmatch

        # プレフィックスからフォルダIDを取得
        if prefix:
            folder_id = self._get_file_id(prefix)
            if not folder_id:
                return []
        else:
            folder_id = self.folder_id

        # フォルダ内のファイルを再帰的に取得
        def list_recursive(current_folder_id: str, current_path: str = "") -> List[str]:
            files = []

            query = f"'{current_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id, name, mimeType)'
            ).execute()

            items = results.get('files', [])

            for item in items:
                item_path = f"{current_path}/{item['name']}" if current_path else item['name']

                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # サブフォルダを再帰的に探索
                    files.extend(list_recursive(item['id'], item_path))
                else:
                    # パターンマッチング
                    if pattern == "*" or fnmatch.fnmatch(item['name'], pattern):
                        # プレフィックスを含めた完全なパスを返す
                        full_path = f"{prefix}/{item_path}" if prefix else item_path
                        files.append(full_path)

            return files

        return sorted(list_recursive(folder_id, ""))

    def exists(self, path: str) -> bool:
        """ファイルの存在確認"""
        return self._get_file_id(path) is not None

    def delete_file(self, path: str) -> None:
        """ファイルを削除"""
        file_id = self._get_file_id(path)
        if file_id:
            self.service.files().delete(fileId=file_id).execute()

    def move_file(self, src: str, dst: str) -> None:
        """ファイルを移動"""
        file_id = self._get_file_id(src)
        if not file_id:
            raise FileNotFoundError(f"Source file not found: {src}")

        # 移動先のパスを分割
        dst_parts = dst.split('/')
        dst_filename = dst_parts[-1]
        dst_folder_path = '/'.join(dst_parts[:-1]) if len(dst_parts) > 1 else ''

        # 移動先のフォルダIDを取得または作成
        if dst_folder_path:
            dst_folder_id = self._create_folder_path(dst_folder_path)
        else:
            dst_folder_id = self.folder_id

        # 現在の親フォルダを取得
        file = self.service.files().get(
            fileId=file_id,
            fields='parents'
        ).execute()
        previous_parents = ",".join(file.get('parents', []))

        # ファイルを移動（親を変更）
        self.service.files().update(
            fileId=file_id,
            addParents=dst_folder_id,
            removeParents=previous_parents,
            body={'name': dst_filename},
            fields='id, parents'
        ).execute()

    def mkdir(self, path: str) -> None:
        """ディレクトリを作成"""
        self._create_folder_path(path)

    def download_to_local(self, remote_path: str, local_path: str) -> None:
        """Google Driveからローカルにダウンロード"""
        from googleapiclient.http import MediaIoBaseDownload

        file_id = self._get_file_id(remote_path)
        if not file_id:
            raise FileNotFoundError(f"File not found: {remote_path}")

        request = self.service.files().get_media(fileId=file_id)

        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

    def upload_from_local(self, local_path: str, remote_path: str) -> None:
        """ローカルからGoogle Driveにアップロード"""
        from googleapiclient.http import MediaFileUpload

        parts = remote_path.split('/')
        filename = parts[-1]
        folder_path = '/'.join(parts[:-1]) if len(parts) > 1 else ''

        if folder_path:
            parent_folder_id = self._create_folder_path(folder_path)
        else:
            parent_folder_id = self.folder_id

        existing_file_id = self._get_file_id(remote_path)

        media = MediaFileUpload(local_path, resumable=True)

        if existing_file_id:
            self.service.files().update(
                fileId=existing_file_id,
                media_body=media
            ).execute()
        else:
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()


class Storage:
    """
    統一ストレージインターフェース
    環境変数でローカル/GCS/Google Driveを自動切り替え

    v3.0: マルチテナント対応
    """

    def __init__(self):
        storage_type = os.getenv("STORAGE_TYPE", "local")
        self.storage_type = storage_type  # v3.0: 外部からアクセス可能に

        if storage_type == "google_drive":
            credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
            folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
            if not credentials_path or not folder_id:
                raise ValueError("Google Drive requires GOOGLE_DRIVE_CREDENTIALS_PATH and GOOGLE_DRIVE_FOLDER_ID")
            self.backend = GoogleDriveStorage(credentials_path, folder_id)
            print(f"Using Google Drive storage: folder_id={folder_id}")
        elif storage_type == "gcs":
            bucket_name = os.getenv("GCS_BUCKET_NAME", "jikkennote-storage")
            self.backend = GCSStorage(bucket_name)
            print(f"Using GCS storage: gs://{bucket_name}")
        else:
            base_path = os.getenv("STORAGE_BASE_PATH", ".")
            self.backend = LocalStorage(base_path)
            print(f"Using local storage: {base_path}")

    @property
    def bucket(self):
        """GCSバケットへのアクセス（teams.pyで使用）"""
        if isinstance(self.backend, GCSStorage):
            return self.backend.bucket
        return None

    def get_team_path(self, team_id: str, resource_type: str) -> str:
        """
        チームスコープのパスを生成（v3.0新規）

        Args:
            team_id: チームID
            resource_type: リソースタイプ
                - 'notes_new': 新規ノート
                - 'notes_processed': 処理済みノート
                - 'prompts': 保存されたプロンプト
                - 'dictionary': 正規化辞書
                - 'chroma': ChromaDB永続化

        Returns:
            チームスコープのパス
        """
        if self.storage_type == 'gcs':
            base = f"teams/{team_id}"
        else:
            base = f"teams/{team_id}"

        paths = {
            'notes_new': f"{base}/notes/new",
            'notes_processed': f"{base}/notes/processed",
            'prompts': f"{base}/saved_prompts",
            'dictionary': f"{base}/dictionary.yaml",
            'chroma': f"{base}/chroma-db"
        }

        return paths.get(resource_type, base)

    def read_file(self, path: str) -> str:
        """ファイルを読み込む"""
        return self.backend.read_file(path)

    def write_file(self, path: str, content: str) -> None:
        """ファイルに書き込む"""
        self.backend.write_file(path, content)

    def read_bytes(self, path: str) -> bytes:
        """バイナリファイルを読み込む"""
        return self.backend.read_bytes(path)

    def write_bytes(self, path: str, content: bytes) -> None:
        """バイナリファイルに書き込む"""
        self.backend.write_bytes(path, content)

    def list_files(self, prefix: str = "", pattern: str = "*") -> List[str]:
        """ファイル一覧を取得"""
        return self.backend.list_files(prefix, pattern)

    def exists(self, path: str) -> bool:
        """ファイルの存在確認"""
        return self.backend.exists(path)

    def delete_file(self, path: str) -> None:
        """ファイルを削除"""
        self.backend.delete_file(path)

    def move_file(self, src: str, dst: str) -> None:
        """ファイルを移動"""
        self.backend.move_file(src, dst)

    def mkdir(self, path: str) -> None:
        """ディレクトリを作成"""
        self.backend.mkdir(path)

    def download_to_local(self, remote_path: str, local_path: str) -> None:
        """リモートからローカルにダウンロード"""
        self.backend.download_to_local(remote_path, local_path)

    def upload_from_local(self, local_path: str, remote_path: str) -> None:
        """ローカルからリモートにアップロード"""
        self.backend.upload_from_local(local_path, remote_path)


# グローバルストレージインスタンス
storage = Storage()
