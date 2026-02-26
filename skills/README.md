# Skills

仕様駆動開発のワークフローを構成するスキル群。

## ワークフロー

```
plan → strategy → implement → verify
                    ↑
                    |
               troubleshoot  ← 「動かない」「期待と違う」
```

## スキル一覧

| スキル | 概要 | 前提 |
|--------|------|------|
| **plan** | 要件定義・技術設計・実装計画を1コマンドで生成。対話で要件確認 → 技術設計を一括提示 → plan.md 生成 | なし |
| **strategy** | 実装戦略。plan.md のタスクをPR単位に分割し、progress.md にデリバリープラン・タスク進捗テーブルを生成 | plan 完了 |
| **implement** | 実装。ブランチ作成、タスク単位のコーディング、テスト、PR作成。中断・再開対応。PR単位実装モード対応 | plan 完了（strategy は任意） |
| **verify** | 検証。実装コードからデータフロー抽出 → plan.md との双方向乖離検出 | implement 完了 |
| **troubleshoot** | 不具合調査。実行フローをトレースし根本原因を特定。推測での修正を禁止し、事実に基づく修正方針を立てる | implement 完了後 |

## 出力先

全スキルの成果物は `docs/plans/{feature-name}/` に格納される。

```
docs/plans/{feature-name}/
├── plan.md                      ← plan（設計ドキュメント。plan 完了後は不変）
├── progress.md                  ← strategy / implement（実装進捗の単一ソース）
├── project-context.md           ← plan
├── implementation-summary.md    ← verify
└── troubleshoot-{YYYY-MM-DD}-{N}.md ← troubleshoot（調査レポート）
```
