# リサーチ: plan.md 変更箇所の差分ハイライト表示

調査日: 2026-03-07
調査タイプ: 外部技術

## 調査ゴール
annotation-viewer で writer 修正後の plan.md を再レビューする際、変更箇所をハイライト表示する実装方針を得る。

## 調査結果

### 差分粒度の比較

| 粒度 | 手法 | 評価 |
|------|------|------|
| 行単位 | `difflib.unified_diff` / jsdiff `diffLines()` | Markdown の構造（見出し、箇条書き）と一致しやすい。推奨 |
| 単語単位 | `difflib.SequenceMatcher` on words / jsdiff `diffWords()` | 行内の細かい変更を捉えられるが実装複雑 |
| セクション単位 | 見出しで split して比較 | セクション内変更を見逃す |

### アプローチの比較

| アプローチ | Python 側変更 | フロント側変更 | 評価 |
|-----------|-------------|--------------|------|
| A: Python difflib でマーカー埋め込み | 大（`<ins>`/`<del>` 挿入ロジック） | 小（CSS のみ） | Python 処理が複雑 |
| B: old/new 両テキストをフロントに渡し jsdiff で diff | 小（bak 読み込み + JSON 拡張） | 中（jsdiff CDN + diff 処理） | 推奨 |
| C: opcodes JSON を送る | 中（SequenceMatcher + JSON 化） | 中（opcodes 再構築） | Python/フロント両方に複雑さ |

### jsdiff（CDN）

- CDN: `https://cdnjs.cloudflare.com/ajax/libs/jsdiff/8.0.2/diff.min.js`
- API: `Diff.diffLines(oldStr, newStr)` -> `[{ value, added?, removed?, count }]`
- グローバルオブジェクト `Diff` として利用可能

### marked.js との相性

- marked.js v5 以降はデフォルトで inline HTML を素通しする
- diff 処理後に `<span class="diff-add">...</span>` で囲んでから `marked.parse()` に渡す流れが成立
- ただし行単位で囲むため、Markdown ブロック要素の途中で span を入れると構造が壊れる可能性あり
- 代替: marked.js でレンダリング後、DOM ベースでハイライトを適用する方が安全

## 推奨アプローチ

**アプローチ B: old/new テキストを渡して jsdiff でブラウザ側 diff**

データフロー:
1. writer 呼び出し前に `plan.md` を `plan.md.bak` にコピー
2. server.py `/api/plan` が `{"content": "...", "old": "..." or null}` を返す
3. viewer.html が `Diff.diffLines(old, new)` で行単位 diff
4. added 行に `.diff-add`、removed 行は非表示 or `.diff-del` で表示

変更量:
- `server.py`: ~5行
- `viewer.html`: ~20行（CDN + diff 処理 + CSS）
- `skills/spec/SKILL.md`: ~2行（bak コピー）

## 注意点

- `plan.md.bak` 読み込み失敗時は diff なし（初回と同じ表示）にフォールバック
- jsdiff の `diffLines()` は行末 `\n` を含めた行単位
- `difflib.SequenceMatcher` は 70KB 超で遅いが plan.md 規模では問題なし
