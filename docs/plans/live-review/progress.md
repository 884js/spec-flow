---
plan: "./plan.md"
feature: "live-review"
started: 2026-03-13
updated: 2026-03-13
mode: single
docs:
  - "README.md"
  - "skills/README.md"
---

# live-review — 実装進捗

## 現在の状況

plan.md の作成が完了し、実装準備が整った段階。まだ実装には着手していない。

## 次にやること

タスク #1（POST /api/done のエンドポイント分離）と #2（GET /api/plan/status 追加）、#3（ボタン分離）を並行して着手する。

## タスク進捗

| # | タスク | 対象ファイル | 見積 | PR | リスク | 状態 |
|---|--------|------------|------|-----|--------|------|
| 1 | POST /api/done を POST /api/comments + POST /api/finish に分離、stdout イベント出力追加 | `scripts/annotation-viewer/server.py` | M | - | - | - |
| 2 | GET /api/plan/status エンドポイント追加 | `scripts/annotation-viewer/server.py` | S | - | - | - |
| 3 | ボタン分離（「コメントを送信」「レビュー完了」） | `scripts/annotation-viewer/viewer.html` | S | - | - | - |
| 4 | ポーリングによる自動リロード機能追加（setInterval + /api/plan/status） | `scripts/annotation-viewer/viewer.html` | M | - | - | - |
| 5 | コメント送信後の「修正中...」スピナー表示 + リロード後のコメントクリア | `scripts/annotation-viewer/viewer.html` | S | - | - | - |
| 6 | Step 4-c のループ制御をイベントベースに変更 | `skills/spec/SKILL.md` | M | - | - | - |
| 7 | 統合テスト | - | M | - | - | - |

> タスク定義の詳細は [plan.md](./plan.md) を参照

## デリバリープラン

分割なし（1 PR）

## ブランチ・PR

| PR | ブランチ | PR URL | 状態 |
|----|---------|--------|------|
| - | - | - | - |

## 作業ログ

| 日時 | 内容 |
|------|------|
| 2026-03-13 | progress.md 作成、実装準備完了 |
