from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_firewall_rulesets(zone_id: str) -> dict:
    """List rulesets (WAF custom rules, rate limiting, etc) attached to a zone."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/rulesets")


@mcp.tool(annotations=READ_ONLY)
async def get_firewall_ruleset(zone_id: str, ruleset_id: str) -> dict:
    """Get a specific ruleset and its rules."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/rulesets/{ruleset_id}")


@mcp.tool(annotations=CREATE)
async def create_firewall_ruleset(
    zone_id: str, name: str, phase: str, rules: list[dict[str, Any]]
) -> dict:
    """Create a new ruleset on a zone.

    phase is typically "http_request_firewall_custom" for custom WAF rules. Each
    rule is a dict like {"expression": "(ip.src eq 1.2.3.4)", "action": "block", "description": "..."}.
    """
    client = get_client()
    body = {"name": name, "kind": "zone", "phase": phase, "rules": rules}
    return await client.request("POST", f"/zones/{zone_id}/rulesets", json_body=body)


@mcp.tool(annotations=UPDATE)
async def update_firewall_ruleset(
    zone_id: str, ruleset_id: str, rules: list[dict[str, Any]]
) -> dict:
    """Replace the rules in an existing ruleset."""
    client = get_client()
    return await client.request(
        "PUT", f"/zones/{zone_id}/rulesets/{ruleset_id}", json_body={"rules": rules}
    )


@mcp.tool(annotations=DELETE)
async def delete_firewall_ruleset(zone_id: str, ruleset_id: str) -> dict:
    """Delete a ruleset from a zone."""
    client = get_client()
    return await client.request("DELETE", f"/zones/{zone_id}/rulesets/{ruleset_id}")


@mcp.tool(annotations=READ_ONLY)
async def list_ip_access_rules(
    account_id: str | None = None,
    zone_id: str | None = None,
    page: int = 1,
    per_page: int = 1000,
) -> dict:
    """List IP Access Rules (allow/block/challenge by IP, IP range, ASN, or country).

    Provide either account_id (account-level rules) or zone_id (zone-level rules).
    per_page: up to 1000 per page (Cloudflare maximum). page: 1-based.
    Check result_info.total_count for the true total and result_info.total_pages
    to detect whether more pages exist.
    """
    client = get_client()
    params: dict = {"page": page, "per_page": per_page}
    if zone_id:
        return await client.request(
            "GET", f"/zones/{zone_id}/firewall/access_rules/rules", params=params
        )
    account_id = account_id or client.account_id
    return await client.request(
        "GET", f"/accounts/{account_id}/firewall/access_rules/rules", params=params
    )


@mcp.tool(annotations=CREATE)
async def create_ip_access_rule(
    mode: str,
    target: str,
    value: str,
    notes: str | None = None,
    zone_id: str | None = None,
    account_id: str | None = None,
) -> dict:
    """Create an IP Access Rule.

    mode: "block", "challenge", "whitelist", or "js_challenge".
    target: "ip", "ip_range", "asn", or "country".
    value: the actual IP/CIDR/ASN/country-code to match.
    Provide either zone_id (zone-level) or account_id (account-level).
    """
    client = get_client()
    body = {"mode": mode, "configuration": {"target": target, "value": value}}
    if notes:
        body["notes"] = notes
    if zone_id:
        return await client.request(
            "POST", f"/zones/{zone_id}/firewall/access_rules/rules", json_body=body
        )
    account_id = account_id or client.account_id
    return await client.request(
        "POST", f"/accounts/{account_id}/firewall/access_rules/rules", json_body=body
    )
