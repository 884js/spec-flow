# リサーチ: コンパクション発生時に plan.md ベースの実装を継続する方法

調査日: 2026-03-12
調査タイプ: 外部技術

## 調査ゴール

Claude Code のコンパクション（コンテキスト圧縮）が発生しても、plan.md に沿ったタスク実装を継続できるか。どう指示・設計すれば良いかを明らかにする。

## 調査結果

### コンパクションとは

- コンテキストウィンドウが上限の約 95-98% に達すると自動発生（出典: deepwiki.com）
- 会話履歴全体を AI が要約してサマリーブロックに置き換える
- 手動 `/compact` も可能。焦点を指定できる（例: `/compact Focus on the API changes`）

### コンパクション後に保持されるもの

- 直近のコード変更とファイル変更
- 進行中のタスクと現在の目標
- 確立されたコーディングパターン
- CLAUDE.md の内容（毎回読まれるため）
- Plan Mode の状態

### コンパクション後に失われるリスクがあるもの

- コンパクション時点で Read していなかった plan.md の詳細セクション
- 解決済みデバッグセッションの詳細
- セッション中の口頭での設計判断（ファイルに記録されていないもの）

### 核心的な発見

> "Plans survive auto-compression (they are on disk, not just in context)"

**ディスク上のファイルはコンパクションの影響を受けない。** plan.md / progress.md を Re-read すれば完全に復元できる。

### 現在の build スキルの脆弱ポイント

| 脆弱点 | 内容 | リスク |
|--------|------|--------|
| plan.md の初回1回読み | Step 0 で1回 Read するが、コンパクション後の再読み込みが「してよい」という弱い記述 | 仕様を見失う |
| 設計判断のコンテキスト依存 | 仕様矛盾検知で「後で対応」を選んだ判断がコンテキスト内のみ | 同じ矛盾で再度停止 |
| libs/ 調査結果の再参照なし | ライブラリ調査結果のコンパクション後の再読み込みフローなし | 調査済み情報の再調査 |

### 対策の比較

| 観点 | コンテキスト内に保持 | コンパクション後に再 Read |
|------|---------------------|-------------------------|
| コンパクション耐性 | 要約精度に依存（脆弱） | ファイルから完全復元（堅牢） |
| トークンコスト | 低 | 中（毎タスクで Read） |
| 実装計画の完整性 | 欠損リスクあり | 常に完全な仕様を参照可能 |

## 推奨・結論

### 対策1: タスク開始前の plan.md / progress.md 再読み込みを強制化

SKILL.md の Step 3 で「タスク開始前に progress.md を確認し、plan.md を再 Read する」を必須ステップにする（現在の「してよい」から「する」へ変更）。

### 対策2: progress.md の「次にやること」の粒度を上げる

コンパクション後に Claude が単独で再開できるレベル（"タスク#3: ○○ファイルの○○関数を修正する"）で記述。

### 対策3: CLAUDE.md に Compact Instructions を追加

```markdown
## Compact Instructions
When compacting, always preserve:
- The current feature name and plan.md path
- The list of completed/in-progress tasks from progress.md
- Any architectural decisions made during this session
```

3-5行以内に収めること（長すぎると無視される）。

## 次のステップ

- build スキルの plan.md 参照ロジックを「してよい」→「各タスク開始前に必ず Read する」に変更
- CLAUDE.md に Compact Instructions セクションを追加するかを検討
