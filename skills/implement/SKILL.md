---
name: implement
description: "Use when starting implementation based on a completed plan. Invoke for feature branch creation, task-by-task coding guided by plan.md, testing, and PR creation. Supports pause/resume via progress.md state tracking. 実装開始, 開発開始, コーディング."
allowed-tools: Read, Glob, Grep, Write, Edit, Task, Bash
metadata:
  triggers: implement, start coding, 実装開始, 開発開始, コーディング開始, start implementation
---

# 実装（Implement）

plan.md が完成した後、**plan.md に沿って実装を進める**。
ブランチ作成 → タスク順の実装 → ビルド確認 → PR 作成 までを一貫してガイドする。
**progress.md によるタスク状態管理で中断・再開** をサポートする。

入力: `docs/plans/{feature-name}/plan.md`（設計仕様。読み取り専用）
状態管理: `docs/plans/{feature-name}/progress.md`（実行状態の単一ソース）
出力: 実装コード + PR

**パスルール**: `docs/plans/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は英語の kebab-case（例: `campaign-notification`）。パス区切り不可

## タスク状態管理

progress.md の実装タスク進捗テーブルの **状態列** でタスクの進捗を管理する:

| 記号 | 意味 |
|------|------|
| `-` | 未着手 |
| `→` | 実施中 |
| `✓` | 完了 |

**重要**: plan.md は設計仕様として **読み取り専用**。全ての状態更新は progress.md に対して行う。

## ワークフロー

```
Step 0: plan.md + progress.md 読み込み + 再開検知
Step 1: feature ブランチ作成（新規開始時のみ）
Step 2: タスク順の実装（plan.md のタスク表に沿って）
Step 3: ビルド確認（plan.md のビルド確認セクションを実行）
Step 4: PR 作成（ユーザー確認後）
```

---

## Step 0: 読み込み + 再開検知 + モード判定

スキル起動直後に、既存のドキュメントを読み込む:

```
Glob docs/plans/**/plan.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

**project-context.md の鮮度チェック**:
`docs/plans/{feature-name}/project-context.md` の先頭数行を Read し、生成日を確認:
- 生成日から7日以上経過している場合: 「project-context.md が {N}日前の情報です。差分更新を行いますか？」と提案
- 更新する場合: context-collector を差分更新モードで起動

### 0-a. plan.md の読み込み（設計仕様として）

```
Read docs/plans/{feature-name}/plan.md
```

plan.md が存在しない場合は「先に `/feature-spec:plan` で設計・実装計画を作成してください」と案内して終了する。

### 0-b. progress.md の読み込み / 自動生成

```
Read docs/plans/{feature-name}/progress.md
```

- **progress.md が存在** → Read して状態を復元（通常はこちら。strategy が作成済み）
- **progress.md が存在しない**（strategy を経由せず直接 implement を実行した場合）→ 自動生成:
  - plan.md のタスク表をコピーし、状態列を追加（全て `-`）
  - mode: single（デリバリープランなし）
  - 「現在の状況」「次にやること」を初期テキストで記述

**自動生成テンプレート（single モード）**:

```markdown
---
plan: "./plan.md"
feature: "{機能名}"
started: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
mode: single
---

# {機能名} — 実装進捗

## 現在の状況

1 PR で実装する。タスク #1 から実装を開始する。

## 次にやること

`/feature-spec:implement` でタスク #1 から実装を開始する。

## タスク進捗

| # | タスク | 対象ファイル | 見積 | 状態 |
|---|-------|------------|------|------|
{plan.md のタスク表をコピー、状態列は全て `-`}

> タスク定義の詳細は [plan.md](./plan.md) を参照

## ブランチ・PR

| ブランチ | PR URL | 状態 |
|---------|--------|------|
| - | - | - |

## 作業ログ

| 日時 | 内容 |
|------|------|
| {YYYY-MM-DD} | 1 PR で実装開始 |
```

### 0-c. troubleshoot ドキュメントの確認（plan.md 自動更新）

`docs/plans/{feature-name}/troubleshoot-*.md` の存在をチェックする:

```
Glob docs/plans/{feature-name}/troubleshoot-*.md
```

ファイルが存在する場合、各ドキュメントの「plan.md の修正」セクションを確認する。
未対応の修正内容（「反映済み」マークがないもの）があれば:

1. 修正内容をユーザーに提示して確認:

   ```
   troubleshoot ドキュメントに plan.md の修正提案があります:

   ■ troubleshoot-{YYYY-MM-DD}.md:
   {修正内容の要約}

   この修正を plan.md に反映しますか？
   ```

2. ユーザーが承認したら plan.md を Edit で更新
3. spec-reviewer で整合性チェック:

   ```
   Task(spec-reviewer) を起動:
     プロンプト: 「docs/plans/{feature-name}/plan.md を読み込み、
     セクション間の整合性（データフロー↔API設計↔DB設計↔フロントエンド設計↔実装タスク）、
     型定義の一致、テスト網羅性をレビューしてください。」
   ```

   - **PASS**: 次のステップに進む
   - **NEEDS_FIX**: 問題点をユーザーに提示し、plan.md を修正 → 必要に応じて再レビュー

4. troubleshoot ドキュメントの該当セクションに「反映済み」を Edit で追記:

   ```
   ### plan.md の修正（該当する場合）
   - {修正内容} ← ✅ 反映済み（{YYYY-MM-DD}）
   ```

5. plan.md の実装タスク表を変更した場合、progress.md のタスク進捗テーブルも同期更新する

### 0-d. モード判定（progress.md の mode フィールド）

- **multi-pr** → **PR単位実装モード**（後述）
- **single** → **single モード**（全タスク 1 PR）

### 0-e. 再開検知

progress.md のタスク進捗テーブルから完了/進行中/未着手を集計:

- **全て `-`** → **新規開始**: Step 1（ブランチ作成）に進む
- **`✓` や `→` あり** → **再開フロー**:

**再開フロー**:

1. Task(git-analyzer) でブランチの実態を調査:
   プロンプト:
   「ブランチの実装状態を調査し、progress.md と突合してください。
   progress.md: docs/plans/{feature-name}/progress.md
   - ブランチのコミット履歴（main からの差分）
   - 未コミットの変更
   - progress.md のタスク進捗テーブルで `✓`（完了）になっているタスクの対象ファイルが
     実際に変更されているか確認し、矛盾があれば報告してください」

2. progress.md の情報と git 調査結果を統合してユーザーに提示:

   ```
   前回の実装状態を検出しました:

   ■ 現在の状況（progress.md）:
   {progress.md の「現在の状況」セクション}

   ■ git 状態:
   ブランチ: {ブランチ名}
   コミット: {N}件（main からの差分）
   未コミット変更: {ファイル一覧 or なし}

   ■ タスク進捗:
   | # | タスク | 状態 |
   |---|-------|------|
   | ... | ... | ... |

   進捗: {完了数}/{全数} タスク

   {矛盾がある場合}
   ⚠ 注意: progress.md と git 状態に不整合があります:
   - {矛盾内容}

   ■ 次にやること（progress.md）:
   {progress.md の「次にやること」セクション}
   ```

3. AskUserQuestion で再開ポイントを確認:
   - 「`→` のタスク #{N} から再開する」
   - 「次の未着手タスク #{M} から始める」
   - 「全体を確認し直す」

---

## Step 1: feature ブランチ作成

feature-name をそのままブランチ名に使用する。

**ブランチ名の規則**:
- 形式: `feature/{feature-name}`
- 例: `docs/plans/reminder/` → `feature/reminder`

```
ブランチ名: feature/{english-name}

この名前で作成しますか？（変更する場合は希望のブランチ名を入力してください）
```

**ブランチ作成**:
- ユーザー確認後、`git checkout -b feature/{english-name}` で作成
- 同名ブランチが既に存在する場合: 「既存ブランチに切り替える」or「別名で作成」を AskUserQuestion で選択

**progress.md の更新**:
- ブランチ作成後、progress.md の「ブランチ・PR」テーブルにブランチ名を記録
- progress.md の作業ログにエントリ追加

---

## Step 2: タスク順の実装（サブエージェント委譲パターン）

plan.md の「実装タスク」表を依存関係順に処理する。
**各タスクは code-researcher サブエージェントで調査 → メインコンテキストで実装** のハイブリッドで進める。

### タスク状態の更新

各タスクの開始時と完了時に **progress.md** の状態列を Edit で更新する:
- 開始: `-` → `→`
- 完了: `→` → `✓`

### 「現在の状況」「次にやること」の更新

各タスク完了時に progress.md の「現在の状況」と「次にやること」を Edit で更新する。

記述ルール:
- **「現在の状況」**: 2-4 文。完了済みの成果 + 進行中の作業 + ブロッカー（あれば）。技術的な具体名を含める
- **「次にやること」**: 1-3 文。具体的なタスク番号とアクション。再開時にそのまま実行指示として使える具体性

### 各タスクの進め方

```
── タスク #{N}: {タスク名} ({見積}) ──

1. progress.md の状態列を `→` に更新

2. Task(code-researcher) を起動:
   プロンプト:
   「タスク #{N}（{タスク名}）の実装に必要な情報を収集してください。
   仕様書: docs/plans/{feature-name}/plan.md の該当セクション
   プロジェクト規約: docs/plans/{feature-name}/project-context.md
   既存コード: {対象ファイル一覧}（存在する場合）
   以下を要約して返してください:
   - 実装に必要な型定義・インターフェース
   - 既存コードのパターン（命名規則、ディレクトリ構造）
   - バリデーションルール、エラーハンドリング
   - テストパターン」

3. code-researcher の調査結果をもとに実装

4. 完了後:
   - progress.md の状態列を `✓` に更新
   - progress.md の「現在の状況」「次にやること」を更新
   - progress.md の updated フィールドを現在日付に更新
```

**仕様書の参照ルール**（code-researcher に渡すセクションの判定）:
- タスク名やファイルパスから該当するセクションを判定:
  - DB/スキーマ関連 → plan.md の「DB変更」セクション
  - API/エンドポイント関連 → plan.md の「バックエンド変更」セクション
  - UI/コンポーネント関連 → plan.md の「フロントエンド変更」セクション
  - 型定義 → 複数のセクションを横断参照
- **メインコンテキストでは plan.md を直接 Read しない**（Step 0 で読み込み済み）。code-researcher が読み、要約を返す。

**見積サイズに応じた戦略**:
- **S（小）**: code-researcher で調査 → 直接実装。実装後にまとめて確認。
- **M（中）**: code-researcher で調査 → 直接実装。主要な判断ポイントで確認。
- **L（大）**: code-researcher で調査 → 実装方針をユーザーに提示 → 承認後に直接実装。

**タスク間の確認**:
- 各タスク完了後: 「タスク #{N} が完了しました。次のタスク #{N+1} に進みますか？」
- ユーザーが修正を求めた場合はその場で対応

**仕様矛盾検知プロトコル**:
仕様書の内容と実際のコードで矛盾が見つかった場合:
1. 矛盾の内容をユーザーに提示し、選択肢を提示:
   a) plan.md を修正してから再開（修正内容をユーザーに確認 → Edit で更新 → spec-reviewer で整合性チェック）
   b) 実装側を仕様に合わせる
   c) このまま進めて後で対応（plan.md のフィードバックログに記録）

---

## Step 3: ビルド確認

plan.md の「ビルド確認」セクションに記載されたコマンドを順に実行する。

```
ビルド確認を実行します（plan.md より）:

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
- plan.md の「手動検証チェックリスト」セクションをユーザーに提示:

```
手動検証チェックリスト（plan.md より）:
- [ ] {チェック項目1}
- [ ] {チェック項目2}

手動検証が完了したら、PR 作成に進みますか？
```

---

## Step 4: PR 作成

ユーザー確認後、`gh pr create` で PR を作成する。

**PR タイトル**:
```
{plan.md の title フィールドから取得}
```

**PR 本文の生成**:

1. リポジトリの PR テンプレートを探す:
   ```
   Glob .github/pull_request_template.md
   Glob .github/PULL_REQUEST_TEMPLATE/*.md
   ```
2. テンプレートが見つかった場合: テンプレートの構造に従い、plan.md の情報で各セクションを埋める
3. テンプレートがない場合: plan.md の概要・影響範囲・テスト方針をもとにシンプルな PR 本文を生成

**PR 作成の流れ**:

1. PR タイトルと本文をユーザーに提示して確認
2. 未コミットの変更があればコミットを提案（ユーザー確認必須 — CLAUDE.md ルール）
3. `git push -u origin feature/{english-name}`
4. `gh pr create --title "..." --body "..."`
5. PR の URL をユーザーに提示

```
PR を作成しました: {PR URL}
```

**progress.md の更新**:
- progress.md の「ブランチ・PR」テーブルに PR URL を記録
- progress.md の作業ログにエントリ追加

---

## Step 4.5: 仕様検証（任意）

実装完了後、仕様との整合性を確認する場合は `/feature-spec:verify` を使用してください。

---

## Step 5: PRフィードバック対応ガイド

PR作成後にレビュー指摘やQA不具合が発生した場合の対応フロー:

| 分類 | 例 | 対応 |
|------|-----|------|
| 実装バグ | ロジックミス | コード修正 → 追加コミット |
| 仕様不足 | エッジケース漏れ | plan.md を修正 → 実装修正 |
| 仕様変更 | 要件自体の変更 | plan.md を修正 → 実装修正 |
| 設計見直し | アーキテクチャ指摘 | plan.md を修正 → 再実装 |

**対応手順**:
1. 指摘内容を分類し、対応方針をユーザーに提示
2. 仕様修正が必要な場合は plan.md を Edit で修正（修正内容をユーザーに確認 → spec-reviewer で整合性チェック）
3. 修正後は Step 3（ビルド確認）から再実行
4. 追加コミット → PR 更新

---

## PR単位実装モード

Step 0 で progress.md の mode が `multi-pr` の場合、このモードで動作する。
デリバリープランに従い、**1 PR ずつ順番に**実装・PR作成を繰り返す。

### PR-Step 0: 次のPRを特定 + 再開検知

progress.md のデリバリープランテーブルと、タスク進捗テーブルの状態列・PR列から、次に実装すべきPRを特定する。

**特定ロジック**:
1. タスク進捗テーブルの PR 列でタスクをグルーピング
2. あるPRに属する全タスクが `✓` → そのPRは完了
3. 未完了の最初のPRを「次のPR」とする

**再開検知**:
- 「次のPR」内に `→`（実施中）のタスクがある → PR内再開フロー
- 「次のPR」内の全タスクが `-` → 新規PR開始

```
デリバリープランに基づくPR単位実装モードです。

■ 現在の状況:
{progress.md の「現在の状況」セクションの内容をそのまま表示}

進捗:
  PR1: {タイトル} — ✓ 完了（{N}/{N} タスク）
  PR2: {タイトル} — → 実施中（{M}/{N} タスク）
  PR3: {タイトル} — 未着手

次は PR2: {タイトル} の実装を続けます。（タスク: #{一覧}）
```

AskUserQuestion で確認:
- 「PR{N} の実装を開始（または再開）する」
- 「別のPRから始める」
- 「全体の状況を確認する」

### PR-Step 1: ブランチ作成

PR単位で個別のブランチを作成する。

**ブランチ名の規則**:
- 形式: `feature/{feature-name}-pr{N}`
- 例: `docs/plans/reminder/` の PR2 → `feature/reminder-pr2`

```
ブランチ名: feature/{english-name}-pr{N}

この名前で作成しますか？
```

**ブランチ作成**:
- ユーザー確認後、`git checkout -b feature/{english-name}-pr{N}` で作成
- 先行PRのブランチがまだマージされていない場合: 先行PRのブランチから分岐する
- 同名ブランチが既に存在する場合: 「既存ブランチに切り替える」or「別名で作成」を AskUserQuestion で選択

**progress.md の更新**:
- ブランチ作成後、progress.md の「ブランチ・PR」テーブルにブランチ名を記録
- progress.md の作業ログにエントリ追加

### PR-Step 2: タスク実装

該当PRに属するタスクのみを、single モードの Step 2 と同じロジックで実装する。

**スコープ制限**:
- タスク進捗テーブルの PR 列が現在のPR番号と一致するタスクのみを対象とする
- 他のPRに属するタスクには触れない

処理フローはsingle モードの Step 2（サブエージェント委譲パターン）と同一。

### PR-Step 3: ビルド確認

single モードの Step 3 と同一。plan.md のビルド確認セクションのコマンドを実行する。

### PR-Step 4: PR作成

single モードの Step 4 と同一のフローでPRを作成する。

**PR タイトル**: progress.md のデリバリープランテーブルのタイトル列の値を使用する。

**PR 本文の追加情報**:
- デリバリープランのどのPRに対応するかを明記
- 先行PRへの依存がある場合は本文に記載

**progress.md の更新**:
- 「ブランチ・PR」テーブルに PR URL を記録
- デリバリープランテーブルの PR 状態を更新
- 作業ログにエントリ追加

### PR-Step 5: 次のPRへの案内

PR作成後、次のステップを案内する:

```
PR{N}: {タイトル} が完了しました。

デリバリー進捗:
  PR1: {タイトル} — ✓ 完了
  PR2: {タイトル} — ✓ 完了（今回）
  PR3: {タイトル} — 未着手

次は PR{N+1}: {タイトル} です。続けますか？
```

AskUserQuestion で確認:
- 「PR{N+1} の実装に進む」→ PR-Step 0 に戻る
- 「今日はここまで」→ 終了（次回 `/feature-spec:implement` で再開可能）

**progress.md の更新**:
- 「現在の状況」「次にやること」を更新

**全PR完了時**:

```
全てのPRが完了しました！

  PR1: {タイトル} — ✓ {PR URL}
  PR2: {タイトル} — ✓ {PR URL}
  PR3: {タイトル} — ✓ {PR URL}

次のステップ:
- 仕様検証を行う場合は `/feature-spec:verify` を使用してください
```

progress.md の作業ログに完了エントリを追加する。

---

## 実行時の不具合が発生した場合

実装完了後のテストで「期待と違う動作」が見つかった場合:
- 原因が明らかな場合 → そのまま修正
- 原因が不明な場合 → `/feature-spec:troubleshoot` で調査を推奨
