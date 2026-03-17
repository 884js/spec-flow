---
name: list
description: "Displays all plans with status information and lets the user select a plan to edit, build, research, or check. Use as a hub for navigating existing plans."
allowed-tools: Bash AskUserQuestion Skill
metadata:
  triggers: list, plans, プラン一覧, 一覧表示, プラン管理
---

# プラン一覧（List）

DB からプラン一覧をステータス付きで取得し、アクション選択のハブとして機能する。

## ワークフロー

```
Step 1: プラン一覧取得 + ステータス表示
Step 2: プラン選択 + アクション選択
```

---

## Step 1: プラン一覧取得 + ステータス表示

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-plans"
```

0件なら「プランが見つかりません。`/spec` で新規作成してください。」と案内して終了。

出力は TSV 形式（feature_name, title, status）。番号付きリストでステータスと共に表示する。

---

## Step 2: プラン選択 + アクション選択

AskUserQuestion でプランを選択させ、続けてアクションを選択させる:
- 仕様を編集する → `Skill(spec, args: "{feature-name}")` で起動
- 実装する → `Skill(build, args: "{feature-name}")` で起動
- 検証する → `Skill(check, args: "{feature-name}")` で起動
