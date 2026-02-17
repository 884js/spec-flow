---
name: revise
description: "Use when modifying or fixing existing spec documents in docs/. Invoke for spec revision, cascade updates, design changes. Also invoke PROACTIVELY when implementation code has changed and specs may be outdated. 仕様修正, 手戻り, 設計変更, 仕様と実装の乖離."
allowed-tools: Read, Glob, Grep, Edit, Task
metadata:
  triggers: revise spec, update spec, fix spec, 仕様修正, 手戻り, 設計変更, cascade update, spec outdated, 仕様と実装の乖離
---

# 仕様修正（Revise）

既存の仕様書ドキュメントを **修正** し、変更の **カスケード影響** を管理する。

入力: `docs/{feature-name}/` の既存ドキュメント（README.md + ドメインdoc）
出力: 修正されたドキュメント + カスケード更新されたドキュメント

**パスルール**: `docs/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は日本語のシンプルな名前（パス区切り不可）

## ワークフロー

```
Step 0: 全ドキュメント読み込み + 現状サマリー提示
Step 1: 修正箇所のヒアリング（AI主導）
Step 2: 修正の実施 ← spec-writer（大幅な書き換えの場合）
Step 3: カスケード影響の判定 + 更新
Step 4: 整合性チェック         ← spec-reviewer エージェント
```

---

## Step 0: 全ドキュメント読み込み + 現状サマリー

スキル起動直後に全ドキュメントを読み込む:

```
Glob docs/**/README.md
```

$ARGUMENTS に feature-name またはドキュメント名が指定されている場合はそれを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

```
Read docs/{feature-name}/README.md
Read docs/{feature-name}/api-spec.md              （存在する場合）
Read docs/{feature-name}/db-spec.md               （存在する場合）
Read docs/{feature-name}/frontend-spec.md         （存在する場合）
Read docs/{feature-name}/implementation-plan.md     （存在する場合）
```

読み込んだ内容を一覧で提示:

```
{feature-name} の仕様書の現状です:

README.md:
  要件:        {一行サマリー}
  データフロー:  {一行サマリー}

api-spec.md:     {エンドポイント数と概要}
db-spec.md:      {テーブル/カラムの概要}
frontend-spec.md: {コンポーネント名の列挙}

implementation-plan.md:（plan済みの場合）
  実装タスク:   {N}タスク
  影響範囲:     {影響を受ける主要機能}

どのあたりを見直したいですか？
```

$ARGUMENTS にドキュメント名がある場合（例: `revise api-spec`）はそのドキュメントから対話を開始。

---

## Step 1: 修正箇所のヒアリング（AI主導）

ユーザーの回答に応じて、対象ドキュメントの現在の内容を提示し深掘りする。

**ヒアリングの進め方**:
1. ユーザーが指定した領域の現在の設計内容を具体的に提示
2. 変更の選択肢を例示して方向性を確認
3. 修正内容が確定するまで対話を続ける

例:
```
ユーザー: 「DBのあたり」
AI: 「db-spec.md について確認します。現在の設計はこうなっています:
     - reminders テーブル: id, memo_id, remind_at, status, created_at
     - memos との 1:1 リレーション

     具体的に変えたい点はどこですか？例えば:
     - カラムの追加/変更/削除
     - テーブル構造の変更
     - リレーションの見直し」
```

**複数ドキュメントにまたがる修正の場合**:
- まず起点となるドキュメントの修正内容を確定
- カスケード影響は Step 3 で扱う（ここでは起点のみに集中）

---

## Step 2: 修正の実施

Step 1 で合意した修正内容で対象ドキュメントを更新する。

**小規模な修正**（セクション単位の変更）の場合:
- 直接 Edit で修正する

**大規模な修正**（ドキュメント全体の書き換え）の場合:
- **spec-writer** に委譲する:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/{対象ドキュメント} を更新してください。
  ドキュメント種別: {種別}
  フォーマット定義: skills/outline/references/formats/{種別}.md を Read して参照
  出力例: skills/outline/references/examples/{種別}.md を Read して参照
  現在のファイル: docs/{feature-name}/{対象ドキュメント} を Read して参照
  プロジェクト規約: {project-context.md の要約}
  修正内容: {Step 1 で確定した修正内容}
  注意: 修正箇所以外の既存内容は維持してください。
  生成完了後、変更箇所の概要を5行以内で返してください。」
```

**修正時のルール**:
- 変更箇所のみ修正し、無関係な部分は触らない
- 修正後の内容をユーザーに提示して確認を取る

---

## Step 3: カスケード影響の判定 + 更新

修正内容をもとに、[references/cascade-map.md](references/cascade-map.md) から影響を受けるドキュメントを判定して提示:

```
{ドキュメント名} を修正しました。以下のドキュメントに影響がある可能性があります:

- [要確認] {ドキュメント}: {影響の概要}
- [要確認] {ドキュメント}: {影響の概要}
- [要更新] README.md: {影響の概要}

どこまで更新しますか？（「全部」「api-specだけ」「READMEは後で」等）
```

**影響の分類**:
- **[要確認]**: 内容の整合性を確認し、必要なら修正（型定義の対応など）
- **[要更新]**: ほぼ確実に更新が必要（README.md の実装タスク・影響範囲等）

**更新の進め方**:
選択されたドキュメントを順次処理。各ドキュメントで:
1. 現在の内容と、修正による影響箇所を提示
2. 更新案を提示 → ユーザー確認 → Edit

implementation-plan.md（plan済みの場合）の更新:
- 実装タスク: タスクの追加/削除/依存関係を更新
- 影響範囲: 影響範囲の再評価
- テスト方針: テスト項目の追加/変更を更新

---

## Step 4: 整合性チェック

全ドキュメントの更新が完了したら、**spec-reviewer** エージェントで整合性を検証。

```
Task(spec-reviewer) を起動:
  プロンプト: 「docs/{feature-name}/ 内の全ドキュメント（README.md, api-spec.md,
  db-spec.md, frontend-spec.md, implementation-plan.md）を読み込み、
  ドキュメント間の整合性、型定義の一致、テスト網羅性をレビューしてください。」
```

**結果の処理**:
- **PASS**: 「修正が完了しました。全ドキュメントの整合性が確認されました。」
- **NEEDS_FIX**: 問題点をユーザーに提示し、該当ドキュメントを修正 → 必要に応じて再レビュー
