# Cloudflare MCP Server

An MCP (Model Context Protocol) server that lets AI agents manage Cloudflare zones through natural language — analytics, DNS records, and WAF/ruleset management.

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A Cloudflare API token with the required permissions (see below)
- Your Cloudflare Account ID

### 2. Create & activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Set environment variables

```bash
export CLOUDFLARE_API_TOKEN=your_api_token_here
export CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

Or use the helper script:

```bash
./scripts/set-credentials.sh --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID
```

### 5. Run the server

```bash
python main.py
```

### 6. Required API token permissions

When creating the token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens), grant:

| Permission | Level | Access |
|---|---|---|
| Zone Analytics | Zone | Read |
| DNS | Zone | Read + Edit |
| Zone Rulesets | Zone | Read + Edit |
| Account Rulesets | Account | Read |

---

## Available Tools

There are **28 active tools** across three categories.

---

## Analytics (10 tools)

All analytics tools accept `since` and `until` time range parameters.

- **`since` / `until`** — ISO 8601 datetime (`"2024-01-01T00:00:00Z"`) or a negative integer representing minutes from now (`"-1440"` = last 24 h, `"-10080"` = last 7 days).

| Tool | What it does |
|---|---|
| `get_traffic_analytics` | Full overview — requests, bandwidth, threats, and pageviews for a zone |
| `get_http_requests` | Request counts broken down by content type, country, HTTP status code, and SSL |
| `get_bandwidth_usage` | Bytes transferred broken down by content type, country, and SSL |
| `get_cache_analytics` | Cached vs. uncached requests and bytes; computes cache-hit ratios |
| `get_top_countries` | Traffic per country and Cloudflare data center (colocation) |
| `get_top_paths` | Most-requested URL paths via GraphQL Analytics API |
| `get_security_analytics` | Threat counts by type and country |
| `get_bot_analytics` | Bot management decision breakdown by host via GraphQL Analytics API |
| `get_origin_performance` | How much traffic reaches your origin vs. is served from Cloudflare cache |
| `get_analytics_by_date` | Full time-series — requests, bandwidth, threats, pageviews per interval |

### Example actions

```
"Show me traffic for zone abc123 over the last 24 hours"
→ get_traffic_analytics(zone_id="abc123", since="-1440")

"What are the top 10 URLs being hit on zone abc123 today?"
→ get_top_paths(zone_id="abc123", since="2024-07-13T00:00:00Z", until="2024-07-13T23:59:59Z", limit=10)

"How is my cache performing this week?"
→ get_cache_analytics(zone_id="abc123", since="-10080")

"Are there any bot threats hitting my site?"
→ get_bot_analytics(zone_id="abc123", since="2024-07-13T00:00:00Z", until="2024-07-13T23:59:59Z")
```

---

## DNS Management (4 tools)

| Tool | What it does |
|---|---|
| `get_dns_record` | Fetch a single DNS record by its ID |
| `search_dns_records` | Search records with filters — type, name, content, AND/OR matching, pagination |
| `import_dns_records` | Bulk-import records from a BIND/RFC-1035 zone file |
| `export_dns_records` | Export all DNS records as a BIND zone file (plain text) |

### Parameters for `search_dns_records`

| Parameter | Description |
|---|---|
| `zone_id` | The zone to search |
| `type` | Record type filter: `A`, `AAAA`, `CNAME`, `TXT`, `MX`, etc. |
| `name` | Filter by record name |
| `content` | Filter by record value/content |
| `match` | `"all"` (AND) or `"any"` (OR) — how filters combine |
| `page` | Page number (default 1) |
| `per_page` | Records per page, up to 5000 (default 5000) |

> **Pagination note:** Every response includes `result_info.total_count` (the true total matching the active filters) and `result_info.total_pages`. If `page < total_pages`, call again with `page=N+1` to get the next batch.

### Example actions

```
"Find all CNAME records in zone abc123"
→ search_dns_records(zone_id="abc123", type="CNAME")

"Get the DNS record with ID xyz"
→ get_dns_record(zone_id="abc123", record_id="xyz")

"Export all DNS records for zone abc123 as a zone file"
→ export_dns_records(zone_id="abc123")

"Import these DNS records from a BIND file"
→ import_dns_records(zone_id="abc123", bind_zone_file="<contents>")
```

---

## Rule Management (10 tools)

Manages individual rules inside Cloudflare Rulesets (WAF custom rules, rate limiting, transforms, etc.).

| Tool | What it does |
|---|---|
| `list_rulesets` | List all rulesets attached to a zone |
| `get_ruleset` | Get a specific ruleset including all its rules and metadata |
| `list_rules` | List rules inside a specific ruleset |
| `create_rule` | Add a new rule to an existing ruleset |
| `update_rule` | Update an existing rule (expression, action, description, or enabled state) |
| `delete_rule` | Permanently remove a rule from a ruleset |
| `enable_rule` | Enable a previously disabled rule |
| `disable_rule` | Disable a rule without deleting it |
| `reorder_rules` | Set the evaluation order of rules by passing an ordered list of rule IDs |
| `validate_rule_expression` | Check whether a filter expression is syntactically valid before using it |

### Rule actions supported by `create_rule` / `update_rule`

`block` · `challenge` · `js_challenge` · `managed_challenge` · `allow` · `log` · `skip` · `rewrite` · `redirect` · `score`

### Example actions

```
"List all rulesets on zone abc123"
→ list_rulesets(zone_id="abc123")

"Show me the rules in ruleset rs456"
→ list_rules(zone_id="abc123", ruleset_id="rs456")

"Block all traffic from IP 1.2.3.4"
→ create_rule(
    zone_id="abc123",
    ruleset_id="rs456",
    expression='(ip.src eq 1.2.3.4)',
    action="block",
    description="Block malicious IP"
  )

"Is this expression valid? (http.request.uri.path eq \"/admin\")"
→ validate_rule_expression(expression='(http.request.uri.path eq "/admin")')

"Disable the rule temporarily without deleting it"
→ disable_rule(zone_id="abc123", ruleset_id="rs456", rule_id="rule789")

"Re-enable the rule"
→ enable_rule(zone_id="abc123", ruleset_id="rs456", rule_id="rule789")

"Move rule A to the top, then rule B, then rule C"
→ reorder_rules(zone_id="abc123", ruleset_id="rs456", rule_ids=["ruleA", "ruleB", "ruleC"])
```

---

## End-to-End Workflow

### Typical flow for investigating traffic and adding a WAF block rule

```
1. Get a traffic overview
   → get_traffic_analytics(zone_id, since="-1440")

2. Identify where threats are coming from
   → get_security_analytics(zone_id, since="-1440")
   → get_top_countries(zone_id, since="-1440")

3. See which paths are being targeted
   → get_top_paths(zone_id, since="...", until="...")

4. Find the relevant WAF ruleset
   → list_rulesets(zone_id)

5. Review existing rules
   → list_rules(zone_id, ruleset_id)

6. Validate your filter expression first
   → validate_rule_expression(expression='(ip.src eq 1.2.3.4)')

7. Create a block rule
   → create_rule(zone_id, ruleset_id, expression='...', action="block", description="...")

8. Verify the rule is active
   → list_rules(zone_id, ruleset_id)

9. Monitor the effect after a few minutes
   → get_security_analytics(zone_id, since="-30")
```

### Typical flow for DNS audit and bulk import

```
1. Export current DNS records as a backup
   → export_dns_records(zone_id)

2. Search for specific record types
   → search_dns_records(zone_id, type="A")
   → search_dns_records(zone_id, type="CNAME")

3. Look up a specific record by ID
   → get_dns_record(zone_id, record_id)

4. Import new records from a BIND zone file
   → import_dns_records(zone_id, bind_zone_file="...", proxied=True)

5. Verify the import
   → search_dns_records(zone_id, name="new-record.example.com")
```

---

## Deployment (Cloud Run)

See [CREDENTIALS.md](./CREDENTIALS.md) for full instructions on updating API credentials and deploying to Google Cloud Run (`verse-cloudflare-mcp`).

Quick deploy:

```bash
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=YOUR_ACCOUNT_ID \
  --quiet
```

---

## Project Structure

```
cloudflared_mcp/
├── app.py              # FastMCP app instance
├── client.py           # Cloudflare API HTTP client
├── annotations.py      # MCP tool annotation constants
├── server.py           # Entry point
└── tools/
    ├── __init__.py     # Active module imports (comment/uncomment to hide/show tool groups)
    ├── analytics.py    # 10 analytics tools  ← ACTIVE
    ├── dns.py          # 4 DNS management tools  ← ACTIVE
    ├── rules.py        # 10 rule management tools  ← ACTIVE
    ├── access.py       # Zero Trust Access  (hidden)
    ├── cache.py        # Cache purge  (hidden)
    ├── firewall.py     # Firewall rulesets  (hidden)
    ├── load_balancers.py  (hidden)
    ├── raw.py          # Raw API escape hatch  (hidden)
    ├── ssl.py          # SSL certificates  (hidden)
    ├── tunnels.py      # Cloudflare Tunnels  (hidden)
    ├── workers_kv.py   # Workers & KV  (hidden)
    └── zones.py        # Zone management  (hidden)
```

To restore any hidden tool group, uncomment its import line in `tools/__init__.py`.
