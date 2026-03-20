---
name: fix
description: "Investigates root causes of runtime issues by tracing actual execution flows. Prohibits speculative fixes until cause is identified. Operates in feature mode (with plan) or standalone mode (without). Use when encountering bugs, errors, or unexpected behavior."
allowed-tools: Read Glob Grep Write Edit Task Bash WebSearch WebFetch
metadata:
  triggers: fix, troubleshoot, 不具合診断, 原因調査, 不具合修正, 動かない, 期待と違う, エラー, バグ
---

# 不具合調査（Fix）

**原則: 原因が特定されるまでコードを修正しない。**

推測に基づく修正は禁止。実際の実行フローを追い、事実に基づいて原因を特定する。
調査用の一時デバッグログの追加や検証スクリプトの作成は許可（修正ではなく調査手段）。

## ワークフロー

```
Step 0: コンテキスト判定
Step 1: 症状の整理
Step 2: 実行フローのトレース + 原因特定
Step 3: 修正方針の提示
Step 4: 修正実行 + テスト追加
Step 5: 対応記録を DB に保存
```

---

## Step 0: コンテキスト判定

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh list-plans"
```

- **feature モード**: $ARGUMENTS の feature-name に該当するプランがある場合。`db.sh get-body` で仕様を参照しながら調査する
- **standalone モード**: 該当プランなし。コードベースのみで調査する

$ARGUMENTS に feature-name があればそれを使用。なければ一覧から AskUserQuestion で選択させる。候補0件なら standalone で進行。

---

## Step 1: 症状の整理

$ARGUMENTS または AskUserQuestion で以下を把握する:
- 何をしたか（操作手順）
- 何が起きるはずだったか
- 実際に何が起きたか
- エラーメッセージ、ログがあれば

---

## Step 2: 実行フローのトレース + 原因特定

エントリポイントから症状発生箇所まで、コードを実際に追って原因を特定する。

- Grep/Read でコードパスをトレース
- 分岐条件と実際の値を確認
- 必要に応じてテスト実行・一時デバッグログで実際の値を確認
- ライブラリ起因の可能性がある場合は WebSearch で公式ドキュメント・既知の Issue を確認

原因が特定できない場合は追加調査をユーザーと繰り返す。**推測で先に進まない。**

---

## Step 3: 修正方針の提示

原因・修正案・根拠・影響範囲をユーザーに提示する。

AskUserQuestion で承認を得てから Step 4 へ。

---

## Step 4: 修正実行 + テスト追加

1. コードを修正
2. 回帰テストを追加（同じ不具合が再発しないことを検証するテスト）。プロジェクトに既存のテストフレームワークがあればそれを使う
3. テストを実行して PASS を確認

---

## Step 5: 対応記録を DB に保存

調査・修正の記録を DB に保存する:

```
echo "{対応記録}" | Bash "${CLAUDE_PLUGIN_ROOT}/scripts/db.sh create-debug --feature {feature-name}"
```

対応記録の構造:
```markdown
# 不具合対応: {症状の1行要約}

## 症状
{Step 1 で整理した内容}

## 原因
{Step 2 で特定した原因}

## 修正内容
{Step 4 で実施した修正の要約}

## テスト
{追加したテストの概要}

## 影響範囲
{修正が影響するモジュール・機能}
```

standalone モードの場合は `--feature` を省略する。
