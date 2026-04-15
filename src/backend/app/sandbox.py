import asyncio
import subprocess
import os
from pydantic import BaseModel
from typing import Optional

# Configuration
USE_DOCKER_SANDBOX = os.getenv("USE_DOCKER_SANDBOX", "true").lower() == "true"
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "python:3.12-slim")
DOCKER_MEMORY_LIMIT = os.getenv("DOCKER_MEMORY_LIMIT", "512m")
DOCKER_TIMEOUT = int(os.getenv("DOCKER_TIMEOUT", "60"))
DEFAULT_TIMEOUT = float(os.getenv("SANDBOX_TIMEOUT", "30"))


class ExecutionResult(BaseModel):
    exit_code: Optional[int]
    stdout: str
    stderr: str
    is_timeout: bool


class BaseExecutor:
    """Base class for command executors"""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def execute(self, command: str) -> ExecutionResult:
        raise NotImplementedError


class DockerExecutor(BaseExecutor):
    """Execute commands in a Docker container with resource limits"""

    def __init__(self, timeout: float = DOCKER_TIMEOUT, memory_limit: str = DOCKER_MEMORY_LIMIT):
        super().__init__(timeout=timeout)
        self.memory_limit = memory_limit

    async def execute(self, command: str) -> ExecutionResult:
        """Execute command in Docker container"""
        # Escape command for shell
        escaped_cmd = command.replace("'", "'\"'\"'")

        docker_command = [
            "docker", "run", "--rm",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--memory", self.memory_limit,
            "--cpus", "1",
            "--network", "none",
            "--pids-limit", "50",
            DOCKER_IMAGE,
            "sh", "-c", command
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *docker_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                is_timeout = False
            except asyncio.TimeoutError:
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()
                is_timeout = True

            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""

            return ExecutionResult(
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                is_timeout=is_timeout
            )

        except FileNotFoundError:
            # Docker not found, fallback to subprocess
            return await SubprocessExecutor(timeout=self.timeout).execute(command)
        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Docker execution failed: {str(e)}",
                is_timeout=False
            )


class SubprocessExecutor(BaseExecutor):
    """Fallback executor using local subprocess"""

    async def execute(self, command: str) -> ExecutionResult:
        """Execute command using subprocess"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                is_timeout = False
            except asyncio.TimeoutError:
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()
                is_timeout = True

            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""

            return ExecutionResult(
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                is_timeout=is_timeout
            )

        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                is_timeout=False
            )


def is_docker_available() -> bool:
    """Check if Docker daemon is running and accessible"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def get_executor() -> BaseExecutor:
    """Factory function to get appropriate executor based on config and availability"""
    if USE_DOCKER_SANDBOX and is_docker_available():
        return DockerExecutor()
    else:
        return SubprocessExecutor()


# Legacy function for backward compatibility
async def execute_command(command: str, timeout: float = DEFAULT_TIMEOUT) -> ExecutionResult:
    """
    Execute a shell command with sandbox isolation.
    Uses Docker if available and enabled, otherwise falls back to subprocess.
    """
    executor = get_executor()
    executor.timeout = timeout
    return await executor.execute(command)
