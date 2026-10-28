# DEVIATIONS — built differently from the spec

Each entry: what differs, why, and Omer's OK (who, when). No entry counts as approved without Omer's OK recorded here.

| # | Area | Spec says | Built / proposed | Reason | Omer's OK |
|---|---|---|---|---|---|
| D-01 | Access route (CLAUDE.md §2) | Connector first; raw API token only from `MONDAY_API_TOKEN` | **Proposed:** raw API only, with the credential injected by the environment's egress proxy (no token in the session) | Connector can't connect: the proxy denies `auth.monday.com`. `MONDAY_API_TOKEN` is not set | **Approved**: Omer, chat, 2026-10-28 ("connection via the proxy api") |
| D-02 | Repo layout (CLAUDE.md §7) | Files at the repo root | Files under `ricco-inventory-demo/` | The repo root holds unrelated work (`bol_data_extraction.py`); keeps this CLAUDE.md scoped to this project | **Pending** (FYI) |
| D-03 | Test items (spec §10 Phases 3, 5; CLAUDE.md rule 6) | `ZZ-TEST-` items live on the demo boards | Tests run on `ZZ-TEST-` boards in a separate folder **`ZZ-TEST- Inventory Demo Tests`** in workspace 15462830; tests that need a project/unit link use the real Projects/Units boards one-way (no column added to Sam's boards) | Keeps the demo boards' Request # / PO # / Movement # auto numbers free of test items | **Approved**: Omer, chat, 2026-10-28 (answer 2) |
| D-04 | Subitem boards (spec §10 Phase 3.1) | Bootstrap `ZZ-TEST-` parent stays on the demo board | `ZZ-TEST-bootstrap` parent + subitem created on Material Requests and on Purchase Orders, then **moved** (`move_item_to_board`) to `ZZ-TEST- bootstrap parking` in the test folder; the subitems column/board stays | The API can't create a subtasks column; moving keeps the demo boards free of test items, as asked at Gate 1 (answer 2). Nothing deleted or archived | **Pending** (FYI; follows answer 2) |
| D-05 | Column positions | Spec order | Repurposed default subitem columns keep monday's positions; `zz-unused – Owner` / `zz-unused – Date` sit mid-table, and connect/reflection columns created later are appended near the end. Hidden in views (Phase 8) | The API has no column-reorder mutation | **Pending** (FYI) |
