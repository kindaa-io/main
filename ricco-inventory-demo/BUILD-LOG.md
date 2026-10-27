# BUILD-LOG — Ricco Cabinetry · Inventory & Procurement Demo

Every write: timestamp (UTC), phase, mutation (no tokens), target board, result.

---

## Phase 0 — Preflight (read-only) · 2026-10-27

**No writes to monday.** Every call below was a GraphQL *query* (reads and schema introspection).

### 0.1 Route and identity

| Check | Result |
|---|---|
| monday.com connector (`plugin:monday-com:monday`) | **Not available.** It failed to connect: the egress proxy denies `auth.monday.com:443` (403 on CONNECT), which the connector needs for OAuth. |
| `MONDAY_API_TOKEN` env var | **Not set.** |
| Raw API `https://api.monday.com/v2` | **Reachable.** The environment's proxy injects the credential for `api.monday.com`, so no token is handled in this session. |
| `me` via raw API | user **103186497** "Kindaa support" (support@kindaa.io), account **34799434** "Ricco cabinetry" → **match** |
| `me` via connector | Not possible (connector down). The "connector and API point at the same account" check is still open. |
| API version | Versions offered: 2025-04 … 2026-07 (maintenance), **2026-10 (current)**, 2027-01/2027-04 (RC). **Pinned: `API-Version: 2026-10`.** |

### 0.2 Capability check (API 2026-10, from schema introspection + `get_column_type_schema` / `get_view_schema_by_type` / `all_widgets_schema`)

The connector could not be checked (down). Unless noted, "API: yes" means the mutation and settings schema exist. Nothing was test-written in Phase 0, so all of it is still unexercised.

| Operation | Connector | API (2026-10) | Manual? | Evidence / notes |
|---|---|---|---|---|
| Create folder in workspace | n/a | **Yes** | — | `create_folder(name, workspace_id)` |
| Create board in folder | n/a | **Yes** | — | `create_board(board_name, board_kind: public, folder_id, workspace_id, empty)`. `empty: true` may avoid default columns; verify in Phase 1 |
| Groups (create, top position, rename) | n/a | **Yes** | — | `create_group(position_relative_method, relative_to)`, `update_group` |
| Status column with labels + colours + done flag | n/a | **Yes** | — | `create_status_column(defaults: {labels: [{label, color, index, is_done}]})`; 40 named colours; label max 30 chars (longest spec label is 20) |
| Dropdown (single / multi) with labels | n/a | **Yes** | — | `create_dropdown_column(defaults: {labels, limit_select, label_limit_count})` |
| Plain columns: text, long text, numbers ($ unit), date (+time), people, email, phone, file, checkbox, auto number, creation log | n/a | **Yes** | — | All exist in the `ColumnType` enum. `auto_number` settings: `prefix`, `scope` (group/board), `order`; no zero-padding |
| Connect, one-way | n/a | **Yes** | — | `board_relation` settings `boardIds`, `allowMultipleItems` |
| Connect, **two-way** | n/a | **Schema yes, unverified** | fallback | `allowCreateReflectionColumn: true`. The same flag is set on Sam's existing two-way links (e.g. Projects `board_relation_mm3ajesj`) |
| Connect, **multi-board** (Projects + Units) | n/a | **Schema yes, unverified** | fallback | `boardIds: [18412939430, 18412939439]`. The pattern exists in the account (Task Manager `board_relation_mm3att2b`, reflected on Units as `board_relation_mm3ad88` and on Projects as `board_relation_mm3ajesj`) |
| Mirror, **sum** (numbers) | n/a | **Schema yes, unverified** | — | `mirror` settings `relation_column`, `displayed_linked_columns`, `function: sum` |
| Mirror, **all statuses** | n/a | **Yes** | — | `sumType: allStatuses`. Already used in the account (Units `lookup_mm3a8xr9`) |
| Mirror via **subitems** column | n/a | **Yes** | — | `relation_column: {subtasks_…: true}`. Already used (Projects `lookup_mm3rfs7n`, a mirror of a mirror) |
| Mirror sum **over a formula** | n/a | **Unknown** | — | Phase 5 aggregation test |
| Formula | n/a | **Yes** | — | `settings.formula`. Formula over a mirror already used (Units `formula_mm5rgrx7`) |
| Rename columns (reflections, defaults) | n/a | **Yes** | — | `change_column_title`, `update_column` |
| Subitems column / subitems | n/a | **Yes** | — | `create_column(column_type: subtasks)` (settings schema exists; try this before the ZZ-TEST bootstrap); `create_subitem` |
| File upload to file column | n/a | **Yes, untested** | — | `add_file_to_column`, multipart to `https://api.monday.com/v2/file` (host allowed) |
| Table views: filter, sort, column visibility, group by | n/a | **Yes** | — | `create_view_table` (`filter`, `sort`, `settings.columns.column_properties`, `settings.group_by.conditions`). Group-by on a connect column unverified → fall back to sort |
| **Kanban** views | n/a | **No** | **Yes** | `ViewKind` = TABLE, FORM, DASHBOARD, APP only |
| **WorkForm on an existing board** | n/a | **Uncertain** | likely | `create_form` always creates a **new** board (`destination_workspace_id`, `destination_name`), so it can't target Stock Movements. Possible route: `create_view(type: FORM)` on Stock Movements, then `create_form_question(formToken, …)` with `show_if_rules`; the form token is not exposed directly. Test in Phase 8 on the demo board; else manual |
| Dashboard in folder | n/a | **Yes** | — | `create_dashboard(name, workspace_id, board_ids, kind, board_folder_id)` |
| Widgets: chart, number, table (list view) with filter | n/a | **Yes, with a gap** | partly | `create_widget(kind: CHART / NUMBER / LISTVIEW, settings, filter)`. **The chart X axis can't group by a connect column** (only `color`, `group`, `multiple-person`, `board`, `name`, `date`), so "by Supplier" (§8 widgets 2, 4) can't be built as written |

### 0.3 Workspace and folder

- Workspace **15462830 "Project Manager"** exists (open, active).
- Folders in the workspace: only **21167685 "Inventory Management"** (Spot-nik). **No folder "Inventory & Procurement (Demo)" exists.**
- FYI: the workspace holds a **deleted** board "Suppliers" 18427408842 (+ "Subitems of Suppliers" 18427408857). It is not active, so there is no name clash. Idempotency checks must filter `state: active`.

### 0.4 Snapshot

`snapshots/pre-build.json` holds the id, title, type, settings and description of every column, plus the groups, of:
- Projects 18412939430: 13 columns, 33 items
- Subitems of Projects 18412939439: 10 columns, 122 subitems
- Production Calendar 18433554480: 10 columns, 5 groups, 55 items

The columns match CLAUDE.md §4. Projects `board_relation_mm6vdxt9` (link to Stock Updates) is present and untouched.

### 0.5 Real-item reads

Read only: Projects (name, Status, subitems with Project Type / Status / Delivery Date) and Production Calendar (name, group, Project, Status, Due Date). The proposed picks are in `data/picks-proposed.json`, pending Gate 1.

### 0.6 Spec arithmetic

All §9.7 expected values (On hand / Reserved / Available / Stock state for P01–P15, Material cost per request, PO subtotals and totals, supplier totals, project costs) were recomputed by hand from §9.3–9.6. **They reconcile.**

### 0.7 Repo

The layout from CLAUDE.md §7 lives in `ricco-inventory-demo/`, because the repo root holds unrelated work. `.env` is git-ignored. `scripts/monday_query.sh` refuses mutations; `scripts/phase0_preflight.sh` re-runs the read-only checks.

**Status: STOP at Gate 1.** Waiting for Omer: approve the picks, and decide on the connector / API route.
