# いきもの図鑑カード画像プロンプト雛形

いきもの図鑑カード用のキャラクター画像プロンプトを組み立てるための雛形。
インタビュー記録から抽出した項目で `{{...}}` を埋め、最終的な英語プロンプトを作る。

## 共通スタイル（固定）

> A friendly creature-encyclopedia illustration in the style of a modern monster-collecting card game.
> Single original fictional creature (NOT a real-world animal, NOT a copyrighted character).
> Clean digital painting, soft shading, vivid but harmonious palette,
> centered subject on a neutral pale background, no text, no logos, no watermarks,
> square composition with a subtle ground shadow. Family-friendly, cute, dignified.

## 可変パート（雛形）

```text
Creature concept: {{creature_concept}}
Inspired by traits: {{key_traits}}
Color palette: {{colors}}
Form / posture: {{posture}}
Distinguishing features: {{features}}
Vibe / mood: {{mood}}
```

## 埋め方ガイド

| フィールド | 抽出元（インタビュー記録の項目） |
|-----------|-------------------------------|
| `creature_concept` | §1「自分を姿を動物に例えるなら」「自分の内面を動物に例えるなら」と §4 各観察者メモの「この人を動物に例えると？」の動物イメージ |
| `key_traits` | 「2. 仕事での姿」「4. その人らしさのまとめ」から3〜5語 |
| `colors` | §1「好きな色」 |
| `posture` | 「大きさ・素早さ・動き方のイメージ」 |
| `features` | 「すがたや体色に入れたい特徴」 |
| `mood` | 「素の性格がわかる一言」「周囲から見た魅力」 |

## 禁則

- 実在の人物名・会社名・サービス名を直接書かない
- 「Pokemon」「Pikachu」など既存IPの名称を書かない
- 「AI画像で避けたい表現」に挙げられた要素は Negative として明示する

## 出力例（参考）

```text
A friendly creature-encyclopedia illustration in the style of a modern monster-collecting card game.
Single original fictional creature, centered on a pale mint background, soft digital painting,
no text, no logos.
Creature concept: a small fox-like guardian with a gentle scholar vibe
Inspired by traits: calm, observant, supportive, quietly persistent
Color palette: navy, silver, soft moonlight white
Form / posture: standing, slight forward lean, alert ears
Distinguishing features: a glowing keyring tail, round glasses-like markings around the eyes
Vibe / mood: trustworthy, quietly confident, warm
Do not include: text, logos, weapons, dark/scary atmosphere.
```