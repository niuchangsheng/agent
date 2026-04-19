"""
AgentEngine - 执行引擎核心

职责:
1. 执行 perception→decision→action 循环
2. 调用 Claude API 进行决策
3. 通过 Tools 执行操作
4. 记录 Trace 到数据库
5. 推送 SSE 实时事件
"""
import asyncio
import logging
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.worker.sse_broadcaster import SSEBroadcaster
from app.worker.claude_client import ClaudeClient
from app.worker.context import TaskContext
from app.worker.tools import execute_tool
from app.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Trace

logger = logging.getLogger(__name__)


class AgentEngine:
    """Agent 执行引擎"""

    def __init__(
        self,
        task_id: int,
        project_id: int,
        project_path: str,
        raw_objective: str,
        worker_id: str,
        sse_broadcaster: Optional[SSEBroadcaster] = None,
        max_iterations: int = 50
    ):
        self.task_id = task_id
        self.project_id = project_id
        self.project_path = project_path
        self.raw_objective = raw_objective
        self.worker_id = worker_id
        self.sse_broadcaster = sse_broadcaster
        self.max_iterations = max_iterations

        self.context = TaskContext(
            task_id=task_id,
            project_id=project_id,
            project_path=project_path,
            raw_objective=raw_objective
        )

        self.claude_client: Optional[ClaudeClient] = None
        self.iteration = 0
        self.history: List[Dict] = []

    async def run(self) -> dict:
        """主执行循环"""
        logger.info(f"AgentEngine started for task {self.task_id}: {self.raw_objective}")

        # 初始化 Claude Client
        self.claude_client = ClaudeClient()

        try:
            for self.iteration in range(self.max_iterations):
                logger.info(f"Task {self.task_id} - Iteration {self.iteration + 1}")

                # 1. Perception: 分析当前状态
                perception = await self._perception()
                await self._emit_event("perception", perception)

                # 2. Decision: Claude 决定下一步
                decision = await self._decision(perception)
                await self._emit_event("decision", decision)

                # 3. Action: 执行决策
                action_result = await self._action(decision)
                await self._emit_event("action", action_result)

                # 4. 记录 Trace
                await self._record_trace(perception, decision, action_result)

                # 5. 更新上下文
                self.context.update(action_result)

                # 6. 记录历史
                self.history.append({
                    "iteration": self.iteration,
                    "perception": perception,
                    "decision": decision,
                    "action_result": action_result
                })

                # 7. 检查是否完成
                if decision.get("action") == "complete":
                    logger.info(f"Task {self.task_id} marked as complete by agent")
                    return {
                        "success": True,
                        "message": decision.get("result", "Task completed"),
                        "iterations": self.iteration + 1
                    }

                # 8. 更新进度
                progress = min(95, (self.iteration + 1) * 2)
                await self._emit_event("progress", {
                    "percent": progress,
                    "iteration": self.iteration + 1,
                    "message": action_result.get("summary", "Processing...")
                })

            # 达到最大迭代次数
            logger.warning(f"Task {self.task_id} reached max iterations ({self.max_iterations})")
            return {
                "success": False,
                "message": f"Max iterations ({self.max_iterations}) reached",
                "iterations": self.max_iterations
            }

        except Exception as e:
            logger.error(f"AgentEngine error for task {self.task_id}: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
                "iterations": self.iteration
            }

    async def _perception(self) -> dict:
        """感知阶段：分析当前项目状态"""
        logger.debug(f"Task {self.task_id} - Perception phase")

        # 扫描项目结构
        await self.context.scan_project()

        # 构建感知摘要
        perception = {
            "phase": "perception",
            "iteration": self.iteration,
            "objective": self.raw_objective,
            "project_path": self.project_path,
            "structure_summary": self.context.get_structure_summary(),
            "recent_history": self.history[-3:] if self.history else [],
            "context": self.context.get_summary()
        }

        return perception

    async def _decision(self, perception: dict) -> dict:
        """决策阶段：Claude 决定下一步行动"""
        logger.debug(f"Task {self.task_id} - Decision phase")

        if not self.claude_client:
            # Mock 模式：没有 API key 时返回简单决策
            return self._mock_decision(perception)

        try:
            decision = await self.claude_client.decide(
                objective=self.raw_objective,
                perception=perception,
                history=self.history,
                iteration=self.iteration
            )
            return decision
        except Exception as e:
            logger.warning(f"Claude API error, using mock decision: {e}")
            return self._mock_decision(perception)

    def _mock_decision(self, perception: dict) -> dict:
        """Mock 决策（无 Claude API 时使用）"""
        # 简单的模拟决策逻辑
        iteration = self.iteration

        if iteration == 0:
            return {
                "action": "read_file",
                "params": {"path": "README.md"},
                "reasoning": "First step: understand the project by reading README"
            }
        elif iteration == 1:
            return {
                "action": "execute_command",
                "params": {"command": "ls -la"},
                "reasoning": "Explore project structure"
            }
        elif iteration < 5:
            return {
                "action": "read_file",
                "params": {"path": f"src/main.py"},
                "reasoning": f"Analyzing source files"
            }
        else:
            # 模拟完成
            return {
                "action": "complete",
                "result": f"Mock execution completed after {iteration + 1} iterations. Objective: {self.raw_objective}",
                "reasoning": "Demo mode - simulated completion"
            }

    async def _action(self, decision: dict) -> dict:
        """执行阶段：根据决策执行操作"""
        logger.debug(f"Task {self.task_id} - Action phase: {decision.get('action')}")

        action_type = decision.get("action")
        params = decision.get("params", {})

        try:
            result = await execute_tool(
                action_type,
                params,
                self.context,
                self.project_path
            )

            action_result = {
                "phase": "action",
                "action_type": action_type,
                "params": params,
                "success": result.get("success", True),
                "result": result,
                "reasoning": decision.get("reasoning", ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            action_result = {
                "phase": "action",
                "action_type": action_type,
                "params": params,
                "success": False,
                "error": str(e),
                "reasoning": decision.get("reasoning", ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return action_result

    async def _record_trace(
        self,
        perception: dict,
        decision: dict,
        action_result: dict
    ):
        """记录 Trace 到数据库"""
        try:
            async with AsyncSession(engine) as session:
                trace = Trace(
                    task_id=self.task_id,
                    tenant_id=1,  # 默认租户
                    agent_role="worker",
                    perception_log=json.dumps(perception),
                    reasoning_log=json.dumps(decision),
                    applied_patch=json.dumps(action_result),
                    is_success=action_result.get("success", False)
                )
                session.add(trace)
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to record trace: {e}")

    async def _emit_event(self, event_type: str, data: dict):
        """推送 SSE 事件"""
        if self.sse_broadcaster:
            await self.sse_broadcaster.emit(self.task_id, event_type, {
                **data,
                "task_id": self.task_id,
                "worker_id": self.worker_id,
                "iteration": self.iteration
            })