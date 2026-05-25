# いきもの図鑑カード生成キット

インタビュー記録から「架空のいきものカード」を生成するための VS Code Copilot スキル、画像生成 CLI、HTML レンダラ、参照データをまとめたリポジトリです。

このリポジトリには、実インタビュー・生成済みカード・公開に不要な資料は含めません。利用者はローカルにクローンまたはダウンロードし、`.env` と `input/` 配下のインタビュー記録を追加して使います。

## 含まれるもの

- `.github/skills/`: Copilot Agent 用スキル
  - `card-params-extract`: インタビューから `params.json` / `image-prompt.md` / `extraction-log.md` を生成
  - `gpt-image-2`: Azure OpenAI / Foundry の GPT-Image 系モデルで PNG を生成
  - `card-html-generate`: `params.json` と `creature.png` から `card.html` を生成
  - `card-pipeline`: 生成済みパラメータから画像生成と HTML 生成をまとめて実行
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

`.env`、`input/` の実インタビュー、`output/` の生成物は `.gitignore` で除外しています。

## 使い方

1. `reference/interview-template.txt` をコピーし、`input/インタビュー_<名前>.txt` として保存します。
2. VS Code Copilot Agent に、対象ファイルを指定して `card-params-extract` または `card-pipeline` を実行するよう依頼します。
3. `output/<folder>/params.json` と `output/<folder>/image-prompt.md` ができたら、画像と HTML を生成します。

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

生成される主なファイル:

- `output/<folder>/params.json`
- `output/<folder>/extraction-log.md`
- `output/<folder>/image-prompt.md`
- `output/<folder>/creature.png`
- `output/<folder>/card.html`

## 直接実行できる CLI

画像生成のみ:

```powershell
python .github/skills/gpt-image-2/scripts/generate.py `
  --prompt-file output/<folder>/image-prompt.md `
  --out output/<folder>/creature.png `
  --size 1024x1024 `
  --quality medium
```

HTML 生成のみ:

```powershell
python .github/skills/card-html-generate/scripts/render_card.py `
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