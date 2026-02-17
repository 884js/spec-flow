# 出力例: README.md（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する README.md の出力例。

```markdown
# リマインダー機能

> メモに日時指定のリマインダーを設定し、プッシュ通知で知らせる機能

## ステータス

Draft

## 背景・課題

ユーザーがメモを書いても、見返すタイミングを逃してしまう。
「後で確認する」メモが埋もれていくのが現状の課題。

## ユーザーストーリー

- As a メモ利用者, I want メモにリマインダーを設定したい, so that 指定した日時に通知を受け取り、メモを見返せる
- As a メモ利用者, I want 設定済みリマインダーを一覧で確認したい, so that 今後のリマインダーを管理できる

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

## データフロー

### シーケンス図

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

## 設計ドキュメント

| ドキュメント | 説明 | ステータス |
|---|---|---|
| [API設計](./api-spec.md) | リマインダーCRUD API | 完了 |
| [DB設計](./db-spec.md) | remindersテーブル追加 | 完了 |
| [フロントエンド設計](./frontend-spec.md) | ReminderPicker、ReminderBadge | 完了 |
| [実装計画](./implementation-plan.md) | 実装タスク、影響範囲、テスト方針 | 完了 |

## 生成情報

- 生成日: 2025-01-15
- 対象プロジェクト: memo-app
```
