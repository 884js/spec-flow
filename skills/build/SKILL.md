---
name: build
description: "Implements features based on plan.md. Handles feature branch creation, task-by-task coding with dependency order, build verification, and PR creation. Supports pause/resume via progress.md state tracking. Detects spec gaps and prompts for spec update. Use when starting implementation."
allowed-tools: Read Glob Grep Write Edit Task Bash
metadata:
  triggers: build, implement, 実装開始, コード実装, PR作成, 実装再開
---

# 実装（Build）

plan.md に沿って実装を進め、PR を作成する。
progress.md によるタスク状態管理で中断・再開をサポートする。

入力: `docs/plans/{feature-name}/plan.md`
状態管理: `docs/plans/{feature-name}/progress.md`
出力: 実装コード + PR

**パスルール**: `docs/plans/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は英語の kebab-case。パス区切り不可

## タスク状態管理

progress.md の状態列で管理する:

| 記号 | 意味 |
|------|------|
| `-` | 未着手 |
| `→` | 実施中 |
| `✓` | 完了 |

**重要**: plan.md は読み取り専用。全ての状態更新は progress.md に対して行う。

## ワークフロー

```
Step 0: plan.md + progress.md 読み込み + 再開検知
Step 1: feature ブランチ作成（新規開始時のみ）
Step 2: タスク順の実装
Step 3: ビルド確認
Step 4: PR 作成
```

---

## Step 0: 読み込み + 再開検知

```
Glob docs/plans/**/plan.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。

### plan.md の読み込み

```
Read docs/plans/{feature-name}/plan.md
```

plan.md が存在しない場合は「先に `/spec` で設計・実装計画を作成してください」と案内して終了。

### progress.md の読み込み

```
Read docs/plans/{feature-name}/progress.md
```

- **存在** → 状態を復元
- **存在しない** → 「先に `/spec` を完了してください（progress.md が生成されます）」と案内して終了

### 外部ライブラリの事前調査

plan.md で外部ライブラリが使われる場合、researcher エージェントで調査する:

```
Task(subagent_type: researcher):
  プロンプト: 「以下のライブラリについて実装に必要な情報を調査してください。
  調査対象: {ライブラリ名} v{バージョン}
  用途: {plan.md での用途}」
```

調査結果は `docs/plans/{feature-name}/libs/{ライブラリ名}.md` に保存する。

### debug ドキュメントの確認

```
Glob docs/plans/{feature-name}/debug-*.md
```

未対応の修正提案があれば、ユーザーに plan.md への反映可否を確認する。

### 再開検知

progress.md のタスク進捗テーブルから集計:

- **全て `-`** → **新規開始**: Step 1 へ
- **`✓` や `→` あり** → **再開フロー**:
  1. ブランチの実装状態と progress.md を突合
  2. ユーザーに再開ポイントを提示

---

## Step 1: feature ブランチ作成

```
Bash: git branch --show-current
```

現在のブランチを表示し、AskUserQuestion でベースブランチを確認する:
- 「現在の {branch} から切る」
- 「別のブランチから切る」

「別のブランチから切る」が選ばれた場合、ブランチ名を入力させて `git checkout {branch}` する。

次に、AskUserQuestion でブランチ名を確認する:
- 「feature/{feature-name}」（推奨）
- 「ブランチ名を指定する」

「ブランチ名を指定する」が選ばれた場合、AskUserQuestion でブランチ名を入力させる。

`git checkout -b {ブランチ名}` で作成する。

---

## Step 2: タスク順の実装

plan.md の実装タスク表を依存関係順に処理する。

### PRスコープ制限（multi-pr の場合）

progress.md に PR 列がある場合、未完了の最初の PR に属するタスクのみを対象とする。

### タスク状態の更新

- 開始: `-` → `→`
- 完了: `→` → `✓`
- 「現在の状況」「次にやること」も更新

### 見積サイズに応じた進め方

**S（小）**: メインコンテキストで直接実装。ユーザー確認なしで次のタスクに連続着手。

**M（中）**: analyzer で調査 → 実装。完了後に簡潔に報告。

**L（大）**: analyzer で調査 → 実装方針をユーザーに提示 → 承認後に実装。

### M/L タスクの進め方

```
Task(subagent_type: analyzer):
  プロンプト: 「タスク #{N}（{タスク名}）の実装に必要な情報を収集してください。
  仕様書: docs/plans/{feature-name}/plan.md の該当セクション
  既存コード: {対象ファイル一覧}
  以下を要約して返してください:
  - 実装に必要な型定義・インターフェース
  - 既存コードのパターン
  - バリデーションルール、エラーハンドリング
  - テストパターン」
```

### plan.md の参照

コンテキストが長くなった場合やタスクの詳細仕様を確認したい場合は plan.md を再度 Read してよい。

### 仕様矛盾検知プロトコル

仕様書と実際のコードで矛盾が見つかった場合:
1. 矛盾の内容をユーザーに提示
2. 選択肢:
   a) plan.md を修正してから再開
   b) 実装側を仕様に合わせる
   c) このまま進めて後で対応

---

## Step 3: ビルド確認

plan.md の「ビルド確認」セクションのコマンドを順に実行。エラーがあれば修正 → 再実行。

AskUserQuestion で手動検証の結果を確認する:
- 「問題なし、PR 作成に進む」→ Step 4 へ
- 「不具合がある」→ 「`/fix` で根本原因を調査できます」と案内
- 「仕様との整合性を確認したい」→ 「`/check` で plan.md との差分を確認できます」と案内

---

## Step 4: PR 作成

1. PR タイトルは plan.md の title フィールドから取得
2. PR テンプレートがあればその構造に従い、なければシンプルな本文を生成
3. ユーザーに確認
4. Draft PR にするか確認
5. 未コミットの変更があればコミットを提案
6. `git push -u origin {ブランチ名}` → `gh pr create`
7. PR URL を提示、progress.md を更新


