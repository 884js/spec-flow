# db-spec.md フォーマット定義

DB設計の全情報を1ファイルに自己完結させる。バックエンド/DBA がこのファイルだけで実装できることが目標。

## テンプレート

```markdown
# DB設計

## 概要

{変更の目的と影響の概要}

## ER図

\`\`\`mermaid
erDiagram
    TABLE_A ||--o{ TABLE_B : has
    TABLE_A {
        string id PK
        string name
        datetime created_at
    }
    TABLE_B {
        string id PK
        string table_a_id FK
        string value
    }
\`\`\`

## テーブル定義

### 新規テーブル: {table_name}

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| id | 文字列 | PK | 主キー |
| {column} | 文字列 | NOT NULL | {説明} |
| {column} | 数値 | - | {説明} |
| {column} | 日時 | NOT NULL | {説明} |

### 既存テーブルの変更: {table_name}

| カラム | 操作 | 型 | 制約 | 説明 |
|-------|------|-----|------|------|
| {column} | 追加 | 文字列 | - | {説明} |
| {column} | 変更 | 数値 | NOT NULL | {変更理由} |

## モデルコード

\`\`\`typescript
// {既存スキーマファイルパス} への追加

export const {tableName} = sqliteTable('{table_name}', {
  id: text('id').primaryKey(),
  // ...
});
\`\`\`

## マイグレーション

\`\`\`sql
-- {マイグレーション名}
CREATE TABLE {table_name} (
  id TEXT PRIMARY KEY,
  -- ...
);

-- インデックス
CREATE INDEX idx_{table}_{column} ON {table}({column});
\`\`\`

## インデックス

| テーブル | カラム | 種別 | 目的 |
|---------|-------|------|------|
| {table} | {column} | 通常 | {検索の高速化等} |
| {table} | {column} | ユニーク | {一意性保証} |

## 型定義の変更

\`\`\`typescript
// {既存型定義ファイルパス} への変更

// Before:
interface Xxx {
  id: string;
  existingField: string;
}

// After:
interface Xxx {
  id: string;
  existingField: string;
  newField: string;       // 追加
}
\`\`\`

## 設計決定事項

| 決定事項 | 理由 |
|---------|------|
| {例: 1:N直接リレーション} | {例: 中間テーブル不要、1メモ1リマインダーのため} |

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/db/schema.ts` | スキーマ定義 | 変更 |
| `src/types/{resource}.ts` | 型定義 | 変更 |
```

## 記述ルール

- ER図はMermaid erDiagram で可視化
- テーブル定義はマークダウン表 + モデルコード（TypeScript/Go等）の両方
- マイグレーションはSQLで記述
- 既存型の変更はBefore/After形式で差分を明示
- 設計決定事項で「なぜそうしたか」を記録
- api-spec.md の型定義と整合性を保つこと
