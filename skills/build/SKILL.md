---
name: build
description: "Implements features based on plan. Handles feature branch creation, task-by-task coding with dependency order, and build verification. Supports pause/resume via DB task state tracking. Use when starting implementation."
allowed-tools: Read Glob Grep Write Edit Task Bash WebSearch WebFetch
metadata:
  triggers: build, implement, 実装開始, コード実装, 実装再開
---

# 実装（Build）

plan に沿って実装を進める。DB のタスク状態で中断・再開をサポートする。

入力: DB 上の plan レコード（`scripts/db.sh` 経由）
状態管理: DB 上のタスク状態 + progress 情報
出力: 実装コード

**feature-name**: 英語の kebab-case

## タスク状態

DB の tasks テーブルで管理: `pending`（未着手）/ `in_progress`（実施中）/ `done`（完了）

**重要**: plan 本文は読み取り専用。状態更新は `db.sh update-task-status` / `db.sh update-progress` で行う。

## ワークフロー

```
Step 0: 読み込み + 再開検知
Step 1: タスク選択
Step 2: feature ブランチ作成（新規開始時のみ）
Step 3: タスク順の実装
Step 4: ビルド確認
```

---

## Step 0: 読み込み + 再開検知

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh get-body --feature {feature-name}"
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-tasks --feature {feature-name}"
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh get-progress --feature {feature-name}"
```

plan が存在しない場合は「先に `/spec` で設計・実装計画を作成してください」と案内して終了。

タスク状態から判定:
- **全て `pending`** → 新規開始: Step 1 へ
- **`done` や `in_progress` あり** → 再開: 実装状態とタスク一覧を突合し、再開ポイントを提示

---

## Step 1: タスク選択

タスク一覧を表示し、AskUserQuestion で確認:
- 「全タスクを実行する」→ Step 2 へ
- 「実装するタスクを選択する」→ タスク番号を選択させる。依存先が未選択なら警告して自動追加

---

## Step 2: feature ブランチ作成

現在のブランチを表示し、AskUserQuestion でベースブランチを確認:
- 「現在の {branch} から切る」
- 「別のブランチから切る」→ ブランチ名を入力

ブランチ名を確認（デフォルト: `feature/{feature-name}`）して `git checkout -b` で作成。

---

## Step 3: タスク順の実装

選択されたタスクを依存関係順に処理する。

各タスク:
1. `Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh update-task-status --feature {feature-name} --number {N} --status in_progress"`
2. plan 本文の該当セクションを参照して実装
3. 完了後: `Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh update-task-status --feature {feature-name} --number {N} --status done"`
4. 進捗情報を更新: `Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh update-progress --feature {feature-name} --situation {現状} --next {次のタスク}"`

### 外部ライブラリの利用

外部ライブラリのAPIを使う際、使い方やパラメータに確信がなければ **実装前に** WebSearch で公式ドキュメントを確認する。学習データが古い可能性があるため、バージョン固有の破壊的変更に特に注意すること。

### 仕様矛盾検知

仕様書と実際のコードで矛盾が見つかった場合、ユーザーに提示して選択させる:
- plan を修正してから再開
- 実装側を仕様に合わせる
- このまま進めて後で対応

---

## Step 4: ビルド確認

plan 本文の「ビルド確認」セクションのコマンドを実行。エラーがあれば修正 → 再実行。

AskUserQuestion で手動検証の結果を確認:
- 「問題なし、完了」→ 終了
- 「不具合がある」→ `/fix` を案内
- 「仕様との整合性を確認したい」→ `/check` を案内
