# Cloudflare MCP Server

A Model Context Protocol (MCP) server that lets AI agents manage Cloudflare zones and accounts through natural language. Deployed on Google Cloud Run and called by AI systems (such as Gemini Enterprise) to interact with the Cloudflare API on behalf of users.

---

## What This Server Does

This server exposes **39 MCP tools** across five categories:

| Category | Tools | What it covers |
|---|---|---|
| Analytics | 10 | Traffic, bandwidth, cache, threats, bots, origin performance |
| DNS | 9 | List, search, create, update, delete, import, export records |
| Rules | 10 | WAF custom rules, rate limiting, rulesets — full CRUD + reorder |
| Zones | 6 | Zone management and per-zone settings |
| Billing | 4 | Subscriptions, billable usage, PayGo usage |

Additionally, the following tool groups are implemented but **disabled by default**. They can be enabled without code changes (see [Maintenance](./docs/MAINTENANCE.md)):

- Zero Trust Access, Cache purge, Firewall rulesets, Load balancers, Raw API, SSL certificates, Cloudflare Tunnels, Workers & KV

---

## Quick Start (Local)

### Prerequisites
- Python 3.10+
- A Cloudflare API token (see [Configuration](./docs/CONFIGURATION.md#api-token-permissions))

### Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Set credentials
./scripts/set-credentials.sh --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID
# Or export directly:
# export CLOUDFLARE_API_TOKEN=your_token
# export CLOUDFLARE_ACCOUNT_ID=your_account_id

# 4. Run
python main.py
```

The server starts on `http://0.0.0.0:8000/mcp` by default.

---

## Documentation

| Document | Contents |
|---|---|
| [Architecture](./docs/ARCHITECTURE.md) | System overview, components, data flow, external services |
| [Deployment](./docs/DEPLOYMENT.md) | Cloud Run deployment, image build, credential rotation |
| [Configuration](./docs/CONFIGURATION.md) | All environment variables, API token permissions, tool activation |
| [Troubleshooting](./docs/TROUBLESHOOTING.md) | Common failures and how to diagnose/fix them |
| [Maintenance](./docs/MAINTENANCE.md) | Updating credentials, enabling tools, dependency upgrades |

---

## Project Structure

```
cloudflare-mcp-server/
├── main.py                         # Entrypoint (delegates to server.py)
├── pyproject.toml                  # Package definition and dependencies
├── Dockerfile                      # Container image for Cloud Run
├── .dockerignore
├── .env.example                    # Template for local credentials
├── scripts/
│   └── set-credentials.sh          # Helper to write/update .env safely
├── cloudflared_mcp/                # Main Python package
│   ├── app.py                      # FastMCP app instance (named "Cloudflare")
│   ├── server.py                   # Server startup — reads config, runs HTTP transport
│   ├── client.py                   # Async Cloudflare API HTTP client
│   ├── config.py                   # Server listen address/port from env vars
│   ├── annotations.py              # MCP tool hint constants (READ_ONLY, CREATE, etc.)
│   └── tools/
│       ├── __init__.py             # Active tool imports — comment/uncomment to toggle groups
│       ├── analytics.py            # 10 analytics tools  ← ACTIVE
│       ├── billing.py              # 4 billing tools     ← ACTIVE
│       ├── dns.py                  # 9 DNS tools         ← ACTIVE
│       ├── rules.py                # 10 ruleset tools    ← ACTIVE
│       ├── zones.py                # 6 zone tools        ← ACTIVE
│       ├── access.py               # Zero Trust Access   (disabled)
│       ├── cache.py                # Cache purge         (disabled)
│       ├── firewall.py             # Firewall rulesets   (disabled)
│       ├── load_balancers.py       # Load balancers      (disabled)
│       ├── raw.py                  # Raw API escape hatch (disabled)
│       ├── ssl.py                  # SSL certificates    (disabled)
│       ├── tunnels.py              # Cloudflare Tunnels  (disabled)
│       └── workers_kv.py          # Workers & KV        (disabled)
└── docs/
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    ├── CONFIGURATION.md
    ├── TROUBLESHOOTING.md
    └── MAINTENANCE.md
```

---

## Available Tools Reference

### Analytics (10 tools)

Time range parameters (`since` / `until`) accept either an ISO 8601 datetime string (`"2024-01-01T00:00:00Z"`) or a negative integer representing minutes from now (`"-1440"` = last 24 h).

| Tool | Description |
|---|---|
| `get_traffic_analytics` | Requests, bandwidth, threats, pageviews overview |
| `get_http_requests` | Request counts by content type, country, status code, SSL |
| `get_bandwidth_usage` | Bytes transferred by content type, country, SSL |
| `get_cache_analytics` | Cached vs uncached — requests, bytes, hit ratios |
| `get_top_countries` | Traffic by country and Cloudflare data center |
| `get_top_paths` | Most-requested URL paths (via GraphQL Analytics API) |
| `get_security_analytics` | Threat counts by type and country |
| `get_bot_analytics` | Bot management decision breakdown (requires Bot Management) |
| `get_origin_performance` | Traffic reaching origin vs served from cache |
| `get_analytics_by_date` | Full time-series: requests, bandwidth, threats, pageviews |

### DNS (9 tools)

| Tool | Description |
|---|---|
| `list_dns_records` | List records, optionally filtered by type or name |
| `get_dns_record` | Fetch a single record by ID |
| `search_dns_records` | Search with type + name + content filters (AND/OR) |
| `import_dns_records` | Bulk-import from a BIND/RFC-1035 zone file |
| `export_dns_records` | Export all records as a BIND zone file |
| `create_dns_record` | Create a record (A, AAAA, CNAME, TXT, MX, etc.) |
| `update_dns_record` | Patch specific fields of an existing record |
| `delete_dns_record` | Delete a record by ID |
| `create_tunnel_dns_route` | Create a CNAME pointing a hostname to a Cloudflare Tunnel |

### Rules / WAF (10 tools)

| Tool | Description |
|---|---|
| `list_rulesets` | List all rulesets on a zone |
| `get_ruleset` | Get a ruleset and all its rules |
| `list_rules` | List rules inside a specific ruleset |
| `create_rule` | Add a new rule (block, challenge, allow, log, skip, etc.) |
| `update_rule` | Patch expression, action, description, or enabled state |
| `delete_rule` | Permanently remove a rule |
| `enable_rule` | Enable a disabled rule |
| `disable_rule` | Disable a rule without deleting it |
| `reorder_rules` | Set rule evaluation order by passing an ordered ID list |
| `validate_rule_expression` | Check a filter expression is syntactically valid |

### Zones (6 tools)

| Tool | Description |
|---|---|
| `list_zones` | List all zones on the account (auto-paginated) |
| `get_zone` | Get details for a single zone |
| `create_zone` | Add a new domain to Cloudflare |
| `delete_zone` | Remove a zone from Cloudflare |
| `get_zone_settings` | Get a specific zone setting (ssl, security_level, etc.) |
| `update_zone_setting` | Update a specific zone setting |

### Billing (4 tools)

| Tool | Description |
|---|---|
| `list_subscriptions` | List all zone subscriptions for the account |
| `get_billable_usage` | Current-period billable usage across all products |
| `get_paygo_usage` | Pay-as-you-go usage (Workers, R2, AI Gateway, etc.) |
| `get_org_billable_usage` | Org-level aggregated billable usage |
