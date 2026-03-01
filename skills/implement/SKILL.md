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

入力: `docs/plans/{feature-name}/plan.md`（設計仕様）
状態管理: `docs/plans/{feature-name}/progress.md`（実行状態の単一ソース）
出力: 実装コード + PR

**パスルール**: `docs/plans/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は英語の kebab-case。パス区切り不可

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

## Step 0: 読み込み + 再開検知

スキル起動直後に plan.md と progress.md を読み込み、新規開始か再開かを判定する。

```
Glob docs/plans/**/plan.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

### plan.md の読み込み

```
Read docs/plans/{feature-name}/plan.md
```

plan.md が存在しない場合は「先に `/feature-spec:plan` で設計・実装計画を作成してください」と案内して終了する。

### 外部ライブラリの事前調査

plan.md で外部ライブラリ（SDK、APIクライアント、UIフレームワーク等）が使われる場合:

1. plan.md と package.json 等から使用ライブラリ＋バージョンを特定
2. ライブラリごとに library-researcher で調査（複数あれば並列実行）:

   ```
   Task(subagent_type: library-researcher):
     プロンプト: 「以下のライブラリについて、実装に必要な情報を調査してください。
     調査対象: {ライブラリ名} v{バージョン}
     用途: {plan.md での用途}
     関連ライブラリ: {同時に使う他のライブラリがあれば記載}」
   ```

3. 調査結果は実装中の参照情報として保持し、該当タスクの実装時に活用する

外部ライブラリが使われない場合はスキップ。

### progress.md の読み込み / 自動生成

```
Read docs/plans/{feature-name}/progress.md
```

- **progress.md が存在** → 状態を復元
- **progress.md が存在しない** → [templates/progress-single.md](templates/progress-single.md) を参照して自動生成:
  - plan.md のタスク表をコピーし、状態列を追加（全て `-`）
  - mode: single

### troubleshoot ドキュメントの確認

```
Glob docs/plans/{feature-name}/troubleshoot-*.md
```

ファイルが存在する場合、「plan.md の修正」セクションに未対応の修正提案（「反映済み」マークがないもの）がないか確認する。未対応の修正があれば:

1. 修正内容をユーザーに提示し、plan.md への反映可否を確認
2. 承認されたら plan.md を Edit → spec-reviewer で整合性チェック → troubleshoot に「✅ 反映済み」追記
3. 実装タスク表に変更があれば progress.md も同期更新

### 再開検知

progress.md のタスク進捗テーブルから状態を集計する:

- **全て `-`** → **新規開始**: Step 1 へ
- **`✓` や `→` あり** → **再開フロー**:

**再開フロー**:

1. git-analyzer サブエージェントでブランチの実装状態を調査し、progress.md と突合する
2. progress.md の情報と git 調査結果を統合してユーザーに提示:

   ```
   前回の実装状態を検出しました:

   ■ 現在の状況: {progress.md の「現在の状況」}
   ■ git: {ブランチ名} / {N}件コミット / 未コミット変更: {有無}
   ■ 進捗: {完了数}/{全数} タスク
   {矛盾があれば: ⚠ progress.md と git 状態に不整合あり}
   ■ 次にやること: {progress.md の「次にやること」}
   ```

3. AskUserQuestion で再開ポイントを確認:
   - 「`→` のタスク #{N} から再開する」
   - 「次の未着手タスク #{M} から始める」
   - 「全体を確認し直す」

---

## Step 1: feature ブランチ作成

ブランチ名は `feature/{feature-name}` 形式。ユーザーに確認し、承認後に `git checkout -b` で作成する。同名ブランチが既に存在する場合は切り替えるか別名にするか選択させる。

ブランチ作成後、progress.md の「ブランチ・PR」テーブルと作業ログを更新する。

---

## Step 2: タスク順の実装

plan.md の「実装タスク」表を依存関係順に処理する。

### PRスコープ制限（multi-pr の場合）

progress.md のタスク進捗テーブルに **PR 列** がある場合、**未完了の最初のPRに属するタスクのみを対象** とする。

### タスク状態の更新

各タスクの開始時と完了時に **progress.md** の状態列を Edit で更新する:
- 開始: `-` → `→`
- 完了: `→` → `✓`

各タスク完了時に「現在の状況」「次にやること」「updated フィールド」も更新する。

- **「現在の状況」**: 2-4 文。完了済みの成果 + 進行中の作業 + ブロッカー（あれば）
- **「次にやること」**: 1-3 文。再開時にそのまま実行指示として使える具体性

### 見積サイズに応じた進め方

タスクの見積サイズによって、調査方法とユーザー確認のタイミングを変える。小さなタスクにまで毎回サブエージェント起動や確認を挟むと、全体のスループットが落ちるため。

**S（小）**: メインコンテキストで直接調査・実装する（code-researcher 不要）。**ユーザー確認なしで次のタスクに連続着手** してよい。複数の S タスクをまとめて完了後に一括報告する。

**M（中）**: code-researcher サブエージェントで調査 → 実装。完了後に簡潔に報告し、次のタスクに進む。

**L（大）**: code-researcher で調査 → **実装方針をユーザーに提示** → 承認後に実装。完了後にユーザー確認。

### M/L タスクの進め方

```
── タスク #{N}: {タスク名} ({見積}) ──

1. progress.md の状態列を `→` に更新

2. Task(subagent_type: code-researcher):
   プロンプト:
   「タスク #{N}（{タスク名}）の実装に必要な情報を収集してください。
   仕様書: docs/plans/{feature-name}/plan.md の該当セクション
   プロジェクト規約: CLAUDE.md / AGENTS.md および既存コードのパターン
   既存コード: {対象ファイル一覧}（存在する場合）
   以下を要約して返してください:
   - 実装に必要な型定義・インターフェース
   - 既存コードのパターン（命名規則、ディレクトリ構造）
   - バリデーションルール、エラーハンドリング
   - テストパターン」

3. code-researcher の調査結果をもとに実装

4. progress.md を更新（状態列 + 「現在の状況」「次にやること」）
```

### plan.md の参照について

plan.md は Step 0 で読み込み済みだが、コンテキストが長くなった場合やタスクの詳細仕様を確認したい場合は **必要に応じて再度 Read してよい**。特に、具体的な型定義やエラーケースの確認時には該当セクションを Read する方が正確。

仕様書の該当セクションの判定:
- DB/スキーマ関連 → plan.md の「DB変更」セクション
- API/エンドポイント関連 → plan.md の「バックエンド変更」セクション
- UI/コンポーネント関連 → plan.md の「フロントエンド変更」セクション
- 型定義 → 複数のセクションを横断参照

### 仕様矛盾検知プロトコル

仕様書の内容と実際のコードで矛盾が見つかった場合:
1. 矛盾の内容をユーザーに提示し、選択肢を提示:
   a) plan.md を修正してから再開（Edit → spec-reviewer で整合性チェック）
   b) 実装側を仕様に合わせる
   c) このまま進めて後で対応

---

## Step 3: ビルド確認

plan.md の「ビルド確認」セクションに記載されたコマンドを順に実行する。エラーがあれば修正 → 再実行を繰り返す。

手動検証チェックリストをユーザーに提示し、動作確認の結果を AskUserQuestion で確認:
- 「問題なし、PR 作成に進む」→ Step 4 へ
- 「不具合がある・動作がおかしい」→ 「`/feature-spec:troubleshoot` で根本原因を調査できます。`/clear` してから実行してください。」と案内して終了

---

## Step 4: PR 作成

1. PR タイトルは plan.md の title フィールドから取得
2. PR テンプレート（`.github/pull_request_template.md`）があればその構造に従い、なければ plan.md の概要・影響範囲・テスト方針からシンプルな本文を生成
3. PR タイトルと本文をユーザーに提示して確認
4. AskUserQuestion で Draft PR にするか確認
5. 未コミットの変更があればコミットを提案（ユーザー確認必須）
6. `git push -u origin feature/{feature-name}` → `gh pr create`
7. PR URL をユーザーに提示し、progress.md の「ブランチ・PR」テーブルと作業ログを更新
