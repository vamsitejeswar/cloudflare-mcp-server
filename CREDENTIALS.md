# Updating Cloudflare credentials

When you get the actual client's Cloudflare account details — API token and
account ID — replace the current ones in both places below: local `.env` and
the deployed Cloud Run service. They're independent of each other.

## 1. Local `.env` (for local runs/testing)

```bash
cd /Users/puttur.kumar/Documents/cloudflared-mcp-server
./scripts/set-credentials.sh --api-token CLIENT_API_TOKEN --account-id CLIENT_ACCOUNT_ID
```

Verify it authenticates:

```bash
.venv/bin/python3 -c "
import asyncio
from cloudflared_mcp.tools.zones import list_zones

async def main():
    print(await list_zones())

asyncio.run(main())
"
```

## 2. Cloud Run (`verse-cloudflare-mcp`) — updates what Gemini Enterprise actually calls

The API token is read from Secret Manager; the account ID is a plain
(non-secret) env var. Add a new secret version for the token:

```bash
printf '%s' 'CLIENT_API_TOKEN' | gcloud secrets versions add cloudflare-api-token \
  --project gemini-project-n1 --data-file=-
```

Then force a new revision, updating the account ID env var at the same time:

```bash
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=CLIENT_ACCOUNT_ID \
  --quiet
```

Verify the deployed service is live (initialize handshake):

```bash
URL="$(gcloud run services describe verse-cloudflare-mcp --project gemini-project-n1 --region asia-south1 --format='value(status.url)')"
TOKEN=$(gcloud auth print-identity-token --project gemini-project-n1)
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" -X POST \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  "$URL/mcp"
```

A `"result"` in the response (not an error) means it's live. To fully verify
the new credentials work end-to-end, capture the `Mcp-Session-Id` response
header from that call and follow up with a `tools/call` for `list_zones` with
empty `arguments` — it should return the client's actual zones.

## Notes

- Cloudflare API tokens are created at
  https://dash.cloudflare.com/profile/api-tokens — scope it to exactly what
  this server needs (Zone/DNS/Tunnel/Firewall/etc edit permissions).
- Old secret versions aren't deleted automatically; disable/destroy them in
  Secret Manager if you want to fully retire the previous token:
  `gcloud secrets versions list cloudflare-api-token --project gemini-project-n1`
- Rotating the token doesn't require re-granting IAM (`run.invoker` for
  Gemini Enterprise's service agent) — that's unaffected by credential changes.
