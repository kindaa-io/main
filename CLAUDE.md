# monday.com access in client environments

Each client has its own cloud environment. In that environment, the client's
monday.com account is reached through a **network-level connection**: a network
secret on the environment makes the proxy add the client's API token to every
request to `api.monday.com`. This is the main, default monday.com connection.

A SessionStart hook (`.claude/hooks/monday-connection.sh`) checks the connection
at the start of every session and reports which client account it reaches.

## Rules

1. **Default to the client's connection.** For any monday.com request ("list the
   boards", "columns of the projects board", "update item X"), call the GraphQL
   API directly:

   ```bash
   curl -sS https://api.monday.com/v2 \
     -H 'Content-Type: application/json' \
     -H 'API-Version: 2024-10' \
     -d '{"query":"{ boards(limit: 50) { id name workspace { name } } }"}'
   ```

   Send **no** `Authorization` header and don't look for a token in env vars or
   files: the proxy adds it. Build larger queries with `jq -n --arg` to avoid
   quoting mistakes.

2. **Don't use the `mcp__monday_com__*` connector by default.** It is signed in
   to Kindaa's own monday.com account, not the client's. Use it only when the
   user explicitly asks about Kindaa's account. Never return data from it as if
   it were the client's.

3. **If the network connection fails** (`Not authenticated`, 401, or the
   account isn't the expected client), say so and tell the user to check the
   environment's network secret for `api.monday.com`. Don't fall back to the
   Kindaa connector.

4. **MCP servers in `.mcp.json` are secondary.** If a client MCP server fails to
   connect (e.g. a rejected static token), don't stop there: use the network
   connection above.

5. When a request names a client (e.g. "Ricco"), it refers to the account the
   SessionStart hook reported. Confirm with
   `{ me { account { name slug } } }` if in doubt.
