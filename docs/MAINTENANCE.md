# Maintenance

---

## Rotating Cloudflare Credentials

### Rotating the API token

```bash
# 1. Create a new token at dash.cloudflare.com/profile/api-tokens
#    (same permissions as the existing one — see CONFIGURATION.md)

# 2. Add a new secret version
printf '%s' 'NEW_API_TOKEN' | gcloud secrets versions add cloudflare-api-token \
  --project gemini-project-n1 --data-file=-

# 3. Force a new Cloud Run revision to pick up the new secret version
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=YOUR_ACCOUNT_ID \
  --quiet

# 4. Verify the new token works (see DEPLOYMENT.md — Step 5)

# 5. Disable the old secret version
gcloud secrets versions list cloudflare-api-token --project gemini-project-n1
gcloud secrets versions disable OLD_VERSION_NUMBER \
  --secret cloudflare-api-token --project gemini-project-n1
```

### Updating the account ID

Include `--set-env-vars=CLOUDFLARE_ACCOUNT_ID=NEW_ID` in the `gcloud run deploy` command above.

---

## Enabling a Disabled Tool Group

All tool implementations are already present in `cloudflared_mcp/tools/`. To activate a group:

1. Open `cloudflared_mcp/tools/__init__.py`
2. Uncomment the import for the desired module:
   ```python
   # Before:
   # tunnels,
   
   # After:
   tunnels,
   ```
3. Ensure the API token has the required permissions for the new tools (see [Configuration](./CONFIGURATION.md#additional-permissions-for-disabled-tool-groups))
4. Rebuild and redeploy:
   ```bash
   docker build -t asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest .
   docker push asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest
   
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

## Deploying a New Application Version

1. Make code changes locally
2. Test locally (see [Deployment — Local Deployment](./DEPLOYMENT.md#local-deployment-development--testing))
3. Build and push the container image
4. Deploy to Cloud Run

```bash
docker build -t asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest .
docker push asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest

gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=YOUR_ACCOUNT_ID \
  --quiet
```

Cloud Run performs a zero-downtime revision swap automatically.

---

## Updating Dependencies

The project has two runtime dependencies (`fastmcp`, `httpx`) and one implicit build dependency (`setuptools`).

```bash
# Activate the virtual environment
source .venv/bin/activate

# Check for outdated packages
pip list --outdated

# Upgrade a specific package
pip install --upgrade fastmcp httpx

# After upgrading, test locally before deploying
python main.py   # verify it starts

# Commit the updated pyproject.toml if you change version constraints
# Then rebuild the Docker image and redeploy
```

> **Note:** `pyproject.toml` specifies minimum version bounds (`>=`), not pinned versions. The Docker image build (`pip install --no-cache-dir .`) always installs the latest compatible version at build time. If a dependency update causes a regression, roll back by adding an upper bound in `pyproject.toml` (e.g. `httpx>=0.27.0,<0.30.0`) and rebuilding.

---

## What Must Be Restarted After Changes

| Change type | Action needed |
|---|---|
| Code change (`.py` files) | Rebuild image + redeploy Cloud Run |
| Enable/disable tool group (`tools/__init__.py`) | Rebuild image + redeploy Cloud Run |
| `CLOUDFLARE_API_TOKEN` rotation | Add new secret version + redeploy Cloud Run |
| `CLOUDFLARE_ACCOUNT_ID` change | Redeploy Cloud Run (`--set-env-vars`) |
| Local `.env` change | Restart `python main.py` |

The server process does **not** hot-reload.

---

## What Should Be Backed Up

| Item | Where it lives | How to back up |
|---|---|---|
| Source code | Git repository | Push to remote regularly |
| Container image | Artifact Registry | Multiple tags / versions are retained there |
| Cloudflare API token | Secret Manager (`cloudflare-api-token`) | Secret Manager retains all versions |
| `.env` (local) | Local disk only | Keep locally; do not commit |

---

## What Must NOT Be Modified Directly in Production

- **Secret Manager secret values** — only add new versions; never edit in-place (Secret Manager doesn't support editing)
- **The running Cloud Run container** — all changes go through a new image build and deployment
- **`cloudflared_mcp/tools/__init__.py`** — only edit locally and redeploy; changes on disk of a running container are lost on next revision

---

## Monitoring

Cloud Run automatically collects metrics (request count, latency, instance count) in Google Cloud Monitoring.

```
console.cloud.google.com → Cloud Run → verse-cloudflare-mcp → Metrics
```

Application logs:
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=verse-cloudflare-mcp" \
  --project gemini-project-n1 \
  --limit 200
```

There is no custom health check endpoint. The MCP `initialize` method serves as a health probe.

---

## Known Limitations

- **No persistent state**: the server is stateless. Any caching of Cloudflare API results must be added by the caller.
- **30-second API timeout**: hardcoded in `client.py`. Very large DNS zone exports or paginated zone lists on large accounts may approach this limit.
- **GraphQL time format**: `get_top_paths` and `get_bot_analytics` require ISO 8601 datetime strings; they do not accept the negative-integer shorthand used by the REST analytics tools.
- **Bot analytics subscription**: `get_bot_analytics` requires a Bot Management add-on on the zone. It will return a Cloudflare error for zones without this subscription.
- **Single-account default**: `CLOUDFLARE_ACCOUNT_ID` is a single value. Tools that operate across multiple Cloudflare accounts must pass `account_id` explicitly in each call.
- **`main.py` in root**: kept for convenience (`python main.py`). The canonical entrypoint for production is the `cloudflared-mcp-server` console script installed by `pyproject.toml`.
