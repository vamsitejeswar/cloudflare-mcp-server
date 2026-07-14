from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def list_load_balancers(
    zone_id: str,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """List load balancers configured on a zone.

    per_page: items per page. page: 1-based.
    When page=1 (default), ALL pages are fetched automatically so result[].length always
    equals result_info.total_count. Pass page>1 to fetch a specific page only.
    """
    client = get_client()
    params = {"page": page, "per_page": per_page}
    if page != 1:
        return await client.request("GET", f"/zones/{zone_id}/load_balancers", params=params)
    return await client.request_all_pages("GET", f"/zones/{zone_id}/load_balancers", params=params)


@mcp.tool(annotations=CREATE)
async def create_load_balancer(
    zone_id: str,
    name: str,
    default_pools: list[str],
    fallback_pool: str,
    proxied: bool = True,
) -> dict:
    """Create a load balancer. default_pools/fallback_pool are pool IDs (see create_pool)."""
    client = get_client()
    body = {
        "name": name,
        "default_pools": default_pools,
        "fallback_pool": fallback_pool,
        "proxied": proxied,
    }
    return await client.request("POST", f"/zones/{zone_id}/load_balancers", json_body=body)


@mcp.tool(annotations=DELETE)
async def delete_load_balancer(zone_id: str, load_balancer_id: str) -> dict:
    """Delete a load balancer from a zone."""
    client = get_client()
    return await client.request("DELETE", f"/zones/{zone_id}/load_balancers/{load_balancer_id}")


@mcp.tool(annotations=READ_ONLY)
async def list_pools(
    account_id: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """List load balancer origin pools on the account.

    per_page: items per page. page: 1-based.
    When page=1 (default), ALL pages are fetched automatically so result[].length always
    equals result_info.total_count. Pass page>1 to fetch a specific page only.
    """
    client = get_client()
    account_id = account_id or client.account_id
    params = {"page": page, "per_page": per_page}
    path = f"/accounts/{account_id}/load_balancers/pools"
    if page != 1:
        return await client.request("GET", path, params=params)
    return await client.request_all_pages("GET", path, params=params)


@mcp.tool(annotations=CREATE)
async def create_pool(
    name: str, origins: list[dict[str, Any]], account_id: str | None = None
) -> dict:
    """Create a load balancer origin pool.

    origins: list of {"name": str, "address": str, "enabled": bool}.
    """
    client = get_client()
    account_id = account_id or client.account_id
    body = {"name": name, "origins": origins}
    return await client.request(
        "POST", f"/accounts/{account_id}/load_balancers/pools", json_body=body
    )


@mcp.tool(annotations=DELETE)
async def delete_pool(pool_id: str, account_id: str | None = None) -> dict:
    """Delete a load balancer origin pool."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "DELETE", f"/accounts/{account_id}/load_balancers/pools/{pool_id}"
    )
