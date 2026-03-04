# Skills

仕様駆動開発のワークフローを構成するスキル群。

## ワークフロー

```
spec → build → check → done
  ^                |
  |   (NEEDS_FIX)  |
  +----------------+

fix は任意タイミングで独立起動（「動かない」「期待と違う」）
```

## スキル一覧

| スキル | 概要 | 前提 |
|--------|------|------|
| **spec** | 要件ヒアリング → 統合分析 → 方向性確認 → plan.md + progress.md 生成。新規/更新の2モード対応。規模に応じて single / multi-pr モード | なし |
| **build** | plan.md に沿って実装。ブランチ作成、タスク順のコーディング、ビルド確認、PR 作成。中断・再開対応 | spec 完了 |
| **check** | plan.md と実装コードを突合し PASS / PARTIAL / NEEDS_FIX の3段階で判定。NEEDS_FIX 時は spec への更新を提案 | build 完了 |
| **fix** | 不具合の根本原因を調査。推測での修正を禁止し、事実に基づく修正方針を立てる。feature / standalone の2モード対応 | build 完了後 |

## 出力先

全スキルの成果物は `docs/plans/{feature-name}/` に格納される。

```
docs/plans/{feature-name}/
├── plan.md          ← spec（設計ドキュメント）
├── progress.md      ← spec（実装進捗の単一ソース）
├── result.md        ← check（検証結果）
└── debug-{YYYY-MM-DD}-{N}.md ← fix（調査レポート）
```
