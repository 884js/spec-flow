# 出力例: plan.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する plan.md の出力例。

```markdown
---
title: "feat: リマインダー機能"
status: ready
date: 2025-01-15
---

# リマインダー機能

## 概要

メモに日時指定のリマインダーを設定し、プッシュ通知で知らせる機能を追加する。
ユーザーがメモを書いても見返すタイミングを逃してしまう問題を解決し、指定した日時に通知を受け取ってメモを確認できるようにする。

**ユーザーストーリー**:
- As a メモ利用者, I want メモにリマインダーを設定したい, so that 指定した日時に通知を受け取り、メモを見返せる
- As a メモ利用者, I want 設定済みリマインダーを一覧で確認したい, so that 今後のリマインダーを管理できる

## 課題と背景

**現状**: ユーザーがメモを書いても、見返すタイミングを逃してしまう。「後で確認する」メモが埋もれていくのが課題。

**目指す状態**: メモに日時を指定してリマインダーを設定でき、指定日時にプッシュ通知が届く。通知タップでメモ詳細に遷移できる。

## 受入条件

- [ ] メモ編集画面からリマインダー日時を設定できる
- [ ] 設定した日時にプッシュ通知が届く
- [ ] 通知をタップするとメモの詳細画面に遷移する
- [ ] リマインダー設定済みのメモにバッジが表示される
- [ ] リマインダーの変更・削除ができる

## スコープ

### 対象

- 単発リマインダー（1回限り）
- プッシュ通知（ブラウザ Notification API）
- メモ詳細画面からのリマインダー設定

### 対象外

- 繰り返しリマインダー（毎日、毎週等）
- メール通知
- リマインダー一覧専用画面

## 提案する解決策

### データフロー

#### リマインダー設定フロー

\`\`\`mermaid
sequenceDiagram
    participant User
    participant MemoEditor
    participant API as /api/reminders
    participant DB
    participant Scheduler

    User->>MemoEditor: リマインダーアイコンタップ
    MemoEditor->>MemoEditor: DateTimePicker表示
    User->>MemoEditor: 日時選択 + 確定
    MemoEditor->>API: POST /api/reminders
    API->>DB: INSERT INTO reminders
    DB-->>API: reminder record
    API-->>MemoEditor: 201 Created
    MemoEditor-->>User: バッジ表示

    Note over Scheduler: 指定日時到達
    Scheduler->>API: トリガー
    API->>User: Push Notification
    User->>MemoEditor: 通知タップ → メモ詳細画面
\`\`\`

### バックエンド変更

#### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /api/reminders | リマインダー作成 |
| GET | /api/memos/:memoId/reminder | メモのリマインダー取得 |
| PATCH | /api/reminders/:id | リマインダー更新 |
| DELETE | /api/reminders/:id | リマインダー削除 |

#### エンドポイント詳細

##### `POST /api/reminders`

**リクエスト:**

\`\`\`typescript
interface CreateReminderRequest {
  memoId: string;
  remindAt: string; // ISO 8601 datetime
}
\`\`\`

**レスポンス (201):**

\`\`\`typescript
interface ReminderResponse {
  id: string;
  memoId: string;
  remindAt: string;
  status: 'pending' | 'sent' | 'cancelled';
  createdAt: string;
}
\`\`\`

**認証・認可:**
- 認証: 必要（既存の認証ミドルウェア）
- 認可: メモの所有者のみ

**バリデーション:**

| フィールド | ルール | エラーメッセージ |
|-----------|--------|---------------|
| memoId | 必須、存在するメモのID | メモが見つかりません |
| remindAt | 必須、ISO 8601形式、未来の日時 | 未来の日時を指定してください |

**エラー:**

| ステータス | コード | 説明 | 条件 |
|----------|--------|------|------|
| 400 | INVALID_DATE | 日時が不正 | 過去の日時を指定した場合 |
| 404 | MEMO_NOT_FOUND | メモが存在しない | memoIdが無効 |
| 409 | REMINDER_EXISTS | リマインダーが既に存在 | 同一メモに重複設定 |

##### `GET /api/memos/:memoId/reminder`

**レスポンス (200):**

\`\`\`typescript
interface GetReminderResponse {
  reminder: ReminderResponse | null;
}
\`\`\`

##### `PATCH /api/reminders/:id`

**リクエスト:**

\`\`\`typescript
interface UpdateReminderRequest {
  remindAt: string; // ISO 8601 datetime
}
\`\`\`

**レスポンス (200):** `ReminderResponse`

##### `DELETE /api/reminders/:id`

**レスポンス:** 204 No Content

#### 内部処理フロー

##### `POST /api/reminders` の処理ステップ

1. リクエストボディのバリデーション（memoId, remindAt）
2. remindAt が未来日時であることを検証
3. memoId に対応するメモの存在確認
4. 既存リマインダーの重複チェック
5. reminders テーブルに INSERT
6. ReminderResponse を構築して返却

### DB変更

#### ER図

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

#### テーブル定義

##### 新規テーブル: reminders

| カラム | 型 | 制約 | 説明 |
|-------|-----|------|------|
| id | TEXT | PK | 主キー（CUID） |
| memo_id | TEXT | NOT NULL, FK(memos.id) | 対象メモ |
| remind_at | INTEGER | NOT NULL | リマインダー日時（Unix timestamp） |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending / sent / cancelled |
| created_at | INTEGER | NOT NULL | 作成日時（Unix timestamp） |

#### モデルコード

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

#### マイグレーション

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

#### インデックス

| テーブル | カラム | 種別 | 目的 |
|---------|-------|------|------|
| reminders | remind_at | 部分（status='pending'） | スケジューラの検索高速化 |
| reminders | memo_id | 通常 | メモ→リマインダーの参照高速化 |

#### 型定義の変更

\`\`\`typescript
// src/types/memo.ts への変更

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

#### 設計決定事項

| 決定事項 | 理由 |
|---------|------|
| 1:1リレーション（memos → reminders） | スコープが単発リマインダーのみ。将来複数対応時にN:1に変更可 |
| statusカラムをenumで管理 | 通知の状態管理が必要。pending/sent/cancelledの3状態 |
| 部分インデックス（status='pending'） | スケジューラはpendingのみ検索するため |

### フロントエンド変更

#### コンポーネントツリー

\`\`\`mermaid
graph TD
    A[MemoDetailPage] --> B[MemoEditor]
    A --> C[MemoActions]
    C --> D[ReminderButton]
    D --> E[ReminderPicker]
    E --> F[DateTimePicker]
    B --> G[ReminderBadge]
\`\`\`

#### 新規コンポーネント

##### `ReminderPicker`

**パス**: `src/features/reminder/components/ReminderPicker.tsx`

**役割**: リマインダーの日時を選択するポップオーバーUI

**Props:**

\`\`\`typescript
interface ReminderPickerProps {
  memoId: string;
  currentReminder?: Reminder;
  onSet: (remindAt: Date) => void;
  onCancel: () => void;
}
\`\`\`

**状態管理:**

\`\`\`typescript
const [selectedDate, setSelectedDate] = useState<Date>(
  currentReminder ? new Date(currentReminder.remindAt) : addHours(new Date(), 1)
);
\`\`\`

**イベントハンドラ:**

\`\`\`typescript
const handleConfirm = async () => {
  // 1. selectedDate が未来日時か検証
  // 2. onSet(selectedDate) を呼び出し
};
\`\`\`

**UIワイヤーフレーム:**

\`\`\`
┌──────────────────────────────┐
│ リマインダーを設定     [×]    │
├──────────────────────────────┤
│                              │
│  📅 2025/01/15               │
│  🕐 14:00                    │
│                              │
│  ┌──────────┐ ┌──────────┐  │
│  │ キャンセル │ │   設定   │  │
│  └──────────┘ └──────────┘  │
└──────────────────────────────┘
\`\`\`

##### `ReminderBadge`

**パス**: `src/features/reminder/components/ReminderBadge.tsx`

**役割**: リマインダー設定済みメモにバッジを表示

**Props:**

\`\`\`typescript
interface ReminderBadgeProps {
  reminder: Reminder;
  size?: 'sm' | 'md';
}
\`\`\`

**UIワイヤーフレーム:**

\`\`\`
[🔔 1/15 14:00]    // size="md"
[🔔]               // size="sm"
\`\`\`

#### Hooks

##### `useReminder`

**パス**: `src/features/reminder/hooks/useReminder.ts`

\`\`\`typescript
function useReminder(memoId: string): {
  reminder: Reminder | undefined;
  isLoading: boolean;
  error: Error | null;
  createReminder: (remindAt: Date) => Promise<void>;
  updateReminder: (id: string, remindAt: Date) => Promise<void>;
  deleteReminder: (id: string) => Promise<void>;
}
\`\`\`

#### 既存コンポーネントの変更

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `src/features/memo/components/MemoActions.tsx` | JSX return内（L45付近） | `ReminderButton` コンポーネントを追加 |
| `src/features/memo/components/MemoCard.tsx` | タイトル横（L28付近） | `ReminderBadge` を追加表示 |

**パターン参照**: 「既存の `BookmarkButton`（`src/features/memo/components/MemoActions.tsx` L32）のパターンに倣う」

#### エッジケース

| ケース | 対応 |
|-------|------|
| リマインダー未設定 | ReminderBadge非表示、ReminderButtonは「設定」ラベル |
| 過去の日時を選択 | バリデーションエラー表示、設定ボタン無効化 |
| API通信エラー | トースト通知でエラー表示、リトライ可能 |

## システム影響

### 影響を受ける既存機能

| 既存機能 | 影響内容 | リスク | 対策 |
|---------|---------|-------|------|
| MemoEditor | アクションバーにボタン追加 | 低 | 既存BookmarkButtonと同パターン |
| MemoCard | バッジ表示追加 | 低 | オプショナル表示のため影響最小 |
| メモ削除 | CASCADE削除でリマインダーも削除 | 中 | 外部キー制約で自動対応 |

### 後方互換性

- Memo型にreminder?: Reminderを追加（オプショナル）のため既存コードに影響なし
- 既存APIに変更なし、新規エンドポイントの追加のみ

### パフォーマンス

- メモ一覧取得時にremindersテーブルをJOIN → idx_reminders_memo_idインデックスで対応
- pending状態のリマインダーのみスケジューラが検索 → 部分インデックスで対応
- ReminderBadge は React.memo でメモ化（メモ一覧で大量レンダリングされるため）

### セキュリティ

- 認証: 既存の認証ミドルウェアを使用
- 認可: メモの所有者のみリマインダーを操作可能（`ensureOwner` パターン）
- 入力バリデーション: remind_at は未来の日時のみ許可

### デプロイメント

#### DBマイグレーション

| マイグレーション | ロールバック可否 | 手順 |
|---------------|---------------|------|
| create_reminders_table | 可 | DROP TABLE reminders |

#### 環境変数・設定変更

新規の環境変数なし。

#### デプロイ順序

通常フローに従う（マイグレーション → アプリデプロイ）

## 実装タスク

| # | タスク | 対象ファイル | 見積 |
|---|-------|------------|------|
| 1 | DBスキーマにremindersテーブル追加 | `src/db/schema.ts` | S |
| 2 | リマインダーAPI実装 | `src/api/reminders.ts`, `src/api/index.ts` | M |
| 3 | 型定義追加 | `src/types/memo.ts`, `src/features/reminder/types.ts` | S |
| 4 | useReminderフック実装 | `src/features/reminder/hooks/useReminder.ts` | S |
| 5 | ReminderPicker, ReminderBadge実装 | `src/features/reminder/components/` | L |
| 6 | MemoActions, MemoCardに統合 | `src/features/memo/components/` | M |

### 依存関係図

\`\`\`mermaid
graph LR
    T1[1: Schema] --> T2[2: API]
    T1 --> T3[3: Types]
    T2 --> T4[4: Hook]
    T3 --> T4
    T4 --> T5[5: Components]
    T5 --> T6[6: Integration]
\`\`\`

## テスト方針

### 自動テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/__tests__/reminders.test.ts` | リマインダーCRUD API | unit |
| `src/features/reminder/__tests__/useReminder.test.ts` | フックの状態管理 | unit |
| `src/features/reminder/__tests__/ReminderPicker.test.tsx` | 日時選択UI | unit |

### 統合テスト

| テストシナリオ | カバー範囲 | 既存フロー影響 |
|-------------|---------|-------------|
| メモ作成→リマインダー設定→通知受信 | API + スケジューラ連携 | メモ作成フローに影響なし |
| メモ削除時のリマインダーCASCADE削除 | DB外部キー制約 | メモ削除フローに追加動作 |

### 手動検証チェックリスト

- [ ] メモ詳細画面でリマインダーアイコンをタップ → DateTimePickerが表示される
- [ ] 未来の日時を選択して設定 → バッジが表示される
- [ ] 設定済みリマインダーを変更 → 新しい日時に更新される
- [ ] リマインダーを削除 → バッジが消える
- [ ] 過去の日時を設定 → エラーメッセージが表示される

### ビルド確認

\`\`\`bash
npm run typecheck  # 型チェック
npm run lint       # Lint
npm run test       # テスト
npm run build      # ビルド
\`\`\`

## リスクと依存関係

| リスク | 影響度 | 軽減策 |
|-------|-------|-------|
| ブラウザのNotification API対応 | 中 | 非対応ブラウザではリマインダー設定のみ（通知なし） |
| メモ一覧のJOINパフォーマンス | 低 | idx_reminders_memo_idインデックスで対応 |

## フィードバックログ

| # | 日付 | 種別 | 内容 | 対応 |
|---|------|------|------|------|
| - | - | - | - | - |
```
