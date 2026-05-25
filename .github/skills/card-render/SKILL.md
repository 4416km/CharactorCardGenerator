---
name: card-render
description: 'output/<###>_<name>/params.json と creature.png をもとに、reference/zukan-card.css に対応したカード HTML (card.html) を生成するレンダリング専用スキル。画像生成は行わず、gpt-image-2 または card-pipeline で作成済みの creature.png を参照する。WHEN: いきものカードを HTML 化、params.json から card.html を生成、カードを再レンダリング、HTML だけ作り直す、いきもの図鑑カードの表示を更新。'
argument-hint: 'output/ 配下の対象フォルダ名（例: 002_tanaka_taro）または params.json パス'
---

# card-render: いきものカード HTML レンダリングスキル

[card-params-extract](../card-params-extract/SKILL.md) が出力した `params.json` と、[gpt-image-2](../gpt-image-2/SKILL.md) が生成した `creature.png` をもとに、[`reference/zukan-card.css`](../../../reference/zukan-card.css) に対応した 1 ページ HTML (`card.html`) を出力する。

このスキルは **HTML レンダリングだけ** を担当する。画像生成は行わない。インタビュー抽出から画像生成、HTML 生成までをまとめて行う場合は [card-pipeline](../card-pipeline/SKILL.md) を使う。

## 利用ケース

- パラメータ抽出済み（`output/<###>_<name>/params.json` あり）の人物について、`card.html` だけを生成
- `params.json` や `creature.png` を更新した後、HTML だけ作り直す
- 仕上がった `card.html` を `reference/zukan-card.css` 直下で開いて目視確認

## 前提

- `output/<###>_<name>/params.json` が存在（[card-params-extract](../card-params-extract/SKILL.md) で生成済み）
- `output/<###>_<name>/creature.png` が存在（[gpt-image-2](../gpt-image-2/SKILL.md) で生成済み。未生成でも HTML は出力できるが画像は表示されない）
- `reference/zukan-card.css` が存在（本リポジトリに同梱されているカード共通スタイル）
- Python 3.11 系（標準ライブラリのみで動作。追加依存なし）

## 手順

1. **対象フォルダを確定する**
   - 引数がフォルダ名（例 `002_tanaka_taro`）なら `output/<arg>/` を対象とする
   - 引数が `params.json` の絶対/相対パスなら、その親フォルダを対象とする
   - `params.json` が無ければエラーで停止（先に `card-params-extract` を実行する旨を提示）

2. **params.json を読み込む**
   - `read_file` で全文ロード（後の差し込みに使用）
   - `creature.types`, `creature.stats.peaks`, `creature.affinity.weak.tags` などの必須キーを軽くチェック

3. **HTML (`card.html`) を生成する**
   - [scripts/render_card.py](./scripts/render_card.py) を実行:
     ```powershell
       python .github/skills/card-render/scripts/render_card.py `
       --params output/<folder>/params.json `
       --out output/<folder>/card.html
     ```
   - スクリプトは `params.json` を読み、[`reference/zukan-card.css`](../../../reference/zukan-card.css) のクラス体系に沿った 1 ページ HTML を出力する
   - `card.html` から画像は `./creature.png` 相対参照、CSS は `../../reference/zukan-card.css` 相対参照
   - 既存 `card.html` は **常に上書き**（パラメータ更新時に追従させるため）

4. **完了報告**
   - 保存先: `output/<folder>/card.html`
   - 生物名・タイプ・レアリティ・とくいわざ を要約表示
   - VS Code で `card.html` をブラウザプレビューする手順を 1 行で添える

## 主要オプション

| 引数 / フラグ | 既定値 | 説明 |
|---------------|--------|------|
| 引数 | — | フォルダ名 (`002_tanaka_taro`) または `params.json` パス |
| `--image` | `creature.png` | HTML から見た画像の相対パス |
| `--css` | `../../reference/zukan-card.css` | HTML から見た CSS の相対パス |

## レンダラの仕様

[scripts/render_card.py](./scripts/render_card.py) は `params.json` から以下のブロックを構築する（CSS クラスは [`reference/zukan-card.css`](../../../reference/zukan-card.css) 準拠）。

`trainer.recorder` は単一文字列、複数名の配列、または `、` / 改行 / `;` 区切り文字列を受け付け、観察者欄へ複数行で表示する。

| ブロック | 主要クラス | 差し込み元 |
|----------|-----------|------------|
| ページ枠 | `.field-guide-page` | — |
| 画像プレート | `.field-guide-plate` / `.specimen-frame` / `.creature-image` | `./creature.png` |
| トレーナー/観察者枠 | `.guide-note-grid` / `.guide-note` / `.observer-comment` | `trainer.{western_name,real_name,real_name_kana,department,recorder}` / `entries.observation_note` |
| ヘッダ | `.field-guide-header` / `.specimen-number` / `.field-guide-alias` | `primary_name` / `alias` |
| タイプ/レアリティ | `.creature-meta-row` / `.type-badge--<class>` / `.rarity-stars` | `types[]` / `rarity` |
| 分類 | `.taxonomy-strip` | `taxonomy.class` / `taxonomy.{genus,species}` |
| ステータス | `.stat-panel` / `.stat-row` / `.stat-row--peak` | `stats.{endurance,...}` / `stats.peaks` |
| わざ | `.move-cards` / `.move-card--signature` / `.move-card--hidden` | `moves.signature` / `moves.hidden` |
| 弱点・耐性 | `.affinity-box` / `.affinity-cell--weak` / `.affinity-cell--resist` | `affinity.{weak,resist}` |
| 進化チェーン | `.evolution-chain` / `.evo-node--current` | `evolution.{previous,current,next}` |
| フレーバー | `.flavor-quote` | `flavor_quote` |
| 図鑑エントリ | `.field-guide-entries` / `.guide-entry--wide` | `entries.*`（`observation_note` を除く） |

タイプ → CSS クラスのマッピング:

| タイプ | クラス |
|--------|--------|
| 思索 | `type-badge--thought` |
| 観察 | `type-badge--observe` |
| 創発 | `type-badge--emerge` |
| 行動 | `type-badge--action` |
| 共鳴 | `type-badge--resonate` |
| 調律 | `type-badge--tune` |

未知のタイプ名が来た場合は既定の `.type-badge` のみ（色は中立色）を付ける。

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| `params.json` が無い | 「先に card-params-extract を実行してください」と提示して停止 |
| `creature.png` が無い | HTML は生成できるが画像は表示されない。必要なら先に `gpt-image-2` または `card-pipeline` で画像生成する |
| 既知のタイプ語彙が増えた | [references/type-class-map.md](./references/type-class-map.md) に追記し、`render_card.py` の `TYPE_CLASS` 辞書も更新する |

## 参照

- [scripts/render_card.py](./scripts/render_card.py) — HTML レンダラ本体
- [references/type-class-map.md](./references/type-class-map.md) — タイプ ↔ CSS クラス対応表
- [reference/zukan-card.css](../../../reference/zukan-card.css) — カード共通スタイル
- [card-params-extract](../card-params-extract/SKILL.md) — 入力 `params.json` を作るスキル
- [gpt-image-2](../gpt-image-2/SKILL.md) — `creature.png` を作る画像生成スキル
- [card-pipeline](../card-pipeline/SKILL.md) — 抽出・画像生成・HTML 生成をまとめて行う入口スキル
- [パラメータ生成ルール](../card-params-extract/references/param-generation-rules.md) §3 / §4

## 注意

- HTML 内に API キーやローカルの絶対パスを書き込まない
- カード文面はパラメータ生成ルール §3 の方針（ポジティブ / 体言止め混在 / 観察記録調）を維持する
- 配布用 HTML インデックスへの組み込みは別タスクで実施（このスキルは 1 枚分のみ）
