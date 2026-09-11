# Deployment

The server runs as a container on **Google Cloud Run**. This document covers both initial deployment from a clean environment and the credential rotation procedure for ongoing operations.

---

## Production Deployment Details

| Property | Value |
|---|---|
| Platform | Google Cloud Run |
| GCP Project | `gemini-project-n1` |
| Region | `asia-south1` |
| Service name | `verse-cloudflare-mcp` |
| Container image | `asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest` |
| MCP endpoint | `POST /mcp` |
| Authentication | IAM (no public access) |
| Cloudflare token storage | Google Secret Manager — secret name: `cloudflare-api-token` |

---

## Prerequisites

### Tools required
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) — for deployment and secret management
- [Docker](https://docs.docker.com/get-docker/) — for building the container image
- Python 3.10+ — for local testing only

### GCP authentication
```bash
gcloud auth login
gcloud auth configure-docker asia-south1-docker.pkg.dev
gcloud config set project gemini-project-n1
```

### Required GCP IAM permissions
The operator running deployment commands needs:
- `roles/run.admin` — to deploy Cloud Run services
- `roles/secretmanager.admin` — to create/update secrets
- `roles/artifactregistry.writer` — to push container images

---

## Step 1: Store the Cloudflare API Token in Secret Manager

This only needs to be done once. For credential rotation, see [Updating Cloudflare Credentials](#updating-cloudflare-credentials).

```bash
# Create the secret (first time only)
gcloud secrets create cloudflare-api-token --project gemini-project-n1

# Add the token value
printf '%s' 'YOUR_CLOUDFLARE_API_TOKEN' | gcloud secrets versions add cloudflare-api-token \
  --project gemini-project-n1 --data-file=-
```

Replace `YOUR_CLOUDFLARE_API_TOKEN` with the actual token. Do **not** use `echo` — it may add a trailing newline.

---

## Step 2: Build and Push the Container Image

```bash
cd /path/to/cloudflare-mcp-server

docker build -t asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest .

docker push asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest
```

Alternatively, use Cloud Build to build and push without a local Docker daemon:

```bash
gcloud builds submit \
  --tag asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1
```

---

## Step 3: Deploy to Cloud Run

```bash
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=YOUR_CLOUDFLARE_ACCOUNT_ID \
  --quiet
```

Replace `YOUR_CLOUDFLARE_ACCOUNT_ID` with the client's Cloudflare account ID (found on any zone's Overview page in the Cloudflare dashboard).

---

## Step 4: Grant Invoker Access to the Calling Service

The AI agent or service that calls this MCP server must have `roles/run.invoker` on the Cloud Run service. To grant it:

```bash
gcloud run services add-iam-policy-binding verse-cloudflare-mcp \
  --project gemini-project-n1 \
  --region asia-south1 \
  --member="serviceAccount:CALLING_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

Replace `CALLING_SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com` with the identity of the service making MCP calls (e.g. the Gemini Enterprise service agent).

---

## Step 5: Verify the Deployment

Get the service URL and test the MCP handshake:

```bash
URL="$(gcloud run services describe verse-cloudflare-mcp \
  --project gemini-project-n1 \
  --region asia-south1 \
  --format='value(status.url)')"

TOKEN=$(gcloud auth print-identity-token --project gemini-project-n1)

curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -X POST \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  "$URL/mcp"
```

A `"result"` key in the response (not `"error"`) confirms the server is live.

To verify the Cloudflare credentials work end-to-end, capture the `Mcp-Session-Id` response header and call `list_zones`:

```bash
SESSION_ID="<value of Mcp-Session-Id header from above>"

curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -X POST \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_zones","arguments":{}}}' \
  "$URL/mcp"
```

The response should list the Cloudflare zones belonging to the configured account.

---

## Updating Cloudflare Credentials

When the Cloudflare API token needs to be rotated or the account ID changes:

### 1. Add a new secret version (for token rotation)

```bash
printf '%s' 'NEW_CLOUDFLARE_API_TOKEN' | gcloud secrets versions add cloudflare-api-token \
  --project gemini-project-n1 --data-file=-
```

### 2. Force a new Cloud Run revision with updated values

```bash
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=NEW_ACCOUNT_ID \
  --quiet
```

### 3. Disable the old secret version (optional but recommended)

```bash
# List all versions
gcloud secrets versions list cloudflare-api-token --project gemini-project-n1

# Disable the old version (replace VERSION_NUMBER)
gcloud secrets versions disable VERSION_NUMBER \
  --secret cloudflare-api-token \
  --project gemini-project-n1
```

---

## Local Deployment (Development / Testing)

```bash
# Clone the repo
git clone <repo-url>
cd cloudflare-mcp-server

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Set credentials interactively (token input is hidden)
./scripts/set-credentials.sh

# Or set directly
./scripts/set-credentials.sh --api-token YOUR_TOKEN --account-id YOUR_ACCOUNT_ID

# Load the .env and run
set -a && source .env && set +a
python main.py
```

The server starts at `http://localhost:8000/mcp`.

### Verify local credentials
```bash
source .venv/bin/activate
python3 -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from cloudflared_mcp.tools.zones import list_zones

async def main():
    print(await list_zones())

asyncio.run(main())
"
```

> Note: `python-dotenv` is not a project dependency. If `load_dotenv()` fails, install it with `pip install python-dotenv` or export the env vars manually before running the script.

---

## Deployment Checklist

- [ ] Cloudflare API token created with correct permissions (see [Configuration](./CONFIGURATION.md#api-token-permissions))
- [ ] Token stored in Secret Manager: `cloudflare-api-token` in project `gemini-project-n1`
- [ ] Container image built and pushed to Artifact Registry
- [ ] `gcloud run deploy` completed successfully
- [ ] `CLOUDFLARE_ACCOUNT_ID` set as env var on the Cloud Run service
- [ ] Calling service account has `roles/run.invoker`
- [ ] MCP `initialize` handshake returns `"result"` (not `"error"`)
- [ ] `list_zones` tool call returns actual zones

---

## Rollback

To roll back to a previous Cloud Run revision:

```bash
# List revisions
gcloud run revisions list \
  --service verse-cloudflare-mcp \
  --project gemini-project-n1 \
  --region asia-south1

# Route all traffic to a specific revision
gcloud run services update-traffic verse-cloudflare-mcp \
  --project gemini-project-n1 \
  --region asia-south1 \
  --to-revisions=REVISION_NAME=100
```
