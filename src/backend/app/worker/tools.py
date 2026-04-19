"""
Tools - Agent 工具定义与执行

职责:
1. 定义可用的 Agent 工具
2. 执行工具操作
3. 与 Sandbox 集成执行命令
"""
import asyncio
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List

from app.worker.context import TaskContext
from app.sandbox import get_executor, execute_command

logger = logging.getLogger(__name__)


async def execute_tool(
    action_type: str,
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """执行指定工具"""

    tool_map = {
        "read_file": tool_read_file,
        "write_file": tool_write_file,
        "execute_command": tool_execute_command,
        "list_directory": tool_list_directory,
        "complete": tool_complete,
    }

    handler = tool_map.get(action_type)
    if not handler:
        return {"success": False, "error": f"Unknown action: {action_type}"}

    try:
        result = await handler(params, context, project_path)
        return result
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"success": False, "error": str(e)}


async def tool_read_file(
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """读取文件"""
    path = params.get("path", "")
    full_path = os.path.join(project_path, path)

    if not os.path.exists(full_path):
        return {"success": False, "error": f"File not found: {path}"}

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 缓存到上下文
        context.cache_file(path, content)

        return {
            "success": True,
            "path": path,
            "content": content,
            "size": len(content),
            "summary": f"Read {len(content)} chars from {path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_write_file(
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """写入文件"""
    path = params.get("path", "")
    content = params.get("content", "")
    full_path = os.path.join(project_path, path)

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "size": len(content),
            "summary": f"Written {len(content)} chars to {path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_execute_command(
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """执行命令"""
    command = params.get("command", "")

    if not command:
        return {"success": False, "error": "No command provided"}

    try:
        # 使用 Sandbox 执行器
        executor = get_executor()
        result = await executor.execute(command)

        return {
            "success": result.exit_code == 0,
            "command": command,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "is_timeout": result.is_timeout,
            "summary": f"Executed: {command}, exit_code={result.exit_code}"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "command": command}


async def tool_list_directory(
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """列出目录内容"""
    path = params.get("path", ".")
    full_path = os.path.join(project_path, path)

    if not os.path.exists(full_path):
        return {"success": False, "error": f"Directory not found: {path}"}

    try:
        entries = []
        for entry in os.listdir(full_path):
            entry_path = os.path.join(full_path, entry)
            entries.append({
                "name": entry,
                "type": "directory" if os.path.isdir(entry_path) else "file",
                "size": os.path.getsize(entry_path) if os.path.isfile(entry_path) else 0
            })

        return {
            "success": True,
            "path": path,
            "entries": entries,
            "count": len(entries),
            "summary": f"Listed {len(entries)} items in {path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_complete(
    params: Dict,
    context: TaskContext,
    project_path: str
) -> Dict:
    """标记任务完成"""
    result = params.get("result", "Task completed")

    return {
        "success": True,
        "result": result,
        "summary": "Task marked as complete"
    }


def get_tool_definitions() -> List[Dict]:
    """获取工具定义列表（供 Claude API）"""
    return [
        {
            "name": "read_file",
            "description": "Read file contents from the project",
            "parameters": {
                "path": {"type": "string", "description": "Relative file path"}
            }
        },
        {
            "name": "write_file",
            "description": "Write content to a file in the project",
            "parameters": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            }
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command in sandbox",
            "parameters": {
                "command": {"type": "string"}
            }
        },
        {
            "name": "list_directory",
            "description": "List contents of a directory",
            "parameters": {
                "path": {"type": "string", "default": "."}
            }
        },
        {
            "name": "complete",
            "description": "Mark the task as complete",
            "parameters": {
                "result": {"type": "string"}
            }
        }
    ]