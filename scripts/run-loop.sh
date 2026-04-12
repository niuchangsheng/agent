#!/bin/bash
# SECA /run 永动脚本 - 每轮自动新建 session
#
# 用法：./scripts/run-loop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "SECA /run 永动循环"
echo "========================================"
echo ""
echo "📋 工作流：每轮执行 1 个 Sprint → 自动新建 session → 继续下一轮"
echo "🛑 中断：Ctrl+C 或所有 Sprint 完成后停止"
echo ""

# 检查登录状态（可选，不需要时注释掉）
# echo "🔐 检查登录状态..."
# if ! claude -p "echo test" 2>&1 | grep -q "test"; then
#     echo "⚠️  未检测到有效登录，请先执行："
#     echo ""
#     echo "   claude -p '/login'"
#     echo ""
#     exit 1
# fi
# echo "✅ 登录状态正常"
# echo ""
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
