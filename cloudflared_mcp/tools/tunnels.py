from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


def _account_path(account_id: str | None, client) -> str:
    account_id = account_id or client.account_id
    if not account_id:
        raise ValueError("account_id must be provided or CLOUDFLARE_ACCOUNT_ID must be set")
    return f"/accounts/{account_id}/cfd_tunnel"


@mcp.tool(annotations=READ_ONLY)
async def list_tunnels(account_id: str | None = None, is_deleted: bool = False) -> dict:
    """List Cloudflare Tunnels on the account."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("GET", base, params={"is_deleted": str(is_deleted).lower()})


@mcp.tool(annotations=READ_ONLY)
async def get_tunnel(tunnel_id: str, account_id: str | None = None) -> dict:
    """Get details for a single tunnel."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("GET", f"{base}/{tunnel_id}")


@mcp.tool(annotations=CREATE)
async def create_tunnel(name: str, account_id: str | None = None) -> dict:
    """Create a new Cloudflare Tunnel. Returns the tunnel id and credentials needed to run cloudflared."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request(
        "POST", base, json_body={"name": name, "config_src": "cloudflare"}
    )


@mcp.tool(annotations=DELETE)
async def delete_tunnel(tunnel_id: str, account_id: str | None = None) -> dict:
    """Delete a tunnel. The tunnel must have no active connections."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("DELETE", f"{base}/{tunnel_id}")


@mcp.tool(annotations=READ_ONLY)
async def get_tunnel_token(tunnel_id: str, account_id: str | None = None) -> dict:
    """Get the token used to run `cloudflared tunnel run --token <token>` for this tunnel."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("GET", f"{base}/{tunnel_id}/token")


@mcp.tool(annotations=READ_ONLY)
async def get_tunnel_configuration(tunnel_id: str, account_id: str | None = None) -> dict:
    """Get the ingress configuration (routing rules) for a remotely-managed tunnel."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("GET", f"{base}/{tunnel_id}/configurations")


@mcp.tool(annotations=UPDATE)
async def update_tunnel_configuration(
    tunnel_id: str, ingress: list[dict[str, Any]], account_id: str | None = None
) -> dict:
    """Update the ingress configuration for a remotely-managed tunnel.

    `ingress` is a list of rules, each with `hostname` and `service` (and optionally
    `path`), e.g. [{"hostname": "app.example.com", "service": "http://localhost:8080"},
    {"service": "http_status:404"}] — the last rule should have no hostname as a catch-all.
    """
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request(
        "PUT",
        f"{base}/{tunnel_id}/configurations",
        json_body={"config": {"ingress": ingress}},
    )


@mcp.tool(annotations=READ_ONLY)
async def list_tunnel_connections(tunnel_id: str, account_id: str | None = None) -> dict:
    """List active connections for a tunnel (which cloudflared instances are connected)."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("GET", f"{base}/{tunnel_id}/connections")


@mcp.tool(annotations=DELETE)
async def cleanup_tunnel_connections(tunnel_id: str, account_id: str | None = None) -> dict:
    """Force-close all active connections for a tunnel (useful for a stuck/stale tunnel)."""
    client = get_client()
    base = _account_path(account_id, client)
    return await client.request("DELETE", f"{base}/{tunnel_id}/connections")
