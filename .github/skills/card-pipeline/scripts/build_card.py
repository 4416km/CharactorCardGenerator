"""card-pipeline: 画像生成 + カード HTML 生成のまとめ実行スクリプト.

前提:
        - 対象フォルダに params.json と image-prompt.md が既にある
            (card-params-extract スキルで生成済み)
        - 画像生成まわりの認証・モデル設定は gpt-image-2 側で解決できる

使用例:
        python build_card.py --folder output/003_suzuki_tsubasa
        python build_card.py --folder output/003_suzuki_tsubasa --force-image
        python build_card.py --folder output/003_suzuki_tsubasa --skip-image
"""

from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser(description="card-pipeline: 画像 + HTML まとめ実行")
    ap.add_argument("--folder", required=True, help="対象フォルダ（output/<###>_<name>/）")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default="medium",
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
    print(f"  image  : {image_path} {'(skipped)' if args.skip_image else ''}")
    print(f"  card   : {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
