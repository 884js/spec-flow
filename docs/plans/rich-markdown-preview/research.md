# リサーチ: Annotation Viewer のマークダウン表示を mo レベルにリッチ化

調査日: 2026-03-08
調査タイプ: 複合（コードベース + 外部技術）

## 調査ゴール
k1LoW/mo と同等レベルのリッチなマークダウン表示を、Annotation Viewer のブラウザプレビューで実現する方法を特定する。

## 現状（コードベース調査）

### アーキテクチャ
- **viewer.html**（630行）: HTML/CSS/JS が1ファイルにインライン
- **server.py**: Python 3 標準ライブラリのみの HTTP サーバー

### 現在の技術スタック
| 要素 | 現状 |
|------|------|
| パーサー | marked.js（CDN） |
| シンタックスハイライト | **なし** |
| ダイアグラム | mermaid.js（CDN） |
| CSS テーマ | 独自インライン CSS（Zenn.dev 風、約330行） |
| 差分表示 | jsdiff（CDN） |

### 現在のデザイン
- フォント: Noto Sans JP（Google Fonts）
- コードブロック: ダーク背景（`#1a2638`）だがハイライトなし
- テーブル: 基本スタイルのみ

## 調査結果

### k1LoW/mo の技術スタック（参照基準）
| 要素 | mo の実装 |
|------|----------|
| GFM 準拠 | あり |
| シンタックスハイライト | Shiki（VS Code と同エンジン） |
| ダイアグラム | Mermaid |
| テーマ | ダーク/ライト自動切替 |
| UI | 目次パネル、フロントマター表示 |

### 選択肢の比較

#### シンタックスハイライター（最大の差分ポイント）

| 観点 | Shiki | highlight.js | Prism.js |
|------|-------|-------------|----------|
| バンドルサイズ | ~280 KiB（WASM含む） | ~16 KiB | ~12 KiB |
| 品質 | VS Code 同等（最高） | 良好 | TypeScript に弱点 |
| 言語自動検出 | なし | あり | なし |
| CDN | `esm.sh/shiki@3.0.0` | jsDelivr | cdnjs |
| GitHub テーマ | あり | `github` / `github-dark` | カスタマイズ要 |

#### マークダウン CSS テーマ

| 観点 | github-markdown-css | 現行の独自CSS |
|------|---------------------|--------------|
| GitHub 再現度 | 完全 | 部分的（Zenn風） |
| ダーク/ライト | メディアクエリ自動切替 | ライトのみ |
| テーブルスタイル | GitHub 準拠 | 基本的 |
| CDN | jsDelivr で配布 | - |
| JS 不要 | 不要 | - |

### CDN URL 一覧

```
# github-markdown-css
https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.css

# highlight.js（軽量推奨）
https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js
https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/github.min.css
https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/github-dark.min.css

# Shiki（品質重視）
https://esm.sh/shiki@3.0.0

# Mermaid（既に使用中）
https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs
```

## 推奨・結論

### 推奨構成: github-markdown-css + highlight.js

| 要素 | 推奨 | 理由 |
|------|------|------|
| CSS テーマ | github-markdown-css | mo と最も近い見た目。ダーク/ライト対応 |
| シンタックスハイライト | highlight.js | 16 KiB で十分な品質。言語自動検出あり |
| パーサー | marked.js（現行維持） | 変更コスト最小。GFM デフォルト対応 |
| ダイアグラム | mermaid.js（現行維持） | 変更不要 |

### 変更ポイント
1. **github-markdown-css を CDN で追加** → コンテンツ部分に `.markdown-body` クラス適用
2. **highlight.js を CDN で追加** → コードブロックの自動ハイライト
3. **独自 CSS を整理** → コメントUI等の独自部分のみ残し、マークダウン表示部分は github-markdown-css に委譲
4. **ダークモード対応**（オプション）→ `prefers-color-scheme` でテーマ自動切替

### 注意点
- marked.js はデフォルトで HTML をサニタイズしない（plan.md は信頼できるソースなので許容可能）
- `<!DOCTYPE html>` が必須（github-markdown-css のダークモードテーブルで既知の問題あり）

## 次のステップ
- `/spec` で実装仕様を作成し、viewer.html を更新する
