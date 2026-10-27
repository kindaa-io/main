#!/usr/bin/env bash
# Phase 0 preflight: read-only. Re-runnable; makes no writes to monday.
# Prints identity, workspace/folder check and column counts of Sam's boards.
set -euo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/q.graphql" <<'EOF'
{
  me { id name account { id name } }
  version { value kind }
  workspaces(ids: [15462830]) { id name state }
  folders(workspace_ids: [15462830], limit: 100) { id name }
  boards(ids: [18412939430, 18412939439, 18433554480]) { id name columns { id } }
}
EOF

./monday_query.sh "$TMP/q.graphql" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if "errors" in d:
    sys.exit("API errors: %s" % d["errors"])
d = d["data"]
me = d["me"]
ok = me["id"] == "103186497" and me["account"]["id"] == "34799434"
print("identity:", me["id"], me["name"], "account", me["account"]["id"], "OK" if ok else "MISMATCH - STOP")
print("api version (default):", d["version"])
print("workspace:", d["workspaces"])
names = [f["name"] for f in d["folders"]]
print("demo folder exists:", "Inventory & Procurement (Demo)" in names, "| folders:", names)
for b in d["boards"]:
    print("board", b["id"], b["name"], "columns:", len(b["columns"]))
sys.exit(0 if ok else 1)
'
