"""Azure OpenAI / Foundry GPT-Image 系モデルを呼び出して PNG を生成する CLI.

対応 API:
    v1         Foundry Models REST API v1
               POST {endpoint}/openai/v1/images/generations?api-version=preview

使用例:
    python generate.py --prompt "a forest fox spirit" --out out.png --model gpt-image-1.5
    python generate.py --prompt-file prompt.txt --out card.png --model gpt-image-1.5 --size 1024x1536 --quality high
    python generate.py --prompt "..." --out o.png --model gpt-image-1.5
    python generate.py --prompt "..." --out o.png --model MAI-Image-2
    python generate.py --prompt "..." --out sample.png --model gpt-image-1.5 --n 3

環境変数:
    AZURE_OPENAI_ENDPOINT          例: https://<resource>.openai.azure.com/
    AZURE_OPENAI_API_KEY           リソースAPIキー
    AZURE_OPENAI_IMAGE_MODEL       使用モデル名 (例: gpt-image-2 / gpt-image-1.5 / MAI-Image-2)。未指定ならエラー
    AZURE_OPENAI_API_VERSION       未指定時は preview

ルートディレクトリの .env は既存のシェル環境変数より優先される。
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# .github/skills/gpt-image-2/scripts/generate.py -> parents[4] = repository root
REPO_ROOT = Path(__file__).resolve().parents[4]


load_dotenv(REPO_ROOT / ".env", override=True, encoding="utf-8")


def build_url(endpoint: str, api_version: str) -> str:
    endpoint = endpoint.rstrip("/")
    return f"{endpoint}/openai/v1/images/generations?api-version={api_version}"


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt
    sys.exit("ERROR: --prompt または --prompt-file を指定してください")


def resolve_model(args: argparse.Namespace) -> str:
    model = (args.model or "").strip()
    if model:
        return model
    env_model = (os.environ.get("AZURE_OPENAI_IMAGE_MODEL") or "").strip()
    if env_model:
        return env_model
    sys.exit(
        "ERROR: 画像モデル名が指定されていません。"
        "--model または AZURE_OPENAI_IMAGE_MODEL を明示してください。"
    )


def save_images(payload: dict, out_path: Path, n: int) -> list[Path]:
    data = payload.get("data")
    if not data:
        raise RuntimeError(f"API応答にdataがありません: {payload}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for idx, item in enumerate(data, start=1):
        b64 = item.get("b64_json")
        if not b64:
            raise RuntimeError(f"b64_json が空です: {item}")
        target = (
            out_path
            if n == 1
            else out_path.with_name(f"{out_path.stem}_{idx}{out_path.suffix}")
        )
        target.write_bytes(base64.b64decode(b64))
        saved.append(target)
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description="Azure OpenAI / Foundry 画像生成 CLI")
    parser.add_argument("--prompt", help="生成プロンプト（テキスト）")
    parser.add_argument("--prompt-file", help="プロンプトを記載したファイルパス")
    parser.add_argument("--out", required=True, help="出力PNGパス")
    parser.add_argument("--size", default="1024x1024",
                        choices=["512x512", "1024x1024", "1024x1536", "1536x1024", "auto"])
    parser.add_argument("--quality", default="medium",
                        choices=["low", "medium", "high", "auto"])
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg"])
    parser.add_argument("--background", choices=["auto", "transparent"],
                        help="透過PNGにするなら transparent（gpt-image-1系のみ）")
    parser.add_argument(
        "--model",
        default=None,
        help="使用する画像モデル名。例: gpt-image-2 / gpt-image-1.5 / gpt-image-1 / MAI-Image-2。"
             "v1 API の body.model にそのまま渡されます。"
             "環境変数 AZURE_OPENAI_IMAGE_MODEL でも指定可。"
             "未指定時の既定モデルはありません。",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("AZURE_OPENAI_TIMEOUT", "600")),
        help="HTTP読み取りタイムアウト秒（既定 600、quality=high だと生成に1〜数分かかることがあります）",
    )
    args = parser.parse_args()

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        sys.exit("ERROR: AZURE_OPENAI_ENDPOINT と AZURE_OPENAI_API_KEY を設定してください")
    model = resolve_model(args)
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "preview")

    prompt = load_prompt(args)
    url = build_url(endpoint, api_version)
    body: dict = {
        "model": model,
        "prompt": prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
    }
    if args.background:
        body["background"] = args.background

    print(f"[gpt-image-2] POST {url}")
    print(f"[gpt-image-2] model={model} size={args.size} "
          f"quality={args.quality} n={args.n} timeout={args.timeout}s")
    resp = requests.post(
        url,
        headers={"Api-Key": api_key, "Content-Type": "application/json"},
        json=body,
        timeout=args.timeout,
    )
    if not resp.ok:
        sys.exit(f"ERROR {resp.status_code}: {resp.text}")
    saved = save_images(resp.json(), Path(args.out), args.n)
    for p in saved:
        print(f"[gpt-image-2] saved: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
