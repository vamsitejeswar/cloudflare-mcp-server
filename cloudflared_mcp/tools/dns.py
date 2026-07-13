from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_dns_records(
    zone_id: str, type: str | None = None, name: str | None = None
) -> dict:
    """List DNS records in a zone, optionally filtered by record type (A, AAAA, CNAME, TXT, MX...) or name."""
    client = get_client()
    params = {}
    if type:
        params["type"] = type
    if name:
        params["name"] = name
    return await client.request("GET", f"/zones/{zone_id}/dns_records", params=params)


@mcp.tool(annotations=CREATE)
async def create_dns_record(
    zone_id: str,
    type: str,
    name: str,
    content: str,
    ttl: int = 1,
    proxied: bool = False,
    priority: int | None = None,
) -> dict:
    """Create a DNS record in a zone.

    ttl=1 means "automatic". Set proxied=True to route traffic through Cloudflare
    (orange-cloud). priority is required for MX/SRV records.
    """
    client = get_client()
    body = {"type": type, "name": name, "content": content, "ttl": ttl, "proxied": proxied}
    if priority is not None:
        body["priority"] = priority
    return await client.request("POST", f"/zones/{zone_id}/dns_records", json_body=body)


@mcp.tool(annotations=UPDATE)
async def update_dns_record(
    zone_id: str,
    record_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    ttl: int | None = None,
    proxied: bool | None = None,
) -> dict:
    """Update an existing DNS record. Only provided fields are changed."""
    client = get_client()
    body = {}
    if type is not None:
        body["type"] = type
    if name is not None:
        body["name"] = name
    if content is not None:
        body["content"] = content
    if ttl is not None:
        body["ttl"] = ttl
    if proxied is not None:
        body["proxied"] = proxied
    return await client.request("PATCH", f"/zones/{zone_id}/dns_records/{record_id}", json_body=body)


@mcp.tool(annotations=DELETE)
async def delete_dns_record(zone_id: str, record_id: str) -> dict:
    """Delete a DNS record from a zone."""
    client = get_client()
    return await client.request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")


@mcp.tool(annotations=CREATE)
async def create_tunnel_dns_route(zone_id: str, tunnel_id: str, hostname: str) -> dict:
    """Create a CNAME DNS record routing a hostname to a Cloudflare Tunnel.

    Points `hostname` at `<tunnel_id>.cfargotunnel.com`, proxied through Cloudflare.
    """
    client = get_client()
    body = {
        "type": "CNAME",
        "name": hostname,
        "content": f"{tunnel_id}.cfargotunnel.com",
        "proxied": True,
        "ttl": 1,
    }
    return await client.request("POST", f"/zones/{zone_id}/dns_records", json_body=body)
