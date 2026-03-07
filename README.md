# spec-flow

A lightweight spec-driven development plugin for Claude Code.
Guides you from requirements hearing through design, implementation, and verification with 5 skills centered around `plan.md`.

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
```

| Step | Skill | Role |
|------|-------|------|
| 0 | `/spec-flow:research` | Technical investigation → research.md generation. Supports codebase analysis and web research |
| 1 | `/spec-flow:spec` | Requirements hearing → integrated analysis → direction confirmation → plan.md generation → browser review (Annotation Cycle) → progress.md generation |
| 2 | `/spec-flow:build` | Branch creation → task-by-task implementation → build verification → PR creation, all guided by plan.md |
| 3 | `/spec-flow:check` | Compares implementation code against plan.md and reports PASS / PARTIAL / NEEDS_FIX |
| - | `/spec-flow:fix` | Root cause investigation with no speculative fixes allowed. Supports feature mode and standalone mode |

## Skills

### spec

Completes everything from requirements hearing to technical design and implementation planning in a single command.
Supports new mode (plan.md generation) and update mode (plan.md update from check results or additional requirements).
Also generates progress.md for task tracking (single mode for small/medium, multi-pr mode for large features).

```
(research) → hearing → analysis → direction confirmation → plan.md generation
               → Annotation Cycle (browser review) → progress.md generation
```

After plan.md generation, offers an **Annotation Cycle** — a browser-based review loop:

1. A local server starts and opens the browser with the rendered plan.md
2. You add comments to sections, paragraphs, or selected text
3. Click "submit comments" → writer agent auto-revises plan.md
4. Browser re-opens with updated plan.md — repeat until satisfied
5. Click "review complete (no changes)" → cycle ends

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

### research

Investigates technical topics through codebase analysis and web research.
Outputs research.md with findings, comparisons, and recommendations.
Results are automatically detected by `/spec` when creating a new spec.

```
/spec-flow:research authentication patterns for this project
```

**Output**: `docs/plans/{feature-name}/research.md`

## Architecture

```
skills/          ← User-facing entry points (orchestration)
  spec/build/check/fix/research

agents/          ← Backend agents invoked via Task()
  analyzer/      ← Project-wide integrated analysis
  writer/        ← plan.md / progress.md / result.md generation
  verifier/      ← Spec vs implementation comparison
  researcher/    ← Technical investigation

scripts/         ← Utility scripts
  annotation-viewer/  ← Browser-based plan.md review server

docs/plans/      ← All artifacts per feature
  {feature-name}/
    ├── plan.md
    ├── progress.md
    ├── result.md
    ├── research.md
    └── debug-*.md
```

## Marketplace

This plugin is published on the [Claude Code Plugin Marketplace](https://github.com/anthropics/claude-code-plugins).

```
/plugin marketplace add 884js/spec-flow
```

## License

MIT
