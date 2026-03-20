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
Step 4: ブラウザレビュー（Annotation Cycle）
Step 5: plan 完全性検証
Step 6: 次のアクション提示
```

---

## Step 1: モード判定 + 要件ヒアリング

### モード判定

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-plans"
```

- **$ARGUMENTS の feature-name に該当するプランなし** → 新規モード → ヒアリングへ
- **該当プランあり** → 更新モード: `db.sh get-body` で plan 本文を取得、`db.sh get-result` で result（あれば）を取得し、変更点をヒアリングして Step 3 へ（Step 2 はスキップ）。plan 更新後、タスク構成が変わっていれば Step 3-b で progress も再生成する

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

## Step 4: Annotation Cycle（ブラウザレビュー）

plan 生成後、ブラウザでのレビューを提案する。

AskUserQuestion:
- 「ブラウザでレビューする」→ 以下のサイクルを開始
- 「スキップして次へ」→ Step 5 へ

### サイクル

1. **初回起動**: `Bash "${CLAUDE_PLUGIN_ROOT}/scripts/annotation-cycle.sh --feature {feature-name}"`
2. **結果に応じて分岐**:
   - **`COMMENTS_SAVED`** → `db.sh get-comments --feature {feature-name}` でコメント取得 → plan 本文を `db.sh get-body` で取得し `.bak` として保存 → writer（plan-revision）で plan 本文を修正 → `db.sh clear-comments --feature {feature-name}` でクリア → `Bash "${CLAUDE_PLUGIN_ROOT}/scripts/annotation-cycle.sh --feature {feature-name} --wait-only"` で再待機
   - **`REVIEW_DONE`** → Step 5 へ

---

## Step 5: plan 完全性検証

`db.sh get-body` で plan 本文を取得し、以下の3つの Agent を**並列**で起動する。各 Agent には plan 本文全体を渡す。

```
Agent("実装者視点で plan を検証。タスクを上から順に実装するシミュレーションを行い、plan だけでは完遂できない箇所を検出せよ。コードベースを実際に読んで確認すること。\n\n{plan本文}")

Agent("テスター視点で plan を検証。各受入条件がテスト可能か、境界条件・エラーパスが定義されているか検証せよ。コードベースを実際に読んで確認すること。\n\n{plan本文}")

Agent("失敗条件の逆算で plan を検証。各タスクが失敗するとしたら何が原因かを列挙し、plan で未対処のものを検出せよ。コードベースを実際に読んで確認すること。\n\n{plan本文}")
```

3つの結果を集約する。
修正事項があれば、ユーザーに検証サマリを提示して**確認後**にwriter（plan-revision）で修正する。

修正完了後、Step 6 へ進む。

検証サマリのフォーマット:
```
## 完全性検証サマリ

| 視点 | 検出事項 | plan 修正内容 |
|------|----------|--------------|
| 実装者 | なし / {検出内容} | - / {修正内容} |
| テスター | なし / {検出内容} | - / {修正内容} |
| 失敗条件 | なし / {検出内容} | - / {修正内容} |
```

---

## Step 6: 完了 + 次のアクション

AskUserQuestion:
- `/build` を実行 — 実装を開始する
- plan を修正したい — 修正内容をヒアリングして Step 3 を再実行
- 何もしない — 後で手動で進める
