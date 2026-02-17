---
name: implement
description: "Use when starting implementation based on a completed spec. Invoke for feature branch creation, task-by-task coding guided by implementation-plan.md, testing, and PR creation. 実装開始, 開発開始, コーディング."
allowed-tools: Read, Glob, Grep, Write, Edit, Task, Bash
metadata:
  triggers: implement, start coding, 実装開始, 開発開始, コーディング開始, start implementation
---

# 実装（Implement）

仕様書（outline → detail → plan）が完成した後、**implementation-plan.md に沿って実装を進める**。
ブランチ作成 → タスク順の実装 → ビルド確認 → PR 作成 までを一貫してガイドする。

入力: `docs/{feature-name}/` の全ドキュメント（README.md + ドメインdoc + implementation-plan.md）
出力: 実装コード + PR

**パスルール**: `docs/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は日本語のシンプルな名前（パス区切り不可）

仕様の修正が必要な場合は `/feature-spec:revise` で行う。

## ワークフロー

```
Step 0: implementation-plan.md + 関連仕様書の読み込み
Step 1: feature ブランチ作成
Step 2: タスク順の実装（implementation-plan.md のタスク表に沿って）
Step 3: ビルド確認（implementation-plan.md のビルド確認セクションを実行）
Step 4: PR 作成（ユーザー確認後）
```

---

## Step 0: 読み込み + 概要提示

スキル起動直後に、既存のドキュメントを全て読み込む:

```
Glob docs/**/README.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

```
Read docs/{feature-name}/README.md
Read docs/{feature-name}/project-context.md
Read docs/{feature-name}/implementation-plan.md
Read docs/{feature-name}/api-spec.md      （存在する場合）
Read docs/{feature-name}/db-spec.md       （存在する場合）
Read docs/{feature-name}/frontend-spec.md （存在する場合）
```

implementation-plan.md が存在しない場合は「先に `/feature-spec:plan` で実装計画を作成してください」と案内して終了する。

読み込んだ内容の概要をユーザーに提示:

```
実装計画を読み込みました:
- 機能: {feature summary}
- タスク数: {N} タスク
- 見積: S×{n}, M×{n}, L×{n}

タスク一覧:
  #1 {タスク名} (S) ← 依存なし
  #2 {タスク名} (M) ← #1
  ...

feature ブランチを作成して実装に進みますか？
```

---

## Step 1: feature ブランチ作成

docs ディレクトリ名（日本語）と README.md の内容から、適切な英語のブランチ名を提案する。

**ブランチ名の規則**:
- 形式: `feature/{english-name}`
- 例: `docs/リマインダー/` → `feature/reminder`、`docs/キャンペーン通知/` → `feature/campaign-notification`

```
ブランチ名: feature/{english-name}

この名前で作成しますか？（変更する場合は希望のブランチ名を入力してください）
```

**ブランチ作成**:
- ユーザー確認後、`git checkout -b feature/{english-name}` で作成
- 同名ブランチが既に存在する場合: 「既存ブランチに切り替える」or「別名で作成」を AskUserQuestion で選択

---

## Step 2: タスク順の実装

implementation-plan.md の「実装タスク」表を依存関係順に処理する。

**各タスクの進め方**:

```
── タスク #{N}: {タスク名} ({見積}) ──

対象ファイル: {ファイル一覧}
依存: #{依存タスク番号}（実装済み）

{該当する仕様書セクションの内容を提示}
（例: api-spec.md のエンドポイント定義、db-spec.md のスキーマ定義）

実装を進めます。
```

**仕様書の参照ルール**:
- タスク名やファイルパスから該当する仕様書を判定:
  - DB/スキーマ関連 → db-spec.md
  - API/エンドポイント関連 → api-spec.md
  - UI/コンポーネント関連 → frontend-spec.md
  - 型定義 → 複数の仕様書を横断参照
- 対象ファイルが既に存在する場合は Read して既存コードを確認してから実装

**code-researcher の使用**:
- 既存パターンの調査が必要な場合のみ使用（例: 既存コードの命名規則、ディレクトリ構造の確認）

**タスク間の確認**:
- 各タスク完了後: 「タスク #{N} が完了しました。次のタスク #{N+1} に進みますか？」
- ユーザーが修正を求めた場合はその場で対応
- 仕様と実装の乖離に気づいた場合: 「仕様の修正が必要そうです。`/feature-spec:revise` で修正しますか？それともこのまま進めますか？」

**見積サイズに応じた確認粒度**:
- S（小）: 実装後にまとめて確認
- M（中）: 主要な判断ポイントで確認
- L（大）: 実装方針を事前に提示し、細かく確認

---

## Step 3: ビルド確認

implementation-plan.md の「ビルド確認」セクションに記載されたコマンドを順に実行する。

```
ビルド確認を実行します（implementation-plan.md より）:

✓ {コマンド1}  # {説明}
✓ {コマンド2}  # {説明}
✗ {コマンド3}  # {説明} ← エラーがあれば内容を提示
✓ {コマンド4}  # {説明}
```

**エラー時の対応**:
- エラー内容を提示し、該当箇所を修正
- 修正後にそのコマンドを再実行して確認
- 全コマンドが通るまで繰り返す

**手動検証チェックリストの提示**:
- implementation-plan.md の「手動検証チェックリスト」セクションをユーザーに提示:

```
手動検証チェックリスト（implementation-plan.md より）:
- [ ] {チェック項目1}
- [ ] {チェック項目2}
- ...

手動検証が完了したら、PR 作成に進みますか？
```

---

## Step 4: PR 作成

ユーザー確認後、`gh pr create` で PR を作成する。

**PR タイトル**:
```
{feature-name}: {README.md の機能概要から1行サマリー}
```

**PR 本文の生成**:

1. リポジトリの PR テンプレートを探す:
   ```
   Glob .github/pull_request_template.md
   Glob .github/PULL_REQUEST_TEMPLATE/*.md
   ```
2. テンプレートが見つかった場合: テンプレートの構造に従い、implementation-plan.md の情報で各セクションを埋める
3. テンプレートがない場合: implementation-plan.md の概要・影響範囲・テスト方針をもとにシンプルな PR 本文を生成

**PR 作成の流れ**:

1. PR タイトルと本文をユーザーに提示して確認
2. 未コミットの変更があればコミットを提案（ユーザー確認必須 — CLAUDE.md ルール）
3. `git push -u origin feature/{english-name}`
4. `gh pr create --title "..." --body "..."`
5. PR の URL をユーザーに提示

```
PR を作成しました: {PR URL}
```
