# DEVIATIONS — built differently from the spec

Each entry: what differs, why, and Omer's OK (who, when). No entry counts as approved without Omer's OK recorded here.

| # | Area | Spec says | Built / proposed | Reason | Omer's OK |
|---|---|---|---|---|---|
| D-01 | Access route (CLAUDE.md §2) | Connector first; raw API token only from `MONDAY_API_TOKEN` | **Proposed:** raw API only, with the credential injected by the environment's egress proxy (no token in the session) | Connector can't connect: the proxy denies `auth.monday.com`. `MONDAY_API_TOKEN` is not set | **Pending** |
| D-02 | Repo layout (CLAUDE.md §7) | Files at the repo root | Files under `ricco-inventory-demo/` | The repo root holds unrelated work (`bol_data_extraction.py`); keeps this CLAUDE.md scoped to this project | **Pending** (FYI) |
