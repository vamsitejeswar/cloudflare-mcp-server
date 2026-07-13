from typing import Any

from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY, UPDATE


@mcp.tool(annotations=READ_ONLY)
async def list_rulesets(zone_id: str) -> dict:
    """List all rulesets attached to a zone (WAF, rate limiting, transforms, etc.)."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/rulesets")


@mcp.tool(annotations=READ_ONLY)
async def get_ruleset(zone_id: str, ruleset_id: str) -> dict:
    """Get a specific ruleset including all its rules and metadata."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/rulesets/{ruleset_id}")


@mcp.tool(annotations=READ_ONLY)
async def list_rules(zone_id: str, ruleset_id: str) -> dict:
    """List all rules within a specific ruleset.

    Returns only the rules array from the ruleset, with each rule's id, expression,
    action, description, and enabled status.
    """
    client = get_client()
    data = await client.request("GET", f"/zones/{zone_id}/rulesets/{ruleset_id}")
    result = data.get("result", {})
    return {
        "success": data.get("success"),
        "result": result.get("rules", []),
        "ruleset_id": ruleset_id,
        "ruleset_name": result.get("name"),
        "phase": result.get("phase"),
    }


@mcp.tool(annotations=CREATE)
async def create_rule(
    zone_id: str,
    ruleset_id: str,
    expression: str,
    action: str,
    description: str = "",
    enabled: bool = True,
    action_parameters: dict[str, Any] | None = None,
) -> dict:
    """Add a new rule to an existing ruleset.

    expression: Cloudflare filter expression (e.g. '(ip.src eq 1.2.3.4)').
    action: rule action — "block", "challenge", "js_challenge", "managed_challenge",
            "allow", "log", "skip", "rewrite", "redirect", "score", etc.
    action_parameters: additional parameters for the action (e.g. {"response": {...}} for block).
    """
    client = get_client()
    body: dict[str, Any] = {
        "expression": expression,
        "action": action,
        "description": description,
        "enabled": enabled,
    }
    if action_parameters is not None:
        body["action_parameters"] = action_parameters
    return await client.request(
        "POST", f"/zones/{zone_id}/rulesets/{ruleset_id}/rules", json_body=body
    )


@mcp.tool(annotations=UPDATE)
async def update_rule(
    zone_id: str,
    ruleset_id: str,
    rule_id: str,
    expression: str | None = None,
    action: str | None = None,
    description: str | None = None,
    enabled: bool | None = None,
    action_parameters: dict[str, Any] | None = None,
) -> dict:
    """Update an individual rule within a ruleset. Only provided fields are changed."""
    client = get_client()
    body: dict[str, Any] = {}
    if expression is not None:
        body["expression"] = expression
    if action is not None:
        body["action"] = action
    if description is not None:
        body["description"] = description
    if enabled is not None:
        body["enabled"] = enabled
    if action_parameters is not None:
        body["action_parameters"] = action_parameters
    return await client.request(
        "PATCH", f"/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}", json_body=body
    )


@mcp.tool(annotations=DELETE)
async def delete_rule(zone_id: str, ruleset_id: str, rule_id: str) -> dict:
    """Delete an individual rule from a ruleset."""
    client = get_client()
    return await client.request(
        "DELETE", f"/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}"
    )


@mcp.tool(annotations=UPDATE)
async def enable_rule(zone_id: str, ruleset_id: str, rule_id: str) -> dict:
    """Enable a previously disabled rule in a ruleset."""
    client = get_client()
    return await client.request(
        "PATCH",
        f"/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}",
        json_body={"enabled": True},
    )


@mcp.tool(annotations=UPDATE)
async def disable_rule(zone_id: str, ruleset_id: str, rule_id: str) -> dict:
    """Disable a rule in a ruleset without deleting it."""
    client = get_client()
    return await client.request(
        "PATCH",
        f"/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}",
        json_body={"enabled": False},
    )


@mcp.tool(annotations=UPDATE)
async def reorder_rules(zone_id: str, ruleset_id: str, rule_ids: list[str]) -> dict:
    """Reorder rules in a ruleset by specifying the desired order of rule IDs.

    rule_ids: ordered list of all rule IDs in the ruleset. Rules are evaluated top-to-bottom,
    so earlier entries have higher priority. All existing rule IDs must be included.
    """
    client = get_client()
    current = await client.request("GET", f"/zones/{zone_id}/rulesets/{ruleset_id}")
    rules_by_id = {r["id"]: r for r in current.get("result", {}).get("rules", [])}
    ordered = [rules_by_id[rid] for rid in rule_ids if rid in rules_by_id]
    return await client.request(
        "PUT",
        f"/zones/{zone_id}/rulesets/{ruleset_id}",
        json_body={"rules": ordered},
    )


@mcp.tool(annotations=READ_ONLY)
async def validate_rule_expression(
    expression: str,
    account_id: str | None = None,
) -> dict:
    """Validate a Cloudflare Ruleset filter expression for correctness before using it in a rule.

    expression: the filter expression to validate (e.g. '(http.request.uri.path eq "/admin")').
    account_id: Cloudflare account ID — falls back to CLOUDFLARE_ACCOUNT_ID env var if omitted.
    """
    client = get_client()
    aid = account_id or client.account_id
    return await client.request(
        "POST",
        f"/accounts/{aid}/rulesets/validate",
        json_body={"expression": expression},
    )
