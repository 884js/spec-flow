---
name: spec
description: "Generates or updates plan through requirements hearing, integrated analysis, and design dialogue. Handles both new spec creation and update mode (from check results). Use when starting a new feature or updating an existing spec."
allowed-tools: Read Glob Grep Edit Task Bash
metadata:
  triggers: spec, plan, create spec, new spec, design, requirements, update spec, 仕様書作成, 要件定義, 仕様更新
---

# 仕様作成（Spec）

ユーザーの要求から plan を DB に生成するスキル。

入力: ユーザーの要求（$ARGUMENTS または対話）
出力: DB 上の plan レコード（`scripts/db.sh` 経由）

**feature-name**: 英語の kebab-case

## ワークフロー

```
Step 1: モード判定 + 要件ヒアリング
Step 2: 統合分析（analyzer）
Step 3: plan + progress 生成（writer）
Step 4: plan 完全性検証
Step 5: ブラウザレビュー（Annotation Cycle）
Step 6: 次のアクション提示
```

---

## Step 1: モード判定 + 要件ヒアリング

### モード判定

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-plans"
```

- **$ARGUMENTS の feature-name に該当するプランなし** → 新規モード → ヒアリングへ
- **該当プランあり** → 更新モード: `db.sh get-body` で plan 本文を取得、`db.sh get-result` で result（あれば）を取得し、変更点をヒアリングして Step 3 へ（Step 2 はスキップ）

### ヒアリング（新規モード）

$ARGUMENTS を評価し、**何を作りたいか** が明確なら Step 2 へ。

不明確な場合（空、動詞のみで対象不明、複数解釈可能）は AskUserQuestion で1往復だけ確認する。

受入条件・スコープ外・非機能要件は聞かない。これらは analyzer の結果をもとに writer が推測して生成する。

---

## Step 2: 統合分析（analyzer）

```
Task(subagent_type: analyzer):
  「このプロジェクトの統合分析を行ってください。
  追加機能の概要: {Step 1 で把握した機能概要}」
```

analyzer がプロジェクトコンテキスト・コードパターン・Git履歴を調査し、統合レポートを返す。

---

## Step 3: plan + progress 生成

### 3-a. plan 生成

```
Task(subagent_type: writer):
  「plan を DB に生成してください。
  ドキュメント種別: plan
  feature-name: {feature-name}
  プロジェクト規約: {analyzer の要約}
  設計内容:
    概要: {ユーザーの要求}
    受入条件: {要求と分析結果から推測}
    スコープ: {要求と分析結果から推測}
    データフロー・バックエンド・DB・フロントエンド: {分析結果から推測}
    実装タスク: {依存関係付きタスク一覧}
    テスト方針: {テスト一覧}
  注意:
  - DB 操作は ${CLAUDE_PLUGIN_ROOT}/scripts/db.sh を使用
  - ソースコードは含めない
  - 自己検証でセクション間の整合性を確認すること
  - 仕様に明示されていないが実装時に判断が必要になる条件を確認事項に列挙すること」
```

### 3-b. progress 生成

```
Task(subagent_type: writer):
  「progress を DB に生成してください。
  ドキュメント種別: progress
  feature-name: {feature-name}
  DB スクリプト: ${CLAUDE_PLUGIN_ROOT}/scripts/db.sh
  mode: single」
```

---

## Step 4: plan 完全性検証

plan 生成後、対象ファイルの変更が他ファイルに波及していないかをコードベースを検索して検証する。

1. `db.sh get-body` で生成された plan 本文を取得
2. plan の実装タスク一覧から「対象ファイル」を全て抽出
3. 各対象ファイルのファイル名を Grep でコードベース内検索し、参照元を特定
4. 参照元がタスクの対象ファイルに含まれていなければ **漏れ** として検出
5. 漏れがあれば writer（plan-revision）で plan に追加（タスク・対象ファイル・システム影響の参照更新箇所を更新）
6. 漏れがなければそのまま Step 5 へ

---

## Step 5: Annotation Cycle（ブラウザレビュー）

plan 生成後、ブラウザでのレビューを提案する。

AskUserQuestion:
- 「ブラウザでレビューする」→ 以下のサイクルを開始
- 「スキップして次へ」→ Step 6 へ

### サイクル

1. **サーバー起動**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/annotation-viewer/server.py --feature {feature-name}` を実行。stdout の `PORT:{port}` からポート取得
2. **ブラウザを開く**: `open http://localhost:{port}`
3. **ファイルポーリングで待機**: 3秒間隔で `/tmp/spec-flow-review/{feature-name}/` をチェック:
   - **`comments.json` が出現** → plan 本文を `db.sh get-body` で取得し `.bak` として保存 → コメントを読み込み、writer（plan-revision）で plan 本文を修正 → comments.json を削除 → 待機に戻る
   - **`review-done.flag` が出現** → Step 6 へ

---

## Step 6: 完了 + 次のアクション

AskUserQuestion:
- `/build` を実行 — 実装を開始する
- plan を修正したい — 修正内容をヒアリングして Step 3 を再実行
- 何もしない — 後で手動で進める
