---
plan: "./plan.md"
feature: "rich-markdown-preview"
started: 2026-03-08
updated: 2026-03-08
mode: single
docs:
  - "docs/plans/rich-markdown-preview/research.md"
  - "docs/plans/annotation-cycle/plan.md"
---

# rich-markdown-preview — 実装進捗

## 現在の状況

全タスク完了。PR 作成待ち。

## 次にやること

PR を作成してマージする。

## タスク進捗

| # | タスク | 対象ファイル | 見積 | PR | リスク | 状態 |
|---|--------|------------|------|-----|--------|------|
| 1 | CDN リンク追加（github-markdown-css, highlight.js 本体・テーマ）+ highlight.js テーマの media 属性設定 | `scripts/annotation-viewer/viewer.html` | S | - | - | ✓ |
| 2 | `.content` に `.markdown-body` クラス追加 + 独自マークダウン CSS 削除 + 共存調整 | `scripts/annotation-viewer/viewer.html` | S | - | - | ✓ |
| 3 | ダークモード CSS 変数・独自 UI のダーク対応追加 | `scripts/annotation-viewer/viewer.html` | M | - | - | ✓ |
| 4 | JS: `loadPlan()` 内で mermaid 変換後に `hljs.highlightAll()` を呼び出す処理を追加 | `scripts/annotation-viewer/viewer.html` | S | - | - | ✓ |
| 5 | 動作確認: シンタックスハイライト、mermaid 描画、コメント UI、差分ハイライト、ダーク/ライト切替 | `scripts/annotation-viewer/viewer.html` | M | - | - | ✓ |

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
| 2026-03-08 | progress.md 作成、実装開始準備完了 |
