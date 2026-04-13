"""
Sprint 12: ETA 预测计算器

使用移动平均算法计算任务预计完成时间
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from collections import deque


class ETACalculator:
    """
    ETA 计算器 - 使用移动平均算法

    工作原理:
    1. 记录每次进度更新的时间和百分比
    2. 计算最近 N 个样本的平均速度
    3. 根据剩余进度和平均速度估算剩余时间
    """

    def __init__(self, window_size: int = 5):
        """
        初始化 ETA 计算器

        Args:
            window_size: 移动平均窗口大小（至少需要 3 个样本才能计算）
        """
        self.window_size = window_size
        self._samples: deque[Tuple[int, datetime]] = deque(maxlen=window_size)

    def add_progress_sample(self, progress_percent: int, timestamp: datetime = None):
        """
        添加进度样本

        Args:
            progress_percent: 进度百分比 (0-100)
            timestamp: 时间戳（默认当前时间）
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # 确保时间戳是 aware datetime
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        self._samples.append((progress_percent, timestamp))

    def get_remaining_seconds(self) -> Optional[int]:
        """
        获取预计剩余时间（秒）

        Returns:
            剩余秒数，如果样本不足则返回 None
        """
        if len(self._samples) < 3:
            return None

        # 获取最新样本
        latest_progress, latest_time = self._samples[-1]

        # 如果已完成，返回 0
        if latest_progress >= 100:
            return 0

        # 计算平均速度（使用最近 3 个样本）
        samples_list = list(self._samples)

        # 计算从第一个样本到最后一个样本的总进度和总时间
        first_progress, first_time = samples_list[0]
        total_progress_change = latest_progress - first_progress

        if total_progress_change <= 0:
            return None  # 没有进展，无法计算

        total_time_seconds = (latest_time - first_time).total_seconds()

        if total_time_seconds <= 0:
            return None  # 时间为 0 或负数，无法计算

        # 计算每秒进度
        progress_per_second = total_progress_change / total_time_seconds

        # 计算剩余时间
        remaining_progress = 100 - latest_progress
        remaining_seconds = remaining_progress / progress_per_second

        return int(remaining_seconds)

    def get_eta(self) -> Optional[str]:
        """
        获取 ETA 字符串表示

        Returns:
            ETA 字符串（如 "剩余约 30 秒"），如果无法计算则返回 None
        """
        remaining = self.get_remaining_seconds()

        if remaining is None:
            return None

        if remaining <= 0:
            return "即将完成"

        if remaining < 60:
            return f"剩余约 {remaining} 秒"
        elif remaining < 3600:
            minutes = remaining // 60
            seconds = remaining % 60
            return f"剩余约 {minutes} 分 {seconds} 秒"
        else:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return f"剩余约 {hours} 小时 {minutes} 分"

    def get_estimated_completion_time(self) -> Optional[datetime]:
        """
        获取预计完成时间

        Returns:
            预计完成时间，如果无法计算则返回 None
        """
        remaining = self.get_remaining_seconds()

        if remaining is None:
            return None

        return datetime.now(timezone.utc) + timedelta(seconds=remaining)

    def reset(self):
        """重置计算器"""
        self._samples.clear()

    def get_samples_count(self) -> int:
        """获取样本数量"""
        return len(self._samples)


# 全局 ETA 计算器缓存 {task_id: ETACalculator}
_eta_calculators: dict[int, ETACalculator] = {}


def get_eta_calculator(task_id: int) -> ETACalculator:
    """获取或创建任务的 ETA 计算器"""
    if task_id not in _eta_calculators:
        _eta_calculators[task_id] = ETACalculator()
    return _eta_calculators[task_id]


def reset_eta_calculator(task_id: int):
    """重置任务的 ETA 计算器"""
    if task_id in _eta_calculators:
        del _eta_calculators[task_id]


def update_task_eta(task_id: int, progress_percent: int) -> Tuple[Optional[int], Optional[str]]:
    """
    更新任务 ETA

    Args:
        task_id: 任务 ID
        progress_percent: 进度百分比

    Returns:
        (remaining_seconds, eta_string) 元组
    """
    calculator = get_eta_calculator(task_id)
    calculator.add_progress_sample(progress_percent)

    remaining = calculator.get_remaining_seconds()
    eta = calculator.get_eta()

    return remaining, eta
