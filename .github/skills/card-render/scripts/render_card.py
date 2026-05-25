"""params.json から いきもの図鑑カードの HTML を生成する CLI.

使用例:
    python render_card.py --params output/002_tanaka_taro/params.json \
                          --out output/002_tanaka_taro/card.html
    python render_card.py --params output/003_suzuki_tsubasa/params.json \
                          --out output/003_suzuki_tsubasa/card.html \
                          --image creature.png \
                          --css ../../reference/zukan-card.css

出力 HTML は reference/zukan-card.css のクラス体系に準拠した 1 ページ構成。
画像は --image（既定 creature.png）相対参照、CSS は --css（既定 ../../reference/zukan-card.css）相対参照。
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import sys
from pathlib import Path

TYPE_CLASS = {
    "思索": "thought",
    "観察": "observe",
    "創発": "emerge",
    "行動": "action",
    "共鳴": "resonate",
    "調律": "tune",
}

STAT_LABELS = {
    "endurance": "持久力",
    "drive": "推進力",
    "observation": "観察力",
    "burst": "瞬発力",
    "empathy": "共感力",
    "thinking": "思考力",
}

ENTRY_ORDER = [
    ("classification", "分類", True),
    ("appearance", "すがた・体色", True),
    ("habitat", "生息地", True),
    ("food", "食べもの", False),
    ("personality", "性格", False),
    ("behavior", "行動", True),
    ("growth", "成長条件", False),
    ("observation_note", "観察メモ", True),
]


def esc(value: object) -> str:
    return html_mod.escape("" if value is None else str(value), quote=True)


def render_type_badges(types: list[str]) -> str:
    parts = []
    for tp in types:
        cls = TYPE_CLASS.get(tp)
        cls_attr = f"type-badge type-badge--{cls}" if cls else "type-badge"
        parts.append(f'<span class="{cls_attr}">{esc(tp)}</span>')
    return "\n        ".join(parts)


def render_rarity(rarity: int) -> str:
    rarity = max(1, min(5, int(rarity)))
    return "★" * rarity + "☆" * (5 - rarity)


def render_stats(stats: dict) -> str:
    peaks = set(stats.get("peaks", []) or [])
    rows = []
    for key, label in STAT_LABELS.items():
        value = int(stats.get(key, 0))
        value = max(0, min(100, value))
        peak_cls = " stat-row--peak" if key in peaks else ""
        rows.append(
            f'<div class="stat-row{peak_cls}">'
            f'<span class="stat-label">{esc(label)}</span>'
            f'<span class="stat-bar"><span style="width:{value}%"></span></span>'
            f'<span class="stat-value">{value}</span>'
            f'</div>'
        )
    return "\n      ".join(rows)


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="affinity-tag">{esc(tg)}</span>' for tg in (tags or []))


def normalize_people(value: object) -> list[str]:
  if isinstance(value, list):
    return [str(item).strip() for item in value if str(item).strip()]
  if value is None:
    return []
  text = str(value).strip()
  if not text:
    return []
  for separator in ("\n", "；", ";"):
    text = text.replace(separator, "、")
  return [part.strip() for part in text.split("、") if part.strip()]


def render_person_list(people: list[str]) -> str:
  if not people:
    return ""
  return "".join(f'<strong>{esc(person)}</strong>' for person in people)


def display_western_name(western_name: object, real_name: object) -> str:
  western = str(western_name or "").strip()
  real = str(real_name or "").strip()
  if real:
    western = western.replace(f"（{real}）", "").strip()
  return western


def render_entries(entries: dict) -> str:
    parts = []
    for key, label, wide in ENTRY_ORDER:
        text = entries.get(key, "")
        if not text:
            continue
        wide_cls = " guide-entry--wide" if wide else ""
        parts.append(
            f'<div class="guide-entry{wide_cls}">'
            f'<dt>{esc(label)}</dt>'
            f'<dd>{esc(text)}</dd>'
            f'</div>'
        )
    return "\n      ".join(parts)


def render(params: dict, image_rel: str, css_rel: str) -> str:
    trainer = params.get("trainer", {})
    creature = params.get("creature", {})
    seq = params.get("sequence", "000")
    taxonomy = creature.get("taxonomy", {})
    stats = creature.get("stats", {})
    moves = creature.get("moves", {})
    sig = moves.get("signature", {})
    hid = moves.get("hidden", {})
    affinity = creature.get("affinity", {})
    weak = affinity.get("weak", {})
    resist = affinity.get("resist", {})
    evo = creature.get("evolution", {})
    entries = creature.get("entries", {})

    primary_name = creature.get("primary_name", "")
    alias = creature.get("alias", "")
    types = creature.get("types", []) or []
    rarity = creature.get("rarity", 1)
    caption = creature.get("caption", "").strip()

    real_name = trainer.get("real_name", "")
    real_kana = trainer.get("real_name_kana", "")
    western_name = trainer.get("western_name", "")
    department = trainer.get("department", "")
    recorders = normalize_people(trainer.get("recorder", ""))

    type_badges = render_type_badges(types)
    rarity_stars = render_rarity(rarity)
    stat_rows = render_stats(stats)
    weak_tags = render_tags(weak.get("tags", []))
    resist_tags = render_tags(resist.get("tags", []))
    entries_html = render_entries(entries)
    recorder_html = render_person_list(recorders)
    western_display = display_western_name(western_name, real_name)

    if not caption:
        caption = f"{real_name}{('（' + real_kana + '）') if real_kana else ''} の内面を架空のいきものとして描写。価値観・思考癖・仕事の進め方やこだわりを反映した内面生物。"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>いきもの図鑑 {esc(primary_name)}</title>
<link rel="stylesheet" href="{esc(css_rel)}">
</head>
<body>
<main>
<article class="field-guide-page" aria-label="いきもの図鑑カード">
  <div class="field-guide-plate">
    <div class="specimen-frame">
      <img class="creature-image" src="{esc(image_rel)}" alt="{esc(primary_name)}">
    </div>
    <p class="specimen-caption">{esc(caption)}</p>
    <div class="guide-note-grid">
      <div class="guide-note guide-note--trainer"><span>トレーナー</span><strong>{esc(western_display)}</strong><small>本名：{esc(real_name)}{('（' + esc(real_kana) + '）') if real_kana else ''}</small><small>所属：{esc(department)}</small></div>
      <div class="guide-note guide-note--observers"><span>観察者</span>{recorder_html}</div>
    </div>
  </div>

  <div class="field-guide-content">
    <header class="field-guide-header">
      <span class="specimen-number">いきものファイル</span>
      <h3>{esc(primary_name)}</h3>
      <p class="field-guide-alias">別名：{esc(alias)}</p>
      <div class="creature-meta-row">
        {type_badges}
        <span class="rarity-stars">{rarity_stars}</span>
      </div>
    </header>

    <div class="taxonomy-strip" aria-label="分類情報">
      <div><span>類</span><strong>{esc(taxonomy.get('class',''))}</strong></div>
      <div><span>属・種</span><strong>{esc(taxonomy.get('genus',''))} {esc(taxonomy.get('species',''))}</strong></div>
    </div>

    <section class="stat-panel" aria-label="ステータス">
      <h4 class="stat-panel-title">ステータス（6軸）</h4>
      {stat_rows}
    </section>

    <section class="move-cards" aria-label="わざ">
      <article class="move-card move-card--signature">
        <span class="move-kind">とくいわざ</span>
        <span class="move-power">威力 {esc(sig.get('power',''))}</span>
        <h4>{esc(sig.get('name',''))}</h4>
        <p class="move-service">{esc(sig.get('azure_service',''))}</p>
        <p class="move-desc">{esc(sig.get('description',''))}</p>
      </article>
      <article class="move-card move-card--hidden">
        <span class="move-kind">ひでんわざ</span>
        <span class="move-power">威力 {esc(hid.get('power',''))}</span>
        <h4>{esc(hid.get('name',''))}</h4>
        <p class="move-service">発動条件：{esc(hid.get('trigger',''))}</p>
        <p class="move-desc">{esc(hid.get('description',''))}</p>
      </article>
    </section>

    <section class="affinity-box" aria-label="弱点・耐性">
      <div class="affinity-cell affinity-cell--weak">
        <span class="affinity-label">弱点</span>
        {weak_tags}
        <p class="affinity-desc">{esc(weak.get('note',''))}</p>
      </div>
      <div class="affinity-cell affinity-cell--resist">
        <span class="affinity-label">耐性</span>
        {resist_tags}
        <p class="affinity-desc">{esc(resist.get('note',''))}</p>
      </div>
    </section>

    <section class="evolution-chain" aria-label="進化チェーン">
      <div class="evo-node"><small>前</small><b>{esc(evo.get('previous',''))}</b></div>
      <div class="evo-arrow">▶</div>
      <div class="evo-node evo-node--current"><small>現</small><b>{esc(evo.get('current',''))}</b></div>
      <div class="evo-arrow">▶</div>
      <div class="evo-node"><small>次</small><b>{esc(evo.get('next',''))}</b></div>
    </section>

    <blockquote class="flavor-quote">{esc(creature.get('flavor_quote',''))}</blockquote>

    <dl class="field-guide-entries">
      {entries_html}
    </dl>
  </div>
</article>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="いきもの図鑑カード HTML レンダラ")
    parser.add_argument("--params", required=True, help="params.json のパス")
    parser.add_argument("--out", required=True, help="出力 card.html のパス")
    parser.add_argument(
        "--image",
        default="creature.png",
        help="HTML から見た画像の相対パス（既定: creature.png）",
    )
    parser.add_argument(
        "--css",
        default="../../reference/zukan-card.css",
        help="HTML から見た CSS の相対パス（既定: ../../reference/zukan-card.css）",
    )
    args = parser.parse_args()

    params_path = Path(args.params)
    if not params_path.is_file():
        sys.exit(f"ERROR: params.json が見つかりません: {params_path}")
    try:
        params = json.loads(params_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: params.json のパースに失敗: {e}")

    html = render(params, args.image, args.css)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"OK: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
