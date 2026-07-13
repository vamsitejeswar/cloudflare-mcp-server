from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_workers_scripts(account_id: str | None = None) -> dict:
    """List Workers scripts deployed on the account."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request("GET", f"/accounts/{account_id}/workers/scripts")


@mcp.tool(annotations=READ_ONLY)
async def get_workers_script(script_name: str, account_id: str | None = None) -> dict:
    """Get the source/metadata for a deployed Workers script."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request("GET", f"/accounts/{account_id}/workers/scripts/{script_name}")


@mcp.tool(annotations=DELETE)
async def delete_workers_script(script_name: str, account_id: str | None = None) -> dict:
    """Delete a deployed Workers script."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "DELETE", f"/accounts/{account_id}/workers/scripts/{script_name}"
    )


@mcp.tool(annotations=READ_ONLY)
async def list_kv_namespaces(
    account_id: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """List Workers KV namespaces on the account.

    per_page: up to 100 per page (Cloudflare maximum). page: 1-based.
    Check result_info.total_count for the true total and result_info.total_pages
    to detect whether more pages exist.
    """
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "GET",
        f"/accounts/{account_id}/storage/kv/namespaces",
        params={"page": page, "per_page": per_page},
    )


@mcp.tool(annotations=CREATE)
async def create_kv_namespace(title: str, account_id: str | None = None) -> dict:
    """Create a new Workers KV namespace."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "POST", f"/accounts/{account_id}/storage/kv/namespaces", json_body={"title": title}
    )


@mcp.tool(annotations=READ_ONLY)
async def list_kv_keys(
    namespace_id: str,
    account_id: str | None = None,
    limit: int = 1000,
    cursor: str | None = None,
    prefix: str | None = None,
) -> dict:
    """List keys in a Workers KV namespace.

    This endpoint uses CURSOR-BASED pagination (not page/per_page).
    limit: keys per call, max 1000 (Cloudflare maximum). Default fetches the maximum batch.
    cursor: pass result_info.cursor from the previous response to fetch the next batch.
    prefix: only return keys that begin with this string.

    KV does NOT expose a total_count. Continue fetching until result_info.cursor is absent
    or empty — that signals the last page. result_info.count is the number of keys in
    this batch (not the grand total).
    """
    client = get_client()
    account_id = account_id or client.account_id
    params: dict = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    if prefix:
        params["prefix"] = prefix
    return await client.request(
        "GET",
        f"/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/keys",
        params=params,
    )


@mcp.tool(annotations=READ_ONLY)
async def get_kv_value(key: str, namespace_id: str, account_id: str | None = None) -> str:
    """Get the value stored under a key in a Workers KV namespace."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request_raw(
        "GET", f"/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
    )


@mcp.tool(annotations=UPDATE)
async def put_kv_value(
    key: str, value: str, namespace_id: str, account_id: str | None = None
) -> dict:
    """Write a value to a key in a Workers KV namespace."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "PUT",
        f"/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/{key}",
        json_body={"value": value},
    )


@mcp.tool(annotations=DELETE)
async def delete_kv_value(key: str, namespace_id: str, account_id: str | None = None) -> dict:
    """Delete a key from a Workers KV namespace."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "DELETE", f"/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
    )
