"""Azure OpenAI / Foundry GPT-Image 系モデルを呼び出して PNG を生成する CLI.

対応 API モード（環境変数 AZURE_OPENAI_API_MODE または --api-mode で切替）:
    v1         (既定) Foundry Models REST API v1
               POST {endpoint}/openai/v1/images/generations?api-version=preview
    deployment 旧来のデプロイ別パス方式
               POST {endpoint}/openai/deployments/{deployment}/images/generations?api-version=...

使用例:
    python generate.py --prompt "a forest fox spirit" --out out.png
    python generate.py --prompt-file prompt.txt --out card.png --size 1024x1536 --quality high
    python generate.py --prompt "..." --out o.png --model gpt-image-1.5
    python generate.py --prompt "..." --out o.png --model MAI-Image-2
    python generate.py --prompt "..." --out sample.png --n 3
    python generate.py --prompt "..." --out o.png --api-mode deployment

環境変数:
    AZURE_OPENAI_ENDPOINT          例: https://<resource>.openai.azure.com/
    AZURE_OPENAI_API_KEY           リソースAPIキー
    AZURE_OPENAI_IMAGE_MODEL       使用モデル名 (例: gpt-image-2 / gpt-image-1.5 / MAI-Image-2)
    AZURE_OPENAI_IMAGE_DEPLOYMENT  （下位互換）deployment mode 用デプロイ名
    AZURE_OPENAI_API_VERSION       v1: 既定 preview / deployment: 既定 2025-04-01-preview
    AZURE_OPENAI_API_MODE          v1 | deployment (既定: v1)
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

import requests

# .github/skills/gpt-image-2/scripts/generate.py → parents[4] = リポジトリルート
REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_dotenv(path: Path) -> None:
    """標準ライブラリのみで .env を読み込み os.environ に注入する軽量ローダー.

    - 既存の環境変数は **上書きしない**（CLI/シェルで設定済みの値を優先）
    - 形式: ``KEY=VALUE`` / ``export KEY=VALUE``
    - 値は前後の `"`/`'` 引用を1組のみ除去
    - `#` で始まる行と空行はスキップ
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("\"", "'"):
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_dotenv(REPO_ROOT / ".env")


def build_url(endpoint: str, deployment: str, api_version: str, api_mode: str) -> str:
    endpoint = endpoint.rstrip("/")
    if api_mode == "v1":
        return f"{endpoint}/openai/v1/images/generations?api-version={api_version}"
    return (
        f"{endpoint}/openai/deployments/{deployment}/images/generations"
        f"?api-version={api_version}"
    )


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt
    sys.exit("ERROR: --prompt または --prompt-file を指定してください")


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
        default=os.environ.get("AZURE_OPENAI_IMAGE_MODEL")
                or os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT", "gpt-image-2"),
        help="使用する画像モデル名。例: gpt-image-2 / gpt-image-1.5 / gpt-image-1 / MAI-Image-2。"
             "v1 mode では body.model、deployment mode では URL 上のデプロイ名として使用されます。"
             "環境変数 AZURE_OPENAI_IMAGE_MODEL または AZURE_OPENAI_IMAGE_DEPLOYMENT でも指定可。",
    )
    parser.add_argument(
        "--api-mode",
        choices=["v1", "deployment"],
        default=os.environ.get("AZURE_OPENAI_API_MODE", "v1"),
        help="v1 (Foundry Models REST API v1, 既定) / deployment (デプロイ別パス方式)",
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
    deployment = args.model
    default_api_version = "preview" if args.api_mode == "v1" else "2025-04-01-preview"
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", default_api_version)

    prompt = load_prompt(args)
    url = build_url(endpoint, deployment, api_version, args.api_mode)
    body: dict = {
        "prompt": prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
    }
    if args.api_mode == "v1":
        body["model"] = deployment
    if args.background:
        body["background"] = args.background

    print(f"[gpt-image-2] mode={args.api_mode} POST {url}")
    print(f"[gpt-image-2] model/deployment={deployment} size={args.size} "
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
