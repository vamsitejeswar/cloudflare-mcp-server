# Architecture

## Overview

This is a **stateless HTTP MCP server** that acts as a bridge between AI agents and the Cloudflare REST API. It exposes Cloudflare operations as MCP tools, which AI agents (such as Gemini Enterprise) can call using the Model Context Protocol over HTTP.

```
AI Agent / LLM Client
        |
        |  POST /mcp
        |  Authorization: Bearer <Google Identity Token>
        |  Content-Type: application/json
        v
┌─────────────────────────────────────┐
│   Google Cloud Run                  │
│   Service: verse-cloudflare-mcp     │
│   Region:  asia-south1              │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  FastMCP HTTP Server        │    │
│  │  (port from $PORT env var)  │    │
│  │                             │    │
│  │  Tool Dispatcher            │    │
│  │  ├── analytics.py (10)      │    │
│  │  ├── billing.py   (4)       │    │
│  │  ├── dns.py       (9)       │    │
│  │  ├── rules.py     (10)      │    │
│  │  └── zones.py     (6)       │    │
│  └────────────┬────────────────┘    │
└───────────────┼─────────────────────┘
                |
                |  HTTPS Bearer <CLOUDFLARE_API_TOKEN>
                v
      Cloudflare REST API
      https://api.cloudflare.com/client/v4
      (+ GraphQL: /graphql for analytics)
```

---

## Components

### `main.py`
Entry point. Delegates to `cloudflared_mcp.server.main()`.

### `cloudflared_mcp/server.py`
Starts the FastMCP HTTP server using configuration from `config.py`. Imports `tools` as a side-effect to register all active tools.

### `cloudflared_mcp/app.py`
Creates the single `FastMCP("Cloudflare")` instance. All `@mcp.tool(...)` decorators in the tool modules register against this instance.

### `cloudflared_mcp/config.py`
Reads server listen address from environment variables:
- `MCP_HOST` → host (default `0.0.0.0`)
- `MCP_PORT` or `PORT` → port (default `8000`)
- `MCP_PATH` → HTTP path (default `/mcp`)

Cloud Run automatically sets `PORT`, which the server respects.

### `cloudflared_mcp/client.py`
Async HTTP client (`httpx.AsyncClient`) that wraps the Cloudflare API. Provides:
- `request()` — standard JSON endpoint
- `request_raw()` — raw-body endpoint (used by DNS export)
- `request_form()` — multipart form (used by DNS import)
- `graphql()` — Cloudflare GraphQL Analytics API
- `request_all_pages()` — auto-pagination across page/per_page endpoints

The client reads `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` from environment at startup. If the token is missing, the server raises `RuntimeError` and refuses to start.

A single `CloudflareClient` instance is created lazily on the first tool call (`get_client()`) and reused for the lifetime of the process.

### `cloudflared_mcp/annotations.py`
Defines MCP `ToolAnnotations` constants (`READ_ONLY`, `CREATE`, `UPDATE`, `DELETE`, `RAW`) that communicate tool safety properties to MCP clients.

### `cloudflared_mcp/tools/__init__.py`
Controls which tool groups are active. Each uncommented import registers that module's tools via Python import side-effects. Commenting out a line disables the entire tool group without removing any code.

### `cloudflared_mcp/tools/*.py`
Each file implements a logical grouping of Cloudflare API operations as `@mcp.tool` async functions. Each tool is independently callable and stateless.

---

## Data Flow — Single Tool Call

```
1. AI agent sends JSON-RPC 2.0 request to POST /mcp
   { "method": "tools/call", "params": { "name": "get_dns_record", "arguments": {...} } }

2. FastMCP HTTP layer authenticates (if configured) and routes to the registered tool

3. Tool function calls get_client() to get the singleton CloudflareClient

4. CloudflareClient makes an HTTPS request to api.cloudflare.com with the Bearer token

5. Response is parsed; errors surface as CloudflareAPIError

6. Tool returns a dict (or str for raw endpoints)

7. FastMCP serializes the result into a JSON-RPC response and sends it back
```

---

## External Services

| Service | Purpose | Auth method |
|---|---|---|
| Cloudflare REST API (`api.cloudflare.com/client/v4`) | All zone, DNS, ruleset, billing operations | Bearer API token |
| Cloudflare GraphQL API (`api.cloudflare.com/graphql`) | Analytics queries (top paths, bot analytics) | Same Bearer API token |
| Google Cloud Run | Hosts and scales the MCP server container | IAM (service-to-service) |
| Google Artifact Registry | Stores the container image | gcloud credentials |
| Google Secret Manager | Stores `CLOUDFLARE_API_TOKEN` securely | IAM (Cloud Run service account) |

---

## Network Requirements

The deployed Cloud Run container needs:

| Direction | Destination | Purpose |
|---|---|---|
| Outbound | `api.cloudflare.com:443` | All Cloudflare API calls |
| Inbound | From AI agent / calling service | MCP protocol (HTTPS, port 443 via Cloud Run) |

Cloud Run handles TLS termination. No inbound port configuration is needed beyond the standard Cloud Run setup.

The service is deployed with `--no-allow-unauthenticated`, meaning callers must present a valid Google identity token (`Authorization: Bearer <token>`).

**No special firewall rules, VPN, or IP allowlisting is required** — Cloud Run handles public HTTPS access with Google IAM authentication.

---

## Authentication Model

### Inbound (AI Agent → MCP Server)
Cloud Run IAM authentication. Callers must have the `roles/run.invoker` IAM role on the Cloud Run service. They obtain a short-lived Google identity token and present it as a Bearer token.

### Outbound (MCP Server → Cloudflare)
A long-lived Cloudflare API token stored in Google Secret Manager (`cloudflare-api-token`). The Cloud Run revision mounts this secret as the `CLOUDFLARE_API_TOKEN` environment variable.

---

## Statelessness

The server holds no persistent state. Each HTTP request is independent. The only process-level state is the `CloudflareClient` singleton (connection pool), which is safe because it holds no user-specific data — only the API token from env.

This means Cloud Run can scale to multiple instances, restart freely, and deploy new revisions with zero data-loss risk.
