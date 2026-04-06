import asyncio
import subprocess
from pydantic import BaseModel
from typing import Optional

class ExecutionResult(BaseModel):
    exit_code: Optional[int]
    stdout: str
    stderr: str
    is_timeout: bool

async def execute_command(command: str, timeout: float = 3.0) -> ExecutionResult:
    """
    Subprocess execution sandbox. Safely execute a shell command asynchronously
    and capture its standard output and errors, with a hard timeout constraint.
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
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
