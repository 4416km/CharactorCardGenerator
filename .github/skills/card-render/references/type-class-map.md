# タイプ ↔ CSS クラス対応表

`reference/zukan-card.css` で定義されているタイプバッジ用クラスとの対応表。
`scripts/render_card.py` の `TYPE_CLASS` 辞書と一致させること。

| タイプ語彙（params.json: `creature.types[]`） | CSS クラス | 配色イメージ |
|----------------------------------------------|-----------|--------------|
| 思索 | `type-badge--thought` | 淡い藤色 × 紺 |
| 観察 | `type-badge--observe` | 浅葱 × 深緑 |
| 創発 | `type-badge--emerge` | オレンジ × ブラウン |
| 行動 | `type-badge--action` | 朱赤 × バーガンディ |
| 共鳴 | `type-badge--resonate` | ターコイズ × 深緑 |
| 調律 | `type-badge--tune` | モスグリーン × 深緑 |

## 運用ルール

- パラメータ生成ルール §3.8 でタイプ語彙が追加されたら、本表と `TYPE_CLASS` の双方を更新する
- 未定義タイプが来た場合、レンダラは既定の `.type-badge` のみ付与する（色は中立 / 警告は出さない）
- 新タイプの CSS を追加するときは `reference/zukan-card.css` に `.type-badge--<class>` ルールを追記する

## 参考

- `reference/zukan-card.css` §「ゲーム要素」内 `.type-badge--*`
- [パラメータ生成ルール](../../card-params-extract/references/param-generation-rules.md) §3.8 タイプ
