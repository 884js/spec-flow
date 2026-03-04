---
name: research
description: "Investigates technical topics through codebase analysis and web research. Outputs research.md with findings, comparisons, and recommendations. Use when exploring options, comparing libraries, or investigating architecture decisions."
allowed-tools: Read Glob Grep Write Task
metadata:
  triggers: research, investigate, 調査, リサーチ, 技術調査, ベストプラクティス, 比較, どうすべきか
---

# 技術調査（Research）

技術トピックを調査し、research.md に結果を出力するスキル。
コードベース分析・Web調査・ライブラリ比較・ベストプラクティス調査に対応。

入力: ユーザーの調査要求（$ARGUMENTS または対話）
出力: `docs/plans/{topic}/research.md`

**パスルール**: `docs/plans/{topic}/` はカレントディレクトリ直下。`{topic}` は英語の kebab-case。パス区切り不可

## ワークフロー

```
Step 0: コンテキスト判定（feature 紐付き / standalone）
Step 1: 調査対象の明確化 + タイプ判定
Step 2: 調査実行（analyzer / researcher に委譲）
Step 3: 結果統合 + research.md 出力
Step 4: 次のアクション提示
```

---

## Step 0: コンテキスト判定

### 0-a. 出力先の決定

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。

```
Glob docs/plans/{feature-name}/plan.md
```

- **feature-name 指定あり** → `docs/plans/{feature-name}/` を出力先とする。plan.md があれば Read してコンテキストにする
- **feature-name 指定なし** → $ARGUMENTS からトピック名を kebab-case で生成。出力先は `docs/plans/{topic}/`

### 0-b. 既存 research.md の確認

```
Glob docs/plans/{topic}/research.md
```

存在する場合、AskUserQuestion で確認:
- 「前回の調査を踏まえて追加調査する」→ 既存 research.md を Read し、追記モード
- 「新規に調査をやり直す」→ 上書きモード

---

## Step 1: 調査対象の明確化 + タイプ判定

### 1-a. ヒアリング

$ARGUMENTS があればそこから、なければ AskUserQuestion で:
- 何を調査したいか
- 何が分かったら完了か（ゴール）

1往復で明確になったら次へ。

### 1-b. タイプ判定

| タイプ | 判定基準 | 使用エージェント |
|-------|---------|--------------|
| **コードベース調査** | 「既存コードがどうなっているか」「この部分の仕組みは」 | analyzer のみ |
| **外部技術調査** | 「ライブラリ比較」「ベストプラクティス」「どう実装するのが良いか」 | researcher のみ |
| **複合調査** | 「既存コードを踏まえて最適な方法を調べたい」 | analyzer → researcher |

判定が曖昧な場合は AskUserQuestion で確認する。

---

## Step 2: 調査実行

### コードベース調査

```
Task(subagent_type: analyzer):
  プロンプト: 「以下のトピックについてプロジェクトの現状を調査してください。
  調査トピック: {トピック}
  調査ゴール: {ゴール}
  {plan.md がある場合: 関連仕様: docs/plans/{feature-name}/plan.md}」
```

### 外部技術調査

```
Task(subagent_type: researcher):
  プロンプト: 「以下のトピックについて技術調査してください。
  調査トピック: {トピック}
  調査ゴール: {ゴール}
  調査観点:
  - 候補の選択肢
  - 各選択肢のメリット・デメリット
  - 推奨とその根拠
  {プロジェクトコンテキストがある場合: 技術スタック概要}」
```

### 複合調査

1. まず analyzer でコードベースの現状を把握
2. analyzer の結果を踏まえて researcher に外部調査を委譲

---

## Step 3: 結果統合 + research.md 出力

エージェントの結果を統合し、`docs/plans/{topic}/research.md` に Write で直接保存する。

追記モードの場合は既存内容の末尾に「## 追加調査（{YYYY-MM-DD}）」セクションとして追記する。

### research.md フォーマット

```markdown
# リサーチ: {トピック一行サマリー}

調査日: {YYYY-MM-DD}
調査タイプ: {コードベース / 外部技術 / 複合}

## 調査ゴール
{何を明らかにしたかったか}

## 現状（コードベース調査がある場合）
{プロジェクトの現在の状態・構造に関する発見}

## 調査結果

### 選択肢の比較（比較がある場合）

| 観点 | {A} | {B} |
|------|-----|-----|

### 発見事項
- {発見}（出典: {URL or ファイルパス}）

## 推奨・結論
{推奨するアプローチとその根拠}

## 次のステップ
{この調査をもとに何をすべきか}
```

**注意**: 該当しないセクションは省略する。

---

## Step 4: 次のアクション提示

AskUserQuestion で選択肢を提示する:
- 「`/spec` で仕様を作成する」→ `/spec {topic}` の実行を案内
- 「追加で調査したい」→ Step 1 に戻る（最大2往復）
- 「調査完了」→ 終了
