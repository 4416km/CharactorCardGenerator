---
name: gpt-image-2
description: 'いきもの図鑑のカード画像を Azure OpenAI の GPT-Image 系モデル（gpt-image-2 / gpt-image-1.5 / gpt-image-1）で生成する。インタビュー記録から人物を架空のいきものとして描いたPNGを出力。WHEN: いきものカードの画像を作る、オリジナルの架空生物キャラ画像生成、Azure OpenAI で画像生成、gpt-image-2 を叩く、PNG画像生成、トレーナー画像生成、いきもの図鑑の挿絵作成。'
argument-hint: 'プロンプトまたはインタビュー記録のパス（任意でサイズ・出力先）'
---

# gpt-image-2 画像生成スキル

いきもの図鑑カード用 PNG 画像を Azure OpenAI の GPT-Image 系モデルで生成する。

## 利用ケース

- インタビュー記録（`input/インタビュー_*.txt`）からカード用のいきものイラストを生成
- 任意のプロンプトを直接渡してテスト画像を生成
- サイズや枚数を指定して比較サンプルを作成

## 前提

以下の環境変数が必要。未設定ならユーザーに確認すること（値を勝手に推測しない）。

| 変数 | 内容 |
|------|------|
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com/` 形式（Azure OpenAI / Foundry リソース共通） |
| `AZURE_OPENAI_API_KEY` | リソースのAPIキー |
| `AZURE_OPENAI_IMAGE_MODEL` | 使用モデル名（例: `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `MAI-Image-2`）。未設定なら `AZURE_OPENAI_IMAGE_DEPLOYMENT` 、さらに `gpt-image-2` |
| `AZURE_OPENAI_IMAGE_DEPLOYMENT` | （下位互換）deployment mode で使用するデプロイ名 |
| `AZURE_OPENAI_API_MODE` | `v1`（既定、Foundry Models REST API v1）または `deployment`（旧方式） |
| `AZURE_OPENAI_API_VERSION` | v1: 未設定なら `preview` / deployment: 未設定なら `2025-04-01-preview` |

Python 依存: `requests` / `python-dotenv`（標準環境にない場合は `pip install -r requirements.txt`）。

実行時は、必ずワークスペースのルートディレクトリにある `.env` を最優先で読み込む。シェルや VS Code ターミナルに同名の環境変数が既にある場合も、ルート `.env` の値を優先する。

## 手順

1. **入力を確定する**
   - インタビュー記録ファイルが指定されていれば読み込み、[assets/prompt-template.md](./assets/prompt-template.md) のテンプレートに沿って画像プロンプトを組み立てる。
   - 自由プロンプトが指定されていればそのまま使用。
2. **生成スクリプトを実行**
   ```powershell
   python .github/skills/gpt-image-2/scripts/generate.py `
     --prompt "<生成プロンプト>" `
     --out output/<no>_<trainer>/creature.png `
     --model gpt-image-2 `
     --size 1024x1024 `
     --quality medium
   ```
   - `--model gpt-image-1.5` / `--model MAI-Image-2` などでモデル切替（Foundry 上にデプロイ済みであること）
   - `--prompt-file <path>` で長文プロンプトをファイル渡し可
   - `--n 2` で複数枚生成（`_1.png` `_2.png` のように連番）
3. **結果確認**
   - 生成された PNG を `output/<no>_<trainer>/` 配下に配置
   - 画像が用途に合わなければプロンプトを調整して再実行

## 主要オプション

| 引数 | 既定値 | 説明 |
|------|--------|------|
| `--model` | `gpt-image-2` | `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `MAI-Image-2` など。Foundry/Azure OpenAI リソースにデプロイ済みの名前を指定 |
| `--size` | `1024x1024` | `512x512` / `1024x1024` / `1024x1536` / `1536x1024` / `auto`（モデルごとにサポート範囲が異なる。512x512 未対応のモデル多し） |
| `--quality` | `medium` | `low` / `medium` / `high` / `auto` |
| `--n` | `1` | 生成枚数 |
| `--background` | （省略） | `transparent` 指定で透過PNG（gpt-image-1系のみ） |
| `--output-format` | `png` | `png` / `jpeg` |
| `--api-mode` | `v1` | `v1` = Foundry Models REST API v1 / `deployment` = デプロイ別パス方式 |
| `--timeout` | `600` | HTTP読み取りタイムアウト秒。quality=high だと 1〜数分かかることあり |

## 参照

- [scripts/generate.py](./scripts/generate.py) — CLI 本体
- [references/api.md](./references/api.md) — Azure OpenAI Image API パラメータ早見表
- [assets/prompt-template.md](./assets/prompt-template.md) — いきもの図鑑カード用プロンプト雛形

## 注意

- APIキーをコードや出力に書き込まない（必ず環境変数経由）
- 生成画像はAzure OpenAIの利用規約・コンテンツポリシーに従う
- 「実在の特定人物そのもの」ではなく架空のいきもの表現に落とし込むこと
