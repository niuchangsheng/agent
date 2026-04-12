#!/usr/bin/env node

/**
 * OnSessionStart Hook - 检测 Sprint 状态并提示继续
 *
 * 读取 artifacts/handoff.md 和 product_spec.md，检测是否有进行中的 Sprint。
 * 若有，输出提示信息引导用户继续执行 /run。
 */

const fs = require('fs');
const path = require('path');

const HANDOFF_PATH = path.join(__dirname, '../../artifacts/handoff.md');
const SPEC_PATH = path.join(__dirname, '../../artifacts/product_spec.md');

function parseHandoff(content) {
  const lastUpdateMatch = content.match(/\*\*最近更新时间\*\*: (.+)/);
  const statusMatch = content.match(/\*\*核心阶段落点\*\*: (.+)/);
  return {
    lastUpdate: lastUpdateMatch ? lastUpdateMatch[1] : '未知',
    status: statusMatch ? statusMatch[1] : '未知'
  };
}

function parseSpec(content) {
  const lines = content.split('\n');
  const pendingSprints = [];
  let currentVersion = '';

  for (const line of lines) {
    if (line.startsWith('### v')) {
      currentVersion = line.replace('### ', '').trim();
    }
    if (line.includes('[ ]') || line.includes('[!]')) {
      const sprintMatch = line.match(/Sprint (\d+): (.+)/);
      if (sprintMatch) {
        pendingSprints.push({
          version: currentVersion,
          id: sprintMatch[1],
          desc: sprintMatch[2],
          status: line.includes('[!]') ? 'blocked' : 'pending'
        });
      }
    }
  }

  return { pendingSprints };
}

function main() {
  // 检查文件是否存在
  if (!fs.existsSync(HANDOFF_PATH) || !fs.existsSync(SPEC_PATH)) {
    return; // 新项目，无需提示
  }

  try {
    const handoff = fs.readFileSync(HANDOFF_PATH, 'utf-8');
    const spec = fs.readFileSync(SPEC_PATH, 'utf-8');

    const handoffData = parseHandoff(handoff);
    const specData = parseSpec(spec);

    if (specData.pendingSprints.length === 0) {
      // 所有 Sprint 完成，检查是否需要新版本规划
      const hasPlanningVersion = spec.includes('🔄 规划中') || spec.includes('⏳ 进行中');
      if (!hasPlanningVersion) {
        console.log('🎉 所有版本已完成！可以执行 /plan 规划下一版本。');
      }
      return;
    }

    // 有待进行的 Sprint - 输出状态摘要
    console.log('\n' + '='.repeat(60));
    console.log('📋 SECA 持续迭代状态检测');
    console.log('='.repeat(60));
    console.log(`最后更新：${handoffData.lastUpdate}`);
    console.log(`当前状态：${handoffData.status}`);
    console.log('\n待执行 Sprint:');

    for (const s of specData.pendingSprints) {
      const icon = s.status === 'blocked' ? '🔴' : '⏳';
      console.log(`  ${icon} [${s.version}] Sprint ${s.id}: ${s.desc}`);
    }

    console.log('\n💡 提示：执行 /run 继续自动构建');
    console.log('='.repeat(60) + '\n');

  } catch (e) {
    // 静默失败，不要阻塞会话
    console.error('[hook] 状态检测失败:', e.message);
  }
}

main();
