#!/bin/bash
# SECA /run 永动脚本 - 每轮自动新建 session
#
# 用法：./scripts/run-loop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 从 ~/.claude/settings.json 加载环境变量
echo "🔐 加载环境变量..."
if [ -f ~/.claude/settings.json ]; then
    # 读取 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY
    API_KEY=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_AUTH_TOKEN"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
    BASE_URL=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_BASE_URL"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

    if [ -n "$API_KEY" ]; then
        export ANTHROPIC_API_KEY="$API_KEY"
        echo "✅ 已加载 ANTHROPIC_API_KEY (****${API_KEY: -8})"
    fi

    if [ -n "$BASE_URL" ]; then
        export ANTHROPIC_BASE_URL="$BASE_URL"
        echo "✅ 已加载 ANTHROPIC_BASE_URL"
    fi
fi

echo ""
echo "========================================"
echo "SECA /run 永动循环"
echo "========================================"
echo ""
echo "📋 工作流：每轮执行 1 个 Sprint → 自动新建 session → 继续下一轮"
echo "🛑 中断：Ctrl+C 或所有 Sprint 完成后停止"
echo ""
echo "按 Enter 开始..."
read

ROUND=0

while true; do
    ROUND=$((ROUND + 1))
    echo ""
    echo "========================================"
    echo "🔄 第 $ROUND 轮循环"
    echo "========================================"
    echo "时间：$(date '+%H:%M:%S')"
    echo ""

    # 检查是否还有待执行的 Sprint
    if ! grep -q '\[ \]\|\[!\]' artifacts/product_spec.md 2>/dev/null; then
        echo "✅ 所有 Sprint 已完成！"
        echo ""
        echo "接下来请选择："
        echo "  1. /release  - 结项交付"
        echo "  2. /plan     - 规划新版本后继续"
        echo ""
        break
    fi

    # 显示当前待执行的 Sprint
    echo "📋 待执行 Sprint:"
    grep '\[ \]\|\[!\]' artifacts/product_spec.md | head -3 | sed 's/^/   /'
    echo ""

    # 执行 /run（阻塞直到完成）
    echo "▶️  执行 /run..."
    echo ""

    if claude -p "/run"; then
        echo ""
        echo "✅ 第 $ROUND 轮完成"
    else
        echo ""
        echo "❌ 第 $ROUND 轮执行失败，退出"
        exit 1
    fi

    # 提交状态
    if [ -n "$(git status --porcelain)" ]; then
        echo "💾 提交状态变更..."
        git add -A
        git commit -m "chore: 第 $ROUND 轮 Sprint 完成"
    fi

    # 检查是否需要继续
    echo ""
    echo "⏸️  等待 3 秒后继续下一轮..."
    echo "   (按 Ctrl+C 中断)"
    sleep 3
done

echo ""
echo "========================================"
echo "🎉 所有 Sprint 完成！"
echo "========================================"
echo ""
echo "接下来可以执行："
echo "  - /release  - 结项交付"
echo ""
