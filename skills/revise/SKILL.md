---
name: revise
description: "Use when modifying or fixing the plan.md spec document. Invoke for spec revision, design changes. Also invoke PROACTIVELY when implementation code has changed and specs may be outdated. 仕様修正, 手戻り, 設計変更, 仕様と実装の乖離."
allowed-tools: Read, Glob, Grep, Edit, Task
metadata:
  triggers: revise spec, update spec, fix spec, 仕様修正, 手戻り, 設計変更, spec outdated, 仕様と実装の乖離
---

# 仕様修正（Revise）

plan.md の特定セクションを **修正** する。
1ファイルに全情報が統合されているため、カスケード追跡は不要 — 同一ファイル内で自然に一貫性を保てる。
修正後に spec-reviewer でセクション間の整合性を事後チェックする。

### いつ revise を使うか

| タイミング | 状況 | 例 |
|-----------|------|-----|
| plan完了後 | 設計レビュー指摘 | エラーコード体系の見直し |
| implement中 | 仕様と実装の矛盾 | DBスキーマが想定と異なる |
| PRレビュー後 | 仕様変更が必要な指摘 | 認証方式の変更 |
| QAテスト後 | 考慮漏れ起因の不具合 | エッジケース未定義 |

入力: `docs/{feature-name}/plan.md`
出力: 修正された plan.md

**パスルール**: `docs/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は日本語のシンプルな名前（パス区切り不可）

## ワークフロー

```
Step 0: plan.md 読み込み + 現状サマリー提示
Step 1: 修正箇所のヒアリング（AI主導）
Step 2: 修正の実施
Step 3: 整合性チェック ← spec-reviewer エージェント
```

---

## Step 0: plan.md 読み込み + 現状サマリー

スキル起動直後に plan.md を読み込む:

```
Glob docs/**/plan.md
```

$ARGUMENTS に feature-name またはセクション名が指定されている場合はそれを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

**project-context.md の鮮度チェック**:
`docs/{feature-name}/project-context.md` の先頭数行を Read し、生成日を確認:
- 生成日から7日以上経過している場合: 「project-context.md が {N}日前の情報です。差分更新を行いますか？」と提案
- 更新する場合: context-collector を差分更新モードで起動

```
Read docs/{feature-name}/plan.md
```

**progress.md の読み込み**（任意）:
`docs/{feature-name}/progress.md` が存在する場合は Read し、タスク進捗情報を取得する。

読み込んだ内容を一覧で提示:

```
{feature-name} の plan.md の現状です:

概要:          {一行サマリー}
受入条件:       {N}件
データフロー:    {一行サマリー}
バックエンド:    {エンドポイント数と概要}
DB:            {テーブル/カラムの概要}
フロントエンド:  {コンポーネント名の列挙}
実装タスク:     {N}タスク（{progress.md がある場合: 完了: {N}, 実施中: {N}, 未着手: {N}。ない場合: 実装未開始}）

どのあたりを見直したいですか？
```

$ARGUMENTS にセクション名がある場合（例: `revise バックエンド`）はそのセクションから対話を開始。

---

## Step 1: 修正箇所のヒアリング（AI主導）

ユーザーの回答に応じて、対象セクションの現在の内容を提示し深掘りする。

**ヒアリングの進め方**:
1. ユーザーが指定した領域の現在の設計内容を具体的に提示
2. 変更の選択肢を例示して方向性を確認
3. 修正内容が確定するまで対話を続ける

例:
```
ユーザー: 「DBのあたり」
AI: 「plan.md のDB変更セクションについて確認します。現在の設計はこうなっています:
     - reminders テーブル: id, memo_id, remind_at, status, created_at
     - memos との 1:1 リレーション

     具体的に変えたい点はどこですか？例えば:
     - カラムの追加/変更/削除
     - テーブル構造の変更
     - リレーションの見直し」
```

---

## Step 2: 修正の実施

Step 1 で合意した修正内容で plan.md を更新する。

**小規模な修正**（セクション内の部分的な変更）の場合:
- 直接 Edit で修正する

**大規模な修正**（セクション全体の書き換え）の場合:
- **spec-writer** に委譲する:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/plan.md を更新。種別: plan
  現在のファイル: docs/{feature-name}/plan.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  修正内容: {Step 1 で確定した修正内容}
  注意: 修正箇所以外の既存内容は維持してください。」
```

**修正時のルール**:
- 変更箇所のみ修正し、無関係な部分は触らない
- **関連セクションの同時修正**: DB変更がAPI型に影響する場合など、同一ファイル内の関連セクションも同時に修正する
- 修正後の内容をユーザーに提示して確認を取る

**関連セクションの修正ガイド**:

| 修正セクション | 同時に確認・修正すべきセクション |
|-------------|--------------------------|
| 受入条件 | テスト方針（手動検証チェックリスト） |
| データフロー | バックエンド変更（エンドポイント） |
| バックエンド変更 | DB変更（型対応）、フロントエンド変更（API呼び出し）、実装タスク |
| DB変更 | バックエンド変更（型対応）、フロントエンド変更（型参照）、実装タスク |
| フロントエンド変更 | 実装タスク |
| 実装タスク | テスト方針 |

**progress.md との同期**:
- plan.md の実装タスク表を変更した場合（タスクの追加/削除/変更）、`docs/{feature-name}/progress.md` が存在すればタスク進捗テーブルも同期更新する
  - タスク追加: progress.md のタスク進捗テーブルに行を追加（状態は `-`）
  - タスク削除: progress.md のタスク進捗テーブルから該当行を削除
  - タスク変更: progress.md のタスク進捗テーブルの該当行を更新（状態は維持）

**変更履歴の記録**:
- 修正完了後、plan.md の「フィードバックログ」テーブルに修正内容を追記する:
  ```
  | {N} | {YYYY-MM-DD} | 修正 | {変更内容の概要} | {対応内容} |
  ```

---

## Step 3: 整合性チェック

修正が完了したら、**spec-reviewer** エージェントで plan.md 内のセクション間整合性を検証。

```
Task(spec-reviewer) を起動:
  プロンプト: 「docs/{feature-name}/plan.md を読み込み、
  セクション間の整合性（データフロー↔API設計↔DB設計↔フロントエンド設計↔実装タスク）、
  型定義の一致、テスト網羅性をレビューしてください。」
```

**結果の処理**:
- **PASS**: 「修正が完了しました。plan.md の整合性が確認されました。」
- **NEEDS_FIX**: 問題点をユーザーに提示し、plan.md を修正 → 必要に応じて再レビュー
