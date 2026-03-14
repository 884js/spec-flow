---
name: spec
description: "Generates or updates plan.md through requirements hearing, integrated analysis, and design dialogue. Handles both new spec creation and update mode (from check results). Includes PR split planning for large features. Use when starting a new feature or updating an existing spec."
allowed-tools: Read Glob Grep Edit Task Bash
metadata:
  triggers: spec, plan, create spec, new spec, design, requirements, update spec, 仕様書作成, 要件定義, 仕様更新
---

# 仕様作成（Spec）

ユーザーの要求から plan.md を生成するスキル。既存の plan.md がある場合は更新モードに切り替える。
plan.md 生成後、progress.md も同時生成する（規模に応じて single / multi-pr モード）。

入力: ユーザーの要求（$ARGUMENTS または対話）
出力: `docs/plans/{feature-name}/plan.md` + `progress.md`

**パスルール**: `docs/plans/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は英語の kebab-case。パス区切り不可

## ワークフロー

```
Step 0: モード判定（新規 / 更新）
Step 1: リクエスト分類 + 要件ヒアリング
Step 2: 統合分析（analyzer）
Step 3: plan.md 生成 + 自己検証（writer）+ ブラウザレビュー
Step 4: 次のアクション提示
```

---

## Step 0: モード判定

```
Glob docs/plans/**/plan.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。

- **plan.md が存在しない** → **新規モード**: Step 0-c → Step 1 へ
- **plan.md が存在する** → **更新モード**: Step 0-b へ

### 0-b. 更新モードの初期化

```
Read docs/plans/{feature-name}/plan.md
```

check 結果（result.md）があれば読み込む:
```
Glob docs/plans/{feature-name}/result.md
```

result.md が存在する場合、NEEDS_FIX の不一致箇所を抽出してユーザーに提示する。
ユーザーに変更点をヒアリングした上で Step 3 へ（統合分析はスキップ）。
更新モードでは analyzer の追加検討事項がないため、そのまま plan.md を修正する。

### 0-c. research ファイルの検出（新規モードのみ）

```
Glob docs/plans/{feature-name}/research*.md
```

research ファイルが1件以上存在する場合、すべて Read して調査結果をコンテキストとして保持する。
ユーザーに通知: 「{feature-name} のリサーチ結果が {N} 件見つかりました。これらの調査を踏まえて仕様を作成します。」

※ research ファイルは「参考情報」として扱い、仕様を拘束しない。

---

## Step 1: 要件ヒアリング

### 1-0. リクエスト分類

$ARGUMENTS の内容から、リクエストの種別を判定する:

- **機能追加/変更**（「〜を追加」「〜を実装」「〜を変更」等）→ 1-a へ進む
- **リサーチ/質問**（「どうすべきか」「ベストプラクティス」「〜ってどうやるの？」等）→ 「技術調査には `/research` を使ってください。調査結果をもとに `/spec` で仕様を作成できます。」と案内して **終了**
- **バグ修正**（「〜が動かない」「エラーが出る」「〜を修正」等）→ 「バグ修正には `/fix` で原因を特定してください。」と案内して **終了**

判定が曖昧な場合は AskUserQuestion で確認する:
- 「機能として実装したいですか？それともリサーチですか？」

### 1-a. 初期ヒアリング

$ARGUMENTS の内容を評価し、以下のいずれかに該当する場合は **不明確** と判定する:

1. $ARGUMENTS が空、または feature-name のみ
2. 対象が特定できない（「改善したい」「もっと良くしたい」等、動詞のみで対象が不明）
3. 複数の解釈が可能（「認証を直す」→ ログイン画面？トークン管理？権限制御？）

- **不明確に該当しない** → ヒアリングをスキップし、Step 1-a2 へ
- **不明確に該当する** → AskUserQuestion で「何を作りたいですか？」のみ1往復で確認し、Step 1-a2 へ

受入条件・スコープ外・非機能要件は聞かない。これらは writer が analyzer の結果と要求から推測して生成し、Annotation Cycle でユーザーがレビューする。

### 1-a2. 入力ファイルの検出

ユーザーの入力にファイル（画像、ドキュメント等）が含まれている場合:
- ファイルパスを記録する
- 画像の場合: レイアウト構成・主要コンポーネント等をテキスト要約する
- ドキュメント（PDF・仕様書等）の場合: Read で全文を読み込み、内容を把握する。ドキュメントの情報は以降のステップ（ヒアリング、方向性確認、writer への引き渡し）全体で使用する

---

## Step 2: 統合分析（analyzer）

analyzer エージェントにプロジェクトの統合分析を依頼する:

```
Task(subagent_type: analyzer):
  プロンプト: 「このプロジェクトの統合分析を行ってください。
  CLAUDE.md、ディレクトリ構造、依存関係、型定義、DBスキーマ、既存仕様書、
  コードパターン（API、DB、コンポーネント、データフロー）、Git履歴を調査し、
  1つの統合レポートで返してください。
  追加機能の概要: {Step 1 で把握した機能概要}
  {research ファイルがある場合: リサーチ結果: {各 research ファイルの要約}}
  また、分析の中で以下の2種類を分けて収集してください:
  - 確認事項（仕様内の不確かさ）: 機能概要・要件ヒアリング結果の中にある推測・仮定。以下の4観点を必ず検討すること:
    1. エッジケース（境界値、0件、上限、同時操作）
    2. 非機能要件（パフォーマンス、認証・認可、データ保護）
    3. 暗黙の前提（既存API・型定義・DBスキーマへの影響）
    4. 技術的制約（フレームワーク制約、外部API制限）
  - 追加検討事項（仕様外の影響観点）: 仕様が触れていないが、コードベース分析の結果として影響しそうな観点。確認事項とは起点が異なる（仕様内 vs コードベース）
  各項目には根拠（コードのファイルパスまたは仕様の出典）を必ず付与すること」
```

### 並行開発チェック + 関連プラン検出

```
Glob docs/plans/**/plan.md
```

他の仕様書が存在する場合:

1. **並行開発チェック（既存）**: 変更対象ファイルの重複を確認し、重複があればユーザーに報告する

2. **関連プラン検出（新規）**: 各プランの frontmatter（title, feature-name）と変更対象ファイル・対象セクションを抽出し、以下の基準で関連候補を検出する:
  - 変更対象ファイルの重複（同一ファイルを変更するプラン）
  - 同一ディレクトリ配下のファイルを対象としている（同一コンポーネント領域）
  - タイトルやスコープのキーワード類似（同一機能領域）

  関連候補が1件以上ある場合、全て `relatedPlans` として保持し、Step 3 で writer に渡す
  関連候補が0件の場合はスキップする。

### 規模判定

analyzer の結果から規模を判定する:
- **小**: タスク3未満
- **中**: タスク3-7
- **大**: タスク8以上

大規模の場合は分割案を提示する:
```
この機能は規模が大きいため、分割を提案します:
Phase 1: {機能名A}
Phase 2: {機能名B}
分割して進めますか？
```

---

## Step 3: plan.md 生成 + 自己検証 + ブラウザレビュー

### 3-a. plan.md 生成

writer エージェントに生成を委譲する:

```
Task(subagent_type: writer):
  プロンプト: 「docs/plans/{feature-name}/plan.md を生成してください。
  **重要**: 生成後、必ず自己検証を行い、内容の整合性を確認すること
  ドキュメント種別: plan
  プロジェクト規約: {analyzer の要約}
  コーディング規約: {analyzer のコーディング規約セクション}
  設計内容:
    概要: {ユーザーの要求}
    ユーザーストーリー: {要求から推測したUS一覧（なければ省略）}
    受入条件: {要求と分析結果から推測した受入条件}
    スコープ: {要求と分析結果から推測したスコープ}
    データフロー: {分析結果から推測したシーケンス図}
    バックエンド: {分析結果から推測したAPI設計}
    DB: {分析結果から推測したDB設計}
    フロントエンド: {分析結果から推測したフロントエンド設計}
    設計判断: {記録した設計判断}
    影響範囲: {把握した影響}
    実装タスク: {依存関係付きタスク一覧}
    テスト方針: {テスト一覧・チェックリスト・ビルドコマンド}
    参考資料: {資料名とURL/パスの一覧（なければ省略）}
    関連プラン: {Step 2 で選択された relatedPlans のリスト（feature-name, title, 関連理由）。なければ省略}
    確認事項: {analyzer が検出した確認事項のリスト（項目, 根拠, ステータス）。なければ省略}
    追加検討事項: {analyzer が検出した追加検討事項のリスト（観点, 詳細, 根拠）。なければ省略}
  入力ファイル: {Step 1-a2 で記録したファイルパスのリスト（なければ省略）}
  注意:
  - frontmatter は title, feature-name, status(done), created, updated の5項目を全て含めること
  - ソースコードは含めない（APIパス・カラム名・型は表や箇条書きで記述する）
  - 自己検証でセクション間の整合性を確認すること
  - 入力ファイルがある場合は Read で読み込み、仕様に反映すること。画像はワイヤーフレームの参考にすること」
```

### 3-b. progress.md 生成

plan.md 生成後、progress.md も同時生成する。mode は規模に応じて設定する:
- 小〜中: `mode: single`
- 大: `mode: multi-pr`

```
Task(subagent_type: writer):
  プロンプト: 「progress.md を生成してください。
  ドキュメント種別: progress
  feature-name: {feature-name}
  plan.md: docs/plans/{feature-name}/plan.md
  mode: {single | multi-pr}
  PR グルーピング: {大規模の場合、Step 1 で決定した PR 分割}
  repositories: {analyzer レポートの「プロジェクト概要」「技術スタック」から抽出}
  docs: {analyzer レポートの「調査ソース > ドキュメント」から抽出}」
```

### 3-c. Annotation Cycle（ブラウザレビュー）

plan.md + progress.md 生成後、ブラウザでの詳細レビューを提案する。

AskUserQuestion で選択肢を提示する:
- 「ブラウザでレビューする」→ 以下のサイクルを開始
- 「スキップして次へ」→ Step 4 へ

**サイクル（イベントベースループ）**:

1. サーバーの起動（ロックファイルチェック付き）:
```
Bash: cat /tmp/annotation-viewer.lock 2>/dev/null
```

- ロックファイルが存在し、そのポートでサーバーが応答する場合 → サーバー起動をスキップ、ポート番号を記録
- それ以外 → サーバーを新規起動:
```
Bash(run_in_background): python3 ${CLAUDE_PLUGIN_ROOT}/scripts/annotation-viewer/server.py docs/plans/{feature-name}
```
stdout から `PORT:{port}` を取得する。

- サーバーが既に起動中だった場合はプラン登録のみ行う（server.py が自動的に `EVENT:registered:{feature-name}` を出力して終了する）

2. ブラウザを開く:
```
Bash: open http://localhost:{port}
```

3. イベントループ: `TaskOutput(block=true)` でサーバーの stdout イベントを待つ。

イベントの種類に応じて処理を分岐:

- **`EVENT:comments_saved:{feature-name}`** → コメントが保存された:
  1. comments.json を読み込む:
  ```
  Read docs/plans/{feature-name}/comments.json
  ```
  2. 修正前の plan.md をバックアップ:
  ```
  Bash: cp docs/plans/{feature-name}/plan.md docs/plans/{feature-name}/plan.md.bak
  ```
  3. writer に修正を委譲:
  ```
  Task(subagent_type: writer):
    プロンプト: 「plan.md をコメントに基づいて修正してください。
    ドキュメント種別: plan-revision
    plan.md: docs/plans/{feature-name}/plan.md
    progress.md: docs/plans/{feature-name}/progress.md
    comments.json: docs/plans/{feature-name}/comments.json
    注意: plan.md の実装タスクを変更した場合（追加・削除・変更）は、progress.md のタスク進捗テーブルも同期すること。新規タスクは状態 `-` で追加する。」
  ```
  4. comments.json を削除:
  ```
  Bash: rm -f docs/plans/{feature-name}/comments.json
  ```
  5. 修正サマリをユーザーに通知。ブラウザは自動的にポーリングで差分ハイライト付きリロードされる。
  6. イベントループに戻る（ステップ3）。

- **`EVENT:review_done:{feature-name}`** → レビュー完了:
  1. 一時ファイルをクリーンアップ:
  ```
  Bash: rm -f docs/plans/{feature-name}/comments.json docs/plans/{feature-name}/plan.md.bak
  ```
  2. Step 4 へ進む。

---

## Step 4: 完了 + 次のアクション

### 次のアクション提示

AskUserQuestion で次のアクションを選択させる:
- `/build` を実行 — 実装を開始する
- plan.md を修正したい — 修正内容をヒアリングして Step 3 を再実行する
- 何もしない — 後で手動で進める
