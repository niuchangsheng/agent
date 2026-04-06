import pytest
import asyncio
from app.sandbox import execute_command, ExecutionResult

@pytest.mark.asyncio
async def test_sandbox_success():
    result: ExecutionResult = await execute_command("echo 'SECA Test'", timeout=2.0)
    assert result.exit_code == 0
    assert "SECA Test" in result.stdout
    assert not result.is_timeout

@pytest.mark.asyncio
async def test_sandbox_stderr_capture_and_safe_return():
    result = await execute_command("python3 -c '1/0'", timeout=2.0)
    assert result.exit_code != 0
    assert "ZeroDivisionError" in result.stderr
    assert not result.is_timeout

@pytest.mark.asyncio
async def test_sandbox_timeout_handling():
    # Wait for 5 seconds but timeout sets to 1
    result = await execute_command("sleep 5", timeout=1.0)
    assert result.is_timeout
    assert result.exit_code is None or result.exit_code != 0
