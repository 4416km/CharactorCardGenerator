---
name: card-html-generate
description: 'output/<###>_<name>/params.json と image-prompt.md をもとに、いきものカードの画像 (creature.png) と HTML (card.html) を生成するスキル。gpt-image-2 スキルで PNG を生成し、reference/zukan-card.css に対応した HTML テンプレートへパラメータを差し込んで 1 ページのカードを出力する。WHEN: いきものカードを HTML 化、params.json からカードを描画、画像とHTMLをまとめて生成、いきもの図鑑カードのレンダリング、いきもの図鑑カード完成。'
argument-hint: 'output/ 配下の対象フォルダ名（例: 002_tanaka_taro）または params.json パス'
---

# card-html-generate: いきものカード画像 + HTML 生成スキル

[card-params-extract](../card-params-extract/SKILL.md) が出力した `params.json` と `image-prompt.md` をもとに、

1. **画像 (`creature.png`)** を [gpt-image-2](../gpt-image-2/SKILL.md) スキルで生成し、
2. **カード HTML (`card.html`)** を [`reference/zukan-card.css`](../../../reference/zukan-card.css) に対応した構造で出力する

ことで、1 名分のいきもの図鑑ページを完成させる。

## 利用ケース

- パラメータ抽出済み（`output/<###>_<name>/params.json` あり）の人物について、画像とカード HTML を一気に生成
- 画像のみ作り直す / HTML のみ作り直す部分実行にも対応
- 仕上がった `card.html` を `reference/zukan-card.css` 直下で開いて目視確認

## 前提

- `output/<###>_<name>/params.json` が存在（[card-params-extract](../card-params-extract/SKILL.md) で生成済み）
- `output/<###>_<name>/image-prompt.md` が存在（画像生成プロンプト本文）
- `reference/zukan-card.css` が存在（本リポジトリに同梱されているカード共通スタイル）
- [gpt-image-2](../gpt-image-2/SKILL.md) の環境変数（`AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_IMAGE_MODEL` 等）が設定済み
- Python 3.11 系（標準ライブラリのみで動作。追加依存なし）

## 手順

1. **対象フォルダを確定する**
   - 引数がフォルダ名（例 `002_tanaka_taro`）なら `output/<arg>/` を対象とする
   - 引数が `params.json` の絶対/相対パスなら、その親フォルダを対象とする
   - `params.json` が無ければエラーで停止（先に `card-params-extract` を実行する旨を提示）

2. **params.json を読み込む**
   - `read_file` で全文ロード（後の差し込みに使用）
   - `creature.types`, `creature.stats.peaks`, `creature.affinity.weak.tags` などの必須キーを軽くチェック

3. **画像 (`creature.png`) を生成する**
   - 既に `creature.png` がある場合は **再生成しない**（`--force-image` 指定時のみ上書き）
   - 無い場合は [gpt-image-2](../gpt-image-2/SKILL.md) の `generate.py` を呼ぶ:
     ```powershell
     python .github/skills/gpt-image-2/scripts/generate.py `
       --prompt-file output/<folder>/image-prompt.md `
       --out output/<folder>/creature.png `
       --model $env:AZURE_OPENAI_IMAGE_MODEL `
       --size 1024x1024 `
       --quality medium
     ```
   - **重要**: `image-prompt.md` 全文をそのまま `--prompt-file` に渡す。スクリプト側はファイル全体を 1 プロンプトとして送信する。Markdown 見出しが混ざるのが嫌な場合は `params.image_prompt.final_prompt` を一時 `.txt` に書き出して渡してもよい
   - エラー時は stderr を抜粋し、Azure OpenAI 側のメッセージを忠実に提示（推測で対処しない）

4. **HTML (`card.html`) を生成する**
   - [scripts/render_card.py](./scripts/render_card.py) を実行:
     ```powershell
     python .github/skills/card-html-generate/scripts/render_card.py `
       --params output/<folder>/params.json `
       --out output/<folder>/card.html
     ```
   - スクリプトは `params.json` を読み、[`reference/zukan-card.css`](../../../reference/zukan-card.css) のクラス体系に沿った 1 ページ HTML を出力する
   - `card.html` から画像は `./creature.png` 相対参照、CSS は `../../reference/zukan-card.css` 相対参照
   - 既存 `card.html` は **常に上書き**（パラメータ更新時に追従させるため）

5. **完了報告**
   - 保存先: `output/<folder>/creature.png` / `output/<folder>/card.html`
   - 生物名・タイプ・レアリティ・とくいわざ を要約表示
   - VS Code で `card.html` をブラウザプレビューする手順を 1 行で添える

## 主要オプション

| 引数 / フラグ | 既定値 | 説明 |
|---------------|--------|------|
| 引数 | — | フォルダ名 (`002_tanaka_taro`) または `params.json` パス |
| `--force-image` | off | 既存 `creature.png` を上書きして再生成 |
| `--skip-image` | off | 画像生成をスキップし HTML のみ作る（プロンプト調整中など） |
| `--size` | `1024x1024` | gpt-image-2 へ渡す画像サイズ |
| `--quality` | `medium` | gpt-image-2 の品質 |

## レンダラの仕様

[scripts/render_card.py](./scripts/render_card.py) は `params.json` から以下のブロックを構築する（CSS クラスは [`reference/zukan-card.css`](../../../reference/zukan-card.css) 準拠）。

| ブロック | 主要クラス | 差し込み元 |
|----------|-----------|------------|
| ページ枠 | `.field-guide-page` | — |
| 画像プレート | `.field-guide-plate` / `.specimen-frame` / `.creature-image` | `./creature.png` |
| 観察メモ枠 | `.guide-note-grid` / `.guide-note` | `trainer.recorder` |
| ヘッダ | `.field-guide-header` / `.specimen-number` / `.field-guide-alias` | `primary_name` / `alias` |
| タイプ/レアリティ | `.creature-meta-row` / `.type-badge--<class>` / `.rarity-stars` | `types[]` / `rarity` |
| 分類 | `.taxonomy-strip` | `trainer.department` / `taxonomy.class` / `taxonomy.{genus,species}` |
| ステータス | `.stat-panel` / `.stat-row` / `.stat-row--peak` | `stats.{endurance,...}` / `stats.peaks` |
| わざ | `.move-cards` / `.move-card--signature` / `.move-card--hidden` | `moves.signature` / `moves.hidden` |
| 弱点・耐性 | `.affinity-box` / `.affinity-cell--weak` / `.affinity-cell--resist` | `affinity.{weak,resist}` |
| 進化チェーン | `.evolution-chain` / `.evo-node--current` | `evolution.{previous,current,next}` |
| フレーバー | `.flavor-quote` | `flavor_quote` |
| 図鑑エントリ | `.field-guide-entries` / `.guide-entry--wide` | `entries.*` |

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
| `image-prompt.md` が無い | プロンプトテキストを `params.image_prompt.final_prompt` から組み立てて一時ファイル化 |
| 画像 API がエラー | stderr 抜粋をそのまま提示し、HTML 生成は続行（プレースホルダー画像なし、`creature.png` 不在のまま `card.html` を出す） |
| 既知のタイプ語彙が増えた | [references/type-class-map.md](./references/type-class-map.md) に追記し、`render_card.py` の `TYPE_CLASS` 辞書も更新する |

## 参照

- [scripts/render_card.py](./scripts/render_card.py) — HTML レンダラ本体
- [references/type-class-map.md](./references/type-class-map.md) — タイプ ↔ CSS クラス対応表
- [reference/zukan-card.css](../../../reference/zukan-card.css) — カード共通スタイル
- [card-params-extract](../card-params-extract/SKILL.md) — 入力 `params.json` を作るスキル
- [gpt-image-2](../gpt-image-2/SKILL.md) — 画像生成 CLI
- [パラメータ生成ルール](../card-params-extract/references/param-generation-rules.md) §3 / §4

## 注意

- HTML 内に API キーやパスを書き込まない（環境変数経由）
- 生成画像は Azure OpenAI 利用規約に従う
- カード文面はパラメータ生成ルール §3 の方針（ポジティブ / 体言止め混在 / 観察記録調）を維持する
- 配布用 HTML インデックスへの組み込みは別タスクで実施（このスキルは 1 枚分のみ）
