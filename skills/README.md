# Skills

A set of skills that compose the spec-driven development workflow.

## Workflow

```
(research) → spec → build → check → done
               ^                |
               |   (NEEDS_FIX)  |
               +----------------+

fix can be invoked independently at any time
```

## Skill List

| Skill | Description | Prerequisite |
|-------|-------------|--------------|
| **spec** | Requirements hearing → integrated analysis → direction confirmation → plan generation → Annotation Cycle (browser review) → progress generation. Supports new/update modes. Single / multi-pr mode based on scale | None |
| **build** | Implements features guided by plan. Branch creation, task-by-task coding, build verification, PR creation. Supports pause/resume | spec completed |
| **check** | Compares plan against implementation code and reports PASS / PARTIAL / NEEDS_FIX. On NEEDS_FIX, proposes spec update | build completed |
| **fix** | Investigates root causes of issues. Prohibits speculative fixes, builds fix strategy based on facts. Supports feature / standalone modes | None |
| **research** | Technical investigation → research generation. Supports codebase analysis and web research. Can be invoked independently at any time | None |

## Data Storage

All plan data is stored in SQLite DB (`~/.claude/spec-flow.db`) via `scripts/db.sh`.
