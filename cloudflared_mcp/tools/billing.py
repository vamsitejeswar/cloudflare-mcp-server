from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def list_subscriptions(account_id: str | None = None) -> dict:
    """List all zone subscriptions for a Cloudflare account.

    account_id: Cloudflare account ID — falls back to CLOUDFLARE_ACCOUNT_ID env var if omitted.
    Returns each subscription's plan, component values, rate plan, state, and zone details.
    """
    client = get_client()
    aid = account_id or client.account_id
    return await client.request("GET", f"/accounts/{aid}/subscriptions")


@mcp.tool(annotations=READ_ONLY)
async def get_billable_usage(account_id: str | None = None) -> dict:
    """Get billable usage for a Cloudflare account for the current billing period.

    account_id: Cloudflare account ID — falls back to CLOUDFLARE_ACCOUNT_ID env var if omitted.
    Returns current-period usage counts across all billable products and add-ons.
    """
    client = get_client()
    aid = account_id or client.account_id
    return await client.request("GET", f"/accounts/{aid}/billable-usage")


@mcp.tool(annotations=READ_ONLY)
async def get_paygo_usage(account_id: str | None = None) -> dict:
    """Get pay-as-you-go (PayGo) usage for a Cloudflare account.

    account_id: Cloudflare account ID — falls back to CLOUDFLARE_ACCOUNT_ID env var if omitted.
    Returns metered usage data for PayGo products such as Workers, R2, and AI Gateway.
    """
    client = get_client()
    aid = account_id or client.account_id
    return await client.request("GET", f"/accounts/{aid}/paygo/usage")


@mcp.tool(annotations=READ_ONLY)
async def get_org_billable_usage(org_id: str) -> dict:
    """Get billable usage for a Cloudflare organization across all member accounts.

    org_id: the Cloudflare organization ID.
    Returns org-level aggregated billable usage including subscriptions and metered products.
    """
    client = get_client()
    return await client.request("GET", f"/orgs/{org_id}/billing/usage")
