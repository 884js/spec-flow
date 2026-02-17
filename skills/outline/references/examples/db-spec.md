# 出力例: db-spec.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する db-spec.md の出力例。

```markdown
# DB設計

## 概要

リマインダー情報を保持する `reminders` テーブルを新規追加する。

## ER図

\`\`\`mermaid
erDiagram
    memos ||--o| reminders : has
    memos {
        string id PK
        string content
        integer created_at
    }
    reminders {
        string id PK
        string memo_id FK
        integer remind_at
        string status
        integer created_at
    }
\`\`\`

## テーブル定義

### 新規テーブル: reminders

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| id | TEXT | PK | 主キー（CUID） |
| memo_id | TEXT | NOT NULL, FK(memos.id) | 対象メモ |
| remind_at | INTEGER | NOT NULL | リマインダー日時（Unix timestamp） |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending / sent / cancelled |
| created_at | INTEGER | NOT NULL | 作成日時（Unix timestamp） |

## モデルコード

\`\`\`typescript
// src/db/schema.ts への追加

export const reminders = sqliteTable('reminders', {
  id: text('id').primaryKey(),
  memoId: text('memo_id').notNull().references(() => memos.id, { onDelete: 'cascade' }),
  remindAt: integer('remind_at', { mode: 'timestamp' }).notNull(),
  status: text('status', { enum: ['pending', 'sent', 'cancelled'] }).notNull().default('pending'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
\`\`\`

## マイグレーション

\`\`\`sql
CREATE TABLE reminders (
  id TEXT PRIMARY KEY,
  memo_id TEXT NOT NULL REFERENCES memos(id) ON DELETE CASCADE,
  remind_at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_reminders_remind_at ON reminders(remind_at) WHERE status = 'pending';
CREATE INDEX idx_reminders_memo_id ON reminders(memo_id);
\`\`\`

## インデックス

| テーブル | カラム | 種別 | 目的 |
|---------|-------|------|------|
| reminders | remind_at | 部分（status='pending'） | スケジューラの検索高速化 |
| reminders | memo_id | 通常 | メモ→リマインダーの参照高速化 |

## 型定義の変更

\`\`\`typescript
// src/types/memo.ts への追加

// Before:
interface Memo {
  id: string;
  content: string;
  createdAt: string;
}

// After:
interface Memo {
  id: string;
  content: string;
  createdAt: string;
  reminder?: Reminder;  // 追加
}

interface Reminder {
  id: string;
  memoId: string;
  remindAt: string;
  status: 'pending' | 'sent' | 'cancelled';
}
\`\`\`

## 設計決定事項

| 決定事項 | 理由 |
|---------|------|
| 1:1リレーション（memos → reminders） | スコープが単発リマインダーのみ。将来複数対応時にN:1に変更可 |
| statusカラムをenumで管理 | 通知の状態管理が必要。pending/sent/cancelledの3状態 |
| 部分インデックス（status='pending'） | スケジューラはpendingのみ検索するため |

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/db/schema.ts` | スキーマ定義 | 変更 |
| `src/types/memo.ts` | Memo型にreminder追加 | 変更 |
| `src/features/reminder/types.ts` | Reminder型定義 | 新規 |
```
