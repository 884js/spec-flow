---
name: list
description: "Displays all plans under docs/plans/ with status information and lets the user select a plan to edit, build, research, or check. Use as a hub for navigating existing plans."
allowed-tools: Read Glob Grep AskUserQuestion
metadata:
  triggers: list, plans, プラン一覧, 一覧表示, プラン管理
---

# プラン一覧（List）

`docs/plans/` 配下のプラン一覧をステータス付きで表示し、アクション選択のハブとして機能する。

入力: なし（または `$ARGUMENTS` で feature-name を直接指定）
出力: 選択されたアクションの実行案内

## ワークフロー

```
Step 1: プラン走査 + ステータス算出
Step 2: プラン選択
Step 3: アクション選択 + 実行案内
```

---

## Step 1: プラン走査 + ステータス算出

### 1-a. プラン一覧取得

```
Glob docs/plans/**/plan.md
```

プランが0件の場合:
「プランが見つかりません。`/spec` で新規作成してください。」と案内して **終了**。

### 1-b. 各プランのメタデータ + ステータス取得（並列実行）

**重要**: 以下の Read / Glob は全プラン分を **1回のツール呼び出しで並列実行** すること。順番に1件ずつ処理しない。

全 plan.md を並列に Read し、frontmatter から `title`、`feature-name`、`updated` を抽出する。
同時に、全プランの progress.md と result.md の存在を並列に Glob で確認する。

```
# 全て並列実行（1回のメッセージで全ツール呼び出しを送信）
Read docs/plans/{feature-name-1}/plan.md
Read docs/plans/{feature-name-2}/plan.md
...
Glob docs/plans/*/progress.md
Glob docs/plans/*/result.md
```

result.md が存在するプランについては、全 result.md を並列に Read し、frontmatter の `judgment` フィールドを抽出する。

### 1-c. ステータス算出

**ステータス判定ルール**（上から順に評価、最初に該当したものを採用）:

| 条件 | ステータス |
|------|-----------|
| result.md が存在し、judgment が `NEEDS_FIX` | `要修正` |
| result.md が存在し、judgment が `PARTIAL` | `部分合格` |
| result.md が存在し、judgment が `PASS`（または judgment フィールドなし※） | `検証済み` |
| progress.md のタスク状態が全て `✓` | `実装完了` |
| progress.md のタスク状態に `→` がある | `実装中` |
| progress.md が存在し、タスク状態が全て `-` | `未着手` |
| plan.md のみ存在（progress.md なし） | `仕様作成済み` |

※ **フォールバック**: judgment フィールドがない既存の result.md は、受入条件テーブルの判定列を確認する。全行が PASS なら `検証済み`、FAIL が1件以上なら `要修正`、それ以外は `部分合格` とする。

progress.md が存在するプランについては、タスク進捗テーブルの「状態」列（`-` / `→` / `✓`）をパースして判定する。
**並列化**: progress.md の Read も全プラン分を1回のツール呼び出しで並列実行すること。

### 1-d. ソート + 一覧表示

プランをステータスの優先度順にソートする:

| 優先度 | ステータス |
|--------|-----------|
| 1（最優先） | `実装中` |
| 2 | `要修正` |
| 3 | `未着手` |
| 4 | `仕様作成済み` |
| 5 | `部分合格` |
| 6 | `実装完了` |
| 7 | `検証済み` |

同じステータス内では plan.md の `updated` が新しい順。

番号付きリストで全プランを表示する:

```
## プラン一覧

1. [実装中] feat: ビルドタスクプレビュー (build-task-preview)
2. [未着手] feat: プラン一覧表示スキル (list-skill)
3. [検証済み] feat: README更新とfix名称変更 (readme-and-fix-rename)
...
```

---

## Step 2: プラン選択

`$ARGUMENTS` で feature-name が指定されている場合はそのプランを自動選択し、Step 3 へ進む。

### ページング方式

プランをソート順に3件ずつページ表示する。AskUserQuestion の選択肢は最大4件（プラン3件 + ナビゲーション）で構成する。

**1ページ目**（プラン1-3件目）:

```
AskUserQuestion:
  question: "どのプランを操作しますか？（1/{総ページ数}ページ）"
  options:
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン1
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン2
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン3
    - {label: "次のページ →", description: "プラン4件目以降を表示"}
```

**2ページ目以降**（プラン4-6件目...）:

```
AskUserQuestion:
  question: "どのプランを操作しますか？（{N}/{総ページ数}ページ）"
  options:
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン4
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン5
    - {label: "{title} ({feature-name})", description: "[{ステータス}]"}  # プラン6
    - {label: "次のページ →", description: "次の3件を表示"}
```

**最終ページ**: 「次のページ →」の代わりに「← 最初に戻る」を表示する。

プランが3件以下の場合はページングなしで全件を AskUserQuestion に表示する。

---

## Step 3: アクション選択 + 実行案内

選択されたプランの feature-name を使って AskUserQuestion でアクションを選択させる:

```
AskUserQuestion:
  question: "{feature-name} に対するアクションを選んでください。"
  options:
    - label: "仕様を編集する (/spec)"
      description: "plan.md を更新モードで開く"
    - label: "実装する (/build)"
      description: "plan.md に沿って実装を開始・再開する"
    - label: "調査する (/research)"
      description: "技術調査を行い research ファイルを生成する"
    - label: "検証する (/check)"
      description: "実装コードと plan.md の突合検証を行う"
```

### 実行案内

選択されたアクションに応じて案内メッセージを表示する:

| アクション | 案内メッセージ |
|-----------|--------------|
| /spec | `次のコマンドを実行してください: /spec {feature-name}` |
| /build | `次のコマンドを実行してください: /build {feature-name}` |
| /research | `次のコマンドを実行してください: /research {feature-name}` |
| /check | `次のコマンドを実行してください: /check {feature-name}` |
