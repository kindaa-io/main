# Test plan after Phase 0 (awaiting go-ahead)

Changes vs the brief, driven by Phase 0:
- **Primary API path = one Transactions item** with name = exact product name and a signed Amount. Stock Updates header+subitem (2.3) stays as a secondary path.
- 2.1 vs 2.2: the link is applied by name-match on create *and* the calc recipes fire on link change. 2.1 checks whether sending the link in `create_item` plus the name-match "append" double-fires steps 5-7. 2.2 uses a **non-matching name** (e.g. `ZZ-TEST-A tx`) so only the late link connects it.
- Add **2.5b**: Take Out of Stock with a *positive* Amount (expect re-type to Add and stock up; silent wrong number).
- 2.7: expect Entry Stock to be re-typed Add and additive.
- Item naming: Transactions items must be named exactly `ZZ-TEST-A` / `ZZ-TEST-B` to be matched, which still satisfies the prefix guard. Stock Update headers: `ZZ-TEST-SU-<n>`.
- Drift check: use Products `Current Quantity Mirror` (ledger sum) plus my own sum from the snapshots.
- Polling: 5 s × 180 s as specified. The golden run took ≈34 s, so 180 s gives room.
- Phase 3 parallel tests will cost ≈ 7-9 automation actions each × 5-20 transactions.

Decisions needed from you before Phase 1:
1. **Target**: there's no sandbox. Run on Ricco production (all rules, zero exceptions), or set up a sandbox (install Spot-nik in a Kindaa workspace) and give me its IDs?
2. **Notifications**: OK that Low/Out-of-stock notifications go to the Products board subscribers? If not, a sandbox is the only clean option. I must not change the client's automations.
3. **Transport**: allow `api.monday.com` in the environment network settings (preferred, keeps the Python guard in the path), or OK to use the monday MCP write tool with the guard applied manually?
4. Set `confirmed_by_user: true` in `config.json`, or tell me to.
