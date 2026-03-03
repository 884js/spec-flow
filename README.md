# spec-flow

A lightweight spec-driven development plugin for Claude Code.
Guides you from requirements hearing through design, implementation, and verification with 4 skills centered around `plan.md`.

## Install

```
/plugin marketplace add 884js/spec-flow
/plugin install spec-flow@884js-spec-flow
```

## Workflow

```
spec → build → check → done
  ^                |
  |   (NEEDS_FIX)  |
  +----------------+

fix can be invoked independently at any time
```

| Step | Skill | Role |
|------|-------|------|
| 1 | `/spec-flow:spec` | Requirements hearing → integrated analysis → direction confirmation → plan.md generation |
| 2 | `/spec-flow:build` | Branch creation → task-by-task implementation → build verification → PR creation, all guided by plan.md |
| 3 | `/spec-flow:check` | Compares implementation code against plan.md and reports PASS / PARTIAL / NEEDS_FIX |
| - | `/spec-flow:fix` | Root cause investigation with no speculative fixes allowed. Supports feature mode and standalone mode |

## Skills

### spec

Completes everything from requirements hearing to technical design and implementation planning in a single command.
Supports new mode (plan.md generation) and update mode (plan.md update from check results or additional requirements).
Also generates progress.md for task tracking (single mode for small/medium, multi-pr mode for large features).

```
/spec-flow:spec add user notification feature
```

**Output**: `docs/plans/{feature-name}/plan.md` + `progress.md`

### build

Implements features guided by plan.md. Covers branch creation → task-by-task coding → build verification → PR creation.
Supports pause/resume via progress.md state tracking.
Detects spec gaps during implementation and prompts for spec update.

```
/spec-flow:build
```

### check

Reads implementation code directly and detects deviations from plan.md bidirectionally.
Reports results as PASS (all conditions met) / PARTIAL (minor mismatches) / NEEDS_FIX (significant mismatches), generating result.md.
On NEEDS_FIX, proposes spec update to close the loop.

```
/spec-flow:check
```

### fix

Prohibits speculative fixes and traces actual execution flows to identify root causes before proposing a fix.
Operates in feature mode (with plan.md for spec correlation) or standalone mode (without plan.md).

```
/spec-flow:fix describe the error symptoms
```

## Marketplace

This plugin is published on the [Claude Code Plugin Marketplace](https://github.com/anthropics/claude-code-plugins).

```
/plugin marketplace add 884js/spec-flow
```

## License

MIT
