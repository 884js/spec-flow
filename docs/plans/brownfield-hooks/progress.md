---
plan: docs/plans/brownfield-hooks/plan.md
feature: brownfield-hooks
started: 2026-03-10
updated: 2026-03-11
mode: single
---

# 進捗: Brownfield検証 + Hooksフェーズ遷移

## 現在の状況

plan.md を作成完了。実装未着手。

## 次にやること

タスク #1（analyzer 出力フォーマット拡張）と #3（verifier 出力フォーマット拡張）と #5（phase-detector.sh 新規作成）は依存なしのため並行着手可能。

## タスク進捗

| # | タスク | 状態 |
|---|--------|------|
| 1 | analyzer 出力フォーマットに「既存コード影響分析」セクション追加 | - |
| 2 | spec Step 3 の方向性サマリに「既存コードへの影響」提示を追加 | - |
| 3 | verifier 出力フォーマットに「既存コード副作用」分類追加 | - |
| 4 | check の verifier 呼び出しに「既存コード影響」検証観点を追加 | - |
| 5 | phase-detector.sh を新規作成（skill-tracker.sh の機能を統合） | - |
| 6 | hooks.json を更新（skill-tracker エントリを phase-detector に置換） | - |

## ブランチ・PR

| ブランチ | PR | 状態 |
|---------|-----|------|
| - | - | 未着手 |

## 作業ログ

- 2026-03-10: plan.md + progress.md 作成
