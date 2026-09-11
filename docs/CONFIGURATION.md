# Configuration

## Environment Variables

### Required

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `CLOUDFLARE_API_TOKEN` | **Yes** | Authenticates all calls to the Cloudflare API | `abc123...` |
| `CLOUDFLARE_ACCOUNT_ID` | **Yes** | Default account ID for account-scoped tools (billing, validate_rule_expression, etc.) | `a1b2c3d4...` |

### Optional (Server Listen Address)

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port the server listens on. Cloud Run sets this automatically; do not override on Cloud Run. |
| `MCP_PORT` | _(uses `PORT`)_ | Explicit port override. Takes precedence over `PORT` if set. |
| `MCP_HOST` | `0.0.0.0` | Host/interface to bind. Set in the Dockerfile; do not change for Cloud Run. |
| `MCP_PATH` | `/mcp` | HTTP path the MCP endpoint is served at. |

### Where to Obtain Each Value

**`CLOUDFLARE_API_TOKEN`**
Create at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens). See [API Token Permissions](#api-token-permissions) below.

**`CLOUDFLARE_ACCOUNT_ID`**
Found on the right-hand sidebar of any zone's Overview page in the Cloudflare dashboard, or via the Cloudflare API: `GET /accounts`.

---

## API Token Permissions

When creating the Cloudflare API token, grant exactly what the active tool groups need:

### Active tools (minimum required permissions)

| Permission | Resource | Access level |
|---|---|---|
| Zone Analytics | Zone | Read |
| DNS | Zone | Read + Edit |
| Zone Rulesets | Zone | Read + Edit |
| Account Rulesets | Account | Read |
| Billing (Subscriptions) | Account | Read |
| Zone Settings | Zone | Read + Edit |

> **Recommendation:** Scope the token to the specific zones and account, not "All zones" or "All accounts", to limit blast radius if the token is compromised.

### Additional permissions for disabled tool groups

If you enable any of the currently disabled tool groups, add the corresponding permissions:

| Tool group | Additional permission needed |
|---|---|
| `access.py` | Zero Trust: Access: Apps and Policies (Account, Read + Edit) |
| `cache.py` | Cache Purge (Zone, Purge) |
| `firewall.py` | Zone WAF (Zone, Read + Edit) |
| `load_balancers.py` | Load Balancing (Account + Zone, Read + Edit) |
| `ssl.py` | SSL and Certificates (Zone, Read + Edit) |
| `tunnels.py` | Cloudflare Tunnel (Account, Read + Edit) |
| `workers_kv.py` | Workers KV Storage (Account, Read + Edit) |
| `raw.py` | Depends on the API paths the caller uses |

---

## Local `.env` File

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:

```
CLOUDFLARE_API_TOKEN=your-api-token-here
CLOUDFLARE_ACCOUNT_ID=your-account-id-here
```

The `.env` file is gitignored and must never be committed. Use `./scripts/set-credentials.sh` as a safe alternative that handles upserts correctly.

---

## Production Configuration (Cloud Run)

On Cloud Run:
- `CLOUDFLARE_API_TOKEN` is injected from **Google Secret Manager** (`cloudflare-api-token:latest`). It never appears in deployment manifests or logs.
- `CLOUDFLARE_ACCOUNT_ID` is a plain environment variable set via `--set-env-vars` in the deploy command.
- `PORT` is set automatically by Cloud Run (typically `8080`). The server reads it via `config.py`.
- `MCP_HOST` is set to `0.0.0.0` in the Dockerfile so the server binds to all interfaces inside the container.

---

## Activating / Deactivating Tool Groups

Tool groups are enabled or disabled by editing `cloudflared_mcp/tools/__init__.py`. Each line controls one group:

```python
from cloudflared_mcp.tools import (  # noqa: F401
    # access,          # ← uncomment to enable Zero Trust Access tools
    analytics,
    billing,
    # cache,           # ← uncomment to enable Cache Purge tools
    dns,
    # firewall,        # ← uncomment to enable Firewall tools
    # load_balancers,
    # raw,
    rules,
    # ssl,
    # tunnels,         # ← uncomment to enable Cloudflare Tunnels tools
    # workers_kv,
    zones,
)
```

After editing this file, **rebuild and redeploy the container** for the change to take effect in production. The server does not hot-reload.
