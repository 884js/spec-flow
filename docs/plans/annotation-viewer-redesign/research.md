# リサーチ: annotation-viewer のエディトリアル系デザインリデザイン

調査日: 2026-03-06
調査タイプ: 外部技術

## 調査ゴール
viewer.html の CSS デザインを「AI生成風の白カード+青アクセント+グレー背景」から、エディトリアル・出版系の洗練されたデザインに変更するための具体的な実装指針を得る。

## 調査結果

### 1. 日本語セリフ体フォントの比較

| 観点 | Shippori Mincho | Noto Serif JP | Zen Old Mincho |
|------|----------------|---------------|----------------|
| 設計目的 | 小説の本文組み専用 | 汎用グローバルセリフ | 新聞・広告の現場由来 |
| 本文適性 | 高（400/500 が長文向け） | 中（汎用） | 中（見出しも強い） |
| デザイン特性 | 筆運びが少なく清潔 | 標準的な現代明朝 | 格調ある旧体仮名 |
| ウェイト | 400-800 | 200-900 | 400-900 |

**推奨: Shippori Mincho**（本文組み専用設計でスクリーン可読性が高い）

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;600;800&display=swap" rel="stylesheet">
```

### 2. 配色パレット

| 役割 | 現状 | 提案 |
|------|------|------|
| ページ背景 | `#f8f9fa`（クールグレー） | `#faf8f5`（ウォームクリーム） |
| コンテンツ背景 | `#fff`（純白） | `#f5f2ed`（暖色ニュートラル） |
| 本文テキスト | `#1a1a2e`（ほぼ黒） | `#2b2823`（インク色） |
| セカンダリテキスト | — | `#6b6560` |
| アクセント | `#4361ee`（鮮やか青） | `#8b5e3c`（暖色ブラウン） |
| ボーダー | `#dee2e6` / `#e9ecef` | `#e0dbd5`（ウォームグレー） |
| コメント背景 | `#fffde7`（蛍光黄） | `#f0ebe2`（ベージュ） |
| コメントボーダー | `#fdd835`（黄色） | `#c5b49a`（カーキ） |
| ヘッダー背景 | `#1a1a2e`（ダーク） | `#faf8f5`（ページと統一） |

### 3. タイポグラフィ

```css
body {
  font-family: 'Shippori Mincho', Georgia, serif;
  font-size: 17px;
  line-height: 1.9;          /* 日本語推奨: 1.7〜2.0 */
  letter-spacing: 0.02em;    /* デジタル庁推奨値 */
}

h1 { font-size: 2rem;    font-weight: 800; line-height: 1.4; letter-spacing: 0.04em; }
h2 { font-size: 1.5rem;  font-weight: 700; line-height: 1.5; border-bottom: 1px solid; }
h3 { font-size: 1.15rem; font-weight: 600; line-height: 1.6; }
```

注意点:
- 日本語に `font-style: italic` は使わない（不自然な傾きになる）
- `line-height` は単位なし数値で指定する
- 行長は15〜35文字が適切。本文カラム幅は 680px 程度が望ましい

### 4. コメント UI

黄色付箋 → 暖色ニュートラルのカードスタイルへ変更:

```css
.comment-item {
  background: #f0ebe2;
  border: 1px solid #d9cfc3;
  border-left: 3px solid #8b5e3c;
  border-radius: 2px;
  padding: 0.9em 1.1em;
  font-size: 0.9rem;
  box-shadow: none;
}

.selected-text {
  background: #f0e6d3;
  border-bottom: 1.5px solid #c5b49a;
}
```

### 5. ヘッダー・ボタン

ダークヘッダー → ライトヘッダー（ボーダーで区切り）:

```css
.header {
  background: #faf8f5;
  border-bottom: 1px solid #e0dbd5;
  color: #2b2823;
}

.btn {
  background: transparent;
  border: 1px solid #8b5e3c;
  color: #8b5e3c;
  border-radius: 0;     /* 角丸なし = 出版系 */
  font-family: inherit;
  letter-spacing: 0.04em;
}

.btn:hover {
  background: #8b5e3c;
  color: #faf8f5;
}
```

### 6. CSS変数による統合

```css
:root {
  --bg-page:       #faf8f5;
  --bg-content:    #f5f2ed;
  --bg-comment:    #f0ebe2;
  --text-primary:  #2b2823;
  --text-secondary:#6b6560;
  --accent:        #8b5e3c;
  --border:        #e0dbd5;
  --border-comment:#c5b49a;
  --font-serif:    'Shippori Mincho', Georgia, serif;
}
```

## 推奨・結論

- **フォント**: Shippori Mincho（3ウェイト: 400/600/800）
- **配色**: 暖色ニュートラル系。アクセントはブラウン `#8b5e3c`
- **レイアウト**: box-shadow 廃止、border-radius: 0、ボーダーのみで区切る
- **ヘッダー**: ダーク → ライト化、ボーダーで区切る
- **コメント**: 黄色付箋 → ベージュ+ブラウンアクセント
- **タイポ**: font-size 17px、line-height 1.9、letter-spacing 0.02em

## 追加調査（2026-03-06）: Zenn.dev のデザイン分析

ユーザーが Zenn のデザインを参考にしたいとのこと。zenn-editor の公開 SCSS ソースを分析。

### Zenn のデザイン特徴

| 観点 | Zenn の実装 |
|------|------------|
| フォント | Inter（ラテン文字）+ システムフォント（日本語） |
| 本文 line-height | 1.9 |
| リスト line-height | 1.7 |
| テーマ | `data-theme="light"` / `"dark-blue"` で CSS変数切り替え |
| カラーシステム | CSS変数ベース（`--c-bg-base`, `--c-bg-dim` 等） |
| コードブロック背景 | `#1a2638`（ダーク系） |

### Zenn の見出しスタイル

| 見出し | font-size | margin-top | border-bottom |
|--------|-----------|------------|---------------|
| h1 | 1.7em | 2.3em | solid 1px |
| h2 | 1.5em | 2.3em | solid 1px |
| h3 | 1.3em | 2.25em | なし |
| h4 | 1.1em | 2.25em | なし |

### Zenn のコンテンツスタイル

| 要素 | スタイル |
|------|---------|
| 段落 margin-top | 1.5em |
| テーブル font-size | 0.95em |
| テーブル padding | 0.5rem |
| コードブロック margin | 1.3rem 0 |
| コードブロック font-size | 0.9em |
| blockquote border-left | 3px |
| blockquote font-size | 0.97em |
| リスト padding-left | ul 1.8em / ol 1.7em |
| li 間隔 | 0.4rem |
| hr margin | 2.5rem 0 |

### Zenn のカラーパレット（ソースから抽出）

| 色名 | ライトモード |
|------|------------|
| ブルー系 | `#f0f7ff` 〜 `#043467` |
| グレー系 | `#f5f9fc` 〜 `#65717b` |
| コードブロック背景 | `#1a2638` |

### 初回調査との統合: 修正方針

Zenn のデザインを参考にすると、初回調査の「完全エディトリアル」からやや調整が必要:

| 観点 | 初回提案 | Zenn 参考に修正 |
|------|---------|----------------|
| フォント | Shippori Mincho（明朝体） | **維持**（Zenn はゴシック系だが、差別化として明朝を採用） |
| line-height | 1.9 | **維持**（Zenn と同値） |
| h1/h2 の border-bottom | 1px solid | **採用**（Zenn と同様） |
| h1 font-size | 2rem | 1.7em に修正（Zenn 準拠、やや控えめ） |
| 見出し margin-top | 未定 | 2.3em（Zenn 準拠、広い余白） |
| 段落 margin-top | 未定 | 1.5em（Zenn 準拠） |
| テーブル font-size | 14px | 0.95em（Zenn 準拠） |
| コードブロック | 未定 | ダーク背景 `#1a2638`（Zenn 準拠、アクセントとして有効） |
| border-radius | 0（角丸なし） | 小さめの角丸（4〜8px）に修正（Zenn は丸みあり） |
| box-shadow | なし | 極薄のシャドウ可（Zenn はカード型UI） |
| 配色 | ウォームクリーム | **維持**（Zenn はクール系だが、エディトリアル感を優先） |

### 最終推奨デザイン方針

1. **フォント**: Shippori Mincho（エディトリアル感の核。Zennとの差別化ポイント）
2. **余白・見出し**: Zenn の数値を採用（line-height 1.9、margin-top 2.3em、border-bottom）
3. **配色**: 初回提案のウォームクリーム系を維持（#faf8f5 背景、#2b2823 テキスト、#8b5e3c アクセント）
4. **コードブロック**: Zenn のダーク背景（#1a2638）を採用してコントラストを作る
5. **角丸**: 完全な 0 ではなく 4px 程度（Zenn の柔らかさを取り入れ）
6. **ボタン**: ゴーストスタイル維持だが border-radius: 4px に調整

## 次のステップ

- `/spec` で仕様を作成し、具体的な CSS 変更を plan.md に落とし込む
- または直接 viewer.html の CSS を書き換える（変更箇所は CSS のみで済むため）
