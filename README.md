# spec-flow

A lightweight spec-driven development plugin for Claude Code.
Guides you from requirements hearing through design, implementation, and verification with 5 skills centered around plan stored in SQLite DB.

## Install

```
/plugin marketplace add 884js/spec-flow
/plugin install spec-flow@884js-spec-flow
```

## Workflow

```
(research) → spec → build → check → done
               ^                |
               |   (NEEDS_FIX)  |
               +----------------+

fix can be invoked independently at any time
list can be invoked at any time as a navigation hub
```

| Step | Skill | Role |
|------|-------|------|
| - | `/spec-flow:list` | Displays all plans with status and lets you navigate to any skill |
| 0 | `/spec-flow:research` | Technical investigation → research generation. Supports codebase analysis and web research |
| 1 | `/spec-flow:spec` | Requirements hearing → integrated analysis → direction confirmation → plan generation → browser review (Annotation Cycle) → progress generation |
| 2 | `/spec-flow:build` | Branch creation → task-by-task implementation → build verification → PR creation, all guided by plan |
| 3 | `/spec-flow:check` | Compares implementation code against plan and reports PASS / PARTIAL / NEEDS_FIX |
| - | `/spec-flow:fix` | Root cause investigation with no speculative fixes allowed. Supports feature mode and standalone mode |

## Skills

### list

Displays all plans in DB with status (in progress / not started / spec only / completed / verified) and lets you select a plan to edit, build, research, or check. Plans are sorted by priority — in-progress and not-started plans appear first. Supports pagination for large plan lists.

```
/spec-flow:list
```

### spec

Completes everything from requirements hearing to technical design and implementation planning in a single command.
Supports new mode (plan generation) and update mode (plan update from check results or additional requirements).
Also generates progress (task tracking) for single mode or multi-pr mode.

```
(research) → hearing → analysis → direction confirmation → plan generation
               → Annotation Cycle (browser review) → progress generation
```

After plan generation, offers an **Annotation Cycle** — a browser-based review loop:

1. A local server starts and opens the browser with the rendered plan
2. You add comments to sections, paragraphs, or selected text
3. Click "submit comments" → writer agent auto-revises plan
4. Browser re-opens with updated plan — repeat until satisfied
5. Click "review complete (no changes)" → cycle ends

```
/spec-flow:spec add user notification feature
```

### build

Implements features guided by plan. Covers branch creation → task-by-task coding → build verification → PR creation.
Supports pause/resume via DB task state tracking.
Detects spec gaps during implementation and prompts for spec update.

```
/spec-flow:build
```

### check

Reads implementation code directly and detects deviations from plan bidirectionally.
Reports results as PASS (all conditions met) / PARTIAL (minor mismatches) / NEEDS_FIX (significant mismatches), generating result.
On NEEDS_FIX, proposes spec update to close the loop.

```
/spec-flow:check
```

### fix

Prohibits speculative fixes and traces actual execution flows to identify root causes before proposing a fix.
Operates in feature mode (with plan for spec correlation) or standalone mode (without plan).

```
/spec-flow:fix describe the error symptoms
```

### research

Investigates technical topics through codebase analysis and web research.
Outputs research with findings, comparisons, and recommendations.
Results are automatically detected by `/spec` when creating a new spec.

```
/spec-flow:research authentication patterns for this project
```

## Data Storage

All plan data is stored in SQLite DB (`~/.claude/spec-flow.db`) managed via `scripts/db.sh`.

## Architecture

```
skills/          ← User-facing entry points (orchestration)
  list/spec/build/check/fix/research

agents/          ← Backend agents invoked via Task()
  analyzer/      ← Project-wide integrated analysis
  writer/        ← plan / progress / result generation (DB storage)
  verifier/      ← Spec vs implementation comparison
  researcher/    ← Technical investigation

scripts/         ← Utility scripts
  db.sh          ← DB operations (plan CRUD, task management, etc.)
  annotation-viewer/  ← Browser-based plan review server
  migrate-md-to-db.sh ← Migration from legacy md files to DB

migrations/      ← SQL schema definitions
```

## Marketplace

This plugin is published on the [Claude Code Plugin Marketplace](https://github.com/anthropics/claude-code-plugins).

```
/plugin marketplace add 884js/spec-flow
```

## License

MIT
