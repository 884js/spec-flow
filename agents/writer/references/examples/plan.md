# 出力例: plan（リマインダー機能）

「メモアプリにリマインダー機能を追加する」という要求に対する plan の出力例。

```markdown
# リマインダー機能

## 概要

メモ利用者が、メモにリマインダーを設定し、指定した日時にプッシュ通知を受け取ってメモを見返せるようにする。メモを書いても見返すタイミングを逃してしまう課題を解決する。

## 確認事項

| # | 項目 | 根拠 | ステータス |
|---|------|------|-----------|
| 1 | ブラウザ Notification API の権限リクエストタイミング | 仕様ではプッシュ通知を使うが、権限リクエストのタイミング（初回設定時 or アプリ起動時）が未指定 | ⚠️要確認 |
| 2 | メモ削除時のリマインダー連動削除 | DB設計で CASCADE を採用。ユーザーへの確認ダイアログ表示の要否が未定義 | ❓要議論 |
| 3 | リマインダー日時のタイムゾーン | ユーザーのローカルタイムゾーンで設定・表示する前提 | ✅確認済み |

## 追加検討事項

| # | 観点 | 詳細 | 根拠 |
|---|------|------|------|
| 1 | メモ一覧のパフォーマンス | リマインダーJOINにより一覧取得が遅くなる可能性。現在のメモ一覧APIはJOINなしで10ms以下 | `src/api/memos.ts:L45-L60` |
| 2 | Service Worker の登録タイミング | プッシュ通知にはService Workerが必要だが、既存コードにSW登録処理がない | `src/app.tsx`（SW関連コードなし） |

## 関連プラン

| プラン | 関連 |
|--------|------|
| notification-system | 本機能の前提。通知基盤を提供 |
| memo-actions | 同じメモ編集画面のアクションバーを変更 |

## スコープ

### やること

- 単発リマインダー（1回限り）
- プッシュ通知（ブラウザ Notification API）
- メモ詳細画面からのリマインダー設定

### やらないこと

- 繰り返しリマインダー（毎日、毎週等）
- メール通知
- リマインダー一覧専用画面

## 受入条件

- [ ] AC-1: メモ編集画面からリマインダー日時を設定できる
- [ ] AC-2: 設定した日時にプッシュ通知が届く
- [ ] AC-3: 通知をタップするとメモの詳細画面に遷移する
- [ ] AC-4: リマインダー設定済みのメモにバッジが表示される
- [ ] AC-5: リマインダーの変更・削除ができる

## 非機能要件

- 認可: メモの所有者のみリマインダーを操作可能
- リマインダー日時は未来の日時のみ許可

## データフロー

### リマインダー設定フロー

```mermaid
sequenceDiagram
    participant User
    participant UI as メモ編集画面
    participant Server
    participant DB
    participant Scheduler as スケジューラ

    User->>UI: リマインダーアイコンタップ
    UI->>UI: 日時選択UIを表示
    User->>UI: 日時選択して確定
    UI->>Server: POST /api/reminders
    Server->>DB: INSERT reminder
    DB-->>Server: 保存結果
    Server-->>UI: 201 Created
    UI-->>User: バッジ表示

    Note over Scheduler: 指定日時到達
    Scheduler->>Server: 通知トリガー
    Server->>User: プッシュ通知送信
    User->>UI: 通知タップでメモ詳細画面に遷移
```

## バックエンド変更

### API設計

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/reminders` | リマインダー作成 |
| GET | `/api/reminders/:id` | リマインダー取得 |
| PUT | `/api/reminders/:id` | リマインダー更新 |
| DELETE | `/api/reminders/:id` | リマインダー削除 |

- 作成時の入力: `memoId`, `reminderAt`
- 取得時の出力: `id`, `memoId`, `reminderAt`, `status`（pending / sent / cancelled）
- 主要なエラーケース:
  - 過去の日時を指定した場合 → 400 Bad Request
  - 存在しないメモを指定した場合 → 404 Not Found
  - 同一メモに重複してリマインダーを設定した場合 → 409 Conflict

### 対象ファイル

- 新規: `src/api/reminders.ts` — リマインダーAPI実装
- 変更: `src/api/index.ts` — ルーティングにリマインダーAPIを追加

## DB変更

### データモデル

#### reminders テーブル

- 目的: メモに紐づくリマインダー情報を管理する
- 関係: memos テーブルと1対1の関係。メモ削除時にリマインダーも連動して削除（CASCADE）

| カラム | 型 | 制約 | デフォルト |
|--------|------|------|-----------|
| id | varchar(26) | PK | ULID自動生成 |
| memoId | varchar(26) | FK(memos.id), UNIQUE, NOT NULL | - |
| reminderAt | timestamp | NOT NULL | - |
| status | varchar(20) | NOT NULL | 'pending' |
| createdAt | timestamp | NOT NULL | now() |

- インデックス: `status = 'pending'` の部分インデックス（スケジューラの検索高速化）
- インデックス: `memoId` のユニークインデックス

### 対象ファイル

- 変更: `src/db/schema.ts` — リマインダーテーブル定義を追加
- 新規: マイグレーションファイル — テーブル作成とインデックス追加

## フロントエンド変更

### 画面・UI設計

- メモ詳細画面のアクションバーに「リマインダー設定」ボタンを追加
- ボタンタップで日時選択ポップオーバーを表示
- 日時選択後、確定でリマインダーを設定
- リマインダー設定済みのメモにはバッジ（日時表示付き）を表示
- 既存の「ブックマーク」ボタンと同じパターンで実装

### ワイヤーフレーム

#### リマインダー設定ポップオーバー

```
+------------------------------+
| リマインダーを設定     [x]    |
+------------------------------+
|                              |
|  日付: 2025/01/15            |
|  時刻: 14:00                 |
|                              |
|  [キャンセル]     [設定]      |
+------------------------------+
```

#### リマインダーバッジ

```
[bell 1/15 14:00]    // 通常サイズ
[bell]               // 小サイズ
```

### 対象ファイル

- 新規: `src/features/reminder/components/ReminderPicker.tsx` — 日時選択ポップオーバー
- 新規: `src/features/reminder/components/ReminderBadge.tsx` — バッジ表示
- 新規: `src/features/reminder/hooks/useReminder.ts` — リマインダーのデータ取得・操作フック
- 変更: `src/features/memo/components/MemoActions.tsx` — アクションバーにリマインダーボタン追加
- 変更: `src/features/memo/components/MemoCard.tsx` — バッジ表示追加

## 設計判断

| 判断事項 | 選択 | 理由 | 検討した代替案 |
|---------|------|------|--------------|
| メモとリマインダーの関係 | 1対1 | スコープが単発リマインダーのみ | 1対多（将来の複数リマインダー対応時に変更可） |
| 状態管理方式 | 3状態（pending/sent/cancelled） | 通知の送信状態を追跡する必要がある | 2状態（有効/無効）— キャンセルと送信済みの区別が必要 |
| 検索最適化 | pending のみの部分インデックス | スケジューラは pending のみ検索する | 全件インデックス — 不要なデータを含み非効率 |

## システム影響

### 影響範囲

- メモ編集画面: アクションバーにボタン追加
- メモカード: バッジ表示追加
- メモ削除: リマインダーの連動削除

### リスク

- メモ一覧取得時のリマインダーJOINによるパフォーマンス影響 → インデックスで対応
- ブラウザのNotification API非対応環境 → リマインダー設定のみ（通知なし）で対応

## 実装タスク

### 依存関係図

```mermaid
graph TD
    T1[#1 DBスキーマ追加] --> T2[#2 API実装]
    T1 --> T3[#3 型定義追加]
    T2 --> T4[#4 フック実装]
    T3 --> T4
    T4 --> T5[#5 UIコンポーネント実装]
    T5 --> T6[#6 既存画面への統合]
```

### タスク一覧

| # | タスク | 対象ファイル | 見積 | 依存 |
|---|--------|------------|------|------|
| 1 | DBスキーマにリマインダーテーブル追加 | `src/db/schema.ts` | S | - |
| 2 | リマインダーAPI実装 | `src/api/reminders.ts`, `src/api/index.ts` | M | #1 |
| 3 | 型定義追加 | `src/types/memo.ts`, `src/features/reminder/types.ts` | S | #1 |
| 4 | useReminderフック実装 | `src/features/reminder/hooks/useReminder.ts` | S | #2, #3 |
| 5 | ReminderPicker, ReminderBadge実装 | `src/features/reminder/components/` | L | #4 |
| 6 | MemoActions, MemoCardに統合 | `src/features/memo/components/` | M | #5 |

> 見積基準: S(〜1h), M(1-3h), L(3h〜)

## テスト方針

### トレーサビリティ

| 受入条件 | 自動テスト | 手動検証 |
|---------|-----------|---------|
| AC-1 | #1, #3 | MV-1 |
| AC-2 | - | MV-2 |
| AC-3 | - | MV-3 |
| AC-4 | #3 | MV-1 |
| AC-5 | #2, #3 | MV-4, MV-5 |

### 自動テスト

| # | テスト | 種別 | 対象 |
|---|--------|------|------|
| 1 | リマインダーCRUD APIの正常系・異常系 | unit | `src/api/reminders.ts` |
| 2 | useReminderフックの状態管理 | unit | `src/features/reminder/hooks/useReminder.ts` |
| 3 | ReminderPicker・ReminderBadgeの表示・操作 | unit | `src/features/reminder/components/` |

### ビルド確認

```bash
npm run typecheck  # 型チェック
npm run lint       # Lint
npm run test       # テスト
npm run build      # ビルド
```

### 手動検証チェックリスト

- [ ] MV-1: メモ詳細画面でリマインダーアイコンをタップし、日時選択UIが表示されること。日時を設定するとバッジが表示されること
- [ ] MV-2: 設定した日時にプッシュ通知が届くこと
- [ ] MV-3: 通知をタップするとメモの詳細画面に遷移すること
- [ ] MV-4: 設定済みリマインダーの日時を変更できること
- [ ] MV-5: リマインダーを削除するとバッジが消えること
- [ ] MV-6: 過去の日時を設定しようとするとエラーメッセージが表示されること
```
