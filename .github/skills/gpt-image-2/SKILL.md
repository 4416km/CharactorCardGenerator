---
name: gpt-image-2
description: 'Azure OpenAI の GPT-Image 系モデル（gpt-image-2 / gpt-image-1.5 / gpt-image-1 など）を呼び出し、任意のプロンプトから PNG/JPEG を生成する汎用画像生成スキル。WHEN: Azure OpenAI で画像生成、gpt-image-2 を叩く、PNG画像生成、JPEG画像生成、prompt-file から画像を作る、画像モデルを試す。'
argument-hint: 'プロンプト文字列または prompt-file のパス（任意でサイズ・出力先）'
---

# gpt-image-2 画像生成スキル

Azure OpenAI / Foundry の GPT-Image 系モデルを呼び出し、任意のプロンプトから PNG/JPEG を生成する。

## 利用ケース

- 任意のプロンプトを直接渡して画像を生成
- `prompt-file` から長文プロンプトを読み込んで画像を生成
- サイズ・品質・枚数を変えて比較サンプルを作成

## 前提

### 環境変数と `.env`

以下の環境変数が必要。これらはプロジェクトルート直下の **`.env` ファイル**に記載する運用を想定している。

| 変数 | 内容 |
|------|------|
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com/` 形式（Azure OpenAI / Foundry リソース共通） |
| `AZURE_OPENAI_API_KEY` | リソースのAPIキー |
| `AZURE_OPENAI_IMAGE_MODEL` | 使用モデル名（例: `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `MAI-Image-2`）。未設定ならエラー |
| `AZURE_OPENAI_API_VERSION` | 未設定なら `preview` |

> **エージェント向け重要事項**:
> - `generate.py` はプロジェクトルートの `.env` を **スクリプト内部で自動的に読み込む**（`python-dotenv` 使用、`override=True`）。
> - そのため、**実行前にシェル環境変数や `.env` の存在をエージェント側で確認する必要はない**。`.env` は `.gitignore` に含まれることが多く、`file_search` やワークスペース検索では見つからない場合がある。
> - エージェントは `.env` の事前チェックをスキップし、**そのまま `generate.py` を実行する**こと。認証情報の不足はスクリプトが明確なエラーメッセージで報告するため、そのエラーが出た場合にのみユーザーへ確認する。

Python 依存: `requests` / `python-dotenv`（標準環境にない場合は `pip install -r requirements.txt`）。

## 手順

1. **入力を確定する**
   - `--prompt` で直接テキストを渡すか、`--prompt-file` で既存ファイルを渡す。
   - ドメイン固有のプロンプト組み立ては呼び出し側の責務とする。
2. **生成スクリプトを実行**
   ```powershell
   python .github/skills/gpt-image-2/scripts/generate.py `
     --prompt "<生成プロンプト>" `
     --out output/sample.png `
     --model <user-specified-model> `
     --size 1024x1024 `
     --quality medium
   ```
   - モデル名はユーザーが明示した名前を必ず使う。エージェント判断で別モデル名へ置き換えたり補完したりしない
   - `--model gpt-image-1.5` / `--model MAI-Image-2` などでモデル切替する場合も、ユーザー指定または `.env` の指定に従う（Foundry 上にデプロイ済みであること）
   - `--model` / `AZURE_OPENAI_IMAGE_MODEL` のいずれにもモデル名が無い場合はエラーで終了する
   - `--prompt-file <path>` で長文プロンプトをファイル渡し可
   - `--n 2` で複数枚生成（`_1.png` `_2.png` のように連番）
   - 旧 deployment パス方式は未サポート。v1 API 前提で利用する
3. **結果確認**
   - 生成された画像を指定出力先に保存
   - 画像が用途に合わなければプロンプトを調整して再実行

## 主要オプション

| 引数 | 既定値 | 説明 |
|------|--------|------|
| `--model` | なし | `gpt-image-2` / `gpt-image-1.5` / `gpt-image-1` / `MAI-Image-2` など。Foundry/Azure OpenAI リソースにデプロイ済みの名前をユーザーが明示指定。未指定時は環境変数を見て、それも無ければエラー |
| `--size` | `1024x1024` | `512x512` / `1024x1024` / `1024x1536` / `1536x1024` / `auto`（モデルごとにサポート範囲が異なる。512x512 未対応のモデル多し） |
| `--quality` | `medium` | `low` / `medium` / `high` / `auto` |
| `--n` | `1` | 生成枚数 |
| `--background` | （省略） | `transparent` 指定で透過PNG（gpt-image-1系のみ） |
| `--output-format` | `png` | `png` / `jpeg` |
| `--timeout` | `600` | HTTP読み取りタイムアウト秒。quality=high だと 1〜数分かかることあり |

## 参照

- [scripts/generate.py](./scripts/generate.py) — CLI 本体
- [references/api.md](./references/api.md) — Azure OpenAI Image API パラメータ早見表

## 注意

- APIキーをコードや出力に書き込まない（必ず環境変数経由）
- 生成画像はAzure OpenAIの利用規約・コンテンツポリシーに従う
- ドメイン固有のプロンプト要件は、このスキルではなく呼び出し側スキルまたはアプリ側で管理する
- 旧 deployment パス方式は未サポート。v1 API で動かない環境は対象外とする

## 呼び出し側との責務分離

- このスキルは「受け取った prompt / prompt-file を Azure OpenAI に送って画像を保存する」ことだけを担当する。
- カード用途のような専用プロンプト構造は呼び出し側で組み立てる。いきもの図鑑カードでは [card-params-extract/assets/prompt-template.md](../card-params-extract/assets/prompt-template.md) を参照する。
- パイプライン側は `generate.py` を呼ぶだけに留め、モデル選択や認証情報の扱いを再実装しない。

## モデル指定ルール

- モデル名は、ユーザーが `--model` で指定した値、またはユーザーが `.env` / 環境変数に設定した `AZURE_OPENAI_IMAGE_MODEL` の値だけを使う。
- 未指定時に `gpt-image-2` や他のモデル名を既定値として補完しない。
- `unknown_model` などの API エラーが出ても、エージェント判断で別モデルへ自動リトライしない。ユーザーに指定モデルの修正を依頼して停止する。
