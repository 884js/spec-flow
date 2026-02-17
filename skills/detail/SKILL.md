---
name: detail
description: "Use when outline is complete and detailed technical design is needed. Invoke for API, DB, and frontend spec generation with type definitions. Requires outline first. 詳細仕様, 詳細設計, 技術設計, 型定義."
allowed-tools: Read, Glob, Grep, Write, Edit, Task
metadata:
  triggers: detail spec, detailed design, API design, DB design, frontend design, type definitions, 詳細仕様, 詳細設計, 技術設計, 型定義
---

# 設計（Detail）

要件定義（outline）で決めた「何を作るか」をもとに、**ドメイン単位の自己完結した設計ドキュメント** を対話で生成する。
各ドメインdocには概要と技術詳細の両方を含み、そのドメインの開発者がファイル1つで実装できる形にする。

入力: `docs/{feature-name}/README.md`
出力: 同ディレクトリに api-spec.md, db-spec.md, frontend-spec.md を追加（省略可）

**パスルール**: `docs/{feature-name}/` はカレントディレクトリ直下。`{feature-name}` は日本語のシンプルな名前（パス区切り不可）

設計の承認後、`/feature-spec:plan` で実装計画に進む。
既存セクションの修正は `/feature-spec:revise` で行う。

## ワークフロー

```
Step 0: README.md 読み込み + 必要ドメイン判定
Step 1: code-researcher で一括調査（API+DB+コンポーネント）
Step 2: api-spec.md 生成 ← spec-writer
Step 3: db-spec.md 生成 ← spec-writer（api-spec.md を参照して型整合性を確保）
Step 4: frontend-spec.md 生成 ← spec-writer（api-spec.md + db-spec.md を参照）
Step 5: セルフ整合性チェック（ドメインdoc間の型・エンドポイント整合性）
Step 6: README.md 更新（設計ドキュメントのステータス更新）
```

**核心: 逐次参照で型整合性を保証**
- Step 3 で api-spec.md を Read → DB型をAPI型と揃える
- Step 4 で api-spec.md + db-spec.md を Read → Props型を揃える

---

## Step 0: README.md 読み込み + 必要ドメイン判定

スキル起動直後に、既存の要件定義を読み込む:

```
Glob docs/**/README.md
```

$ARGUMENTS に feature-name が指定されている場合はそのディレクトリを使用。
複数の仕様書ディレクトリがある場合はユーザーに選択を求める。

```
Read docs/{feature-name}/README.md
Read docs/{feature-name}/project-context.md
```

読み込んだ内容をもとに、必要なドメインdocを判定して提示:

```
要件定義を読み込みました:
- 機能: {feature summary}
- データフロー: {flow summary}

プロジェクト規約を把握しました:
- 命名規則: {naming conventions}
- ディレクトリ構成: {directory patterns}
- 使用ライブラリ: {key libraries}

この機能では以下の設計ドキュメントを生成します:
- [x] api-spec.md（API設計）
- [x] db-spec.md（DB設計）
- [x] frontend-spec.md（フロントエンド設計）
- [ ] (該当なしのドキュメントは省略)
```

**省略判定**:
- API変更なし → api-spec.md 省略
- DB変更なし → db-spec.md 省略
- UI変更なし → frontend-spec.md 省略

---

## Step 1: code-researcher で一括調査

必要なドメインdocに応じて、**code-researcher** で一括調査する:

```
Task(code-researcher) を起動:
  プロンプト: 「このプロジェクトの技術スタック: {project-context.md の情報}
  以下のパターンを調査してください:
  - API ルーティング、ハンドラ、型定義、エラーハンドリング、バリデーション
  - DB スキーマ定義、マイグレーション、テーブル構造、リレーション、ID生成
  - コンポーネント構成、UIライブラリ、Props型、状態管理、フォーム処理（フロントエンド設計が必要な場合）」
```

調査結果をユーザーに提示し、設計に入る。

---

## Step 2: api-spec.md 生成

**project-context.md で把握した既存パターン・命名規則に従ってコードを提案する。**

調査結果を踏まえて「APIを設計します。」

対話で確認する観点:
- 必要なエンドポイント（CRUD等）
- 各エンドポイントの入力/出力の型定義（TypeScript interface）
- エラーケースとエラーコード
- 内部処理フロー
- ファイル構成
- テストケース

確認が取れたら **spec-writer** に生成を委譲:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/api-spec.md を生成してください。
  ドキュメント種別: api-spec（API設計）
  フォーマット定義: skills/outline/references/formats/api-spec.md を Read して参照
  出力例: skills/outline/references/examples/api-spec.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  設計内容:
    エンドポイント: {確定したエンドポイント一覧}
    型定義: {確定したリクエスト/レスポンス型}
    エラーケース: {確定したエラーコード}
    内部処理フロー: {確定した処理ステップ}
    ファイル構成: {確定したファイル構成}
    テストケース: {確定したテスト方針}
  生成完了後、ファイルの概要を5行以内で返してください。」
```

→ 「API設計を確認してください。次に進みます」

---

## Step 3: db-spec.md 生成

**project-context.md で把握した既存パターン・命名規則に従ってコードを提案する。**

**型整合性の確保**:
```
Read docs/{feature-name}/api-spec.md
```

api-spec.md のリクエスト/レスポンス型を確認し、DB型と揃える。

対話で確認する観点:
- 新規テーブル/カラムの設計
- 既存テーブルとのリレーション（ER図）
- モデルコード（TypeScript/Go等のスキーマ定義）
- マイグレーションSQL
- インデックス、制約
- 型定義の変更（Before/After）
- 設計決定事項（なぜそうしたか）

確認が取れたら **spec-writer** に生成を委譲:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/db-spec.md を生成してください。
  ドキュメント種別: db-spec（DB設計）
  フォーマット定義: skills/outline/references/formats/db-spec.md を Read して参照
  出力例: skills/outline/references/examples/db-spec.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  API型定義との整合性: {api-spec.md のリクエスト/レスポンス型の要約}
  設計内容:
    テーブル設計: {確定したテーブル/カラム}
    リレーション: {確定したER関係}
    モデルコード: {確定したスキーマ定義}
    マイグレーション: {確定したSQL}
    インデックス: {確定したインデックス}
    型定義変更: {確定したBefore/After}
    設計決定事項: {確定した理由}
  生成完了後、ファイルの概要を5行以内で返してください。」
```

→ 「DB設計を確認してください。次に進みます」

---

## Step 4: frontend-spec.md 生成

**project-context.md で把握した既存パターン・命名規則に従ってコードを提案する。**

**型整合性の確保**:
```
Read docs/{feature-name}/api-spec.md
Read docs/{feature-name}/db-spec.md
```

api-spec.md のレスポンス型と db-spec.md の型定義を確認し、Props型を揃える。

対話で確認する観点:
- コンポーネントツリー（Mermaid図）
- 新規コンポーネントの役割・Props型・状態管理・イベントハンドラ
- UIワイヤーフレーム（ASCIIアート）
- Hooks の設計
- 既存コンポーネントの変更箇所
- エッジケース
- ファイル構成
- テストケース

確認が取れたら **spec-writer** に生成を委譲:

```
Task(spec-writer) を起動:
  プロンプト: 「docs/{feature-name}/frontend-spec.md を生成してください。
  ドキュメント種別: frontend-spec（フロントエンド設計）
  フォーマット定義: skills/outline/references/formats/frontend-spec.md を Read して参照
  出力例: skills/outline/references/examples/frontend-spec.md を Read して参照
  プロジェクト規約: {project-context.md の要約}
  API型定義との整合性: {api-spec.md のレスポンス型の要約}
  DB型定義との整合性: {db-spec.md の型定義の要約}
  設計内容:
    コンポーネントツリー: {確定したツリー構造}
    新規コンポーネント: {確定したProps・状態管理・ハンドラ}
    ワイヤーフレーム: {確定したUI}
    Hooks: {確定したフック設計}
    既存変更: {確定した変更箇所}
    エッジケース: {確定したケース}
    ファイル構成: {確定したファイル構成}
    テストケース: {確定したテスト方針}
  生成完了後、ファイルの概要を5行以内で返してください。」
```

→ 「フロントエンド設計を確認してください」

---

## Step 5: セルフ整合性チェック

全ドメインdocを Read し、以下の整合性を確認:

```
Read docs/{feature-name}/api-spec.md
Read docs/{feature-name}/db-spec.md
Read docs/{feature-name}/frontend-spec.md
```

**チェック項目**:
1. **型整合性**: API のリクエスト/レスポンス型 ↔ DB のカラム/型定義 ↔ フロントエンドの Props型
2. **エンドポイント整合性**: README.md のシーケンス図のAPI呼び出し ↔ api-spec.md のエンドポイント一覧
3. **ファイル参照整合性**: 各ドメインdocのファイル構成に矛盾がないか

問題があればユーザーに提示し、該当ドメインdocを Edit で修正。

---

## Step 6: README.md 更新

既存の README.md を Read し、設計ドキュメント表のステータスを更新:
- 生成したドメインdocのステータスを「完了」に更新
- **次のステップ**: `/feature-spec:plan` で実装計画に進む旨を記載
