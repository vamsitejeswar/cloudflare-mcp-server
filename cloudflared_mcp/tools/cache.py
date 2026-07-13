from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import DELETE


@mcp.tool(annotations=DELETE)
async def purge_cache_everything(zone_id: str) -> dict:
    """Purge all cached content for a zone."""
    client = get_client()
    return await client.request(
        "POST", f"/zones/{zone_id}/purge_cache", json_body={"purge_everything": True}
    )


@mcp.tool(annotations=DELETE)
async def purge_cache_by_urls(zone_id: str, urls: list[str]) -> dict:
    """Purge specific URLs from a zone's cache (up to 30 per request)."""
    client = get_client()
    return await client.request(
        "POST", f"/zones/{zone_id}/purge_cache", json_body={"files": urls}
    )


@mcp.tool(annotations=DELETE)
async def purge_cache_by_tags(zone_id: str, tags: list[str]) -> dict:
    """Purge cached content by Cache-Tag (requires Enterprise plan)."""
    client = get_client()
    return await client.request(
        "POST", f"/zones/{zone_id}/purge_cache", json_body={"tags": tags}
    )
