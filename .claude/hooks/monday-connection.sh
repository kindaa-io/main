#!/usr/bin/env bash
# SessionStart hook: tells Claude which monday.com account this environment's
# network-level connection points at. The environment's network secret makes the
# proxy add the client's API token to requests for api.monday.com, so no token
# lives in the repo or in an env var.

resp=$(curl -sS -m 15 https://api.monday.com/v2 \
  -H 'Content-Type: application/json' \
  -H 'API-Version: 2024-10' \
  -d '{"query":"{ me { name email account { id name slug } } }"}' 2>&1)

account=$(printf '%s' "$resp" | jq -r '.data.me.account | select(.) | "\(.name) (slug: \(.slug), id: \(.id))"' 2>/dev/null)

if [ -n "$account" ]; then
  user=$(printf '%s' "$resp" | jq -r '.data.me.name // empty')
  cat <<MSG
monday.com: this environment's MAIN connection is the network-level API connection
(POST https://api.monday.com/v2, auth added by the proxy — send no Authorization header).
Connected client account: ${account}, acting as ${user}.
Use it for every monday.com request in this session. Do NOT use the mcp__monday_com__*
connector: it is Kindaa's own account, not this client's. See CLAUDE.md.
MSG
else
  cat <<MSG
monday.com: the network-level connection to api.monday.com did not authenticate at
session start (response: $(printf '%s' "$resp" | head -c 300)).
This environment is expected to use it as its main monday.com connection. Tell the user
the network secret for api.monday.com is missing or invalid in this environment's
settings. Do NOT fall back to the mcp__monday_com__* connector (Kindaa's account) unless
the user explicitly asks for Kindaa's account.
MSG
fi
exit 0
