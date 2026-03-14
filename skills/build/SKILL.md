---
name: build
description: "Implements features based on plan.md. Handles feature branch creation, task-by-task coding with dependency order, and build verification. Supports pause/resume via progress.md state tracking. Detects spec gaps and prompts for spec update. Use when starting implementation."
allowed-tools: Read Glob Grep Write Edit Task Bash
metadata:
  triggers: build, implement, 実装開始, コード実装, 実装再開
---

# 実装（Build）

plan.md に沿って実装を進める。
progress.md によるタスク状態管理で中断・再開をサポートする。

入力: `docs/plans/{feature-name}/plan.md`
状態管理: `docs/plans/{feature-name}/progress.md`
出力: 実装コード

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
Step 1: タスクプレビュー + 選択
Step 2: feature ブランチ作成（新規開始時のみ）
Step 3: タスク順の実装
Step 4: ビルド確認
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

- **全て `-`** → **新規開始**: Step 1 へ（タスクプレビュー + 選択）
- **`✓` や `→` あり** → **再開フロー**:
  1. ブランチの実装状態と progress.md を突合
  2. ユーザーに再開ポイントを提示

---

## Step 1: タスクプレビュー + 選択

plan.md のタスク一覧をユーザーに提示し、実装対象を選択させる。

### 1-a. タスク一覧の提示

plan.md の実装タスク表をフォーマット付きで表示する。再開フローの場合は、`✓`（完了）と `→`（実施中）のタスクに状態を付記し、選択対象外であることを示す。

表示例:
```
実装タスク一覧:
| # | タスク | 見積 | 状態 |
|---|--------|------|------|
| 1 | ○○の実装 | M | - |
| 2 | △△の追加 | S | ✓（完了） |
| 3 | □□の修正 | S | - |
```

### 1-b. 第1段階: 実行モード選択

AskUserQuestion で確認する:
- 「全タスクを実行する（Recommended）」→ 全未着手タスクを実装対象とし、Step 2 へ
- 「実装するタスクを選択する」→ 1-c へ

### 1-c. 第2段階: タスク選択

未着手（`-`）のタスクのみを選択肢として提示する。

**タスクが4個以下の場合**:

AskUserQuestion（`multiSelect: true`）で全タスクを1回で列挙する。各選択肢の label は `#{番号} {タスク名}（{見積}）` とする。

**タスクが5個以上の場合**:

依存関係・機能単位で4個以下のグループに分割し、グループごとに AskUserQuestion（`multiSelect: true`）を提示する。

グループ分割の基準:
1. 依存関係で連なるタスクを同一グループにする
2. 対象ファイルが同じタスクを同一グループにする
3. 上記で4個を超える場合は機能的なまとまりで分割する

各グループの AskUserQuestion には header にグループ名を付ける（例: 「バックエンド系」「フロントエンド系」）。

### 1-d. 依存関係チェック + 自動補完

全グループの選択結果を統合後、plan.md の依存列を参照して検証する:
- 選択したタスクの依存先が未選択の場合、警告メッセージを表示して自動的に依存先を追加する

```
⚠ タスク #3 は #1 に依存しています。#1 を自動的に追加しました。
最終的な実装対象: #1, #3, #5
```

選択結果を以降の Step で実装対象として保持する。

---

## Step 2: feature ブランチ作成

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

## Step 3: タスク順の実装

plan.md の実装タスク表を依存関係順に処理する。**Step 1 で選択されたタスクのみを対象とする。**

### スコープ制限

1. **PRスコープ制限（multi-pr の場合）**: progress.md に PR 列がある場合、未完了の最初の PR に属するタスクのみを対象とする
2. **ユーザー選択制限**: Step 1 で選択されたタスクのみを処理対象とする（PR スコープで絞った後、さらにユーザー選択で絞る）

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

コンテキストが長くなった場合やタスクの詳細仕様を確認したい場合は以下を実行する:

```
Read docs/plans/{feature-name}/progress.md
Read docs/plans/{feature-name}/plan.md（該当タスクの詳細セクション）
```


### 仕様矛盾検知プロトコル

仕様書と実際のコードで矛盾が見つかった場合:
1. 矛盾の内容をユーザーに提示
2. 選択肢:
   a) plan.md を修正してから再開
   b) 実装側を仕様に合わせる
   c) このまま進めて後で対応

---

## Step 4: ビルド確認

plan.md の「ビルド確認」セクションのコマンドを順に実行。エラーがあれば修正 → 再実行。

AskUserQuestion で手動検証の結果を確認する:
- 「問題なし、完了」→ 終了
- 「不具合がある」→ 「`/fix` で根本原因を調査できます」と案内
- 「仕様との整合性を確認したい」→ 「`/check` で plan.md との差分を確認できます」と案内


