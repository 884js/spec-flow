# 出力例: implementation-plan.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する implementation-plan.md の出力例。

```markdown
# 実装計画

## 参照ドキュメント

| ドキュメント | 説明 |
|---|---|
| [要件定義](./README.md) | 要件、データフロー、スコープ |
| [API設計](./api-spec.md) | リマインダーCRUD API |
| [DB設計](./db-spec.md) | remindersテーブル追加 |
| [フロントエンド設計](./frontend-spec.md) | ReminderPicker、ReminderBadge |

## 実装タスク

| # | タスク | 依存 | 対象ファイル | 見積 |
|---|-------|------|------------|------|
| 1 | DBスキーマにremindersテーブル追加 | - | `src/db/schema.ts` | S |
| 2 | リマインダーAPI実装 | #1 | `src/api/reminders.ts`, `src/api/index.ts` | M |
| 3 | 型定義追加 | #1 | `src/types/memo.ts`, `src/features/reminder/types.ts` | S |
| 4 | useReminderフック実装 | #2, #3 | `src/features/reminder/hooks/useReminder.ts` | S |
| 5 | ReminderPicker, ReminderBadge実装 | #4 | `src/features/reminder/components/` | L |
| 6 | MemoActions, MemoCardに統合 | #5 | `src/features/memo/components/` | M |

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

## 影響範囲・リスク

### 影響を受ける既存機能

| 既存機能 | 影響内容 | リスク | 対策 |
|---------|---------|-------|------|
| MemoEditor | アクションバーにボタン追加 | 低 | 既存BookmarkButtonと同パターン |
| MemoCard | バッジ表示追加 | 低 | オプショナル表示のため影響最小 |
| メモ削除 | CASCADE削除でリマインダーも削除 | 中 | 外部キー制約で自動対応 |

### 後方互換性

- Memo型にreminder?: Reminderを追加（オプショナル）のため既存コードに影響なし
- 既存APIに変更なし、新規エンドポイントの追加のみ

### パフォーマンスへの影響

- メモ一覧取得時にremindersテーブルをJOIN → idx_reminders_memo_idインデックスで対応
- pending状態のリマインダーのみスケジューラが検索 → 部分インデックスで対応

## テスト方針

### 自動テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/__tests__/reminders.test.ts` | リマインダーCRUD API | unit |
| `src/features/reminder/__tests__/useReminder.test.ts` | フックの状態管理 | unit |
| `src/features/reminder/__tests__/ReminderPicker.test.tsx` | 日時選択UI | unit |

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
```
