#!/bin/bash
# SECA 永动循环：Plan → Run → Release → 无限循环
#
# 用法：./scripts/auto-seca.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 从 ~/.claude/settings.json 加载环境变量
echo "🔐 加载环境变量..."
if [ -f ~/.claude/settings.json ]; then
    API_KEY=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_AUTH_TOKEN"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
    BASE_URL=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_BASE_URL"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

    if [ -n "$API_KEY" ]; then
        export ANTHROPIC_API_KEY="$API_KEY"
        echo "✅ 已加载 ANTHROPIC_API_KEY"
    fi
    if [ -n "$BASE_URL" ]; then
        export ANTHROPIC_BASE_URL="$BASE_URL"
        echo "✅ 已加载 ANTHROPIC_BASE_URL"
    fi
fi
echo ""

echo "========================================"
echo "SECA 永动循环：Plan → Run → Release"
echo "========================================"
echo ""
echo "📋 工作流："
echo "  1. /plan  - 规划新版本的功能"
echo "  2. /run   - 循环实现所有 Sprint"
echo "  3. /release - 结项交付"
echo "  4. 回到步骤 1，规划下一版本"
echo ""
echo "🛑 中断：Ctrl+C"
echo ""
echo "按 Enter 开始..."
read

ROUND=0

while true; do
    ROUND=$((ROUND + 1))
    echo ""
    echo "========================================"
    echo "🚀 第 $ROUND 轮大循环"
    echo "========================================"
    echo "时间：$(date '+%H:%M:%S')"
    echo ""

    # ========== Step 1: Plan ==========
    echo "📋 步骤 1/3: 规划新版本 (/plan)"
    echo "========================================"
    echo ""

    claude -p "/plan" || { echo "❌ /plan 失败，退出"; exit 1; }

    echo ""
    echo "✅ 规划完成"

    # 提交规划
    if [ -n "$(git status --porcelain)" ]; then
        git add -A && git commit -m "feat: 第 $ROUND 轮版本规划完成"
    fi

    echo ""
    echo "⏸️  等待 5 秒后进入构建阶段..."
    sleep 5

    # ========== Step 2: Run (循环实现) ==========
    echo ""
    echo "📋 步骤 2/3: 循环实现所有 Sprint (/run-loop)"
    echo "========================================"
    echo ""

    # 执行 run 循环直到所有 Sprint 完成
    while grep -q '\[ \]\|\[!\]' artifacts/product_spec.md 2>/dev/null; do
        echo "⏳ 还有待执行的 Sprint，继续执行 /run..."

        claude -p "/run" || { echo "❌ /run 失败，退出"; exit 1; }

        # 提交状态
        if [ -n "$(git status --porcelain)" ]; then
            git add -A && git commit -m "chore: Sprint 完成"
        fi

        echo ""
        echo "⏸️  等待 3 秒后检查下一轮..."
        sleep 3
    done

    echo ""
    echo "✅ 所有 Sprint 完成！"

    echo ""
    echo "⏸️  等待 5 秒后进入结项阶段..."
    sleep 5

    # ========== Step 3: Release ==========
    echo ""
    echo "📋 步骤 3/3: 结项交付 (/release)"
    echo "========================================"
    echo ""

    claude -p "/release" || { echo "❌ /release 失败，退出"; exit 1; }

    echo ""
    echo "✅ 第 $ROUND 轮大循环完成！"

    # 提交结项报告
    if [ -n "$(git status --porcelain)" ]; then
        git add -A && git commit -m "docs: 第 $ROUND 轮结项报告"
    fi

    echo ""
    echo "========================================"
    echo "🎉 第 $ROUND 轮大循环完成！"
    echo "========================================"
    echo ""
    echo "⏸️  等待 10 秒后开始下一轮大循环..."
    echo "   (按 Ctrl+C 中断)"
    sleep 10
done
