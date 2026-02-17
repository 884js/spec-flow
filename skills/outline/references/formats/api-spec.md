# api-spec.md フォーマット定義

API設計の全情報を1ファイルに自己完結させる。バックエンド開発者がこのファイルだけで実装できることが目標。

## テンプレート

```markdown
# API設計

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /api/{resource} | {説明} |
| GET | /api/{resource}/:id | {説明} |
| PATCH | /api/{resource}/:id | {説明} |
| DELETE | /api/{resource}/:id | {説明} |

## エンドポイント詳細

### `POST /api/{resource}`

**リクエスト:**

\`\`\`typescript
interface CreateXxxRequest {
  field1: string;
  field2: number;
  optionalField?: boolean;
}
\`\`\`

**レスポンス (201):**

\`\`\`typescript
interface CreateXxxResponse {
  id: string;
  field1: string;
  createdAt: string; // ISO 8601
}
\`\`\`

**エラー:**

| ステータス | コード | 説明 | 条件 |
|----------|--------|------|------|
| 400 | INVALID_INPUT | 入力値が不正 | {具体的な条件} |
| 404 | NOT_FOUND | リソースが存在しない | {具体的な条件} |
| 409 | CONFLICT | 競合 | {具体的な条件} |

## 内部処理フロー

### `POST /api/{resource}` の処理ステップ

1. リクエストバリデーション
2. 認証・認可チェック
3. ビジネスロジック実行
4. DB操作
5. レスポンス構築

## ファイル構成

| ファイル | 役割 | 操作 |
|---------|------|------|
| `src/api/{resource}.ts` | ハンドラ | 新規 |
| `src/api/index.ts` | ルート登録 | 変更 |
| `src/types/{resource}.ts` | 型定義 | 新規 |

## テスト

| テストファイル | テスト内容 | 種別 |
|-------------|---------|------|
| `src/__tests__/{resource}.test.ts` | CRUD API | unit |

### テストケース

\`\`\`typescript
describe('{resource} API', () => {
  it('正常に作成できること', async () => {
    // Arrange: {前提条件}
    // Act: POST /api/{resource}
    // Assert: 201 + レスポンスボディ検証
  });

  it('不正な入力で400を返すこと', async () => {
    // Arrange: {不正な入力}
    // Act: POST /api/{resource}
    // Assert: 400 + INVALID_INPUT
  });
});
\`\`\`
```

## 記述ルール

- TypeScript interface でリクエスト/レスポンス型を定義（プロジェクトの既存型を参照・拡張）
- エラーコードはマシンリーダブルなコード文字列を付与
- 内部処理フローはステップ形式で記述
- ファイル構成と操作（新規/変更/削除）を明記
- テストケースはArrange/Act/Assert形式
- 認証・認可の要件がある場合は明記
