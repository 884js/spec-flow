# Brownfield検証（既存コード影響分析） — 最終仕様（Result）

> 生成日: 2026-03-13
> 検証モード: フル検証

## 機能概要

既存コードとの統合リスクを明示的に検証する Brownfield 検証機能を実装した。analyzer / verifier の出力フォーマット拡張により「既存コード影響分析」と「既存コード副作用」分類を追加し、spec / check スキルの検証観点にも既存コード影響の提示・検証を組み込んだ。

## 仕様からの変更点

plan.md 通りに実装。変更なし。

> Info: hooks/hooks.json の空化と hooks/skill-tracker.sh の削除は plan.md のスコープ外だが、debug 調査に基づく意図的な廃止であり、Brownfield 検証機能への影響はない。

## ロジック

### 仕様

- `/spec` 実行時に analyzer が既存コードのパターンを調査し「既存コード影響分析」テーブルを生成する
- 影響分析テーブルには対象ファイル・影響内容・リスク・信頼度ラベル（確認済み/推測）を含む
- spec の方向性サマリでリスク「高」の影響箇所をユーザーに提示する（リスク高がなければ省略）
- `/check` 実行時に verifier が「既存コード副作用」分類で仕様と実装の不一致を検出する

### Brownfield検証フロー

```mermaid
flowchart TD
    A[/spec 実行] --> B[analyzer: 既存コードパターン調査]
    B --> C[既存コード影響分析テーブル生成]
    C --> D{リスク高の影響あり?}
    D -- Yes --> E[方向性サマリにリスク高を提示]
    D -- No --> F[方向性サマリ通常表示]
    E --> G[ユーザーが方向性承認]
    F --> G
    G --> H[plan.md 生成]
```

### 既存コード副作用検証フロー

```mermaid
flowchart TD
    A[/check 実行] --> B[verifier: 仕様vs実装 突合]
    B --> C[既存コード副作用チェック]
    C --> D{副作用あり?}
    D -- Yes --> E[既存コード副作用として不一致報告]
    D -- No --> F[副作用なしとして記録]
    E --> G[result.md に結果出力]
    F --> G
```

## 受入条件

| # | 受入条件 | 判定 | 備考 |
|---|---------|------|------|
| AC-1 | `/spec` 実行時に analyzer の出力に「既存コード影響分析」テーブルが含まれる | PASS | `agents/analyzer/references/formats/output.md` L122-129 に追加済み |
| AC-2 | spec の Step 3 でリスク「高」の影響箇所がユーザーに提示される | PASS | `skills/spec/SKILL.md` L165 に追加済み。リスク高の場合のみ提示、なければ省略 |
| AC-3 | `/check` 実行時に verifier が「既存コード副作用」分類で不一致を検出できる | PASS | `agents/verifier/references/formats/output.md` L24 + `skills/check/SKILL.md` L107 に追加済み |
