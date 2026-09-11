# Troubleshooting

---

## Server Won't Start

**Symptom:** Server exits immediately with `RuntimeError: CLOUDFLARE_API_TOKEN environment variable is required`.

**Cause:** The `CLOUDFLARE_API_TOKEN` env var is not set.

**Diagnose:**
```bash
echo $CLOUDFLARE_API_TOKEN
```

**Fix:**
- Local: `source .env` or run `./scripts/set-credentials.sh`
- Cloud Run: verify the `--set-secrets` flag in the deploy command and that the secret version exists:
  ```bash
  gcloud secrets versions list cloudflare-api-token --project gemini-project-n1
  ```

---

## HTTP 401 / 403 When Calling the MCP Endpoint

**Symptom:** `curl` or the AI agent returns a 401 or 403 from the Cloud Run service.

**Cause:** The caller does not have `roles/run.invoker` on the Cloud Run service, or the identity token is missing/expired.

**Diagnose:**
```bash
TOKEN=$(gcloud auth print-identity-token)
echo $TOKEN   # should be a non-empty JWT
```

**Fix:**
```bash
# Grant invoker to a service account
gcloud run services add-iam-policy-binding verse-cloudflare-mcp \
  --project gemini-project-n1 \
  --region asia-south1 \
  --member="serviceAccount:SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Cloudflare API Authentication Failure

**Symptom:** Tool call returns `CloudflareAPIError` with status 401 and message `Authentication error`.

**Cause:** `CLOUDFLARE_API_TOKEN` is invalid, expired, or has been revoked.

**Diagnose:**
```bash
# Test the token directly
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/user/tokens/verify"
```
A `"result": {"status": "active"}` response means the token is valid.

**Fix:** Rotate the token (see [Deployment — Updating Cloudflare Credentials](./DEPLOYMENT.md#updating-cloudflare-credentials)).

---

## Cloudflare API Permission Denied

**Symptom:** Tool call returns a 403 from Cloudflare with `"code": 10000` or a similar permissions error.

**Cause:** The API token lacks the required permission for the operation.

**Diagnose:** Check the exact error message in the tool response — Cloudflare includes a human-readable description of which permission is missing.

**Fix:** Edit the token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) and add the required permission. Refer to [Configuration — API Token Permissions](./CONFIGURATION.md#api-token-permissions).

---

## Wrong Account ID

**Symptom:** Account-scoped tools (`list_subscriptions`, `validate_rule_expression`, billing tools) return `"error": "Invalid account"` or `404`.

**Cause:** `CLOUDFLARE_ACCOUNT_ID` is set to the wrong value.

**Diagnose:**
```bash
# List accounts the token has access to
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts" | python3 -m json.tool
```

**Fix:** Update the `CLOUDFLARE_ACCOUNT_ID` environment variable on Cloud Run:
```bash
gcloud run deploy verse-cloudflare-mcp \
  --image=asia-south1-docker.pkg.dev/gemini-project-n1/cloud-run-source-deploy/verse-cloudflare-mcp:latest \
  --project gemini-project-n1 \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --set-secrets=CLOUDFLARE_API_TOKEN=cloudflare-api-token:latest \
  --set-env-vars=CLOUDFLARE_ACCOUNT_ID=CORRECT_ACCOUNT_ID \
  --quiet
```

---

## Tool Not Found

**Symptom:** AI agent reports the tool doesn't exist, or `tools/list` doesn't include the expected tool.

**Cause:** The tool's module is commented out in `cloudflared_mcp/tools/__init__.py`.

**Diagnose:**
```bash
grep -n "^#\|^    #" cloudflared_mcp/tools/__init__.py
```

**Fix:** Uncomment the relevant import in `tools/__init__.py`, then rebuild and redeploy (see [Maintenance — Enabling a Disabled Tool Group](./MAINTENANCE.md#enabling-a-disabled-tool-group)).

---

## Deployment Failure

**Symptom:** `gcloud run deploy` fails.

**Common causes and fixes:**

| Error message | Cause | Fix |
|---|---|---|
| `permission denied on resource project` | Missing IAM roles | Ensure the deploying account has `roles/run.admin` and `roles/artifactregistry.writer` |
| `failed to pull image` | Image not in Artifact Registry | Run the `docker build` + `docker push` step first |
| `secret not found` | Secret Manager secret doesn't exist | Create it: `gcloud secrets create cloudflare-api-token --project gemini-project-n1` |
| `container failed to start` | Missing env var or startup crash | Check Cloud Run logs (see below) |

---

## Viewing Logs

```bash
# Stream recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=verse-cloudflare-mcp" \
  --project gemini-project-n1 \
  --limit 100 \
  --format "value(textPayload)"

# Or use the Logs Explorer:
# console.cloud.google.com/logs → filter by service verse-cloudflare-mcp
```

---

## MCP Initialize Returns an Error

**Symptom:** The `initialize` handshake responds with `"error"` instead of `"result"`.

**Diagnose:** Check the `message` field in the error body, then check Cloud Run logs for the startup trace.

**Common cause:** The container started but the server immediately crashed (missing env var, import error). Logs will show the Python traceback.

---

## Tool Calls Time Out

**Symptom:** MCP call takes > 30 seconds and returns a timeout error.

**Cause:** The `CloudflareClient` has a 30-second timeout (`timeout=30.0` in `client.py`). If Cloudflare's API is slow or unreachable, calls will time out.

**Diagnose:**
```bash
curl -s --max-time 10 "https://api.cloudflare.com/client/v4/ips" | head -c 200
```
If this times out, there's a network issue between the Cloud Run instance and Cloudflare.

**Fix:** Cloud Run instances have standard internet egress. If the Cloud Run service is in a VPC with restricted egress, ensure `api.cloudflare.com:443` is reachable.

---

## Bot Analytics Returns an Error

**Symptom:** `get_bot_analytics` returns a Cloudflare error about subscription or access.

**Cause:** Bot Management analytics require a Bot Management or equivalent Cloudflare subscription on the zone.

**Fix:** This tool only works on zones with a Bot Management add-on. It can be disabled or ignored without affecting other tools.

---

## GraphQL Analytics Tools Fail

**Symptom:** `get_top_paths` or `get_bot_analytics` return `"errors"` in the response.

**Cause:** GraphQL analytics require the API token to have Zone Analytics (Read) permission, and the time range parameters must be ISO 8601 datetime strings (not the negative-integer shorthand used by REST analytics tools).

**Fix:** Ensure `since` and `until` are passed as ISO 8601 strings: `"2024-01-01T00:00:00Z"`. These tools do not accept the negative-integer format.
