# カスケード影響マップ

仕様書ドキュメントの修正時に、どのドキュメントに影響が波及するかを定義する。

## ドキュメント間の依存関係

```
README.md (要件+データフロー) ─→ api-spec, db-spec, frontend-spec
api-spec   ─→ db-spec(型対応), frontend-spec(API呼び出し)
db-spec    ─→ api-spec(型対応), frontend-spec(型参照)
frontend-spec ─→ (他への影響小)
implementation-plan.md ─→ (他への影響小、全ドメインdocの統合情報)
```

## 影響マップ

| 修正元 | 必ず確認 | 確認推奨 |
|-------|---------|---------|
| README.md（要件） | api-spec, db-spec, frontend-spec | implementation-plan.md |
| README.md（データフロー） | api-spec | db-spec, frontend-spec |
| api-spec | db-spec, frontend-spec | implementation-plan.md |
| db-spec | api-spec, frontend-spec | implementation-plan.md |
| frontend-spec | - | implementation-plan.md |

## 影響の分類基準

- **必ず確認**: 型定義・データ構造の整合性に直接影響する。確認なしでは矛盾が生じる可能性が高い
- **確認推奨**: implementation-plan.md（タスク、影響範囲、テスト）への反映。修正内容次第では更新不要な場合もある

## 典型的なカスケードパターン

### パターン1: DB変更（db-spec 起点）
```
db-spec 修正
  → api-spec: リクエスト/レスポンス型の変更
  → frontend-spec: Props型の変更
  → implementation-plan.md: 実装タスク・テスト方針の更新
```

### パターン2: API追加/変更（api-spec 起点）
```
api-spec 修正
  → db-spec: 新カラム/テーブルの必要性確認
  → frontend-spec: 新API呼び出しの反映、Props型の変更
  → implementation-plan.md: 実装タスク・テスト方針の更新
```

### パターン3: 要件変更（README.md 起点）
```
README.md（要件/スコープ）修正
  → api-spec: エンドポイントの追加/変更
  → db-spec: テーブル/カラムの追加/変更
  → frontend-spec: コンポーネントの追加/変更
  → implementation-plan.md: データフロー・実装タスク・影響範囲の再評価
```

### パターン4: UI変更（frontend-spec 起点）
```
frontend-spec 修正
  → implementation-plan.md: 実装タスク・テスト方針の更新
  （API/DB への影響は通常小さい）
```
