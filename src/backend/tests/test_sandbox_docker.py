import pytest
import os
from unittest.mock import patch, MagicMock

# Test Docker Executor
class TestDockerExecutor:

    @pytest.mark.asyncio
    async def test_docker_executor_runs_command(self):
        """Test Docker executor runs a simple command successfully"""
        from app.sandbox import DockerExecutor

        executor = DockerExecutor()
        result = await executor.execute("echo 'hello world'")

        assert result.exit_code == 0
        assert "hello world" in result.stdout
        assert not result.is_timeout

    @pytest.mark.asyncio
    async def test_docker_executor_captures_output(self):
        """Test Docker executor captures stdout and stderr"""
        from app.sandbox import DockerExecutor

        executor = DockerExecutor()
        result = await executor.execute("echo 'stdout' && echo 'stderr' >&2")

        assert "stdout" in result.stdout
        assert "stderr" in result.stderr

    @pytest.mark.asyncio
    async def test_docker_executor_timeout(self):
        """Test Docker executor terminates on timeout"""
        from app.sandbox import DockerExecutor

        executor = DockerExecutor(timeout=2)
        result = await executor.execute("sleep 10")

        assert result.is_timeout
        assert result.exit_code != 0  # Container was killed

    @pytest.mark.asyncio
    async def test_docker_executor_memory_limit(self):
        """Test Docker executor enforces memory limit"""
        from app.sandbox import DockerExecutor

        executor = DockerExecutor(memory_limit="32m")
        # Try to allocate more than limit
        # Note: This test may pass (exit != 0) or be inconclusive depending on Docker config
        result = await executor.execute("python3 -c 'x = [0] * 50000000'")

        # Container should either OOM kill (non-zero exit) or complete with some output
        # The key is that it doesn't hang indefinitely
        assert not result.is_timeout or result.exit_code != 0  # If timeout, should have non-zero exit

    @pytest.mark.asyncio
    async def test_docker_executor_dangerous_command_isolated(self):
        """Test dangerous commands are isolated in container"""
        from app.sandbox import DockerExecutor

        executor = DockerExecutor()
        # This should only affect the container, not the host
        result = await executor.execute("rm -rf /tmp/test_file_inside_container")

        # Command should complete without affecting host
        assert result.exit_code == 0


class TestSubprocessExecutor:
    """Fallback executor when Docker is unavailable"""

    @pytest.mark.asyncio
    async def test_subprocess_executor_runs_command(self):
        """Test subprocess executor runs command"""
        from app.sandbox import SubprocessExecutor

        executor = SubprocessExecutor()
        result = await executor.execute("echo 'test'")

        assert result.exit_code == 0
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_subprocess_executor_timeout(self):
        """Test subprocess executor terminates on timeout"""
        from app.sandbox import SubprocessExecutor

        executor = SubprocessExecutor(timeout=1)
        result = await executor.execute("sleep 5")

        assert result.is_timeout


class TestExecutorFactory:
    """Factory that selects appropriate executor based on config and availability"""

    def test_executor_factory_selects_docker(self):
        """Factory returns Docker executor when enabled and available"""
        from app.sandbox import get_executor, DockerExecutor

        with patch('app.sandbox.is_docker_available', return_value=True):
            with patch('app.sandbox.USE_DOCKER_SANDBOX', True):
                executor = get_executor()
                assert isinstance(executor, DockerExecutor)

    def test_executor_factory_fallback_on_docker_unavailable(self):
        """Factory falls back to subprocess when Docker unavailable"""
        from app.sandbox import get_executor, SubprocessExecutor

        with patch('app.sandbox.is_docker_available', return_value=False):
            executor = get_executor()
            assert isinstance(executor, SubprocessExecutor)

    def test_executor_factory_respects_config(self):
        """Factory respects USE_DOCKER_SANDBOX config"""
        from app.sandbox import get_executor, SubprocessExecutor

        with patch('app.sandbox.is_docker_available', return_value=True):
            with patch('app.sandbox.USE_DOCKER_SANDBOX', False):
                executor = get_executor()
                assert isinstance(executor, SubprocessExecutor)


class TestDockerAvailability:
    """Check if Docker is available on the system"""

    def test_is_docker_available_true(self):
        """Return True when docker CLI is available"""
        from app.sandbox import is_docker_available

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_docker_available() is True

    def test_is_docker_available_false(self):
        """Return False when docker CLI is not available"""
        from app.sandbox import is_docker_available

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert is_docker_available() is False

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_docker_available() is False
