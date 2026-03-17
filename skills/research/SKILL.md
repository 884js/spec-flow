---
name: research
description: "Investigates technical topics through codebase analysis and web research. Outputs research findings to DB with comparisons and recommendations. Use when exploring options, comparing libraries, or investigating architecture decisions."
allowed-tools: Read Glob Grep Edit Bash Task
metadata:
  triggers: research, investigate, 調査, リサーチ, 技術調査, ベストプラクティス, 比較, どうすべきか
---

# 技術調査（Research）

技術トピックを調査し、結果を DB に残すスキル。
コードベース分析が必要な場合は analyzer、Web 調査が必要な場合は researcher に委譲する（メインコンテキストの節約のため）。

入力: ユーザーの調査要求（$ARGUMENTS または対話）
出力: DB 上の research レコード（`scripts/db.sh` 経由）

**feature-name**: 英語の kebab-case

## ワークフロー

```
Step 1: 調査対象の明確化
Step 2: 調査実行（analyzer / researcher に委譲）
Step 3: 結果を DB に保存
Step 4: 次のアクション提示
```

---

## Step 1: 調査対象の明確化

$ARGUMENTS から調査トピックとゴールを把握する。不明確なら AskUserQuestion で1往復確認。

feature-name が指定されていれば `db.sh get-body --feature {feature-name}` で plan 本文を取得してコンテキストにする。

既存リサーチの確認:
```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-research --feature {feature-name}"
```

---

## Step 2: 調査実行

調査内容に応じて analyzer / researcher に委譲する:

- **コードベースの現状把握が必要** → analyzer に委譲
- **外部の技術情報が必要** → researcher に委譲
- **両方必要** → analyzer → その結果を踏まえて researcher

---

## Step 3: research を DB に保存

調査結果を DB に保存する:

```
echo "{research 本文}" | Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh create-research --feature {feature-name} --topic {トピック} --type {codebase|external|combined}"
```

research 本文の構造:
```markdown
# リサーチ: {トピック}

## 調査ゴール
{何を明らかにしたかったか}

## 調査結果
{発見事項、比較がある場合はテーブル形式}

## 推奨・結論
{推奨するアプローチとその根拠}

## 次のステップ
{この調査をもとに何をすべきか}
```

---

## Step 4: 次のアクション提示

AskUserQuestion:
- `/spec` で仕様を作成する
- 追加で別トピックを調査したい → Step 1 に戻る
- 調査完了 → 終了
