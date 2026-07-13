from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_dns_records(
    zone_id: str,
    type: str | None = None,
    name: str | None = None,
    page: int = 1,
    per_page: int = 5000,
) -> dict:
    """List DNS records in a zone, optionally filtered by record type (A, AAAA, CNAME, TXT, MX...) or name.

    per_page: up to 5000 per page (Cloudflare maximum). Default fetches all records in one call
    for zones with ≤5000 records (covers virtually every zone). page: 1-based.
    The response includes result_info.total_count (the true count for the active filters, NOT the
    unfiltered zone total when type/name are supplied) and result_info.total_pages.
    If result_info.page < result_info.total_pages, call again with page=N+1.
    """
    client = get_client()
    params: dict = {"page": page, "per_page": per_page}
    if type:
        params["type"] = type
    if name:
        params["name"] = name
    return await client.request("GET", f"/zones/{zone_id}/dns_records", params=params)


@mcp.tool(annotations=READ_ONLY)
async def get_dns_record(zone_id: str, record_id: str) -> dict:
    """Get a single DNS record by its ID."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/dns_records/{record_id}")


@mcp.tool(annotations=READ_ONLY)
async def search_dns_records(
    zone_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    match: str = "all",
    page: int = 1,
    per_page: int = 5000,
) -> dict:
    """Search DNS records with extended filters.

    type: record type (A, AAAA, CNAME, TXT, MX, …).
    name: exact or partial record name.
    content: filter by record content/value.
    match: "all" (AND) or "any" (OR) — how multiple filters are combined.
    per_page: up to 5000 (Cloudflare maximum). page: 1-based.
    result_info.total_count reflects the filtered subset count, NOT the unfiltered zone total.
    Check result_info.total_pages to detect whether more pages exist.
    """
    client = get_client()
    params: dict = {"match": match, "page": page, "per_page": per_page}
    if type:
        params["type"] = type
    if name:
        params["name"] = name
    if content:
        params["content"] = content
    return await client.request("GET", f"/zones/{zone_id}/dns_records", params=params)


@mcp.tool(annotations=CREATE)
async def import_dns_records(
    zone_id: str,
    bind_zone_file: str,
    proxied: bool = False,
) -> dict:
    """Bulk-import DNS records from a BIND-formatted zone file.

    bind_zone_file: the full text content of a BIND/RFC-1035 zone file.
    proxied: if True, eligible imported records will be proxied through Cloudflare.
    """
    client = get_client()
    return await client.request_form(
        "POST",
        f"/zones/{zone_id}/dns_records/import",
        data={"proxied": str(proxied).lower()},
        files={"file": ("zone.txt", bind_zone_file.encode(), "text/plain")},
    )


@mcp.tool(annotations=READ_ONLY)
async def export_dns_records(zone_id: str) -> str:
    """Export all DNS records for a zone as a BIND-formatted zone file (plain text)."""
    client = get_client()
    return await client.request_raw("GET", f"/zones/{zone_id}/dns_records/export")


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
