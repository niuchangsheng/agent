"""
ClaudeClient - Claude API 集成

职责:
1. 调用 Anthropic Claude API
2. 支持 Tool Use
3. 管理对话历史
4. 处理流式响应
"""
import asyncio
import logging
import os
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Claude API 客户端"""

    def __init__(self):
        # 支持多种环境变量名
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.model = os.getenv("CLAUDE_MODEL") or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

        # 初始化 Anthropic SDK（如果可用）
        self.client = None
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                # 支持自定义 base_url（如阿里云代理）
                if self.base_url:
                    self.client = AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)
                    logger.info(f"ClaudeClient initialized with model {self.model}, base_url={self.base_url}")
                else:
                    self.client = AsyncAnthropic(api_key=self.api_key)
                    logger.info(f"ClaudeClient initialized with model {self.model}")
            except ImportError:
                logger.warning("anthropic SDK not installed, using mock mode")
        else:
            logger.warning("No ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN set, using mock mode")

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """You are a coding agent assistant. Your role is to help complete coding tasks.

You have access to these tools:
- read_file(path): Read file contents
- write_file(path, content): Write content to file
- execute_command(command): Run a shell command
- list_directory(path): List directory contents
- complete(result): Mark task as complete

Decision Process:
1. Analyze the objective and current project state
2. Decide the next action based on what needs to be done
3. Provide clear reasoning for your decision

Return your decision as JSON:
{
    "action": "tool_name",
    "params": {...},
    "reasoning": "why this action"
}

For complete action:
{
    "action": "complete",
    "result": "final result summary"
}"""

    async def decide(
        self,
        objective: str,
        perception: Dict,
        history: List[Dict],
        iteration: int
    ) -> Dict:
        """调用 Claude API 进行决策"""
        if not self.client:
            # Mock 模式
            return self._mock_decide(objective, perception, iteration)

        # 构建用户消息
        user_message = f"""
Objective: {objective}

Current Iteration: {iteration + 1}

Project State:
- Path: {perception.get('project_path', 'unknown')}
- Structure: {perception.get('structure_summary', 'unknown')}

Recent History (last 3 actions):
{json.dumps(history[-3:], indent=2) if history else 'No previous actions'}

Based on the objective and current state, decide your next action.
Return your decision as JSON.
"""

        try:
            # 调用 Claude API
            response = await self.client.messages.create(
                model=self.model,
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": user_message}],
                max_tokens=self.max_tokens,
                tools=self._get_tool_definitions() if iteration == 0 else None  # 首次调用包含工具定义
            )

            # 解析响应
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._mock_decide(objective, perception, iteration)

    def _get_tool_definitions(self) -> List[Dict]:
        """获取工具定义"""
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative file path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "execute_command",
                "description": "Execute a shell command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "complete",
                "description": "Mark task as complete",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"}
                    },
                    "required": ["result"]
                }
            }
        ]

    def _parse_response(self, response) -> Dict:
        """解析 Claude 响应"""
        # 从响应中提取决策
        content = response.content[0] if response.content else None

        if content and hasattr(content, 'text'):
            text = content.text
            # 尝试解析 JSON
            try:
                # 尝试找到 JSON 部分
                if "{" in text and "}" in text:
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    json_str = text[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 默认决策
        return {"action": "complete", "result": "Claude response parsed"}

    def _mock_decide(self, objective: str, perception: Dict, iteration: int) -> Dict:
        """Mock 决策逻辑"""
        if iteration < 3:
            return {
                "action": "read_file",
                "params": {"path": "README.md"},
                "reasoning": f"Mock: Exploring project for {objective}"
            }
        elif iteration < 6:
            return {
                "action": "execute_command",
                "params": {"command": "ls -la"},
                "reasoning": "Mock: Analyzing project structure"
            }
        else:
            return {
                "action": "complete",
                "result": f"Mock completed: {objective}",
                "reasoning": "Mock: Simulating task completion"
            }