#!/usr/bin/env bash
# Create/update the .env file used by cloudflared-mcp-server with Cloudflare credentials.
#
# Usage:
#   ./scripts/set-credentials.sh                                    # interactive prompt (token hidden)
#   ./scripts/set-credentials.sh --api-token TOKEN --account-id ID   # non-interactive
#   ./scripts/set-credentials.sh --account-id ID                     # set only the account id
#   ./scripts/set-credentials.sh --clear                             # remove stored credentials from .env
#
# Safe to re-run: it upserts keys in .env rather than duplicating or wiping the file.
# Never pass the token as a bare shell arg in a shared terminal/history if you can avoid it —
# prefer running with no flags so it's read via a hidden prompt instead.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"

API_TOKEN=""
ACCOUNT_ID=""
CLEAR=false

usage() {
    grep '^#' "$0" | sed -n '2,10p' | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --api-token) API_TOKEN="$2"; shift 2 ;;
        --account-id) ACCOUNT_ID="$2"; shift 2 ;;
        --clear) CLEAR=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
    esac
done

if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi
fi

# upsert_key <KEY> <VALUE>: replaces an existing "KEY=" line or appends one.
upsert_key() {
    local key="$1" value="$2"
    local tmp
    tmp="$(mktemp)"
    grep -v "^${key}=" "$ENV_FILE" > "$tmp" || true
    mv "$tmp" "$ENV_FILE"
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
}

remove_key() {
    local key="$1"
    local tmp
    tmp="$(mktemp)"
    grep -v "^${key}=" "$ENV_FILE" > "$tmp" || true
    mv "$tmp" "$ENV_FILE"
}

if [[ "$CLEAR" == true ]]; then
    for key in CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID; do
        remove_key "$key"
    done
    echo "Cleared Cloudflare credentials from $ENV_FILE"
    exit 0
fi

# Non-interactive: flags were provided.
if [[ -n "$API_TOKEN" || -n "$ACCOUNT_ID" ]]; then
    if [[ -n "$API_TOKEN" ]]; then
        upsert_key CLOUDFLARE_API_TOKEN "$API_TOKEN"
    fi
    if [[ -n "$ACCOUNT_ID" ]]; then
        upsert_key CLOUDFLARE_ACCOUNT_ID "$ACCOUNT_ID"
    fi
    echo "Updated $ENV_FILE"
    exit 0
fi

# Interactive mode.
read -r -s -p "Cloudflare API token (hidden input): " API_TOKEN
echo
read -r -p "Cloudflare account ID: " ACCOUNT_ID
upsert_key CLOUDFLARE_API_TOKEN "$API_TOKEN"
upsert_key CLOUDFLARE_ACCOUNT_ID "$ACCOUNT_ID"

echo "Updated $ENV_FILE"
