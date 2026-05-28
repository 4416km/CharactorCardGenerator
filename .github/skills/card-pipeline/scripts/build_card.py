"""card-pipeline: 画像生成 + カード HTML 生成のまとめ実行スクリプト.

前提:
        - 対象フォルダに params.json と image-prompt.md が既にある
            (card-params-extract スキルで生成済み)
        - 画像生成まわりの認証・モデル設定は gpt-image-2 側で解決できる

使用例:
    python build_card.py --folder output/260528143015_鈴木つばさ
    python build_card.py --folder output/260528143015_鈴木つばさ --force-image
    python build_card.py --folder output/260528143015_鈴木つばさ --skip-image
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
GPT_IMAGE_SCRIPT = REPO_ROOT / ".github" / "skills" / "gpt-image-2" / "scripts" / "generate.py"
RENDER_SCRIPT = REPO_ROOT / ".github" / "skills" / "card-render" / "scripts" / "render_card.py"


def run(cmd: list[str]) -> int:
    print("$ " + " ".join(str(c) for c in cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def copy_source_interview(params_path: Path, folder: Path) -> Path | None:
    try:
        params = json.loads(params_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: params.json のパースに失敗: {exc}")

    source_value = str(params.get("source_file", "") or "").strip()
    if not source_value:
        print("[skip] params.source_file が空のため、元インタビューのコピーをスキップ")
        return None

    source_path = Path(source_value)
    if not source_path.is_absolute():
        source_path = REPO_ROOT / source_path
    if not source_path.is_file():
        print(f"[warn] 元インタビューが見つかりません: {source_path}", file=sys.stderr)
        return None

    dest_value = str(params.get("source_interview_copy", "") or "").strip()
    dest_rel = Path(dest_value) if dest_value else Path("source") / source_path.name
    if dest_rel.is_absolute() or ".." in dest_rel.parts:
        print(f"[warn] source_interview_copy が相対パスではないため既定値を使います: {dest_value}", file=sys.stderr)
        dest_rel = Path("source") / source_path.name

    dest_path = folder / dest_rel
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    print(f"[copy] 元インタビュー: {dest_path}")
    return dest_path


def main() -> int:
    ap = argparse.ArgumentParser(description="card-pipeline: 画像 + HTML まとめ実行")
    ap.add_argument("--folder", required=True, help="対象フォルダ（output/YYMMDDHHMMSS_<氏名漢字>/）")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default="low",
                    choices=["low", "medium", "high", "auto"])
    ap.add_argument("--force-image", action="store_true",
                    help="既存 creature.png を上書き再生成")
    ap.add_argument("--skip-image", action="store_true",
                    help="画像生成をスキップして HTML のみ作る")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        sys.exit(f"ERROR: フォルダが存在しません: {folder}")

    params_path = folder / "params.json"
    prompt_path = folder / "image-prompt.md"
    image_path = folder / "creature.png"
    card_path = folder / "card.html"

    if not params_path.is_file():
        sys.exit(f"ERROR: {params_path} が見つかりません。先に card-params-extract を実行してください。")

    source_copy_path = copy_source_interview(params_path, folder)

    python_exe = sys.executable

    # ステップ B: 画像生成
    if args.skip_image:
        print(f"[skip] 画像生成をスキップ: {image_path}")
    elif image_path.exists() and not args.force_image:
        print(f"[skip] 既存画像を再利用: {image_path} (--force-image で上書き)")
    else:
        if not prompt_path.is_file():
            sys.exit(f"ERROR: {prompt_path} が見つかりません。先に card-params-extract を実行してください。")
        if not GPT_IMAGE_SCRIPT.is_file():
            sys.exit(f"ERROR: gpt-image-2 スクリプトが見つかりません: {GPT_IMAGE_SCRIPT}")

        cmd = [
            python_exe, str(GPT_IMAGE_SCRIPT),
            "--prompt-file", str(prompt_path),
            "--out", str(image_path),
            "--size", args.size,
            "--quality", args.quality,
        ]
        rc = run(cmd)
        if rc != 0:
            print(f"[warn] 画像生成に失敗 (exit={rc})。HTML 生成は続行します。", file=sys.stderr)

    # ステップ C: HTML 生成
    if not RENDER_SCRIPT.is_file():
        sys.exit(f"ERROR: render_card.py が見つかりません: {RENDER_SCRIPT}")

    cmd = [
        python_exe, str(RENDER_SCRIPT),
        "--params", str(params_path),
        "--out", str(card_path),
    ]
    rc = run(cmd)
    if rc != 0:
        sys.exit(f"ERROR: HTML 生成に失敗 (exit={rc})")

    print()
    print("=== 完了 ===")
    print(f"  params : {params_path}")
    if source_copy_path:
        print(f"  source : {source_copy_path}")
    print(f"  image  : {image_path} {'(skipped)' if args.skip_image else ''}")
    print(f"  card   : {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
