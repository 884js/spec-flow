---
name: plan
description: "Use when detail is complete and implementation planning is needed. Invoke for task breakdown, dependency ordering, impact analysis, and test strategy. Requires detail first. 実装計画, タスク分解, テスト方針."
allowed-tools: Read, Glob, Grep, Write, Edit, Task
metadata:
  triggers: implementation plan, task breakdown, test strategy, impact analysis, 実装計画, タスク分解, テスト方針
---

# 実装計画（Plan）

設計（detail）で作成したドメインdocをもとに、**「どう進めるか」** の実装計画を策定する。
各ドメインdocに含まれるファイル構成・テスト情報を **横断的に統合** し、
ドメイン間の依存関係を考慮した実装順序を策定する。
最後に spec-reviewer で仕様書全体の整合性をチェックし、品質を担保する。

入力: `docs/{feature-name}/` の README.md + 各ドメインdoc
出力: implementation-plan.md を生成（実装タスク、影響範囲、テスト方針）

**パスルール**: `docs/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は日本語のシンプルな名前（パス区切り不可）

仕様書完成後の修正は `/feature-spec:revise` で行う。

## ワークフロー

```
Step 0: README.md + 全ドメインdoc 読み込み
Step 1: 横断的な実装タスク策定（依存関係付き）
Step 2: 影響範囲の評価  ← code-researcher で調査
Step 3: テスト方針の整理（各ドメインdocのテスト情報を統合 + 横断テスト追加）
Step 4: implementation-plan.md 生成 ← spec-writer
Step 5: 品質レビュー    ← spec-reviewer エージェント
Step 6: README.md 更新（設計ドキュメント表に追加のみ）
```

---

## Step 0: 全ドキュメント読み込み

スキル起動直後に、既存のドキュメントを全て読み込む:

```
Glob docs/**/README.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

```
Read docs/{feature-name}/README.md
Read docs/{feature-name}/project-context.md
Read docs/{feature-name}/api-spec.md      （存在する場合）
Read docs/{feature-name}/db-spec.md       （存在する場合）
Read docs/{feature-name}/frontend-spec.md （存在する場合）
```

読み込んだ内容の概要をユーザーに提示:

```
設計ドキュメントを読み込みました:
- 機能: {feature summary}
- API: {エンドポイント数と概要}
- DB: {テーブル/カラムの概要}
- フロントエンド: {コンポーネント数と概要}
- プロジェクト規約: {ビルド/テストコマンド、命名規則等}

これらをもとに実装計画を策定します。
```

---

## Step 1: 横断的な実装タスク策定

各ドメインdocのファイル構成セクションを統合し、依存関係を考慮したタスク分解を提示。

**統合の観点**:
- api-spec.md のファイル構成 → DB変更後に実装
- db-spec.md のファイル構成 → 最初に実装（他の依存元）
- frontend-spec.md のファイル構成 → API実装後に実装
- ドメイン間の依存関係（DB → API → フロントエンド）

→ タスク一覧 + 依存関係図（Mermaid）を作成
→ 「タスク分解と順序はこれで良いですか？」

---

## Step 2: 影響範囲の評価

各ドメインdocの変更ファイルを統合し、既存機能への影響を評価。

**code-researcher で依存関係を調査**:

```
Task(code-researcher) を起動:
  プロンプト: 「以下のファイルの依存関係・参照元を調査してください:
  {各ドメインdocのファイル構成から抽出した変更対象ファイル一覧}
  - バックエンド: これらのファイルを import/参照している箇所と、影響を受ける既存機能を報告してください
  - フロントエンド: コンポーネント/フックの使用箇所と、影響を受ける画面を報告してください（フロントエンド設計がある場合）」
```

**調査結果をもとに評価**:
- 既存機能への影響（影響内容、リスク、対策）
- 後方互換性
- パフォーマンスへの影響
- セキュリティ考慮事項

→ 影響範囲をまとめて提示
→ 「影響範囲の評価を確認してください」

---

## Step 3: テスト方針の整理

各ドメインdocのテストセクションを統合し、横断テストを追加。

**統合の観点**:
- api-spec.md のテスト → APIテスト
- db-spec.md のテスト → DBマイグレーションテスト
- frontend-spec.md のテスト → UIコンポーネントテスト
- **横断テスト**: E2Eテスト、統合テスト（ドメイン間の結合）

→ テスト一覧 + 手動検証チェックリスト + ビルド確認コマンドを作成
→ 「テスト方針を確認してください」

---

## Step 4: implementation-plan.md 生成

Step 1〜3 で策定した実装計画を **spec-writer** に委譲して生成:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/implementation-plan.md を生成してください。
  ドキュメント種別: implementation-plan（実装計画）
  フォーマット定義: skills/outline/references/formats/implementation-plan.md を Read して参照
  出力例: skills/outline/references/examples/implementation-plan.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  実装計画の内容:
    実装タスク: {Step 1 で確定したタスク一覧と依存関係}
    影響範囲: {Step 2 で確定した影響範囲・リスク}
    テスト方針: {Step 3 で確定したテスト一覧・チェックリスト・ビルドコマンド}
  生成完了後、ファイルの概要を5行以内で返してください。」
```

---

## Step 5: 品質レビュー

全ドキュメントが揃ったら、**spec-reviewer** エージェントで整合性をチェック。

```
Task(spec-reviewer) を起動:
  プロンプト: 「docs/{feature-name}/ 内の全ドキュメント（README.md, api-spec.md,
  db-spec.md, frontend-spec.md, implementation-plan.md）を読み込み、
  ドキュメント間の整合性、型定義の一致、テスト網羅性をレビューしてください。」
```

**レビュー観点**:
- ドメインdoc間整合性（API型↔DB型↔Props型）
- エンドポイント整合性（README.md のシーケンス図 ↔ api-spec.md）
- ファイル構成整合性（各ドメインdocのファイル構成 ↔ 実装タスク）
- テスト網羅性（受入条件 ↔ テスト項目）
- 影響範囲網羅性（変更ファイル ↔ 影響評価）

**結果の処理**:
- **PASS**: Step 6 に進む
- **NEEDS_FIX**: 問題点をユーザーに提示し、該当ドキュメントを修正 → 必要に応じて再レビュー

---

## Step 6: README.md 更新

既存の README.md を Read し、設計ドキュメント表に `implementation-plan.md` へのリンクを追加:

```
| [実装計画](./implementation-plan.md) | 実装タスク、影響範囲、テスト方針 | 完了 |
```

```
「仕様書が完成しました。
- 実装に進む場合は `/feature-spec:implement` を使用してください
- 修正したい箇所がある場合は `/feature-spec:revise` を使用してください」
```

修正があれば該当ドキュメントを Edit、必要に応じて更新。
