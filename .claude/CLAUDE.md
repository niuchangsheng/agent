# SECA Project Instructions

## Available Slash Commands

- `/plan` - Execute Planner role for product specification
- `/build` - Execute Generator role for TDD development  
- `/qa` - Execute Evaluator role for QA review
- `/run` - Run automated build loop (plan→build→qa)
- `/release` - Execute release workflow when all sprints complete

## Agent Roles

Refer to `.claude/agents/` for detailed role definitions:
- `planner.md` - Product architect role
- `generator.md` - TDD full-stack engineer role
- `evaluator.md` - Zero-tolerance QA evaluator role

## Workflow

1. Start with `/plan` to generate `artifacts/product_spec.md`
2. Use `/build` to implement sprints with TDD (Red→Green→Refactor)
3. Run `/qa` for evaluation (smoke test → scoring → pass/fail)
4. Repeat build→qa until all sprints marked `[x]`
5. Execute `/release` for final delivery

## Key Rules

- **TDD Required**: Tests first, then implementation
- **No YAGNI**: Don't add features not in sprint contract
- **Evidence Required**: QA must include terminal/curl/browser evidence
- **ADR Documentation**: Record technical decisions in `artifacts/decisions/`
