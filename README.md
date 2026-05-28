# いきもの図鑑カード生成キット

インタビュー記録から「架空のいきものカード」を生成するための VS Code Copilot スキル、画像生成 CLI、HTML レンダラ、参照データをまとめたリポジトリです。

このリポジトリには、実インタビュー・生成済みカード・公開に不要な資料は含めません。利用者はローカルにクローンまたはダウンロードし、`.env` と `input/` 配下のインタビュー記録を追加して使います。

## 含まれるもの

- `.github/skills/`: Copilot Agent 用スキル
  - `card-params-extract`: インタビューから `params.json` / `image-prompt.md` / `extraction-log.md` を生成
  - `gpt-image-2`: Azure OpenAI / Foundry の GPT-Image 系モデルで任意プロンプトから画像を生成
  - `card-render`: `params.json` と `creature.png` から `card.html` を生成
  - `card-pipeline`: インタビューから抽出・画像生成・HTML レンダリングまでまとめて実行
- `reference/`: 入力テンプレート、Azure サービス別わざ表、カード CSS
- `.env.example`: Azure OpenAI / Foundry 接続設定のサンプル
- `requirements.txt`: Python CLI の最小依存関係

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

`.env` を開き、自分の Azure OpenAI / Foundry リソースに合わせて設定します。

```dotenv
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_IMAGE_MODEL=gpt-image-2
```

画像モデル名は `AZURE_OPENAI_IMAGE_MODEL` または実行時の `--model` で必ず指定します。未指定時の既定モデルはありません。

`.env`、`input/` の実インタビュー、`output/` の生成物は `.gitignore` で除外しています。

## 使い方

基本的には、VS Code の Copilot Chat で **Agent モード**を開き、日本語で依頼します。

たとえば、インタビューシートのひな型を作りたい場合:

```text
空野ひかりさんのインタビューシートのひな型を作ってください。
```

インタビューシートを埋めたあと、カードまで生成したい場合:

```text
空野ひかりさんのカードを生成してください。
```

既存のインタビュー記録を指定してカード化したい場合:

```text
input/インタビュー_空野ひかり.txt からカードを生成してください。
```

Agent は必要に応じて `card-params-extract` / `gpt-image-2` / `card-render` / `card-pipeline` の各スキルを使い、`output/YYMMDDHHMMSS_<氏名漢字>/` に生成物を保存します。

例: `output/260528143015_空野ひかり/`

出力フォルダ名の先頭は生成時刻、末尾はインタビュー内の漢字氏名です。連番とローマ字名は使いません。

生成される主なファイル:

- `output/<folder>/params.json`
- `output/<folder>/extraction-log.md`
- `output/<folder>/image-prompt.md`
- `output/<folder>/source/インタビュー_<氏名>.txt`
- `output/<folder>/creature.png`
- `output/<folder>/card.html`

元インタビューも `source/` 配下にコピーされるため、人物ごとに別の場所へ退避・共有する場合は `output/<folder>/` を丸ごとコピーできます。

### CLI で続きの処理を実行する場合

`params.json` と `image-prompt.md` ができた後は、以下のコマンドでも画像と HTML を生成できます。

```powershell
python .github/skills/card-pipeline/scripts/build_card.py --folder output/<folder>
```

画像を作り直したい場合:

```powershell
python .github/skills/card-pipeline/scripts/build_card.py --folder output/<folder> --force-image
```

HTML だけ作り直したい場合:

```powershell
python .github/skills/card-pipeline/scripts/build_card.py --folder output/<folder> --skip-image
```

## 直接実行できる CLI

画像生成のみ:

```powershell
python .github/skills/gpt-image-2/scripts/generate.py `
  --prompt-file output/<folder>/image-prompt.md `
  --out output/<folder>/creature.png `
  --model <your-image-model> `
  --size 1024x1024 `
  --quality low
```

HTML 生成のみ:

```powershell
python .github/skills/card-render/scripts/render_card.py `
  --params output/<folder>/params.json `
  --out output/<folder>/card.html
```

## 公開・運用時の注意

- API キーやエンドポイントを `.env.example`、README、生成物に書き込まないでください。
- 実インタビューには個人情報が含まれるため、`input/` の中身は公開しないでください。
- `params.json` と `extraction-log.md` にも個人情報や推論過程が含まれ得ます。公開対象にする場合は必ずレビューしてください。
- 画像プロンプトでは既存 IP 名や実在人物そのものの描写を避け、オリジナルの架空生物として表現してください。

## ディレクトリ構成

```text
.
├── .github/skills/
├── input/
├── output/
├── reference/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## ライセンス

このリポジトリは MIT License で公開しています。詳細は [LICENSE](LICENSE) を参照してください。