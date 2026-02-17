# 出力例: frontend-spec.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する frontend-spec.md の出力例。

```markdown
# フロントエンド設計

## コンポーネントツリー

\`\`\`mermaid
graph TD
    A[MemoDetailPage] --> B[MemoEditor]
    A --> C[MemoActions]
    C --> D[ReminderButton]
    D --> E[ReminderPicker]
    E --> F[DateTimePicker]
    B --> G[ReminderBadge]
\`\`\`

## 新規コンポーネント

### `ReminderPicker`

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

### `ReminderBadge`

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

## Hooks

### `useReminder`

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

## 既存コンポーネントの変更

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `src/features/memo/components/MemoActions.tsx` | JSX return内（L45付近） | `ReminderButton` コンポーネントを追加 |
| `src/features/memo/components/MemoCard.tsx` | タイトル横（L28付近） | `ReminderBadge` を追加表示 |

**パターン参照**: 「既存の `BookmarkButton`（`src/features/memo/components/MemoActions.tsx` L32）のパターンに倣う」

## エッジケース

| ケース | 対応 |
|-------|------|
| リマインダー未設定 | ReminderBadge非表示、ReminderButtonは「設定」ラベル |
| 過去の日時を選択 | バリデーションエラー表示、設定ボタン無効化 |
| API通信エラー | トースト通知でエラー表示、リトライ可能 |

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/features/reminder/components/ReminderPicker.tsx` | 日時選択UI | 新規 |
| `src/features/reminder/components/ReminderBadge.tsx` | バッジ表示 | 新規 |
| `src/features/reminder/hooks/useReminder.ts` | リマインダーCRUDフック | 新規 |
| `src/features/reminder/types.ts` | 型定義 | 新規 |
| `src/features/memo/components/MemoActions.tsx` | アクションバー | 変更 |
| `src/features/memo/components/MemoCard.tsx` | メモカード | 変更 |

## テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/features/reminder/__tests__/ReminderPicker.test.tsx` | 日時選択・バリデーション | unit |
| `src/features/reminder/__tests__/ReminderBadge.test.tsx` | バッジ表示・サイズ切替 | unit |
| `src/features/reminder/__tests__/useReminder.test.ts` | フックの状態管理 | unit |
```
