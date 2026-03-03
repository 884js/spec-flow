---
plan: "./plan.md"
feature: "readme-and-fix-rename"
started: 2026-03-03
updated: 2026-03-03
mode: single
---

# debug スキルの fix リネームと README 改善 — 実装進捗

## 現在の状況

全タスク完了。ビルド確認待ち。

## 次にやること

ビルド確認 → PR 作成。

## タスク進捗

| # | タスク | 対象ファイル | 見積 | PR | リスク | 状態 |
|---|--------|------------|------|-----|--------|------|
| 1 | `debug` → `fix` ディレクトリ移動 + `SKILL.md` 更新 | `skills/debug/` → `skills/fix/`, `skills/fix/SKILL.md` | S | - | - | ✓ |
| 2 | `spec` / `build` `SKILL.md` の `/debug` 参照を `/fix` に修正 | `skills/spec/SKILL.md`, `skills/build/SKILL.md` | S | - | - | ✓ |
| 3 | `README.md` 全面更新（軽量仕様駆動開発の強調、インストールコマンド修正、マーケットプレイス追加、`fix` 参照更新） | `README.md` | S | - | - | ✓ |
| 4 | `skills/README.md` の `fix` 参照更新 | `skills/README.md` | S | - | - | ✓ |

> タスク定義の詳細は [plan.md](./plan.md) を参照

## デリバリープラン

分割なし（1 PR）

## ブランチ・PR

| PR | ブランチ | PR URL | 状態 |
|----|---------|--------|------|
| - | - | - | - |

## 作業ログ

| 日時 | 内容 |
|------|------|
| 2026-03-03 | progress.md 作成 |
