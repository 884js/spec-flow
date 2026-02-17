# README.md フォーマット定義

機能全体の要件・データフロー・スコープを1ファイルにまとめたマスタードキュメント。
全メンバーが最初に読むファイル。

**出力先ルール**:
- `docs/{feature-name}/` は **カレントディレクトリ（Claude Code 起動ディレクトリ）直下** に作成する。サブディレクトリ内には作らない
- `{feature-name}` は **日本語のシンプルな名前**（例: `キャンペーン通知`）。パス区切り（`/`）を含めない

## ドキュメント構造

```
docs/{feature-name}/
├── README.md              # 要件 + データフロー + スコープ
├── project-context.md     # プロジェクトコンテキスト（規約、技術スタック、パターン）
├── api-spec.md          # API設計
├── db-spec.md           # DB設計
├── frontend-spec.md     # フロントエンド設計
└── implementation-plan.md  # 実装計画（タスク、影響範囲、テスト方針）
```

## テンプレート

```markdown
# {機能名}

> {一行サマリー: この機能が何を実現するか}

## ステータス

Draft

## 背景・課題

{現状の問題点。具体的なユーザーのペインポイントを記述}

## ユーザーストーリー

- As a {ユーザー種別}, I want {やりたいこと}, so that {得られる価値}

## 受入条件

- [ ] {具体的で検証可能な条件1}
- [ ] {具体的で検証可能な条件2}

## スコープ

### 対象

- {今回実装する範囲1}
- {今回実装する範囲2}

### 対象外

- {今回やらないこと1}
- {今回やらないこと2}

## データフロー

### シーケンス図

{メインユースケースのデータの流れ}

\`\`\`mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB

    User->>Frontend: {ユーザー操作}
    Frontend->>API: POST /api/{resource}
    API->>DB: INSERT INTO {table}
    DB-->>API: {result}
    API-->>Frontend: 200 {response}
    Frontend-->>User: {UI更新}
\`\`\`

### 状態遷移図

{状態を持つ機能の場合のみ}

\`\`\`mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Loading: ユーザー操作
    Loading --> Success: API成功
    Loading --> Error: API失敗
    Error --> Loading: リトライ
    Success --> [*]
\`\`\`

## 設計ドキュメント

| ドキュメント | 説明 | ステータス |
|---|---|---|
| [プロジェクトコンテキスト](./project-context.md) | プロジェクト規約、技術スタック、パターン | 完了 |
| [API設計](./api-spec.md) | エンドポイント、型定義、内部処理フロー | 未作成 |
| [DB設計](./db-spec.md) | テーブル定義、マイグレーション、ER図 | 未作成 |
| [フロントエンド設計](./frontend-spec.md) | コンポーネント、Hooks、ワイヤーフレーム | 未作成 |

## 生成情報

- 生成日: {YYYY-MM-DD}
- 対象プロジェクト: {project-name}
```

## 記述ルール

- ユーザーストーリーは最低1つ、主要なユースケースを全てカバー
- 受入条件は「〜できること」「〜が表示されること」のように検証可能な形で書く
- スコープ外を明示することで実装の膨張を防ぐ
- シーケンス図は必須。メインのユースケースを1つ以上図示
- participant名は実際のコンポーネント/サービス名を使う
- 状態遷移図は該当する場合のみ
- 設計ドキュメント表は省略判定に基づき「該当なし」も可

## ドキュメント省略ルール

全ての機能追加が全ドキュメントを必要とするわけではない。以下のルールで省略可能:

| ドキュメント | 省略条件 |
|----------|---------|
| api-spec.md | API変更がない場合 |
| db-spec.md | DB変更がない場合 |
| frontend-spec.md | UI変更がない場合（バックエンドのみ） |

以下は**常に必須**:
- README.md（要件、データフロー、スコープ）
- project-context.md（プロジェクト規約、技術スタック、パターン）

`implementation-plan.md` は plan フェーズで生成される。plan 未実施の場合は存在しない。

省略する場合、README.md の設計ドキュメント表で「該当なし」と記載する。
