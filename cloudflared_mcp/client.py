import os

import httpx

CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareAPIError(Exception):
    def __init__(self, status_code: int, errors: list):
        self.status_code = status_code
        self.errors = errors
        super().__init__(f"Cloudflare API error {status_code}: {errors}")


class CloudflareClient:
    def __init__(self):
        api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN environment variable is required")

        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self._client = httpx.AsyncClient(
            base_url=CLOUDFLARE_API_BASE,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict:
        path = path if path.startswith("/") else f"/{path}"
        response = await self._client.request(method.upper(), path, params=params, json=json_body)
        data = response.json()
        if not data.get("success", False):
            raise CloudflareAPIError(response.status_code, data.get("errors", []))
        return data

    async def request_raw(
        self,
        method: str,
        path: str,
        params: dict | None = None,
    ) -> str:
        """For endpoints that return a raw body instead of the {success, result} envelope."""
        path = path if path.startswith("/") else f"/{path}"
        response = await self._client.request(method.upper(), path, params=params)
        response.raise_for_status()
        return response.text

    async def aclose(self):
        await self._client.aclose()


_client: CloudflareClient | None = None


def get_client() -> CloudflareClient:
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client
