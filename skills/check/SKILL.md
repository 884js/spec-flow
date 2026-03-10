---
name: check
description: "Verifies implementation code matches plan.md specifications. Performs acceptance criteria checks, file structure comparison, and domain-level spec matching. Reports PASS / PARTIAL / NEEDS_FIX. On NEEDS_FIX, guides user back to spec update. Use after /build completion or before PR merge."
allowed-tools: Read Glob Grep Write Task
metadata:
  triggers: check, verify, validate, 仕様検証, 実装確認, 受入条件チェック
---

# 仕様検証（Check）

plan.md と実装コードの突合検証を行い、PASS / PARTIAL / NEEDS_FIX の3段階で判定する。
NEEDS_FIX の場合は spec での仕様更新または build での修正を提案し、ループを成立させる。

入力: `docs/plans/{feature-name}/plan.md` + 実装コード
出力: 検証レポート + `result.md`

**パスルール**: `docs/plans/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は英語の kebab-case。パス区切り不可

## 重要度レベル

| レベル | 基準 |
|--------|------|
| **Critical** | 仕様の主要機能が未実装、または根本的に異なる |
| **Warning** | 仕様との部分的な不一致。動作はするが仕様通りではない |
| **Info** | 軽微な差異。仕様の意図は満たしているが記述と異なる |

## ワークフロー

```
Step 0: plan.md + 変更範囲の特定 + スコーピング
Step 1: 仕様と実装の直接突合（verifier — セクション突合 + フロー検証）
Step 2: ファイル構成の突合
Step 3: 受入条件の検証
Step 4: result.md 生成 + 検証レポート + 次のアクション
```

---

## Step 0: plan.md + 変更範囲の特定

```
Glob docs/plans/**/plan.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。

```
Read docs/plans/{feature-name}/plan.md
```

### 0-a. progress.md によるスコーピング

```
Read docs/plans/{feature-name}/progress.md
```

- **全タスク `✓`** → **フル検証**
- **一部タスク `✓`** → **部分検証**: 完了タスクの対象ファイルのみ
- **全タスク `-`** → 「実装が開始されていません」と案内して終了

### 0-b. 実装差分の取得

```
Bash: git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
Bash: git diff {base-branch} --name-only
```

### 0-c. debug ドキュメントの読み込み

```
Glob docs/plans/{feature-name}/debug-*.md
```

存在する場合は各ファイルの原因・修正方針を読み込み、debug コンテキストとして保持する。

### 0-d. 検証範囲の提示

```
plan.md と実装差分を読み込みました:
- 機能: {feature summary}
- 検証モード: {フル検証 / 部分検証}
- 検証対象セクション: {バックエンド / DB / フロントエンド}
- 変更ファイル: {N}ファイル
- debug: {N}件（{あり / なし}）

検証を開始します。
```

---

## Step 1: 仕様と実装の直接突合

verifier エージェントに突合を依頼する。

### 適応的実行

- **小規模**（変更ファイル5個以下）: 単一の verifier で一括検証
- **中〜大規模**（変更ファイル6個以上）: ドメイン別に並列実行

```
Task(subagent_type: verifier):
  プロンプト: 「仕様と実装の突合検証を行ってください。
  チェック観点: {ドメイン}
  仕様書: docs/plans/{feature-name}/plan.md の「{セクション}」
  実装ファイル: {対象ファイル一覧}
  注意: 仕様書は機能仕様書。機能・振る舞いの観点で検証してください。データフロー図がある場合は処理フローの突合も行ってください。
  {debug コンテキストがある場合}
  debug コンテキスト: {原因と修正方針の要約}」
```

---

## Step 2: ファイル構成の突合

plan.md の各セクションのファイル情報と git diff の変更ファイル一覧を突合する。

- 仕様で「新規」とされたファイルが作成されているか
- 仕様で「変更」とされたファイルが変更されているか
- 仕様外のファイルが変更されていないか

---

## Step 3: 受入条件の検証

plan.md の受入条件を1つずつ検証:
- テストコードまたは実装コードを Grep/Read で確認
- 実装もテストもなし → Critical
- 実装はあるがテストなし → Warning
- 両方あり → PASS

---

## Step 4: result.md 生成 + 検証レポート

### 4-a. result.md の生成

writer エージェントに生成を依頼する:

```
Task(subagent_type: writer):
  プロンプト: 「result.md を生成してください。
  ドキュメント種別: result
  plan.md: docs/plans/{feature-name}/plan.md
  verifier 結果: {Step 1 の結果}
  受入条件検証: {Step 3 の結果}
  出力先: docs/plans/{feature-name}/result.md」
```

### 4-b. 最終判定

| 判定 | 基準 |
|------|------|
| **PASS** | Critical 0件 & Warning 0件 |
| **PARTIAL** | Critical 0件、Warning のみ |
| **NEEDS_FIX** | Critical 1件以上 |

### 4-c. 次のアクション

- **PASS（Info 0件）**: 「検証完了。PR のマージに進めます。」
- **PASS（Info 1件以上）**: 不一致一覧を提示し、AskUserQuestion で確認:
  - 「plan.md を実装に合わせて更新する」→ `/spec` の更新モードを案内
  - 「そのままマージに進む」
- **PARTIAL**: 修正項目を提示。実装修正 or 仕様修正を選択
- **NEEDS_FIX**: 不一致箇所を具体的に列挙し、以下を提案:
  - 実装漏れ → 「`/build` で修正してください」
  - 仕様不足 → 「`/spec` で仕様を更新してください」（ループ成立）
  - 型不一致/ロジック差異 → 「どちらに合わせるか確認してください」
