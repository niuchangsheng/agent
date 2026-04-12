---
description: 自动删除此文件 - 已用 scripts/auto-seca.sh 替代
---

# 废弃说明

`/run` 命令已废弃。

请使用 `scripts/auto-seca.sh` 脚本驱动完整流程：

```bash
./scripts/auto-seca.sh
```

## 流程

```
/plan → [ /build → /qa → 更新 handoff ] × N → /release → 下一轮
```

每个 Sprint 完成后自动更新 `handoff.md` 并提交 git。
所有 Sprint 完成后自动执行 `/release`。
