---
name: card-params-extract
description: 'input/ 配下のインタビュー記録テキスト 1 件を読み、いきものカード生成に必要なパラメータ一式を JSON 形式で抽出するスキル。同時に各パラメータの導出理由を Markdown ログとして保存。画像生成プロンプト用の構造化フィールド（creature_concept / colors / posture / features / mood / negative）も含む。WHEN: いきものカードのパラメータを抽出、インタビュー記録から JSON 化、カード生成前の構造化、画像プロンプトを構造化、抽出ログを残す、いきもの図鑑のパラメータ生成。'
argument-hint: 'input フォルダ内のインタビューファイル名（例: インタビュー_田中太郎.txt）'
---

# card-params-extract: インタビュー → カード生成パラメータ抽出スキル

**1 名分のインタビュー記録テキスト**から、いきものカード生成に必要なすべてのパラメータを抽出し、JSON + 推論ログ（Markdown）として保存する。

このスキルは **抽出と整形に専念**し、画像生成や HTML 生成は行わない（後続スキル [gpt-image-2](../gpt-image-2/SKILL.md) や HTML テンプレート展開側で利用する）。

## 利用ケース

- ワークショップ後、`input/インタビュー_*.txt` を 1 件指定して JSON 化
- カード生成前のレビュー素材として「なぜこの語彙になったか」をログで提示
- 後段の画像生成スキルへ `image_prompt` パラメータをそのまま渡す

## 前提

- 入力ファイルは `input/` フォルダ配下に存在（テンプレート原本: [reference/interview-template.txt](../../../reference/interview-template.txt) ／ パラメータ生成ルール: [references/param-generation-rules.md](./references/param-generation-rules.md) §1）
- 参考リソース:
  - 固定わざ表: `reference/azure-move-map.json`（存在しない場合はわざ説明を AI 補完）
  - パラメータ生成ルール（生物名・分類・ステータス・わざ・進化チェーン等）: [references/param-generation-rules.md](./references/param-generation-rules.md) §3
- 出力先: `output/{連番3桁}_{氏名ローマ字}/`
  - 連番は `input/` 内のファイル名昇順ソートを基準に採番
  - 既に同名フォルダがあればそれを再利用（params.json と extraction-log.md を上書き）

## 手順

1. **入力ファイルを読む**
   - `read_file` で `input/<指定ファイル名>` を全文取得
   - 見出し（`■ 0.` 〜 `■ 4.`）でセクション分割し、各キー：値を抽出
2. **必須項目チェック**
  - `対象者の名前（漢字/よみ）`, `所属・チーム名`, `得意・好き・よく使うAzureサービス` のいずれかが空なら**追加質問フェーズ（手順 2.5）へ**
3. **出力フォルダ決定**
   - `input/` を `list_dir` し、対象ファイルの昇順位置から連番を確定
   - 氏名ローマ字（ヘボン式・小文字・スペース→`_`）でフォルダ名生成
4. **`reference/azure-move-map.json` を読む（存在すれば）**
   - 「得意Azureサービス」「苦手Azureサービス」を照合し、わざ名・効果を引き当て
5. **[references/param-generation-rules.md](./references/param-generation-rules.md) §3 のルールに沿ってパラメータを決定**
   - 生物名 / 別名 / 分類 / トレーナー欧米名 / タイプ ×2 / レアリティ / 6軸ステータス / とくいわざ / ひでんわざ / 弱点 / 耐性 / 進化チェーン / フレーバー / 各項目テキスト
   - **情報不足検知**: 下記「§ 追加質問の判定基準」のいずれかに該当する場合、推測で埋めずに**手順 5.5（追加質問フェーズ）へ**
6. **画像生成プロンプト用フィールドを構築**
   - §1「自分を姿を動物に例えるなら」「自分の内面を動物に例えるなら」「好きな色」と §4「この人を動物に例えると？」「この人に似あう色は？」を主軸に `creature_concept / key_traits / colors / posture / features / mood / negative` を英語キーワード化
   - 「動物の例え」と「色」のどちらかが §1/§4 双方とも欠落している場合は**手順 5.5（追加質問フェーズ）へ**
7. **JSON とログを保存**
   - `create_file` で `output/<###>_<name>/params.json`（後述スキーマ）
   - `create_file` で `output/<###>_<name>/extraction-log.md`（後述フォーマット）
   - `create_file` で `output/<###>_<name>/image-prompt.md`（後述フォーマット）
     - `params.image_prompt.final_prompt` を本文として、メタ情報（モデル / サイズ / 品質 / negative）と画像生成コマンド例を併記
     - 後段の [gpt-image-2](../gpt-image-2/SKILL.md) スキルが `--prompt-file` で直接参照できる形にする
8. **完了報告**
   - 保存先パス・主要パラメータ（生物名、タイプ、レアリティ、とくいわざ）を要約表示

## 出力スキーマ（`params.json`）

```json
{
  "schema_version": "0.1",
  "source_file": "input/インタビュー_田中太郎.txt",
  "observed_date": "2026/05/22",
  "sequence": "002",
  "folder_name": "002_tanaka_taro",
  "trainer": {
    "real_name": "田中 太郎",
    "real_name_kana": "たなか たろう",
    "western_name": "テオ・フィールドハート（田中 太郎）",
    "department": "クラウド技術本部",
    "recorder": "山田 静香"
  },
  "creature": {
    "primary_name": "ハシリビ",
    "alias": "朱火の即興ハヤブサ",
    "taxonomy": {
      "class": "創発類",
      "genus": "速駆ハヤブサ属",
      "species": "即興種",
      "sentence": "創発類の一種で、速駆ハヤブサ属の即興種として分類される。"
    },
    "types": ["創発", "行動"],
    "rarity": 4,
    "stats": {
      "endurance": 70,
      "drive": 92,
      "observation": 75,
      "burst": 95,
      "empathy": 65,
      "thinking": 70,
      "peaks": ["drive", "burst"]
    },
    "moves": {
      "signature": {
        "name": "イベントトリガー",
        "azure_service": "Azure Functions",
        "power": 85,
        "description": "..."
      },
      "hidden": {
        "name": "ハシリギメ",
        "trigger": "雑な相談を受けたとき",
        "power": 95,
        "description": "..."
      }
    },
    "affinity": {
      "weak": { "tags": ["長時間座学"], "note": "..." },
      "resist": { "tags": ["突発負荷", "曖昧な仕様"], "note": "..." }
    },
    "evolution": {
      "previous": "ハシリコ",
      "current": "ハシリビ",
      "next": "ハシリビノタイショウ"
    },
    "flavor_quote": "議論を、走るプロトに変える瞬発の火。",
    "caption": "会議の途中で「ちょっと作ってきます」と本当に走り出すタイプのハヤブサ。雑な相談を投げかけた瞬間に足元の炎がぼっと燃え上がり、気づくと動くデモが置いてある。長時間の検討会には弱く、座って 3 時間目で羽の縁の朱色がしんぼり始める。",
    "entries": {
      "classification": "...",
      "appearance": "...",
      "habitat": "...",
      "food": "...",
      "personality": "...",
      "behavior": "...",
      "growth": "...",
      "observation_note": "..."
    }
  },
  "image_prompt": {
    "creature_concept": "a small fictional falcon-like creature with sneaker-shaped feet",
    "key_traits": ["fast", "improvising", "rhythmic", "warm"],
    "colors": ["vermillion red", "morning-sky pale blue", "ember orange"],
    "posture": "mid-stride, forward-leaning, ready to dash",
    "features": ["vermillion-trimmed wings", "tiny ember markings on feet"],
    "mood": "energetic, friendly, dignified",
    "negative": ["humanoid", "weapons", "photorealistic raptor", "blood", "dark tone"],
    "size": "1024x1024",
    "quality": "medium",
    "model_recommendation": "gpt-image-2"
  }
}
```

### フィールドの根拠

| フィールド | 由来 | ルール |
|-----------|------|------|
| `trainer.western_name` | §0 `対象者の名前（漢字/よみ）` から音派生 + 漢字意味派生 | §3.7 |
| `creature.primary_name` | カタカナ 8〜20 文字。エピソード語感由来 | §3.1 |
| `creature.alias` | `{色or状態}の{動作}{生物}` | §3.2 |
| `creature.taxonomy` | 「類」=働き方、「属種」=造語 | §3.3 |
| `creature.caption` | カード画像下のキャプション。2～3 文・ユーモア調 | §3.5 |
| `creature.types` | 主=類、副=行動傾向 | §3.8 |
| `creature.rarity` | エピソードの豊かさで 1〜5 | §3.9 |
| `creature.stats` | ピーク 1〜2 を 90‐100、中間 60‐80、低 40‐55 | §3.10 |
| `creature.moves.signature` | 得意Azureサービス → `azure-move-map.json` | §3.6 |
| `creature.moves.hidden` | 個体独自の造語必殺技、発動条件付き | §3.11 |
| `creature.affinity` | 1〜3 タグ、前向き表現 | §3.6 / §3.12 |
| `creature.evolution` | 前形態（簡略）→現→次（拡張） | §3.13 |
| `creature.flavor_quote` | 20〜35 字、観察者コメントなどから | §3.14 |
| `image_prompt.*` | §1 「動物の例え」「好きな色」 / §4 「この人を動物に例えると？」「似あう色は？」中心。英語キーワード | §3.15 / gpt-image-2 スキル assets/prompt-template.md |

ルールの詳細は [references/param-generation-rules.md](./references/param-generation-rules.md) を参照。

`trainer.recorder` は単一名なら文字列、複数名なら配列または `、` 区切り文字列で保存してよい。HTML レンダラは複数名を個別行で表示する。

## 推論ログ（`extraction-log.md`）

各パラメータの「どの入力箇所をどう解釈したか」を 1 セクション 3〜6 行で記録する。

```markdown
# 抽出ログ: インタビュー_田中太郎.txt

## メタ
- 連番: 002
- 出力フォルダ: output/002_tanaka_taro
- 必須項目チェック: OK
- 抽出日時: 2026-05-22

## 1. トレーナー
- 実名「田中 太郎」（よみかた「たなか たろう」）から欧米風名を生成:
  - 「太郎」→ Theo（Theodore = 神の贈り物 / 一郎=英雄系の音）
  - 「田中」→ Fieldheart（田=field、中=heart のメタファー）
  - 採用: **テオ・フィールドハート（田中 太郎）**
- 所属「クラウド技術本部」はトレーナー欄の所属として表示
- 記録係「山田 静香」は params.trainer.recorder へ格納し、観察者欄へ表示。複数名の場合は配列または `、` 区切りで保持

## 2. 生物名・別名・分類
- §1「最近ハマっている＝トレイルランニング」「§5 動物例＝ハヤブサ」「§5 すがた＝足元に炎」
  → "走る + 炎" を主モチーフとし、**生物名「ハシリビ」** を採用
- 別名: §5 似合う色「朱赤」+ §2 「即興のプロトタイプ」→ **「朱火の即興ハヤブサ」**
- 類: §2「走り出して考える」= 行動先行 → **創発類**（思索類との対比）
- 属種: ハヤブサ + 即興 → **速駆ハヤブサ属 即興種**

## 3. タイプ・レアリティ・ステータス
- 主タイプ: 類と同じ **創発**
- 副タイプ: §2「とにかく走り出す」= **行動**
- レアリティ: §6 IV係コメントの具体性 + §2 自分らしいエピソードがあるため **★★★★☆**
- ピーク: §2「動き出しが早い」「議論より先にデモ」→ **推進力 92 / 瞬発力 95**
- ボトム: §3「Azure SQL Database が苦手」「きっちりした設計は腰が重い」→ **共感力 65**（修行中）

## 4. わざ
- とくいわざ: §3「Azure Functions」「Event Grid」「Logic Apps」のうち、§2 エピソード「Functions でデモAPI即席」に裏付けあり → **Azure Functions** を選定
  - `azure-move-map.json` 参照 → 「イベントトリガー」採用、威力 85
- ひでんわざ: §2「雑な相談大歓迎」「議論→デモ」の瞬間芸 → **「ハシリギメ」** を造語、発動条件「雑な相談を受けたとき」

## 5. 弱点・耐性
- 弱点: §1「終わりの見えない検討会」 → **「長時間座学」**
- 耐性: §2「PoC / ハッカソン / 突発障害」 → **「突発負荷」「曖昧な仕様」**
- いずれも前向き表現で記述（[references/param-generation-rules.md](./references/param-generation-rules.md) §3.4 / §3.12）

## 6. 画像プロンプト
- creature_concept: §5 動物「ハヤブサ」 + §5 道具「スニーカー」 → falcon-like + sneaker feet
- colors: §5 似合う色「朱赤、晴れた朝」 → vermillion / morning-sky pale blue / ember
- features: §5「羽の縁が朱色、足元に炎」 → wings trim + ember markings
- negative: §5「AI画像で避けたい：人型、武器、写実猛禽の血、暗いトーン」をそのまま英訳
- 推奨サイズ/品質: 1024x1024 / medium（既定の安定値）

## 7. 残課題 / 留意点
- §3 苦手サービスが「Azure SQL Database」と明記済みのため、デフォルト AKS への置換は不要
- IV係コメントが厚いため、フレーバーキャッチコピーは IV係発言「議論を動くプロトに変える瞬発力」を 25 字に圧縮して採用
```

## 画像生成プロンプト（`image-prompt.md`）

`params.image_prompt.final_prompt` を主役にした、後段の画像生成スキル向け単独ファイル。Markdown 内のコードブロック部分は、そのままプロンプトとして利用される想定。

### フォーマット

```markdown
# 画像生成プロンプト: {生物名}（{連番}）

- 対象: {対象者の名前}（{所属・チーム名}）
- 生物名: {primary_name} ／ 別名: {alias}
- 推奨モデル: {model_recommendation}
- 推奨サイズ: {size} ／ 品質: {quality}
- 出力ファイル想定: `creature.png`
- 元データ: [params.json](./params.json) ／ [extraction-log.md](./extraction-log.md)

## プロンプト（gpt-image-2 にそのまま渡す）

```text
{final_prompt}
```

## 避ける表現（negative）

- {negative[0]}
- {negative[1]}
- ...

## 画像生成コマンド例

```powershell
python .github/skills/gpt-image-2/scripts/generate.py `
  --prompt-file output/{folder_name}/image-prompt.md `
  --out output/{folder_name}/creature.png `
  --size {size} `
  --quality {quality} `
  --model {model_recommendation}
```

> `--prompt-file` は本ファイル全体を読み込むため、不要な見出しが混ざる場合は ` ```text ... ``` ` ブロックのみを別 `.txt` に書き出して渡してもよい。
```

### ルール

- ファイル名は固定で `image-prompt.md`
- 本文の英語プロンプトブロックは ` ```text ` フェンスで囲い、整形・引用記号を含めない
- `negative` リストは箇条書きで全件列挙
- 推奨モデルは「動作確認済モデル（gpt-image-2 / gpt-image-1.5）」のいずれかに限定する

## エラーハンドリング

| ケース | 動作 |
|--------|------|
| 必須項目（名前（漢字/よみ）/所属/得意Azure）が空 | **追加質問フェーズへ**（後述）。質問してもユーザーが「不明」と回答した場合のみ停止 |
| ファイルが存在しない | パスを明示してエラー |
| `azure-move-map.json` が無い | 警告ログを残し、わざ名/効果を AI 補完で生成（log にその旨記録）|
| 出力先フォルダの既存ファイル | 上書きする（事前確認は省略） |

## 追加質問フェーズ（情報不足時の挙動）

インタビュー記録が薄い／空欄が多い場合、**推測で埋めず**にユーザーへ追加質問を投げる。質問は会話 UI（チャット）に対して投げ、ユーザー回答を取り込んでから抽出を続行する。

### 追加質問の判定基準

以下のいずれかに該当したら追加質問を発動する。

| 区分 | 条件 |
|------|------|
| 必須欠落 | §0 の `対象者の名前（漢字/よみ）` `所属・チーム名` のいずれかが空 |
| わざ決定不能 | §3「得意・好き・よく使うAzureサービス」が空、または `azure-move-map.json` に該当エントリなし |
| 個性材料不足 | §2 + §4 + §6 の合計埋まり項目数が **5 項目未満** |
| 画像材料不足 | §1「動物の例え」「好きな色」 と §4「この人を動物に例えると？」「似あう色」 が双方とも空欄 |
| 矛盾検知 | §2 と §4 で「らしさ」が真逆（例: 「慎重」と「即断即決」）で、優先判断が付かない |

### 質問の出し方

1. **まとめて 1 度に質問する**（往復回数を最小化）
2. 質問数は **最大 5 件**まで。最低限カードが破綻しないラインに絞る
3. 各質問は短文（30 字以内）＋必要なら 2〜4 個の選択肢提示
4. UI 形式: チャット本文で番号付きリストで提示するか、可能なら `vscode_askQuestions` 相当の構造化フォームを利用
5. 質問前に「以下が不足しているため追加で伺います」と明示し、対象フィールド名を併記
6. ユーザー回答後、回答内容を `extraction-log.md` の「追加ヒアリング」セクションに**そのまま引用**して残す

### 質問テンプレート例

```
インタビュー記録に以下の不足がありました。カードを破綻なく仕上げるため、5 項目だけ追加で教えてください。

1. 【必須】対象者の「よみかた」を教えてください（例: たなか たろう）
2. 【画像】似合う色を 1〜3 語で（例: 朱赤、深緑、銀）
3. 【画像】動物・植物・道具で例えるなら？（例: ハヤブサ、ランタン）
4. 【わざ】得意・好きな Azure サービスを 1 つ（例: Azure Functions）
5. 【らしさ】「素の性格がわかる一言」を 20 字以内で
```

### ユーザーが「不明」「お任せ」と回答した場合

- 必須項目（名前（漢字/よみ）/所属）が依然不明 → 停止し、入力ファイル修正を依頼
- 画像材料・わざ・らしさが不明 → デフォルト（[references/param-generation-rules.md](./references/param-generation-rules.md) §3.6 のデフォルト AKS、汎用パレット「藍色×銀×淡白」、汎用動物「フクロウ」など）で補完し、`extraction-log.md` に**デフォルト適用の根拠**を明記
- 補完したフィールドは `params.json` のフィールドコメント代わりに、対応するログセクションへ「source: default-fallback」と記す

### スキップしてよいケース

- ユーザーが最初の指示で「足りない部分は推測で埋めて」「質問せずに進めて」と明示した場合
- バッチ処理（複数ファイル一括）モードで運用される場合（その旨を呼出側が宣言）
- いずれも `extraction-log.md` 冒頭に「追加質問スキップ: 理由」を記録



## 参照

- パラメータ生成ルール: [references/param-generation-rules.md](./references/param-generation-rules.md)
- 画像生成スキル: [gpt-image-2/SKILL.md](../gpt-image-2/SKILL.md)
- 画像プロンプト雛形: [gpt-image-2/assets/prompt-template.md](../gpt-image-2/assets/prompt-template.md)
- スキーマ例: [assets/example-params.json](./assets/example-params.json)

## 注意

- 実名そのものは `trainer.real_name` のみに保持し、`creature.*` 側へ書き込まない
- 入力テキスト内のセンシティブな個人情報（家族・住所・健康など）は JSON にもログにも転記しない
- ログは「導出理由」を簡潔に残すことが目的。長文の心理分析は不要
