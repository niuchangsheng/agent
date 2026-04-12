#!/usr/bin/env node

/**
 * /run 前置状态检测脚本
 *
 * 在 /run 主逻辑执行前：
 * 1. 检测 handoff.md 和 product_spec.md 状态
 * 2. 输出当前进度摘要
 * 3. 若有阻塞错误，输出告警
 */

const fs = require('fs');
const path = require('path');

const HANDOFF_PATH = path.join(__dirname, '../../artifacts/handoff.md');
const SPEC_PATH = path.join(__dirname, '../../artifacts/product_spec.md');

function parseSpec(content) {
  const lines = content.split('\n');
  const pendingSprints = [];
  let currentVersion = '';
  let hasPlanningVersion = false;

  for (const line of lines) {
    if (line.startsWith('### v')) {
      currentVersion = line.replace('### ', '').trim();
      if (line.includes('规划中') || line.includes('进行中')) {
        hasPlanningVersion = true;
      }
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

  return { pendingSprints, hasPlanningVersion };
}

function parseHandoff(content) {
  const lastUpdateMatch = content.match(/\*\*最近更新时间\*\*: (.+)/);
  const statusMatch = content.match(/\*\*核心阶段落点\*\*: (.+)/);
  return {
    lastUpdate: lastUpdateMatch ? lastUpdateMatch[1] : '未知',
    status: statusMatch ? statusMatch[1] : '未知'
  };
}

function main() {
  if (!fs.existsSync(SPEC_PATH)) {
    console.log('[run] 未检测到 product_spec.md，需要先执行 /plan');
    return;
  }

  const spec = fs.readFileSync(SPEC_PATH, 'utf-8');
  const { pendingSprints, hasPlanningVersion } = parseSpec(spec);

  // 所有 Sprint 完成，无待规划版本
  if (pendingSprints.length === 0 && !hasPlanningVersion) {
    console.log('');
    console.log('🎉 所有版本已完成！');
    console.log('📋 即将执行 /plan 规划下一版本...');
    console.log('');
    return;
  }

  // 有待执行的 Sprint
  if (pendingSprints.length > 0) {
    const handoff = fs.existsSync(HANDOFF_PATH)
      ? fs.readFileSync(HANDOFF_PATH, 'utf-8')
      : '';
    const handoffData = parseHandoff(handoff);

    console.log('');
    console.log('='.repeat(60));
    console.log('📋 SECA 持续迭代状态检测');
    console.log('='.repeat(60));
    console.log(`最后更新：${handoffData.lastUpdate}`);
    console.log(`当前状态：${handoffData.status}`);
    console.log('');
    console.log(`待执行 Sprint: ${pendingSprints.length} 个`);

    for (const s of pendingSprints.slice(0, 5)) { // 最多显示 5 个
      const icon = s.status === 'blocked' ? '🔴' : '⏳';
      console.log(`  ${icon} [${s.version}] Sprint ${s.id}: ${s.desc.slice(0, 40)}...`);
    }

    if (pendingSprints.length > 5) {
      console.log(`  ... 还有 ${pendingSprints.length - 5} 个`);
    }

    console.log('');

    // 检查是否有阻塞的 Sprint
    const blocked = pendingSprints.filter(s => s.status === 'blocked');
    if (blocked.length > 0) {
      console.log('⚠️  检测到被 QA 打回的 Sprint，需要特别关注！');
    }

    console.log('='.repeat(60));
    console.log('');
  }
}

main();
