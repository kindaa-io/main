#!/usr/bin/env bash
# Read-only helper: send one GraphQL query file to the monday API.
# Usage: scripts/monday_query.sh <query.graphql>
#
# Auth: uses MONDAY_API_TOKEN if set. In the Claude Code cloud environment the
# egress proxy injects credentials for api.monday.com, so the token may be unset.
# The token is never printed.
set -euo pipefail

API_VERSION="${MONDAY_API_VERSION:-2026-10}"   # pinned in Phase 0
QUERY_FILE="$1"

if grep -qiE '^\s*mutation' "$QUERY_FILE"; then
  echo "refusing: monday_query.sh is read-only (file starts with 'mutation')" >&2
  exit 2
fi

AUTH_ARGS=()
if [[ -n "${MONDAY_API_TOKEN:-}" ]]; then
  AUTH_ARGS=(-H "Authorization: ${MONDAY_API_TOKEN}")
fi

python3 -c 'import json,sys; print(json.dumps({"query": open(sys.argv[1]).read()}))' "$QUERY_FILE" |
  curl -sS https://api.monday.com/v2 \
    -H "Content-Type: application/json" \
    -H "API-Version: ${API_VERSION}" \
    "${AUTH_ARGS[@]}" \
    --data-binary @-
