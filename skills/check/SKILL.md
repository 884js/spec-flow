---
name: check
description: "Verifies plan-code alignment after implementation. Compares spec against actual code changes and produces a result (PASS / PARTIAL / NEEDS_FIX). Use after build completion."
allowed-tools: Read Glob Grep Write Task Bash
metadata:
  triggers: check, verify, validate, 仕様検証, 実装確認, 受入条件チェック
---

# プラン検証（Check）

実装が仕様通りか突合検証する。

入力: DB 上の plan レコード + コードベース
出力: DB 上の result レコード

**feature-name**: 英語の kebab-case

## ワークフロー

```
Step 0: 読み込み
Step 1: verifier で突合検証
Step 2: 最終判定 + result 生成
Step 3: 次のアクション
```

---

## Step 0: 読み込み

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh get-body --feature {feature-name}"
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-tasks --feature {feature-name}"
```

---

## Step 1: verifier で突合検証

```
Bash: git diff {base-branch} --name-only
```

verifier に仕様・実装・受入条件の突合を一括で依頼する:

```
Task(subagent_type: verifier):
  「仕様と実装の突合検証を行ってください。
  DB スクリプト: ${CLAUDE_PLUGIN_ROOT}/scripts/db.sh
  feature-name: {feature-name}
  実装ファイル: {git diff の変更ファイル一覧}
  検証内容:
  - 各セクション（バックエンド・DB・フロントエンド等）の仕様と実装の突合
  - データフロー図がある場合は処理フローの突合
  - 受入条件の充足確認
  - 仕様で指定されたファイルの作成・変更の確認」
```

---

## Step 2: 最終判定 + result 生成

| 判定 | 基準 |
|------|------|
| **PASS** | Critical 0件 & Warning 0件 |
| **PARTIAL** | Critical 0件、Warning のみ |
| **NEEDS_FIX** | Critical 1件以上 |

```
Task(subagent_type: writer):
  「result を DB に生成してください。
  ドキュメント種別: result
  DB スクリプト: ${CLAUDE_PLUGIN_ROOT}/scripts/db.sh
  feature-name: {feature-name}
  verifier 結果: {Step 1 の結果}
  judgment: {最終判定}」
```

---

## Step 3: 次のアクション

- **PASS**: 「検証完了。PR のマージに進めます。」
- **PARTIAL**: 不一致一覧を提示し、実装修正か仕様修正かを選択させる
- **NEEDS_FIX**: 不一致箇所を列挙し提案:
  - 実装漏れ → `/build` で修正
  - 仕様不足 → `/spec` で仕様更新
