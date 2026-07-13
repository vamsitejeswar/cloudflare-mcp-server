from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def list_access_applications(
    account_id: str | None = None,
    page: int = 1,
    per_page: int = 300,
) -> dict:
    """List Zero Trust Access applications on the account.

    per_page: items per page. page: 1-based.
    Check result_info.total_count for the true total and result_info.total_pages
    to detect whether more pages exist.
    """
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "GET",
        f"/accounts/{account_id}/access/apps",
        params={"page": page, "per_page": per_page},
    )


@mcp.tool(annotations=CREATE)
async def create_access_application(
    name: str, domain: str, session_duration: str = "24h", account_id: str | None = None
) -> dict:
    """Create a Zero Trust Access application protecting `domain` (e.g. app.example.com)."""
    client = get_client()
    account_id = account_id or client.account_id
    body = {"name": name, "domain": domain, "session_duration": session_duration}
    return await client.request("POST", f"/accounts/{account_id}/access/apps", json_body=body)


@mcp.tool(annotations=DELETE)
async def delete_access_application(app_id: str, account_id: str | None = None) -> dict:
    """Delete a Zero Trust Access application."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request("DELETE", f"/accounts/{account_id}/access/apps/{app_id}")


@mcp.tool(annotations=READ_ONLY)
async def list_access_policies(
    app_id: str,
    account_id: str | None = None,
    page: int = 1,
    per_page: int = 300,
) -> dict:
    """List the access policies attached to an Access application.

    per_page: items per page. page: 1-based.
    Check result_info.total_count for the true total and result_info.total_pages
    to detect whether more pages exist.
    """
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "GET",
        f"/accounts/{account_id}/access/apps/{app_id}/policies",
        params={"page": page, "per_page": per_page},
    )


@mcp.tool(annotations=CREATE)
async def create_access_policy(
    app_id: str,
    name: str,
    decision: str,
    include: list[dict[str, Any]],
    account_id: str | None = None,
) -> dict:
    """Create an access policy on an Access application.

    decision: "allow", "deny", "non_identity", or "bypass".
    include: list of rule dicts, e.g. [{"email": {"email": "user@example.com"}}] or
        [{"email_domain": {"domain": "example.com"}}].
    """
    client = get_client()
    account_id = account_id or client.account_id
    body = {"name": name, "decision": decision, "include": include}
    return await client.request(
        "POST", f"/accounts/{account_id}/access/apps/{app_id}/policies", json_body=body
    )


@mcp.tool(annotations=DELETE)
async def delete_access_policy(app_id: str, policy_id: str, account_id: str | None = None) -> dict:
    """Delete an access policy from an Access application."""
    client = get_client()
    account_id = account_id or client.account_id
    return await client.request(
        "DELETE", f"/accounts/{account_id}/access/apps/{app_id}/policies/{policy_id}"
    )
