---
name: fix
description: "Investigates root causes of runtime issues by tracing actual execution flows. Prohibits speculative fixes until cause is identified. Operates in feature mode (with plan.md) or standalone mode (without). Use when encountering bugs, errors, or unexpected behavior."
allowed-tools: Read Glob Grep Write Edit Task Bash AskUserQuestion
metadata:
  triggers: fix, troubleshoot, 不具合診断, 原因調査, 不具合修正, 動かない, 期待と違う, エラー, バグ
---

# 不具合調査（Debug）

**原則: 原因が特定されるまでコードを修正しない。**

推測に基づく修正は禁止。実際の実行フローを追い、事実に基づいて原因を特定する。
調査用の一時デバッグログの追加や検証スクリプトの作成は許可（修正ではなく調査手段）。

## ワークフロー

```
Step 0: コンテキスト判定（feature / standalone）
Step 1: 症状の整理 + パターン判定
Step 2: 実行フローのトレース
Step 3: 原因箇所の特定
Step 4: 修正方針の提示 + 調査ドキュメント出力
```

---

## Step 0: コンテキスト判定

- **feature モード**: `docs/plans/{feature-name}/plan.md` を参照しながら調査する
- **standalone モード**: plan.md なし。コードベースのみで調査する

### 0-a. モード判定

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリの plan.md を直接使用し、feature モードで進行する。以下の分岐はスキップ。

指定がない場合、候補を検索する:

```
Glob docs/plans/**/plan.md
```

候補数に応じて分岐:

**0 件**: standalone モードで自動進行（AskUserQuestion 不要）。

**1 件**: AskUserQuestion で確認:
- `{feature-name} の plan を使って調査する`
- `plan なしで調査する`

**2-3 件**: AskUserQuestion で選択:
- 各 plan の `{feature-name} の plan を使う`（候補数分）
- `plan なしで調査する`

**4 件以上**: AskUserQuestion で確認:
- `feature 名を入力して指定する`
- `plan なしで調査する`

`feature 名を入力して指定する` が選ばれた場合、続けて AskUserQuestion で feature 名をテキスト入力させる。

### 0-b. state.json の参照（feature モードのみ）

```
Read docs/plans/{feature-name}/state.json
```

phase を把握して症状整理の参考にする。

### 0-c. 過去の調査確認（feature モードのみ）

```
Glob docs/plans/{feature-name}/debug-*.md
```

過去の調査ドキュメントがある場合:
1. 全ドキュメントの原因・修正方針を Read
2. AskUserQuestion で確認:
   - 「前回の修正が効かなかったので再調査したい」
   - 「前回とは別の不具合を調査したい」
3. 再調査の場合は棄却済み仮説も含めて再検討

出力ファイル名: `debug-{YYYY-MM-DD}-{N}.md`（当日の連番）

---

## Step 1: 症状の整理 + パターン判定

### 1-a. ヒアリング

$ARGUMENTS があればそこから、なければ AskUserQuestion で:
- 何をしたか（操作手順）
- 何が起きるはずだったか
- 実際に何が起きたか
- エラーメッセージ、ログがあれば

### 1-b. パターン判定

| パターン | 判定基準 | 調査方針 |
|---------|---------|---------|
| **A vs B 比較** | 「X だと動くが Y だと動かない」 | 両方の実行パスをトレースし分岐点を特定 |
| **期待 vs 実際** | 「X のはずが Y になる」 | 期待される実行パスを追い値が変わる箇所を特定 |
| **エラー・クラッシュ** | エラーメッセージ、例外、無反応 | エラー発生箇所からスタックを遡る |
| **不安定** | 「たまに起きる」 | タイミング依存の条件を洗い出す |
| **リグレッション** | 「前は動いてた」 | git diff と実行パスの交点を調べる |

AskUserQuestion でパターン判定結果を確認する。

---

## Step 2: 実行フローのトレース

### 2-a. コードパスの調査

analyzer エージェントに実行フローのトレースを依頼する:

```
Task(subagent_type: analyzer):
  プロンプト: 「以下の機能の実行フローを、エントリポイントから最終出力まで
  コードを追って完全にトレースしてください。
  機能: {症状に関連する機能}
  報告形式:
  1. イベント/トリガーの起点
  2. 各ステップの処理内容（ファイル:行番号）
  3. 分岐条件とその条件値
  4. 最終的な出力/副作用」
```

### 2-b. パターン別の追加調査

パターンに応じて追加調査を実施する（Step 1-b の表に準拠）。

### 2-c. 環境・設定の確認

コードだけでは説明がつかない場合、環境変数・パッケージバージョン・DB状態を確認する。

### 2-d. 実際の値の確認

推測ではなく、テスト実行・一時デバッグログ・ログ確認で実際の値を確認する。

---

## Step 3: 原因箇所の特定

Step 2 の結果から正確な原因箇所を特定する:

```
■ 原因の特定

実行フロー:
  1. {ステップ} （ファイル:行番号）  ← ✓ ここまで正常
  2. {ステップ} （ファイル:行番号）  ← ★ ここで問題発生
  3. {ステップ} （ファイル:行番号）  ← ✗ 以降が不正

原因: {なぜ問題が起きるかの説明}
根拠: {コード調査 or ログ確認で得られた事実}
```

原因が特定できない場合は追加調査をユーザーと繰り返す。推測で先に進まない。

---

## Step 4: 修正方針の提示 + 調査ドキュメント出力

### 4-a. 修正方針の提示

```
■ 修正方針

原因: {特定した原因}
修正案: {具体的な修正内容}（{ファイル:行番号}）
根拠: {なぜこの修正で直るか}
影響範囲: {他の動作への影響}
```

### 4-b. 調査ドキュメント出力（feature モードのみ）

`docs/plans/{feature-name}/debug-{YYYY-MM-DD}-{N}.md` に Write で保存:

```markdown
# 不具合調査: {症状の一行サマリー}

調査日: {YYYY-MM-DD}

## 関連する過去の調査
{過去の調査がある場合はリンクと要約}

## 症状
パターン: {判定されたパターン}
{症状の詳細}

## 原因
{原因と実行フロー}

## 修正方針
### コード修正
- {修正内容}（{ファイル:行番号}）

### plan.md の修正（該当する場合）
- {仕様の修正箇所}

### デバッグログの除去
- {追加したデバッグログのリスト}
```

state.json の debug.references に調査レポートパスを追加する。phase は変更しない。

### 4-c. standalone モードの場合

ドキュメント保存はしない。修正方針の提示で調査完了。
