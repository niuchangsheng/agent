#!/usr/bin/env node

/**
 * OnCommandComplete Hook - 在命令执行后自动检测并提交 Sprint 状态
 *
 * 当 /build 或 /qa 执行完成后，检测 product_spec.md 的变更并自动 commit。
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SPEC_PATH = path.join(__dirname, '../../artifacts/product_spec.md');
const HANDOFF_PATH = path.join(__dirname, '../../artifacts/handoff.md');

function getSprintStatus(content) {
  const completed = (content.match(/\[x\]/g) || []).length;
  const pending = (content.match(/\[ \]/g) || []).length;
  const blocked = (content.match(/\[!\]/g) || []).length;
  return { completed, pending, blocked };
}

function gitStatus() {
  try {
    execSync('git status --porcelain', { stdio: 'pipe' });
    return true; // 有未提交的变更
  } catch (e) {
    return false;
  }
}

function autoCommit(message) {
  try {
    execSync('git add -A', { stdio: 'pipe' });
    execSync(`git commit -m "${message}"`, { stdio: 'pipe' });
    console.log(`[hook] 自动提交：${message}`);
    return true;
  } catch (e) {
    console.error('[hook] 提交失败:', e.message);
    return false;
  }
}

function main() {
  // 检查是否有未提交的变更
  if (!gitStatus()) {
    return; // 无需提交
  }

  // 读取 spec 获取当前状态
  if (!fs.existsSync(SPEC_PATH)) {
    return;
  }

  const content = fs.readFileSync(SPEC_PATH, 'utf-8');
  const status = getSprintStatus(content);

  // 生成提交信息
  const timestamp = new Date().toISOString().slice(0, 10);
  let message = `chore(sprint): 进度更新 ${timestamp} - 已完成:${status.completed}, 待办:${status.pending}`;

  if (status.blocked > 0) {
    message += `, 阻塞:${status.blocked} ⚠️`;
  }

  autoCommit(message);

  // 更新 handoff.md 的 timestamp
  if (fs.existsSync(HANDOFF_PATH)) {
    let handoff = fs.readFileSync(HANDOFF_PATH, 'utf-8');
    const newDate = `**最近更新时间**: ${timestamp}`;
    if (handoff.includes('**最近更新时间**:')) {
      handoff = handoff.replace(/\*\*最近更新时间\*\*: .+/, newDate);
    } else {
      handoff = handoff.replace(
        /## 最新进度与心跳留存/,
        `## 最新进度与心跳留存\n- **最近更新时间**: ${timestamp}`
      );
    }
    fs.writeFileSync(HANDOFF_PATH, handoff);
    autoCommit(`chore(handoff): 更新进度时间戳 ${timestamp}`);
  }
}

main();
