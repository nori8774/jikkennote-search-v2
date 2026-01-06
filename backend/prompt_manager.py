"""
プロンプト管理機能
YAMLファイルでプロンプトを保存・読み込み
"""
import os
import yaml
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from storage import storage


class PromptManager:
    """プロンプト管理クラス"""

    def __init__(self, team_id: Optional[str] = None, prompts_dir: Optional[str] = None):
        """
        Args:
            team_id: チームID（マルチテナント対応）
            prompts_dir: プロンプトを保存するディレクトリ（デフォルト: チームディレクトリまたは./saved_prompts）
        """
        if prompts_dir:
            self.prompts_dir_path = prompts_dir
        elif team_id:
            # チーム専用のプロンプトディレクトリ
            self.prompts_dir_path = f"teams/{team_id}/prompts"
        else:
            # デフォルトパス（後方互換性のため）
            self.prompts_dir_path = "./saved_prompts"

        self.team_id = team_id

        # ディレクトリが存在しない場合は作成（GCSの場合は不要だが、ローカルでは必要）
        if not storage.exists(self.prompts_dir_path):
            # GCSの場合、ディレクトリは自動作成されるのでスキップ
            # ローカルの場合のみ明示的に作成
            if hasattr(storage, 'storage_type') and storage.storage_type == 'local':
                Path(self.prompts_dir_path).mkdir(parents=True, exist_ok=True)

    def save_prompt(
        self,
        name: str,
        prompts: Dict[str, str],
        description: str = ""
    ) -> Dict[str, any]:
        """
        プロンプトをYAMLファイルとして保存

        Args:
            name: プロンプト名（ファイル名になる）
            prompts: プロンプト辞書 {"query_generation": "...", "compare": "..."}
            description: プロンプトの説明

        Returns:
            保存結果 {"success": bool, "error": str (optional), "file_path": str}
        """
        try:
            # ファイル名のサニタイズ（特殊文字を除去）
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')

            if not safe_name:
                return {"success": False, "error": "無効なプロンプト名です"}

            file_path = f"{self.prompts_dir_path}/{safe_name}.yaml"

            # 既存ファイルのチェック
            if storage.exists(file_path):
                return {"success": False, "error": "同じ名前のプロンプトが既に存在します"}

            # YAMLデータの作成
            data = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "prompts": prompts
            }

            # YAMLファイルに保存
            yaml_content = yaml.dump(data, allow_unicode=True, sort_keys=False)
            storage.write_file(file_path, yaml_content)

            return {
                "success": True,
                "file_path": file_path,
                "name": name
            }

        except Exception as e:
            return {"success": False, "error": f"保存エラー: {str(e)}"}

    def load_prompt(self, name: str) -> Optional[Dict]:
        """
        プロンプトをYAMLファイルから読み込み

        Args:
            name: プロンプト名

        Returns:
            プロンプトデータ または None
        """
        try:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')

            file_path = f"{self.prompts_dir_path}/{safe_name}.yaml"

            if not storage.exists(file_path):
                return None

            content = storage.read_file(file_path)
            data = yaml.safe_load(content)

            return data

        except Exception as e:
            print(f"プロンプト読み込みエラー: {e}")
            return None

    def list_prompts(self) -> List[Dict]:
        """
        保存されているプロンプトの一覧を取得

        Returns:
            プロンプト一覧 [{"name": "...", "description": "...", ...}]
        """
        prompts = []

        try:
            # プロンプトディレクトリ配下の*.yamlファイルを取得
            yaml_files = storage.list_files(prefix=self.prompts_dir_path, pattern="*.yaml")

            for file_path in yaml_files:
                try:
                    content = storage.read_file(file_path)
                    data = yaml.safe_load(content)

                    # ファイル名（拡張子なし）を取得
                    filename = file_path.split('/')[-1]
                    file_id = filename.replace('.yaml', '')

                    prompts.append({
                        "id": file_id,
                        "name": data.get("name", file_id),
                        "description": data.get("description", ""),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                    })
                except Exception as file_error:
                    print(f"ファイル読み込みエラー ({file_path}): {file_error}")
                    continue

            # 更新日時でソート（新しい順）
            prompts.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        except Exception as e:
            print(f"プロンプト一覧取得エラー: {e}")

        return prompts

    def delete_prompt(self, name: str) -> Dict[str, any]:
        """
        プロンプトを削除

        Args:
            name: プロンプト名

        Returns:
            削除結果 {"success": bool, "error": str (optional)}
        """
        try:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')

            file_path = f"{self.prompts_dir_path}/{safe_name}.yaml"

            if not storage.exists(file_path):
                return {"success": False, "error": "プロンプトが見つかりません"}

            storage.delete_file(file_path)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": f"削除エラー: {str(e)}"}

    def update_prompt(
        self,
        name: str,
        prompts: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, any]:
        """
        プロンプトを更新

        Args:
            name: プロンプト名
            prompts: 新しいプロンプト辞書（Noneの場合は変更なし）
            description: 新しい説明（Noneの場合は変更なし）

        Returns:
            更新結果 {"success": bool, "error": str (optional)}
        """
        try:
            # 既存データを読み込み
            data = self.load_prompt(name)
            if not data:
                return {"success": False, "error": "プロンプトが見つかりません"}

            # 更新
            if prompts is not None:
                data["prompts"] = prompts

            if description is not None:
                data["description"] = description

            data["updated_at"] = datetime.now().isoformat()

            # 保存
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            file_path = f"{self.prompts_dir_path}/{safe_name}.yaml"

            yaml_content = yaml.dump(data, allow_unicode=True, sort_keys=False)
            storage.write_file(file_path, yaml_content)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": f"更新エラー: {str(e)}"}
