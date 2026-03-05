以下の形式で統合レポートを返すこと:

```
## プロジェクト概要
- プロジェクト名: {name}
- プロジェクトパス: {pwd の結果}
- 説明: {description from CLAUDE.md or package.json}

## 技術スタック
### フロントエンド ({リポジトリ名 or ディレクトリ名})
- フレームワーク: {framework + version}
- 言語: {language + version}
- UIライブラリ: {ui library}
- 状態管理: {state management}
- テスト: {test framework}

### バックエンド ({リポジトリ名 or ディレクトリ名})
- フレームワーク: {framework + version}
- 言語: {language + version}
- ORM: {orm}
- DB: {db}
- テスト: {test framework}

※ 片方しか存在しない場合は該当セクションのみ記載。

## フレームワーク制約
- {フレームワーク} {バージョン}: {ルーティング方式、推奨パターン}
- 設定: {主要な設定内容}
- 非推奨/注意: {あれば記載、なければ「なし」}

## アーキテクチャパターン
### バックエンド
- アーキテクチャ: {例: Controllers -> Services -> Repository}
- エラーハンドリング: {パターン}
- ミドルウェア: {構成}

### フロントエンド
- ディレクトリパターン: {例: Features Directory パターン}
- コンポーネント配置: {例: [名前]/index.tsx + index.test.tsx}
- 型定義の生成元: {例: OpenAPI から自動生成}

## ディレクトリ構成
- 主要ディレクトリ: {dirs with brief description}
- エントリポイント: {main entry files}
- ルーティング: {routing pattern}

## データベース
- DB種別: {db type}
- ORM: {orm}
- マイグレーション: {migration tool}
- スキーマファイル: `{path}`

### 主要テーブル（関連するもの）
- {table_name}: {brief description}
  - カラム: {column1}, {column2}, ...
  - リレーション: {他テーブルとの関係}

## コードパターン

### API パターン
- ルート定義場所: {file paths}
- パターン: {routing pattern}

| メソッド | パス | ハンドラファイル | 位置 |
|---------|------|----------------|------|
| {method} | {path} | `{file}` | L{start}-{end} |

- 型定義パターン: {how types are defined}
- バリデーション: {validation method}
- エラーハンドリング: {error handling pattern}

### コンポーネントパターン
- UIライブラリ: {library}
- スタイリング: {method}
- Props定義: {pattern}
- 状態管理: {pattern}

### データフローパターン
- レイヤー構成: {handler → service → repository, etc.}
- API通信: {client library and pattern}
- 外部サービス連携: {external services}

## 既存の型定義
- `{path}`: {主要な型の列挙}

## 開発コマンド
- dev: {dev command}
- build: {build command}
- test: {test command}
- lint: {lint command}

## コーディング規約
- {conventions from CLAUDE.md}
- {conventions from AGENTS.md}

### 命名パターン（コードから検出）
- DB テーブル名: {検出した命名パターン}
- DB カラム名: {検出した命名パターン}
- ID 生成: {検出した方式}
- ファイル名: {検出した命名パターン}

## Git 分析

### ブランチ状態
- 現在のブランチ: {ブランチ名}
- ベースからの差分コミット: {N}件
- 未コミット変更: {有/無}

### ホットスポット（関連ファイル）
| ファイル | 変更回数 | 変更者数 | 並行開発リスク |
|---------|---------|---------|-------------|
| {ファイルパス} | {N}回 | {M}人 | {低/中/高} |

## 既存仕様書
- `{path}`: {spec summary}
※ なければ「なし」

## 関連する既存機能
- {機能名}: {概要}
※ 機能概要が渡されていない場合はこのセクション自体を省略する。

## 調査ソース
- 規約: `CLAUDE.md`, `AGENTS.md`
- マニフェスト: `{path}`
- スキーマ: `{path}`
- 型定義: `{path}`, ...
- 既存仕様書: `{path}`
- ドキュメント: `{path}`, ...
```

**出力ルール**:
- プロンプトで依頼された調査スコープに応じてセクションを選択する（全セクション必須ではない）
- 該当しないセクションは省略する
- 各セクションは50行以内に収める
- ファイルパス+行番号範囲は `file:L{start}-{end}` 形式で報告
- 信頼度ラベル [確認済み]/[推測]/[該当なし] を付与する
