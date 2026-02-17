# 出力例: api-spec.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する api-spec.md の出力例。

```markdown
# API設計

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /api/reminders | リマインダー作成 |
| GET | /api/memos/:memoId/reminder | メモのリマインダー取得 |
| PATCH | /api/reminders/:id | リマインダー更新 |
| DELETE | /api/reminders/:id | リマインダー削除 |

## エンドポイント詳細

### `POST /api/reminders`

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

**エラー:**

| ステータス | コード | 説明 | 条件 |
|----------|--------|------|------|
| 400 | INVALID_DATE | 日時が不正 | 過去の日時を指定した場合 |
| 404 | MEMO_NOT_FOUND | メモが存在しない | memoIdが無効 |
| 409 | REMINDER_EXISTS | リマインダーが既に存在 | 同一メモに重複設定 |

### `GET /api/memos/:memoId/reminder`

**レスポンス (200):**

\`\`\`typescript
interface GetReminderResponse {
  reminder: ReminderResponse | null;
}
\`\`\`

### `PATCH /api/reminders/:id`

**リクエスト:**

\`\`\`typescript
interface UpdateReminderRequest {
  remindAt: string; // ISO 8601 datetime
}
\`\`\`

**レスポンス (200):** `ReminderResponse`

### `DELETE /api/reminders/:id`

**レスポンス:** 204 No Content

## 内部処理フロー

### `POST /api/reminders` の処理ステップ

1. リクエストボディのバリデーション（memoId, remindAt）
2. remindAt が未来日時であることを検証
3. memoId に対応するメモの存在確認
4. 既存リマインダーの重複チェック
5. reminders テーブルに INSERT
6. ReminderResponse を構築して返却

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/api/reminders.ts` | リマインダーAPIハンドラ | 新規 |
| `src/api/index.ts` | ルート登録 | 変更 |
| `src/types/reminder.ts` | リマインダー型定義 | 新規 |

## テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/__tests__/reminders.test.ts` | リマインダーCRUD API | unit |

### テストケース

\`\`\`typescript
describe('Reminders API', () => {
  it('正常にリマインダーを作成できること', async () => {
    // Arrange: 有効なメモIDと未来の日時
    // Act: POST /api/reminders
    // Assert: 201 + ReminderResponse
  });

  it('過去の日時で400を返すこと', async () => {
    // Arrange: 過去の日時
    // Act: POST /api/reminders
    // Assert: 400 + INVALID_DATE
  });

  it('存在しないメモで404を返すこと', async () => {
    // Arrange: 無効なmemoId
    // Act: POST /api/reminders
    // Assert: 404 + MEMO_NOT_FOUND
  });

  it('重複設定で409を返すこと', async () => {
    // Arrange: 既にリマインダーがあるメモ
    // Act: POST /api/reminders
    // Assert: 409 + REMINDER_EXISTS
  });
});
\`\`\`
```
