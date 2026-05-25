---
name: card-pipeline
description: 'input/ 配下のインタビュー記録テキスト 1 件を起点に、パラメータ抽出 → 画像生成 → カード HTML レンダリングまでを一気通貫で実行する入口スキル。card-params-extract → gpt-image-2 → card-render の 3 ステップで、output/<###>_<name>/ に params.json / extraction-log.md / image-prompt.md / creature.png / card.html を揃える。WHEN: インタビューからカードを一気に作る、いきもの図鑑カードをエンドツーエンド生成、抽出から HTML までまとめて実行、いきもの図鑑のフル生成、ワンショットでカード化、人物ごとに一発でカードを作る。'
argument-hint: 'input フォルダ内のインタビューファイル名（例: インタビュー_鈴木つばさ.txt）'
---

# card-pipeline: インタビュー → カード完成 一気通貫スキル

[card-params-extract](../card-params-extract/SKILL.md) → [gpt-image-2](../gpt-image-2/SKILL.md) → [card-render](../card-render/SKILL.md) の 3 ステップをオーケストレーションし、**インタビュー記録 1 件から完成カードまでを一回の指示で生成する**入口スキル。

本スキル自体はロジックを持たず、既存スキルを順番に呼び出すだけ。各ステップの詳細仕様は各スキルの SKILL.md を必ず参照すること。

## 利用ケース

- ワークショップ後、`input/インタビュー_<名前>.txt` 1 件を投入して当日中にカードを揃える
- 既存メンバー分のカードをスクリプトで一気に作り直したい（オプション [scripts/build_card.py](./scripts/build_card.py) で 1 名分を自動化）
- 仕様変更後、複数人分のカードを順次再生成（フォルダ単位で `--force-image` / `--skip-image` を切替）

## 前提

- 入力: `input/インタビュー_*.txt` が存在（テンプレート原本: [reference/interview-template.txt](../../../reference/interview-template.txt) ／ パラメータ生成ルール: [param-generation-rules.md](../card-params-extract/references/param-generation-rules.md) §1）
- [card-params-extract](../card-params-extract/SKILL.md) / [gpt-image-2](../gpt-image-2/SKILL.md) / [card-render](../card-render/SKILL.md) の前提を満たしている（特に gpt-image-2 の Azure OpenAI 環境変数）
- Python 3.11 系（標準ライブラリのみ）

## 手順（エージェントの動き）

1. **引数を確認**
   - 引数 = `input/` 配下のファイル名（例: `インタビュー_鈴木つばさ.txt`）。
   - ファイルが無い場合はエラー停止。

2. **ステップ A: パラメータ抽出**
   - [card-params-extract](../card-params-extract/SKILL.md) の手順に従い、`output/<###>_<name>/` に以下を生成:
     - `params.json`
     - `extraction-log.md`
     - `image-prompt.md`
   - 必須項目欠落 / §5 画像材料 3 項目以上空欄 / わざ決定不能 などに該当する場合は、[card-params-extract](../card-params-extract/SKILL.md) §「追加質問の判定基準」に従い**ユーザーへ質問**してから先に進む（推測で埋めない）。
   - 採番した `folder_name`（例: `003_suzuki_tsubasa`）を控える。

3. **ステップ B: 画像生成**
   - [gpt-image-2](../gpt-image-2/SKILL.md) の `generate.py` を呼ぶ:
     ```powershell
     python .github/skills/gpt-image-2/scripts/generate.py `
       --prompt-file output/<folder>/image-prompt.md `
       --out output/<folder>/creature.png `
       --model <ユーザー指定モデル名> `
       --size 1024x1024 `
       --quality medium
     ```
   - `generate.py` はルート `.env` を**スクリプト内部で自動的に読み込む**ため、エージェントが事前に `.env` の存在確認やシェル環境変数の検証を行う必要はない。`.env` は `.gitignore` 対象のため `file_search` では見つからないことがある。**そのまま実行し、エラーが出た場合のみユーザーへ確認する**こと。
   - モデル名はユーザーが `--model` で指定した名前、または `.env` / 環境変数の `AZURE_OPENAI_IMAGE_MODEL` / `AZURE_OPENAI_IMAGE_DEPLOYMENT` の値だけを使う。未指定時はエラー停止し、エージェント判断で補完しない。
   - 既に `creature.png` がある場合は **スキップ**（ユーザーが明示的に再生成を求めた場合のみ上書き）。
   - API エラー時は stderr の Azure 側メッセージを抜粋提示し、ステップ C は続行（壊れた `<img>` の状態で `card.html` を出す）。`unknown_model` の場合も別モデルへ自動リトライせず、ユーザーにモデル名の修正を依頼する。

4. **ステップ C: HTML レンダリング**
   - [card-render](../card-render/SKILL.md) の `render_card.py` を呼ぶ:
     ```powershell
     python .github/skills/card-render/scripts/render_card.py `
       --params output/<folder>/params.json `
       --out output/<folder>/card.html
     ```
   - 既存 `card.html` は常に上書き。

5. **完了報告**
   - 生成物パス（5 ファイル）と主要パラメータ（生物名 / タイプ / レアリティ / とくいわざ）を要約。
   - VS Code 上で `card.html` をプレビューする 1 行手順を添える。

## 一括実行ショートカット

3 ステップを 1 コマンドで叩きたい場合は [scripts/build_card.py](./scripts/build_card.py) を使う。ただし**ステップ A（パラメータ抽出）はエージェント側の AI 推論が必要なため自動化できない**。本スクリプトは既に `params.json` と `image-prompt.md` が揃っているフォルダに対し、ステップ B → C をまとめて実行する。

```powershell
# params.json 抽出後（=card-params-extract 実行後）に:
python .github/skills/card-pipeline/scripts/build_card.py `
  --folder output/003_suzuki_tsubasa
```

主要オプション:

| 引数 | 既定値 | 説明 |
|------|--------|------|
| `--folder` | 必須 | 対象フォルダ（`output/<###>_<name>/`） |
| `--model` | なし | 画像モデル。未指定時は `AZURE_OPENAI_IMAGE_MODEL` / `AZURE_OPENAI_IMAGE_DEPLOYMENT` を使い、それも無ければエラー |
| `--size` | `1024x1024` | 画像サイズ |
| `--quality` | `medium` | 画像品質 |
| `--force-image` | off | 既存 `creature.png` を上書き再生成 |
| `--skip-image` | off | 画像生成をスキップして HTML のみ作る |
| `--api-mode` | `v1` | `v1` / `deployment` |

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| `input/<ファイル>` が無い | エラー停止し、`input/` 一覧を提示 |
| 必須項目欠落・情報不足 | [card-params-extract](../card-params-extract/SKILL.md) の追加質問フェーズへ。推測補完は不可 |
| 画像 API がエラー | stderr 抜粋を提示。HTML 生成は続行 |
| `creature.png` 既存 | 既定スキップ。再生成は `--force-image` 明示時のみ |
| `card.html` 既存 | 常に上書き |

## 参照

- [scripts/build_card.py](./scripts/build_card.py) — ステップ B+C を 1 コマンドで実行
- [card-params-extract](../card-params-extract/SKILL.md) — ステップ A 仕様
- [gpt-image-2](../gpt-image-2/SKILL.md) — ステップ B 仕様
- [card-render](../card-render/SKILL.md) — ステップ C 仕様
- [パラメータ生成ルール](../card-params-extract/references/param-generation-rules.md) — 全体方針

## 注意

- 配布用 HTML インデックスへの組み込みは別タスク。本スキルは 1 枚分のカード生成までを対象とする。
- 本スキルは 1 名分ずつ実行することを想定。複数人を回す場合は、エージェントが対象ファイルを 1 件ずつループする。
- `input/` と `output/` は個人情報や生成物を含み得るため、既定の `.gitignore` では中身をコミットしない。
