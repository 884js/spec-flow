---
name: outline
description: "Use when starting a new feature spec from scratch. Invoke for requirements definition, scope planning, and data flow design. First step in the spec workflow (outline → detail → plan). 仕様書作成, 要件定義, 概要設計."
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Task, Bash
metadata:
  triggers: create spec, new spec, requirements, 仕様書作成, 要件定義, 概要設計, スペック作成
---

# 要件定義（Outline）

既存システムへの機能追加の **要件定義** を対話で生成する。
「何を作るか」を明確にし、方向性の合意を取るためのドキュメント。

出力: `docs/{feature-name}/README.md`（要件 + データフロー + スコープ + 省略判定）

**出力先ルール**:
- `docs/{feature-name}/` は **カレントディレクトリ（Claude Code 起動ディレクトリ）直下** に作成する。サブディレクトリ内には作らない
- `{feature-name}` は **日本語のシンプルな名前**（例: `キャンペーン通知`）。パス区切り（`/`）を含めない

要件定義の承認後、`/feature-spec:detail` で設計に進む。
既存セクションの修正は `/feature-spec:revise` で行う。

## ワークフロー

```
Step 1: 要求ヒアリング（対話のみ）
Step 2: コンテキスト収集 + 要件作成  ← context-collector → project-context.md, spec-writer → README.md
Step 3: データフロー設計             → README.md にデータフローセクション ← code-researcher
Step 4: 省略判定 + README.md 完成
```

---

## Step 1: 要求ヒアリング

$ARGUMENTS が渡されている場合は、それを初期要求として扱い、不明点があれば AskUserQuestion で確認する。

$ARGUMENTS がない場合は、AskUserQuestion で以下を確認する:
- 「どんな機能を追加したいですか？」（ユーザーストーリー: 誰が、何を、なぜしたいのか）
- 「何ができたら完成ですか？」（受入条件）
- 「スコープ外にすることはありますか？」（スコープ: やること / やらないこと）

1-2往復で明確になったら次のステップへ。

---

## Step 2: コンテキスト収集 + 要件作成

### 2-a. コンテキスト自動収集

**context-collector** エージェントにプロジェクト全体の調査を委譲。

```
Task(context-collector) を起動:
  プロンプト: 「このプロジェクトのコンテキストを収集してください。
  CLAUDE.md、ディレクトリ構造、package.json、型定義、DBスキーマ、
  既存仕様書を調査し、構造化された要約を返してください。
  追加機能の概要: {Step 1 で把握した機能概要}
  関連しそうなテーブルやモジュールがあれば、関連する既存機能として報告してください。」
```

要約を以下のフォーマットでユーザーに提示（省略しない）:

```
プロジェクトの構造を把握しました:
- フレームワーク: {framework}
- 主要ディレクトリ: {dirs}
- DB: {db type}
- 既存の型定義: {N}ファイル
- テスト/ビルドコマンド: {commands}
```

context-collector の出力を `docs/{feature-name}/project-context.md` として Write（プロジェクト規約を後続フェーズで参照するため）。

### 2-b. 要件セクション作成 → README.md

コンテキスト収集結果を踏まえ、**spec-writer** エージェントに README.md の初期生成を委譲する。

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/README.md を生成してください。
  ドキュメント種別: README（要件セクションのみ: 背景・課題、ユーザーストーリー、受入条件、スコープ）
  フォーマット定義: skills/outline/references/formats/readme.md を Read して参照
  出力例: skills/outline/references/examples/readme.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  要件:
    ユーザーストーリー: {Step 1 で確定した内容}
    受入条件: {Step 1 で確定した内容}
    スコープ: {Step 1 で確定した内容}
  注意: この時点ではデータフロー・省略判定・設計ドキュメント表は含めないでください。
  生成完了後、ファイルの概要を5行以内で返してください。」
```

生成された README.md の概要をユーザーに提示し、AskUserQuestion で確認を取る（確認が取れるまで Step 3 に進まない）:
- 「問題なし、次へ進む」
- 「要件を修正したい」

---

## Step 3: データフロー設計 → README.md にデータフローセクション追記

**事前調査**:
```
Task(code-researcher) を起動:
  プロンプト: 「このプロジェクトのデータフローパターンを調査してください。
  - バックエンド: API ハンドラ間のデータの流れ、ミドルウェアチェーン、サービス層の呼び出しパターン
  - フロントエンド: API通信パターン、状態管理、データフェッチングの仕組み（フロントエンドがある場合）
  要約を返してください。」
```

調査結果を踏まえて「メインのユースケースの流れを確認します。」と提示し、
**以下の観点をユーザーと対話で確認する（自動生成せず、必ずユーザーの入力を待つ）**:
- データの流れの参加者（ユーザー、フロントエンド、API、DB等）
- メインフローのステップ
- 状態を持つ場合はその遷移

ユーザーの確認が取れたら → README.md にデータフローセクションを Edit で追記（Mermaid sequenceDiagram を含む）

⏸ データフロー追記後、AskUserQuestion で確認を取る（Step 4 に進まない）:
- 「問題なし、次へ進む」
- 「データフローを修正したい」

---

## Step 4: 省略判定 + README.md 完成

要件とデータフローをもとに、どのドメインdocが必要かを判定し、**必ず以下の `[x]`/`[ ]` 形式でユーザーに提示する**:

```
この機能では以下の設計ドキュメントが必要です:
- [x] api-spec.md（API設計）
- [x] db-spec.md（DB設計）
- [x] frontend-spec.md（フロントエンド設計）
- [ ] (該当なしのドキュメントは省略)
```

**省略判定**:
- API変更なし → api-spec.md 省略
- DB変更なし → db-spec.md 省略
- UI変更なし → frontend-spec.md 省略

README.md に以下を **必ず** 追記して完成:
- 設計ドキュメント表（必要なドキュメントのリンク + ステータス「未作成」、省略は「該当なし」）
- 生成情報（生成日、対象プロジェクト）
- **次のステップ**（必須）: `/feature-spec:detail` で設計に進む旨を記載。このセクションを省略しない

README.md 完成後、AskUserQuestion で次のアクションを提示する:
- 「`/feature-spec:detail` で設計に進む」
- 「要件を修正する（`/feature-spec:revise`）」
