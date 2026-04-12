#!/bin/bash
# SECA 永动循环：Plan → (Build→QA)×N → Release → 无限迭代
#
# 用法：./scripts/auto-seca.sh
#
# 流程说明：
#   1. /plan   - 规划新版本的功能和 Sprint
#   2. 循环执行每个 Sprint:
#      a. /build - TDD 开发单个 Sprint
#      b. /qa    - 评审该 Sprint
#      c. 更新 handoff.md 并提交
#   3. /release - 所有 Sprint 完成后结项
#   4. 回到步骤 1，规划下一版本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 从 ~/.claude/settings.json 加载环境变量
load_env() {
    if [ -f ~/.claude/settings.json ]; then
        API_KEY=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_AUTH_TOKEN"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
        BASE_URL=$(cat ~/.claude/settings.json | grep -o '"ANTHROPIC_BASE_URL"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

        if [ -n "$API_KEY" ]; then
            export ANTHROPIC_API_KEY="$API_KEY"
        fi
        if [ -n "$BASE_URL" ]; then
            export ANTHROPIC_BASE_URL="$BASE_URL"
        fi
    fi
}

# 更新 handoff.md
update_handoff() {
    local sprint_id="$1"
    local status="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    if [ -f artifacts/handoff.md ]; then
        # 更新时间戳和当前 Sprint 状态
        sed -i "s/\*\*最近更新时间\*\*: .*/\*\*最近更新时间\*\*: $timestamp/" artifacts/handoff.md 2>/dev/null || true
        sed -i "s/\*\*当前 Sprint\*\*: .*/\*\*当前 Sprint\*\*: Sprint $sprint_id - $status/" artifacts/handoff.md 2>/dev/null || true
    fi
}

# 检查是否还有待执行的 Sprint
has_pending_sprints() {
    grep -q '\[ \]\|\[!\]' artifacts/product_spec.md 2>/dev/null
}

# 主流程
main() {
    load_env

    echo "========================================"
    echo "SECA 永动循环：Plan → (Build→QA)×N → Release"
    echo "========================================"
    echo ""
    echo "📋 流程："
    echo "  1. /plan   - 规划新版本"
    echo "  2. /build  - 开发单个 Sprint"
    echo "  3. /qa     - 评审该 Sprint"
    echo "  4. 更新 handoff 并提交"
    echo "  5. 重复 2-4 直到所有 Sprint 完成"
    echo "  6. /release - 结项交付"
    echo "  7. 回到步骤 1"
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
        echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        # ========== Step 1: Plan ==========
        echo "📋 步骤 1/3: 规划新版本"
        echo "========================================"

        claude -p "/plan" || { echo "❌ /plan 失败，退出"; exit 1; }

        echo "✅ 规划完成"

        # 提交规划
        if [ -n "$(git status --porcelain)" ]; then
            git add -A && git commit -m "feat: 第 $ROUND 轮版本规划"
        fi

        echo ""
        echo "⏸️  等待 5 秒后进入构建阶段..."
        sleep 5

        # ========== Step 2: Build → QA 循环 ==========
        echo ""
        echo "📋 步骤 2/3: 循环构建 (Build→QA)"
        echo "========================================"

        SPRINT_COUNT=0

        while has_pending_sprints; do
            SPRINT_COUNT=$((SPRINT_COUNT + 1))
            echo ""
            echo "┌─────────────────────────────────────────┐"
            echo "│ 🔨 Sprint $SPRINT_COUNT 开始               │"
            echo "└─────────────────────────────────────────┘"

            # 更新 handoff
            update_handoff "$SPRINT_COUNT" "构建中"

            # Build
            echo ""
            echo "  → 执行 /build..."
            claude -p "/build" || {
                echo "❌ /build 失败"
                update_handoff "$SPRINT_COUNT" "构建失败"
                exit 1
            }

            # 提交 build 结果
            if [ -n "$(git status --porcelain)" ]; then
                git add -A && git commit -m "feat: Sprint $SPRINT_COUNT 实现"
            fi

            # QA
            echo ""
            echo "  → 执行 /qa..."
            claude -p "/qa" || {
                echo "❌ /qa 失败"
                update_handoff "$SPRINT_COUNT" "QA 失败 [!]"
                exit 1
            }

            # 提交 qa 结果
            if [ -n "$(git status --porcelain)" ]; then
                git add -A && git commit -m "test: Sprint $SPRINT_COUNT QA 评审"
            fi

            # 更新 handoff
            update_handoff "$SPRINT_COUNT" "已完成"

            echo ""
            echo "✅ Sprint $SPRINT_COUNT 完成"
            echo ""
            echo "⏸️  等待 3 秒后继续下一个 Sprint..."
            sleep 3
        done

        echo ""
        echo "✅ 所有 Sprint 完成！共 $SPRINT_COUNT 个"

        echo ""
        echo "⏸️  等待 5 秒后进入结项阶段..."
        sleep 5

        # ========== Step 3: Release ==========
        echo ""
        echo "📋 步骤 3/3: 结项交付"
        echo "========================================"

        claude -p "/release" || { echo "❌ /release 失败，退出"; exit 1; }

        echo "✅ 第 $ROUND 轮结项完成"

        # 提交结项报告
        if [ -n "$(git status --porcelain)" ]; then
            git add -A && git commit -m "docs: 第 $ROUND 轮结项报告"
        fi

        echo ""
        echo "========================================"
        echo "🎉 第 $ROUND 轮大循环完成！"
        echo "========================================"
        echo ""
        echo "⏸️  等待 10 秒后开始下一轮..."
        echo "   (按 Ctrl+C 中断)"
        sleep 10
    done
}

main
