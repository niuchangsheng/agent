"""
TaskContext - 任务上下文管理

职责:
1. 管理项目路径和目标
2. 缓存已读取的文件
3. 维护执行历史
4. 提供上下文摘要
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """任务执行上下文"""

    task_id: int
    project_id: int
    project_path: str
    raw_objective: str

    # 缓存
    _file_cache: Dict[str, str] = field(default_factory=dict)
    _project_structure: Dict = field(default_factory=dict)
    _execution_history: List[Dict] = field(default_factory=list)

    _scanned: bool = False

    async def scan_project(self):
        """扫描项目结构"""
        if self._scanned:
            return

        try:
            directories = []
            files = []
            key_files = []

            # 递归扫描
            for root, dirs, filenames in os.walk(self.project_path):
                # 排除隐藏目录和常见排除目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build'
                ]]

                rel_root = os.path.relpath(root, self.project_path)

                for d in dirs:
                    directories.append(os.path.join(rel_root, d) if rel_root != '.' else d)

                for f in filenames:
                    if f.startswith('.'):
                        continue
                    rel_path = os.path.join(rel_root, f) if rel_root != '.' else f
                    files.append(rel_path)

                    # 标记关键文件
                    if f in ['README.md', 'main.py', 'app.py', 'index.ts', 'package.json', 'pyproject.toml']:
                        key_files.append(rel_path)

            self._project_structure = {
                "directories": directories[:50],  # 限制数量
                "files": files[:100],
                "key_files": key_files,
                "total_dirs": len(directories),
                "total_files": len(files)
            }

            self._scanned = True
            logger.info(f"Project scanned: {len(files)} files, {len(directories)} dirs")

        except Exception as e:
            logger.warning(f"Project scan error: {e}")
            self._project_structure = {"error": str(e)}

    def cache_file(self, path: str, content: str):
        """缓存文件内容"""
        self._file_cache[path] = content

    def get_cached_file(self, path: str) -> Optional[str]:
        """获取缓存的文件"""
        return self._file_cache.get(path)

    def update(self, action_result: Dict):
        """更新执行历史"""
        self._execution_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_result.get("action_type"),
            "success": action_result.get("success"),
            "summary": action_result.get("summary", "")
        })

    def get_structure_summary(self) -> str:
        """获取项目结构摘要"""
        if not self._project_structure:
            return "Not scanned"

        return json.dumps({
            "key_files": self._project_structure.get("key_files", []),
            "file_count": self._project_structure.get("total_files", 0),
            "dir_count": self._project_structure.get("total_dirs", 0)
        })

    def get_summary(self) -> str:
        """获取完整上下文摘要"""
        return json.dumps({
            "task_id": self.task_id,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "objective": self.raw_objective,
            "scanned": self._scanned,
            "cached_files": len(self._file_cache),
            "history_length": len(self._execution_history),
            "structure": self._project_structure if self._scanned else {}
        }, indent=2)