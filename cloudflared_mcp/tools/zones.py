from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_zones(name: str | None = None, status: str | None = None) -> dict:
    """List Cloudflare zones (domains) on the account, optionally filtered by name or status."""
    client = get_client()
    params = {}
    if name:
        params["name"] = name
    if status:
        params["status"] = status
    return await client.request("GET", "/zones", params=params)


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
