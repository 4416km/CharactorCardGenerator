# Azure OpenAI / Foundry Image Generation API 早見表

Foundry リソース（旧 Azure OpenAI リソース）では、以下の 2 パターンを使える。どちらもエンドポイントは `https://<resource>.openai.azure.com/`。

## エンドポイント

### v1 方式（Foundry Models REST API v1、推奨）

```
POST {endpoint}/openai/v1/images/generations?api-version=preview
```

- モデルはボディの `"model"` で指定
- `api-version`: `preview` または `v1`

### deployment 方式（旧来形式、互換性維持用）

```
POST {endpoint}/openai/deployments/{deployment}/images/generations?api-version=2025-04-01-preview
```

- モデルは URL パスの `{deployment}` で指定

## 認証

- ヘッダ: `Api-Key: <AZURE_OPENAI_API_KEY>`
- Entra ID の場合: `Authorization: Bearer <token>`（スコープ `https://cognitiveservices.azure.com/.default` または `https://ai.azure.com/.default`）

## リクエストボディ

| パラメータ | 型 | 必須 | 説明 |
|------------|----|------|------|
| `prompt` | string | ✅ | 生成プロンプト |
| `n` | int | | 生成枚数（1〜） |
| `size` | string | | `1024x1024` / `1024x1536` / `1536x1024` |
| `quality` | string | | `low` / `medium` / `high` |
| `output_format` | string | | `png` / `jpeg` |
| `background` | string | | `auto` / `transparent`（gpt-image-1系・PNGのみ） |
| `output_compression` | int | | 0〜100（JPEGのみ） |

## レスポンス

```json
{
  "created": 1735000000,
  "data": [
    { "b64_json": "<base64エンコードされたPNG/JPEG>" }
  ]
}
```

GPT-Image 系モデルは常に base64 (`b64_json`) で返却される。URLは返らない。

## エラーパターン

| ステータス | 主因 |
|-----------|------|
| 401 | APIキー誤り / リソース不一致 |
| 404 | デプロイ名 / api-version の指定誤り |
| 400 | プロンプトがコンテンツポリシー違反、パラメータ不正 |
| 429 | レート / TPM 超過 |

## 参考

- Azure OpenAI / Foundry の画像生成 API 公式ドキュメント
