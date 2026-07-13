from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import RAW


@mcp.tool(annotations=RAW)
async def cloudflare_api_request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict:
    """Call any Cloudflare API v4 endpoint directly.

    Use this for anything not covered by a dedicated tool (e.g. Workers scripts,
    R2 buckets, Durable Objects, Queues, Spectrum, Logpush, Email Routing, Page
    Rules, Rulesets, Bot Management, Waiting Rooms, Access apps, Billing, etc).

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE).
        path: API path relative to https://api.cloudflare.com/client/v4,
            e.g. "/zones/{zone_id}/workers/scripts" or "/accounts/{account_id}/r2/buckets".
        params: Query string parameters.
        json_body: JSON request body for POST/PUT/PATCH.

    Returns:
        The parsed Cloudflare API response (the full envelope: result, result_info, etc).
    """
    client = get_client()
    return await client.request(method, path, params=params, json_body=json_body)
