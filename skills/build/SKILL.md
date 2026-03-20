---
name: build
description: "Implements features based on plan. Handles feature branch creation, task-by-task coding with dependency order, and build verification. Supports pause/resume via DB task state tracking. Use when starting implementation."
allowed-tools: Read Glob Grep Write Edit Task Bash WebSearch WebFetch Agent
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
Step 0.5: 実現性チェック（新規開始時のみ）
Step 1: タスク選択
Step 2: feature ブランチ作成（新規開始時のみ）
Step 3: タスク順の実装 + ビルド確認
Step 4: 実装検証
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
- **全て `pending`** → 新規開始: Step 0.5 へ
- **`done` や `in_progress` あり** → 再開: 実装状態とタスク一覧を突合し、再開ポイントを提示

---

## Step 0.5: 実現性チェック（新規開始時のみ）

plan の前提が現在のコードベースで成り立つか検証する:

```
Task(subagent_type: analyzer):
  「このプランの実現性を検証してください。
  DB スクリプト: ${CLAUDE_PLUGIN_ROOT}/scripts/db.sh
  feature-name: {feature-name}
  検証観点:
  - プランが触る予定のファイル・関数・APIに、プラン作成後の変更が入っていないか
  - プランが依存するライブラリ・スキーマ・型定義が現在も存在し互換性があるか
  - プランの設計方針と矛盾する変更が他で入っていないか
  - プランの設計アプローチ自体が現在のコードベースに対して妥当か」
```

| 判定 | 基準 | アクション |
|------|------|------------|
| **GO** | 前提に影響する変更なし | Step 1 へ |
| **UPDATE_NEEDED** | 前提の一部が変化 | 乖離箇所を列挙し、AskUserQuestion で `/spec`（プラン更新）か続行かを選択 |
| **BLOCKED** | 前提が根本的に崩れている | 乖離箇所を列挙し、`/spec` でのプラン再設計を案内して終了 |

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

### ビルド確認

全タスク完了後、plan 本文の「ビルド確認」セクションのコマンドを実行。エラーがあれば修正 → 再実行。成功したら Step 4 へ。

---

## Step 4: 実装検証

`db.sh get-body` で plan 本文を取得し、`git diff --name-only $(git merge-base HEAD main)...HEAD` で変更ファイルリストを取得する。以下の 3 Agent を**並列**で起動する。各 Agent には plan 本文と変更ファイルリストを渡す。

```
Agent("トレーサビリティ + 自己検証。plan の受入条件・自己検証チェックリスト（SV-N）・タスクと実装コードを照合し、plan にあるが実装されていない項目、実装にあるが plan にない変更を検出せよ。SV-N 項目は具体的に検証すること。\n\n{plan本文}\n\n変更ファイル:\n{変更ファイルリスト}")

Agent("AI ミスパターン検証。変更ファイルを読み、典型的な AI 実装ミス（存在しない API の呼び出し、不完全なエラーハンドリング、ハードコードされた値、未使用のインポート・変数）を検出せよ。\n\n{plan本文}\n\n変更ファイル:\n{変更ファイルリスト}")

Agent("コードベース一貫性検証。変更ファイルが既存コードの命名規則・ディレクトリ構成・エラー処理パターンと一貫しているか検証せよ。セキュリティ上の問題（インジェクション、未検証入力等）も検出せよ。\n\n{plan本文}\n\n変更ファイル:\n{変更ファイルリスト}")
```

3つの結果を集約し、Critical な問題があれば修正して再検証する（最大 2 回）。

検証サマリをユーザーに提示して完了:
```
## 実装検証サマリ

| 視点 | 検出事項 | 修正内容 |
|------|----------|----------|
| トレーサビリティ+SV | なし / {検出内容} | - / {修正内容} |
| AI ミスパターン | なし / {検出内容} | - / {修正内容} |
| 一貫性+セキュリティ | なし / {検出内容} | - / {修正内容} |
```
