# frontend-spec.md フォーマット定義

フロントエンド設計の全情報を1ファイルに自己完結させる。フロントエンド開発者がこのファイルだけで実装できることが目標。

## テンプレート

```markdown
# フロントエンド設計

## コンポーネントツリー

\`\`\`mermaid
graph TD
    A[PageComponent] --> B[HeaderSection]
    A --> C[MainContent]
    C --> D[ItemList]
    C --> E[ActionPanel]
    D --> F[ItemCard]
\`\`\`

## 新規コンポーネント

### `XxxComponent`

**パス**: `src/features/{feature}/components/XxxComponent.tsx`

**役割**: {このコンポーネントが何をするか}

**Props:**

\`\`\`typescript
interface XxxComponentProps {
  prop1: string;
  prop2: number;
  onAction: (id: string) => void;
  className?: string;
}
\`\`\`

**状態管理:**

\`\`\`typescript
// ローカル状態
const [isOpen, setIsOpen] = useState(false);

// カスタムフック（既存の useYyy と同じパターン）
const { data, isLoading, mutate } = useXxx(params);
\`\`\`

**イベントハンドラ:**

\`\`\`typescript
const handleSubmit = async () => {
  // 1. フォームバリデーション
  // 2. API呼び出し（POST /api/xxx）
  // 3. 成功: 状態更新 + トースト通知
  // 4. 失敗: エラー表示
};
\`\`\`

**UIワイヤーフレーム:**

\`\`\`
┌─────────────────────────────────┐
│ Header          [Close Button]  │
├─────────────────────────────────┤
│                                 │
│  ┌──────┐  Title text           │
│  │ Icon │  Description          │
│  └──────┘  [Primary Action]     │
│                                 │
├─────────────────────────────────┤
│ Footer status    [Cancel] [OK]  │
└─────────────────────────────────┘
\`\`\`

## Hooks

### `useXxx`

**パス**: `src/features/{feature}/hooks/useXxx.ts`

\`\`\`typescript
function useXxx(params: XxxParams): {
  data: XxxData | undefined;
  isLoading: boolean;
  error: Error | null;
  mutate: (input: CreateXxxInput) => Promise<void>;
}
\`\`\`

## 既存コンポーネントの変更

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `src/components/Xxx.tsx` | `handleAction`関数内（L{行番号}付近） | {具体的な変更内容} |
| `src/features/yyy/Zzz.tsx` | JSX return部（L{行番号}付近） | {新しいコンポーネントの追加} |

**パターン参照**: 「既存の `{ExistingComponent}`（`{ファイルパス}`）のパターンに倣う」

## エッジケース

| ケース | 対応 |
|-------|------|
| {例: データ0件} | {例: EmptyStateコンポーネントを表示} |
| {例: ネットワークエラー} | {例: リトライボタン付きエラー表示} |
| {例: 長いテキスト} | {例: truncate + ツールチップ} |

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/features/{feature}/components/Xxx.tsx` | メインコンポーネント | 新規 |
| `src/features/{feature}/hooks/useXxx.ts` | データフェッチフック | 新規 |
| `src/features/{feature}/types.ts` | 型定義 | 新規 |

## テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/features/{feature}/__tests__/Xxx.test.tsx` | コンポーネントレンダリング | unit |
| `src/features/{feature}/__tests__/useXxx.test.ts` | フックの状態管理 | unit |
```

## 記述ルール

- Props型はTypeScript interfaceで定義
- 状態管理は具体的なhooksのコードを記述
- イベントハンドラはステップの概要をコメントで記述
- ASCIIワイヤーフレームは必須（テキストベースで表現）
- コンポーネントツリーはMermaidで可視化
- 既存コンポーネントの変更は行番号を含める
- 「既存のXのパターンに倣う」形式で既存実装を参照
- エッジケースを明記
- api-spec.md のレスポンス型と Props型の整合性を保つこと
