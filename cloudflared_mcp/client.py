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

    async def request_form(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        files: dict | None = None,
    ) -> dict:
        """For endpoints that require multipart/form-data (e.g. DNS import)."""
        path = path if path.startswith("/") else f"/{path}"
        response = await self._client.request(method.upper(), path, data=data or {}, files=files or {})
        result = response.json()
        if not result.get("success", False):
            raise CloudflareAPIError(response.status_code, result.get("errors", []))
        return result

    async def graphql(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query against the Cloudflare Analytics GraphQL API."""
        body: dict = {"query": query}
        if variables:
            body["variables"] = variables
        response = await self._client.request("POST", "/graphql", json=body)
        data = response.json()
        if "errors" in data and data["errors"]:
            raise CloudflareAPIError(response.status_code, data["errors"])
        return data.get("data", data)

    async def request_all_pages(
        self,
        method: str,
        path: str,
        params: dict | None = None,
    ) -> dict:
        """Fetch every page of a page/per_page-paginated endpoint and return combined results.

        Combines all result[] arrays across pages. result_info.total_count comes from the
        first-page response (the API's authoritative value) so it reflects the true filtered
        total, not just the items returned. Stops when current page >= total_pages.
        """
        params = dict(params or {})
        first = await self.request(method, path, params=params)
        result_info = first.get("result_info", {})
        total_pages = result_info.get("total_pages", 1)
        if total_pages <= 1:
            return first
        all_results = list(first.get("result", []))
        for page in range(2, total_pages + 1):
            params["page"] = page
            page_data = await self.request(method, path, params=params)
            all_results.extend(page_data.get("result", []))
        return {
            "success": True,
            "result": all_results,
            "result_info": {
                **result_info,
                "page": 1,
                "count": len(all_results),
                "total_count": result_info.get("total_count", len(all_results)),
            },
        }

    async def aclose(self):
        await self._client.aclose()


_client: CloudflareClient | None = None


def get_client() -> CloudflareClient:
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client
