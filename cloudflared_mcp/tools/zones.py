from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_zones(
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """List Cloudflare zones (domains) on the account, optionally filtered by name or status.

    per_page: max 50 (Cloudflare hard limit for this endpoint). page: 1-based.
    When page=1 (default), ALL pages are fetched automatically so result[].length always
    equals result_info.total_count — never partial. Pass page>1 to fetch a specific page only.
    result_info.total_count is the true count matching the active name/status filters.
    """
    client = get_client()
    params: dict = {"page": page, "per_page": per_page}
    if name:
        params["name"] = name
    if status:
        params["status"] = status
    if page != 1:
        return await client.request("GET", "/zones", params=params)
    return await client.request_all_pages("GET", "/zones", params=params)


@mcp.tool(annotations=READ_ONLY)
async def get_zone(zone_id: str) -> dict:
    """Get details for a single zone."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}")


@mcp.tool(annotations=CREATE)
async def create_zone(name: str, account_id: str | None = None, jump_start: bool = True) -> dict:
    """Add a new zone (domain) to Cloudflare."""
    client = get_client()
    body = {"name": name, "jump_start": jump_start}
    body["account"] = {"id": account_id or client.account_id}
    return await client.request("POST", "/zones", json_body=body)


@mcp.tool(annotations=DELETE)
async def delete_zone(zone_id: str) -> dict:
    """Delete a zone from Cloudflare."""
    client = get_client()
    return await client.request("DELETE", f"/zones/{zone_id}")


@mcp.tool(annotations=READ_ONLY)
async def get_zone_settings(zone_id: str, setting_id: str) -> dict:
    """Get a specific zone setting (e.g. ssl, always_use_https, min_tls_version, security_level)."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/settings/{setting_id}")


@mcp.tool(annotations=UPDATE)
async def update_zone_setting(zone_id: str, setting_id: str, value: str) -> dict:
    """Update a specific zone setting (e.g. ssl, always_use_https, min_tls_version, security_level)."""
    client = get_client()
    return await client.request(
        "PATCH", f"/zones/{zone_id}/settings/{setting_id}", json_body={"value": value}
    )
