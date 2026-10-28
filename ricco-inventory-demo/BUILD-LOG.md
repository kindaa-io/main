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

---

## Gate 1 — decisions (Omer, chat, 2026-10-28)

1. Route: **raw API through the environment's proxy-injected credential** (connector stays unavailable). → DEVIATIONS D-01 approved.
2. Test items: tests that need a project/unit link use the **real Projects board**; all other test boards go in a **separate test folder** with their own boards, so demo-board auto numbers stay clean. → DEVIATIONS D-03.
3. PO # auto number prefix `PO-000`: OK.
4. Dashboard charts: build whatever the API allows; report the rest.
5. Mirror-chain depth on Sam's boards (#2 → #8): flag if it fails.
6. Picks: "continue" with no changes → proposed picks recorded in `data/id-map.json` (reconfirm at Gate 2 before first use).

---

## Phase 1 — Folder, boards, groups · 2026-10-28

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:17:02Z | 1 | `create_folder` | 15462830 | Inventory & Procurement (Demo) | {"create_folder": {"id": "21780002", "name": "Inventory & Procurement (Demo)"}} |
| 2026-10-28T09:17:03Z | 1 | `create_board` | 21780002 | Suppliers | {"create_board": {"id": "18437453018", "name": "Suppliers"}} |
| 2026-10-28T09:17:12Z | 1 | `create_board` | 21780002 | Materials Catalogue | {"create_board": {"id": "18437453024", "name": "Materials Catalogue"}} |
| 2026-10-28T09:17:14Z | 1 | `create_board` | 21780002 | Material Requests | {"create_board": {"id": "18437453027", "name": "Material Requests"}} |
| 2026-10-28T09:17:15Z | 1 | `create_board` | 21780002 | Purchase Orders | {"create_board": {"id": "18437453028", "name": "Purchase Orders"}} |
| 2026-10-28T09:17:16Z | 1 | `create_board` | 21780002 | Stock Movements | {"create_board": {"id": "18437453030", "name": "Stock Movements"}} |
| 2026-10-28T09:17:17Z | 1 | `update_group(title)` | 18437453018 | Suppliers: rename default 'Group Title' | {"update_group": {"id": "topics", "title": "Suppliers"}} |
| 2026-10-28T09:17:19Z | 1 | `update_group(title)` | 18437453024 | Materials Catalogue: rename default 'Group Title' | {"update_group": {"id": "topics", "title": "🆕 New – needs review"}} |
| 2026-10-28T09:17:20Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Sheet Goods | {"create_group": {"id": "group_mm8jdb5g", "title": "Sheet Goods"}} |
| 2026-10-28T09:17:20Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Edgeband | {"create_group": {"id": "group_mm8jgwxy", "title": "Edgeband"}} |
| 2026-10-28T09:17:21Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Hinges | {"create_group": {"id": "group_mm8jdrvk", "title": "Hinges"}} |
| 2026-10-28T09:17:22Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Slides & Hardware | {"create_group": {"id": "group_mm8jvr8z", "title": "Slides & Hardware"}} |
| 2026-10-28T09:17:22Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Accessories | {"create_group": {"id": "group_mm8jt5n5", "title": "Accessories"}} |
| 2026-10-28T09:17:23Z | 1 | `create_group` | 18437453024 | Materials Catalogue: Finish / Paint | {"create_group": {"id": "group_mm8j3aar", "title": "Finish / Paint"}} |
| 2026-10-28T09:17:24Z | 1 | `update_group(title)` | 18437453027 | Material Requests: rename default 'Group Title' | {"update_group": {"id": "topics", "title": "Active requests"}} |
| 2026-10-28T09:17:26Z | 1 | `create_group` | 18437453027 | Material Requests: Closed & cancelled | {"create_group": {"id": "group_mm8jt77n", "title": "Closed & cancelled"}} |
| 2026-10-28T09:17:27Z | 1 | `update_group(title)` | 18437453028 | Purchase Orders: rename default 'Group Title' | {"update_group": {"id": "topics", "title": "Open POs"}} |
| 2026-10-28T09:17:28Z | 1 | `create_group` | 18437453028 | Purchase Orders: Closed & cancelled | {"create_group": {"id": "group_mm8jgqsc", "title": "Closed & cancelled"}} |
| 2026-10-28T09:17:29Z | 1 | `update_group(title)` | 18437453030 | Stock Movements: rename default 'Group Title' | {"update_group": {"id": "topics", "title": "Ledger"}} |

---

## Phase 2 — Plain columns on the main boards · 2026-10-28

Colour mapping (spec name → monday colour): grey=explosive, dark grey=american_gray, light blue=chili_blue, blue=bright_blue, purple=purple, orange=working_orange, dark orange=dark_orange, light green=bright_green, green=done_green, dark green=grass_green, yellow=egg_yolk, red=stuck_red. Catalogue `Category` colours are not in the spec; chosen for distinctness (dark_blue, sunset, teal, berry, lavender, peach). Custom column IDs (lowercase/underscore) are set so formulas read cleanly.

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:18:19Z | 2 | `create_column(text)` | 18437453018 | Suppliers: Contact person (custom id test) | {"create_column": {"id": "contact_person", "title": "Contact person", "type": "text"}} |
| 2026-10-28T09:19:21Z | 2 | `create_column(email)` | 18437453018 | Suppliers: Email | {"create_column": {"id": "email", "title": "Email", "type": "email"}} |
| 2026-10-28T09:19:22Z | 2 | `create_column(numbers)` | 18437453024 | Materials Catalogue: Last purchase price | {"create_column": {"id": "last_price", "title": "Last purchase price", "type": "numbers"}} |
| 2026-10-28T09:19:23Z | 2 | `create_status_column` | 18437453018 | Suppliers: Active | {"create_status_column": {"id": "active", "title": "Active", "type": "status"}} |
| 2026-10-28T09:19:24Z | 2 | `create_dropdown_column` | 18437453018 | Suppliers: Categories supplied | {"create_dropdown_column": {"id": "categories", "title": "Categories supplied", "type": "dropdown"}} |
| 2026-10-28T09:19:41Z | 2 | `create_column(phone)` | 18437453018 | Suppliers: Phone | {"create_column": {"id": "phone", "title": "Phone", "type": "phone"}} |
| 2026-10-28T09:19:42Z | 2 | `create_column(text)` | 18437453018 | Suppliers: Payment terms | {"create_column": {"id": "payment_terms", "title": "Payment terms", "type": "text"}} |
| 2026-10-28T09:19:44Z | 2 | `create_status_column` | 18437453024 | Materials Catalogue: Category | {"create_status_column": {"id": "category", "title": "Category", "type": "status"}} |
| 2026-10-28T09:19:45Z | 2 | `create_status_column` | 18437453024 | Materials Catalogue: Stock type | {"create_status_column": {"id": "stock_type", "title": "Stock type", "type": "status"}} |
| 2026-10-28T09:19:46Z | 2 | `create_dropdown_column` | 18437453024 | Materials Catalogue: UoM | {"create_dropdown_column": {"id": "uom", "title": "UoM", "type": "dropdown"}} |
| 2026-10-28T09:19:47Z | 2 | `create_column(numbers)` | 18437453024 | Materials Catalogue: Pack size | {"create_column": {"id": "pack_size", "title": "Pack size", "type": "numbers"}} |
| 2026-10-28T09:19:48Z | 2 | `create_column(text)` | 18437453024 | Materials Catalogue: Supplier Part # | {"create_column": {"id": "supplier_part", "title": "Supplier Part #", "type": "text"}} |
| 2026-10-28T09:19:49Z | 2 | `create_column(numbers)` | 18437453024 | Materials Catalogue: Minimum level | {"create_column": {"id": "minimum_level", "title": "Minimum level", "type": "numbers"}} |
| 2026-10-28T09:19:51Z | 2 | `create_column(long_text)` | 18437453024 | Materials Catalogue: Notes | {"create_column": {"id": "notes", "title": "Notes", "type": "long_text"}} |
| 2026-10-28T09:19:52Z | 2 | `create_column(auto_number)` | 18437453027 | Material Requests: Request # | {"create_column": {"id": "request_no", "title": "Request #", "type": "auto_number"}} |
| 2026-10-28T09:19:53Z | 2 | `create_status_column` | 18437453027 | Material Requests: Status | {"create_status_column": {"id": "status", "title": "Status", "type": "status"}} |
| 2026-10-28T09:19:54Z | 2 | `create_column(checkbox)` | 18437453027 | Material Requests: ✅ Materials complete | {"create_column": {"id": "materials_complete", "title": "✅ Materials complete", "type": "checkbox"}} |
| 2026-10-28T09:19:55Z | 2 | `create_column(people)` | 18437453027 | Material Requests: Programmer | {"create_column": {"id": "programmer", "title": "Programmer", "type": "people"}} |
| 2026-10-28T09:19:56Z | 2 | `create_column(people)` | 18437453027 | Material Requests: Purchaser | {"create_column": {"id": "purchaser", "title": "Purchaser", "type": "people"}} |
| 2026-10-28T09:19:57Z | 2 | `create_column(people)` | 18437453027 | Material Requests: Inventory owner | {"create_column": {"id": "inventory_owner", "title": "Inventory owner", "type": "people"}} |
| 2026-10-28T09:19:58Z | 2 | `create_column(date)` | 18437453027 | Material Requests: Needed by | {"create_column": {"id": "needed_by", "title": "Needed by", "type": "date"}} |
| 2026-10-28T09:19:59Z | 2 | `create_column(date)` | 18437453027 | Material Requests: Submitted on | {"create_column": {"id": "submitted_on", "title": "Submitted on", "type": "date"}} |
| 2026-10-28T09:20:00Z | 2 | `create_column(file)` | 18437453027 | Material Requests: Source file | {"create_column": {"id": "source_file", "title": "Source file", "type": "file"}} |
| 2026-10-28T09:20:01Z | 2 | `create_column(long_text)` | 18437453027 | Material Requests: Notes | {"create_column": {"id": "notes", "title": "Notes", "type": "long_text"}} |
| 2026-10-28T09:20:03Z | 2 | `create_column(auto_number)` | 18437453028 | Purchase Orders: PO # | {"create_column": {"id": "po_no", "title": "PO #", "type": "auto_number"}} |
| 2026-10-28T09:20:04Z | 2 | `create_status_column` | 18437453028 | Purchase Orders: Status | {"create_status_column": {"id": "status", "title": "Status", "type": "status"}} |
| 2026-10-28T09:20:05Z | 2 | `create_column(people)` | 18437453028 | Purchase Orders: Purchaser | {"create_column": {"id": "purchaser", "title": "Purchaser", "type": "people"}} |
| 2026-10-28T09:20:06Z | 2 | `create_column(people)` | 18437453028 | Purchase Orders: Approved by | {"create_column": {"id": "approved_by", "title": "Approved by", "type": "people"}} |
| 2026-10-28T09:20:07Z | 2 | `create_column(date)` | 18437453028 | Purchase Orders: Order date | {"create_column": {"id": "order_date", "title": "Order date", "type": "date"}} |
| 2026-10-28T09:20:08Z | 2 | `create_column(date)` | 18437453028 | Purchase Orders: Expected delivery | {"create_column": {"id": "expected_delivery", "title": "Expected delivery", "type": "date"}} |
| 2026-10-28T09:20:09Z | 2 | `create_column(date)` | 18437453028 | Purchase Orders: Sent date | {"create_column": {"id": "sent_date", "title": "Sent date", "type": "date"}} |
| 2026-10-28T09:20:10Z | 2 | `create_column(file)` | 18437453028 | Purchase Orders: PO document | {"create_column": {"id": "po_document", "title": "PO document", "type": "file"}} |
| 2026-10-28T09:20:11Z | 2 | `create_column(numbers)` | 18437453028 | Purchase Orders: Tax / Shipping | {"create_column": {"id": "tax_shipping", "title": "Tax / Shipping", "type": "numbers"}} |
| 2026-10-28T09:20:12Z | 2 | `create_column(long_text)` | 18437453028 | Purchase Orders: Notes to supplier | {"create_column": {"id": "notes_to_supplier", "title": "Notes to supplier", "type": "long_text"}} |
| 2026-10-28T09:20:14Z | 2 | `create_column(auto_number)` | 18437453030 | Stock Movements: Movement # | {"create_column": {"id": "movement_no", "title": "Movement #", "type": "auto_number"}} |
| 2026-10-28T09:20:15Z | 2 | `create_status_column` | 18437453030 | Stock Movements: Movement type | {"create_status_column": {"id": "movement_type", "title": "Movement type", "type": "status"}} |
| 2026-10-28T09:20:16Z | 2 | `create_column(numbers)` | 18437453030 | Stock Movements: Qty | {"create_column": {"id": "qty", "title": "Qty", "type": "numbers"}} |
| 2026-10-28T09:20:17Z | 2 | `create_column(numbers)` | 18437453030 | Stock Movements: Counted qty | {"create_column": {"id": "counted_qty", "title": "Counted qty", "type": "numbers"}} |
| 2026-10-28T09:20:18Z | 2 | `create_dropdown_column` | 18437453030 | Stock Movements: Reason | {"create_dropdown_column": {"id": "reason", "title": "Reason", "type": "dropdown"}} |
| 2026-10-28T09:20:19Z | 2 | `create_column(long_text)` | 18437453030 | Stock Movements: Note | {"create_column": {"id": "note", "title": "Note", "type": "long_text"}} |
| 2026-10-28T09:20:20Z | 2 | `create_status_column` | 18437453030 | Stock Movements: Status | {"create_status_column": {"id": "status", "title": "Status", "type": "status"}} |
| 2026-10-28T09:20:21Z | 2 | `create_column(text)` | 18437453030 | Stock Movements: Rejection reason | {"create_column": {"id": "rejection_reason", "title": "Rejection reason", "type": "text"}} |
| 2026-10-28T09:20:22Z | 2 | `create_column(numbers)` | 18437453030 | Stock Movements: Qty before | {"create_column": {"id": "qty_before", "title": "Qty before", "type": "numbers"}} |
| 2026-10-28T09:20:23Z | 2 | `create_column(numbers)` | 18437453030 | Stock Movements: Qty after | {"create_column": {"id": "qty_after", "title": "Qty after", "type": "numbers"}} |
| 2026-10-28T09:20:24Z | 2 | `create_column(date)` | 18437453030 | Stock Movements: Applied at | {"create_column": {"id": "applied_at", "title": "Applied at", "type": "date"}} |
| 2026-10-28T09:20:25Z | 2 | `create_column(creation_log)` | 18437453030 | Stock Movements: Created by | {"create_column": {"id": "created_by", "title": "Created by", "type": "creation_log"}} |

Phase 2 read-back: all label sets, label order, done flags, dropdown single-select limits, `$` units, auto-number settings (PO # prefix `PO-000`) and `Applied at` show-time verified. ✅

---

## Phase 3 — Subitem boards · 2026-10-28

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:20:46Z | 3 | `create_column(subtasks)` | 18437453027 | Material Requests: Subitems column | ERROR: invalid column type |
| 2026-10-28T09:21:20Z | 3-test | `create_folder` | 15462830 | ZZ-TEST- Inventory Demo Tests | {"create_folder": {"id": "21780014", "name": "ZZ-TEST- Inventory Demo Tests"}} |
| 2026-10-28T09:21:21Z | 3-test | `create_board` | 21780014 | ZZ-TEST- autonumber A | {"create_board": {"id": "18437453330", "name": "ZZ-TEST- autonumber A"}} |
| 2026-10-28T09:21:23Z | 3-test | `create_board` | 21780014 | ZZ-TEST- autonumber B | {"create_board": {"id": "18437453331", "name": "ZZ-TEST- autonumber B"}} |
| 2026-10-28T09:21:23Z | 3-test | `create_column(auto_number)` | 18437453330 | auto number test column | {"create_column": {"id": "no"}} |
| 2026-10-28T09:21:24Z | 3-test | `create_item` | 18437453330 | ZZ-TEST-X1 | {"create_item": {"id": "13404248866", "name": "ZZ-TEST-X1"}} |
| 2026-10-28T09:21:25Z | 3-test | `create_item` | 18437453330 | ZZ-TEST-X2 | {"create_item": {"id": "13404228939", "name": "ZZ-TEST-X2"}} |
| 2026-10-28T09:21:26Z | 3-test | `create_item` | 18437453330 | ZZ-TEST-X3 | {"create_item": {"id": "13404226374", "name": "ZZ-TEST-X3"}} |
| 2026-10-28T09:21:26Z | 3-test | `move_item_to_board` | 18437453330 | move ZZ-TEST-X1 to board B | ERROR: argument: group_id is required on field: move_item_to_board but missing |
| 2026-10-28T09:21:28Z | 3-test | `create_item` | 18437453330 | ZZ-TEST-X4 | {"create_item": {"id": "13404229437", "name": "ZZ-TEST-X4"}} |
| 2026-10-28T09:22:07Z | 3-test | `create_subitem` | 18437453330 | subitem under ZZ-TEST-X1 | {"create_subitem": {"id": "13404210145", "board": {"id": "18437453379", "name": "Subitems of ZZ-TEST- autonumber A"}}} |
| 2026-10-28T09:22:16Z | 3-test | `move_item_to_board` | 18437453330 | move ZZ-TEST-X1 (+subitem) to board B | {"move_item_to_board": {"id": "13404248866", "board": {"id": "18437453331"}, "subitems": [{"id": "13404210145", "board": {"id": "18437453385"}}]}} |
| 2026-10-28T09:22:40Z | 3 | `create_item` | 18437453027 | Material Requests: bootstrap parent | {"create_item": {"id": "13404211573"}} |
| 2026-10-28T09:22:48Z | 3 | `create_subitem` | 18437453027 | Material Requests: bootstrap subitem | {"create_subitem": {"id": "13404226858", "board": {"id": "18437453414", "name": "Subitems of Material Requests"}}} |
| 2026-10-28T09:22:49Z | 3 | `create_board` | 21780014 | ZZ-TEST- bootstrap parking | {"create_board": {"id": "18437453425", "name": "ZZ-TEST- bootstrap parking"}} |
| 2026-10-28T09:22:59Z | 3 | `move_item_to_board` | 18437453027 | Material Requests: park ZZ-TEST-bootstrap (+subitem) in test folder | {"move_item_to_board": {"id": "13404211573", "board": {"id": "18437453425"}}} |
| 2026-10-28T09:23:01Z | 3 | `create_item` | 18437453028 | Purchase Orders: bootstrap parent | {"create_item": {"id": "13404234652"}} |
| 2026-10-28T09:23:07Z | 3 | `create_subitem` | 18437453028 | Purchase Orders: bootstrap subitem | {"create_subitem": {"id": "13404249732", "board": {"id": "18437453449", "name": "Subitems of Purchase Orders"}}} |
| 2026-10-28T09:23:12Z | 3 | `move_item_to_board` | 18437453028 | Purchase Orders: park ZZ-TEST-bootstrap (+subitem) in test folder | {"move_item_to_board": {"id": "13404234652", "board": {"id": "18437453425"}}} |
| 2026-10-28T09:23:42Z | 3 | `update_status_column` | 18437453414 | Request lines: repurpose default Status -> Decision (labels per §4.4) | {"update_status_column": {"id": "status", "title": "Decision"}} |
| 2026-10-28T09:24:02Z | 3 | `change_column_title` | 18437453414 | Request lines: unused default Owner | {"change_column_title": {"id": "person", "title": "zz-unused – Owner"}} |
| 2026-10-28T09:24:03Z | 3 | `change_column_title` | 18437453414 | Request lines: unused default Date | {"change_column_title": {"id": "date0", "title": "zz-unused – Date"}} |
| 2026-10-28T09:24:04Z | 3 | `change_column_title` | 18437453449 | PO lines: repurpose default Date -> Received date | {"change_column_title": {"id": "date0", "title": "Received date"}} |
| 2026-10-28T09:24:06Z | 3 | `update_status_column` | 18437453449 | PO lines: repurpose default Status -> Line status | {"update_status_column": {"id": "status", "title": "Line status"}} |
| 2026-10-28T09:24:07Z | 3 | `change_column_title` | 18437453449 | PO lines: unused default Owner | {"change_column_title": {"id": "person", "title": "zz-unused – Owner"}} |
| 2026-10-28T09:24:08Z | 3 | `create_column(numbers)` | 18437453414 | Request lines: Qty requested | {"create_column": {"id": "qty_requested", "title": "Qty requested", "type": "numbers"}} |
| 2026-10-28T09:24:10Z | 3 | `create_column(numbers)` | 18437453414 | Request lines: Qty reserved | {"create_column": {"id": "qty_reserved", "title": "Qty reserved", "type": "numbers"}} |
| 2026-10-28T09:24:11Z | 3 | `create_column(numbers)` | 18437453414 | Request lines: Qty to order | {"create_column": {"id": "qty_to_order", "title": "Qty to order", "type": "numbers"}} |
| 2026-10-28T09:24:12Z | 3 | `create_column(numbers)` | 18437453414 | Request lines: Qty issued | {"create_column": {"id": "qty_issued", "title": "Qty issued", "type": "numbers"}} |
| 2026-10-28T09:24:13Z | 3 | `create_column(numbers)` | 18437453449 | PO lines: Qty ordered | {"create_column": {"id": "qty_ordered", "title": "Qty ordered", "type": "numbers"}} |
| 2026-10-28T09:24:14Z | 3 | `create_column(numbers)` | 18437453449 | PO lines: Unit price | {"create_column": {"id": "unit_price", "title": "Unit price", "type": "numbers"}} |
| 2026-10-28T09:24:15Z | 3 | `create_column(numbers)` | 18437453449 | PO lines: Qty received | {"create_column": {"id": "qty_received", "title": "Qty received", "type": "numbers"}} |

Phase 3 notes:
- `create_column(column_type: subtasks)` → API error *"This column type 'subtasks' is not supported yet in the API"*. Used the spec fallback: one `ZZ-TEST-bootstrap` parent + one subitem per board, then **moved the parent (with its subitem) to the test board `ZZ-TEST- bootstrap parking`** in the test folder so no test item stays on a demo board (D-03/D-04). The subitems column and subitem board stay on the demo board (verified on test boards first).
- Auto-number values are **not exposed by the API** (column value empty for every item), so Request # / PO # / Movement # can only be checked in the UI.
- Default subitem columns: Request lines `status` → **Decision**, PO lines `status` → **Line status**, PO lines `date0` → **Received date** (repurposed); `person` (Owner) on both and `date0` on Request lines → `zz-unused – …`. Read-back of labels and done flags ✅.

---

## Phase 4 — Connect columns · 2026-10-28

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:24:51Z | 4 | `create_column(board_relation)` | 18437453024 | Materials Catalogue: Default supplier | {"create_column": {"id": "default_supplier", "title": "Default supplier", "type": "board_relation"}} |
| 2026-10-28T09:24:53Z | 4 | `change_column_title` | 18437453018 | rename reflection of Materials Catalogue.default_supplier (was 'link to Materials Catalogue') | {"change_column_title": {"id": "board_relation_mm8jpkj0", "title": "Products"}} |
| 2026-10-28T09:25:08Z | 4 | `create_column(board_relation)` | 18437453028 | Purchase Orders: Supplier | {"create_column": {"id": "supplier", "title": "Supplier", "type": "board_relation"}} |
| 2026-10-28T09:25:10Z | 4 | `change_column_title` | 18437453018 | rename reflection of Purchase Orders.supplier (was 'link to Purchase Orders') | {"change_column_title": {"id": "board_relation_mm8jymv7", "title": "Purchase Orders"}} |
| 2026-10-28T09:25:13Z | 4 | `create_column(board_relation)` | 18437453027 | Material Requests: Purchase Orders | {"create_column": {"id": "purchase_orders", "title": "Purchase Orders", "type": "board_relation"}} |
| 2026-10-28T09:25:15Z | 4 | `change_column_title` | 18437453028 | rename reflection of Material Requests.purchase_orders (was 'link to Material Requests') | {"change_column_title": {"id": "board_relation_mm8jvqxq", "title": "Material Requests"}} |
| 2026-10-28T09:25:19Z | 4 | `create_column(board_relation)` | 18437453414 | Request lines: Product | {"create_column": {"id": "product", "title": "Product", "type": "board_relation"}} |
| 2026-10-28T09:25:21Z | 4 | `change_column_title` | 18437453024 | rename reflection of Request lines.product (was 'link to Subitems of Material Requests') | {"change_column_title": {"id": "board_relation_mm8jsje6", "title": "⚙️ Request lines"}} |
| 2026-10-28T09:25:24Z | 4 | `create_column(board_relation)` | 18437453414 | Request lines: PO line | {"create_column": {"id": "po_line", "title": "PO line", "type": "board_relation"}} |
| 2026-10-28T09:25:26Z | 4 | `change_column_title` | 18437453449 | rename reflection of Request lines.po_line (was 'link to Subitems of Material Requests') | {"change_column_title": {"id": "board_relation_mm8jf34y", "title": "Request line"}} |
| 2026-10-28T09:25:30Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: ⚙️ Applied in → Product | {"create_column": {"id": "applied_in", "title": "⚙️ Applied in → Product", "type": "board_relation"}} |
| 2026-10-28T09:25:32Z | 4 | `change_column_title` | 18437453024 | rename reflection of Stock Movements.applied_in (was 'link to Stock Movements') | {"change_column_title": {"id": "board_relation_mm8jprtb", "title": "⚙️ Applied in"}} |
| 2026-10-28T09:25:35Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: ⚙️ Applied out → Product | {"create_column": {"id": "applied_out", "title": "⚙️ Applied out → Product", "type": "board_relation"}} |
| 2026-10-28T09:25:37Z | 4 | `change_column_title` | 18437453024 | rename reflection of Stock Movements.applied_out (was 'link to Stock Movements') | {"change_column_title": {"id": "board_relation_mm8jqbay", "title": "⚙️ Applied out"}} |
| 2026-10-28T09:25:40Z | 4 | `create_column(board_relation)` | 18437453449 | PO lines: Product | {"create_column": {"id": "product", "title": "Product", "type": "board_relation"}} |
| 2026-10-28T09:25:43Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: Product | {"create_column": {"id": "product", "title": "Product", "type": "board_relation"}} |
| 2026-10-28T09:25:46Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: Request line | {"create_column": {"id": "request_line", "title": "Request line", "type": "board_relation"}} |
| 2026-10-28T09:25:49Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: PO line | {"create_column": {"id": "po_line", "title": "PO line", "type": "board_relation"}} |
| 2026-10-28T09:25:52Z | 4 | `create_column(board_relation)` | 18437453027 | Material Requests: Production Calendar job | {"create_column": {"id": "pc_job", "title": "Production Calendar job", "type": "board_relation"}} |
| 2026-10-28T09:25:56Z | 4 | `create_column(board_relation)` | 18437453449 | PO lines: Project | {"create_column": {"id": "project", "title": "Project", "type": "board_relation"}} |
| 2026-10-28T09:26:00Z | 4 | `create_column(board_relation)` | 18437453030 | Stock Movements: Unit / Project | {"create_column": {"id": "unit_project", "title": "Unit / Project", "type": "board_relation"}} |

Phase 4 result: 7 two-way connects (each produced exactly one reflection on the target, renamed to the spec title) and 7 one-way connects, including the multi-board one-way `Stock Movements.Unit / Project` → Projects + Units. **Two-way and multi-board connects work through the API**, so no MANUAL-STEPS M5 entries. Sam's boards re-read after **every** connect: **no change** vs `snapshots/pre-build.json` (`snapshots/post-phase-4.json`). Column IDs in `data/column-map.json`.

---

## Phase 5 — Aggregation test, mirrors and formulas · 2026-10-28

Aggregation test runs on `ZZ-TEST-` boards in folder `ZZ-TEST- Inventory Demo Tests` (D-03). It mirrors the real dependency chain: catalogue price → line mirror → line formula → parent mirror-sum → parent formula → supplier mirror-sum, and units mirror → project mirror-of-mirror (the §5 #2/#8 pattern), without touching Sam's boards.

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:27:11Z | 5-test | `create_board` | 21780014 | ZZ-TEST- agg catalogue | {"create_board": {"id": "18437453723", "name": "ZZ-TEST- agg catalogue"}} |
| 2026-10-28T09:27:12Z | 5-test | `create_board` | 21780014 | ZZ-TEST- agg requests | {"create_board": {"id": "18437453726", "name": "ZZ-TEST- agg requests"}} |
| 2026-10-28T09:27:14Z | 5-test | `create_board` | 21780014 | ZZ-TEST- agg supplier | {"create_board": {"id": "18437453727", "name": "ZZ-TEST- agg supplier"}} |
| 2026-10-28T09:27:15Z | 5-test | `create_board` | 21780014 | ZZ-TEST- agg movements | {"create_board": {"id": "18437453734", "name": "ZZ-TEST- agg movements"}} |
| 2026-10-28T09:27:16Z | 5-test | `create_board` | 21780014 | ZZ-TEST- agg projects | {"create_board": {"id": "18437453735", "name": "ZZ-TEST- agg projects"}} |
| 2026-10-28T09:27:17Z | 5-test | `create_column(numbers)` | 18437453723 | test col price | {"create_column": {"id": "price"}} |
| 2026-10-28T09:27:18Z | 5-test | `create_item` | 18437453723 | ZZ-TEST-product | {"create_item": {"id": "13404273572", "name": "ZZ-TEST-product"}} |
| 2026-10-28T09:27:20Z | 5-test | `create_column(numbers)` | 18437453734 | test col qty | {"create_column": {"id": "qty"}} |
| 2026-10-28T09:27:21Z | 5-test | `create_column(board_relation)` | 18437453734 | test col applied_in | {"create_column": {"id": "applied_in"}} |
| 2026-10-28T09:27:23Z | 5-test | `create_column(board_relation)` | 18437453734 | test col applied_out | {"create_column": {"id": "applied_out"}} |
| 2026-10-28T09:27:26Z | 5-test | `create_item` | 18437453734 | ZZ-TEST-in | {"create_item": {"id": "13404253555", "name": "ZZ-TEST-in"}} |
| 2026-10-28T09:27:29Z | 5-test | `create_item` | 18437453734 | ZZ-TEST-out | {"create_item": {"id": "13404273716", "name": "ZZ-TEST-out"}} |
| 2026-10-28T09:27:32Z | 5-test | `create_column(mirror)` | 18437453723 | test col in_total | {"create_column": {"id": "in_total"}} |
| 2026-10-28T09:27:33Z | 5-test | `create_column(mirror)` | 18437453723 | test col out_total | {"create_column": {"id": "out_total"}} |
| 2026-10-28T09:27:34Z | 5-test | `create_column(formula)` | 18437453723 | test col on_hand | {"create_column": {"id": "on_hand"}} |
| 2026-10-28T09:27:36Z | 5-test | `create_item` | 18437453726 | ZZ-TEST-request | {"create_item": {"id": "13404241126", "name": "ZZ-TEST-request"}} |
| 2026-10-28T09:27:42Z | 5-test | `create_subitem` | 18437453726 | ZZ-TEST-line1 | {"create_subitem": {"id": "13404245584", "board": {"id": "18437453790"}}} |
| 2026-10-28T09:27:43Z | 5-test | `create_column(numbers)` | 18437453790 | test col qty | {"create_column": {"id": "qty"}} |
| 2026-10-28T09:27:45Z | 5-test | `create_column(board_relation)` | 18437453790 | test col product | {"create_column": {"id": "product"}} |
| 2026-10-28T09:27:46Z | 5-test | `create_column(mirror)` | 18437453790 | test col est | {"create_column": {"id": "est"}} |
| 2026-10-28T09:27:47Z | 5-test | `create_column(formula)` | 18437453790 | test col lc | {"create_column": {"id": "lc"}} |
| 2026-10-28T09:27:49Z | 5-test | `create_subitem` | 18437453726 | ZZ-TEST-line2 | {"create_subitem": {"id": "13404262822", "board": {"id": "18437453790"}}} |
| 2026-10-28T09:27:51Z | 5-test | `change_multiple_column_values` | 18437453790 | test values | {"change_multiple_column_values": {"id": "13404245584"}} |
| 2026-10-28T09:27:53Z | 5-test | `change_multiple_column_values` | 18437453790 | test values | {"change_multiple_column_values": {"id": "13404262822"}} |
| 2026-10-28T09:27:54Z | 5-test | `create_column(mirror)` | 18437453726 | test col cost | {"create_column": {"id": "cost"}} |
| 2026-10-28T09:27:55Z | 5-test | `create_column(numbers)` | 18437453726 | test col tax | {"create_column": {"id": "tax"}} |
| 2026-10-28T09:27:56Z | 5-test | `change_multiple_column_values` | 18437453726 | test values | {"change_multiple_column_values": {"id": "13404241126"}} |
| 2026-10-28T09:27:57Z | 5-test | `create_column(formula)` | 18437453726 | test col total | {"create_column": {"id": "total"}} |
| 2026-10-28T09:27:59Z | 5-test | `create_column(board_relation)` | 18437453727 | test col conn | {"create_column": {"id": "conn"}} |
| 2026-10-28T09:28:01Z | 5-test | `create_item` | 18437453727 | ZZ-TEST-supplier | {"create_item": {"id": "13404245487", "name": "ZZ-TEST-supplier"}} |
| 2026-10-28T09:28:02Z | 5-test | `create_column(mirror)` | 18437453727 | test col ordered | {"create_column": {"id": "ordered"}} |
| 2026-10-28T09:28:04Z | 5-test | `create_item` | 18437453735 | ZZ-TEST-project | {"create_item": {"id": "13404262531", "name": "ZZ-TEST-project"}} |
| 2026-10-28T09:28:10Z | 5-test | `create_subitem` | 18437453735 | ZZ-TEST-unit | {"create_subitem": {"id": "13404245583", "board": {"id": "18437453844"}}} |
| 2026-10-28T09:28:11Z | 5-test | `create_column(board_relation)` | 18437453844 | test col mr | {"create_column": {"id": "mr"}} |
| 2026-10-28T09:28:13Z | 5-test | `change_multiple_column_values` | 18437453844 | test values | {"change_multiple_column_values": {"id": "13404245583"}} |
| 2026-10-28T09:28:14Z | 5-test | `create_column(mirror)` | 18437453844 | test col ucost | {"create_column": {"id": "ucost"}} |
| 2026-10-28T09:28:16Z | 5-test | `create_column(mirror)` | 18437453735 | test col units_cost | {"create_column": {"id": "units_cost"}} |
| 2026-10-28T09:30:18Z | 5-test | `create_column(formula)` | 18437453727 | test col probe | {"create_column": {"id": "probe"}} |
| 2026-10-28T09:30:19Z | 5-test | `create_column(formula)` | 18437453735 | test col probe | {"create_column": {"id": "probe"}} |
| 2026-10-28T09:30:20Z | 5-test | `create_column(formula)` | 18437453844 | test col probe | {"create_column": {"id": "probe"}} |
| 2026-10-28T09:30:21Z | 5-test | `create_column(formula)` | 18437453726 | test col probe | {"create_column": {"id": "probe"}} |
| 2026-10-28T09:30:56Z | 5-test | `create_column(formula)` | 18437453726 | test col plainf | {"create_column": {"id": "plainf"}} |
| 2026-10-28T09:30:57Z | 5-test | `create_column(mirror)` | 18437453727 | test col m_num | {"create_column": {"id": "m_num"}} |
| 2026-10-28T09:30:58Z | 5-test | `create_column(mirror)` | 18437453727 | test col m_plainf | {"create_column": {"id": "m_plainf"}} |
| 2026-10-28T09:30:59Z | 5-test | `create_column(formula)` | 18437453727 | test col p_num | {"create_column": {"id": "p_num"}} |
| 2026-10-28T09:31:00Z | 5-test | `create_column(formula)` | 18437453727 | test col p_plainf | {"create_column": {"id": "p_plainf"}} |
| 2026-10-28T09:31:01Z | 5-test | `create_column(mirror)` | 18437453844 | test col m_tax | {"create_column": {"id": "m_tax"}} |
| 2026-10-28T09:31:02Z | 5-test | `create_column(formula)` | 18437453844 | test col p_tax | {"create_column": {"id": "p_tax"}} |
| 2026-10-28T09:31:33Z | 5-test | `create_column(board_relation)` | 18437453727 | test col conn_single | {"create_column": {"id": "conn_single"}} |
| 2026-10-28T09:31:35Z | 5-test | `change_multiple_column_values` | 18437453727 | test values | {"change_multiple_column_values": {"id": "13404245487"}} |
| 2026-10-28T09:31:36Z | 5-test | `create_column(mirror)` | 18437453727 | test col s_tax | {"create_column": {"id": "s_tax"}} |
| 2026-10-28T09:31:37Z | 5-test | `create_column(mirror)` | 18437453727 | test col s_total | {"create_column": {"id": "s_total"}} |
| 2026-10-28T09:31:38Z | 5-test | `create_column(formula)` | 18437453727 | test col ps_tax | {"create_column": {"id": "ps_tax"}} |
| 2026-10-28T09:31:40Z | 5-test | `create_column(formula)` | 18437453727 | test col ps_total | {"create_column": {"id": "ps_total"}} |
| 2026-10-28T09:32:03Z | 5-test | `create_column(numbers)` | 18437453727 | test col nudge | {"create_column": {"id": "nudge"}} |
| 2026-10-28T09:32:04Z | 5-test | `create_column(numbers)` | 18437453844 | test col nudge | {"create_column": {"id": "nudge"}} |
| 2026-10-28T09:32:05Z | 5-test | `create_column(numbers)` | 18437453735 | test col nudge | {"create_column": {"id": "nudge"}} |
| 2026-10-28T09:32:11Z | 5-test | `change_multiple_column_values` | 18437453727 | test values | {"change_multiple_column_values": {"id": "13404245487"}} |
| 2026-10-28T09:32:13Z | 5-test | `change_multiple_column_values` | 18437453844 | test values | {"change_multiple_column_values": {"id": "13404245583"}} |
| 2026-10-28T09:32:13Z | 5-test | `change_multiple_column_values` | 18437453735 | test values | {"change_multiple_column_values": {"id": "13404262531"}} |
| 2026-10-28T09:32:46Z | 5-test | `create_column(formula)` | 18437453727 | test col f_plus | {"create_column": {"id": "f_plus"}} |
| 2026-10-28T09:32:47Z | 5-test | `create_column(formula)` | 18437453727 | test col f_if | {"create_column": {"id": "f_if"}} |
| 2026-10-28T09:32:48Z | 5-test | `create_column(formula)` | 18437453727 | test col f_total_plus | {"create_column": {"id": "f_total_plus"}} |
| 2026-10-28T09:32:50Z | 5-test | `create_column(formula)` | 18437453727 | test col f_ordered_plus | {"create_column": {"id": "f_ordered_plus"}} |
| 2026-10-28T09:32:53Z | 5-test | `change_multiple_column_values` | 18437453727 | test values | {"change_multiple_column_values": {"id": "13404245487"}} |
| 2026-10-28T09:32:57Z | 5-test | `change_multiple_column_values` | 18437453727 | test values | {"change_multiple_column_values": {"id": "13404245487"}} |
| 2026-10-28T09:33:37Z | 5-test | `create_column(board_relation)` | 18437453727 | test col conn_cat | {"create_column": {"id": "conn_cat"}} |
| 2026-10-28T09:33:38Z | 5-test | `create_column(mirror)` | 18437453727 | test col c_price | {"create_column": {"id": "c_price"}} |
| 2026-10-28T09:33:39Z | 5-test | `create_column(mirror)` | 18437453727 | test col c_onhand | {"create_column": {"id": "c_onhand"}} |
| 2026-10-28T09:33:40Z | 5-test | `create_column(formula)` | 18437453727 | test col pc_price | {"create_column": {"id": "pc_price"}} |
| 2026-10-28T09:33:42Z | 5-test | `create_column(formula)` | 18437453727 | test col pc_onhand | {"create_column": {"id": "pc_onhand"}} |
| 2026-10-28T09:33:44Z | 5-test | `change_multiple_column_values` | 18437453727 | test values | {"change_multiple_column_values": {"id": "13404245487"}} |
| 2026-10-28T09:34:17Z | 5-test | `create_column(board_relation)` | 18437453723 | test col conn_lines | {"create_column": {"id": "conn_lines"}} |
| 2026-10-28T09:34:18Z | 5-test | `create_column(mirror)` | 18437453723 | test col reserved | {"create_column": {"id": "reserved"}} |
| 2026-10-28T09:34:19Z | 5-test | `create_column(formula)` | 18437453723 | test col available | {"create_column": {"id": "available"}} |
| 2026-10-28T09:34:22Z | 5-test | `change_multiple_column_values` | 18437453723 | test values | {"change_multiple_column_values": {"id": "13404273572"}} |

### Phase 5.1 — Aggregation test result

Read through the API (`display_value`). Where a mirror's value isn't exposed, a probe formula `{mirror} + 0` on the test board reads it instead.

| Pattern (spec use) | Result |
|---|---|
| Formula over a mirror of numbers, one-way single connect (line `Line cost` over `Est. unit price`) | ✅ 30 / 20 |
| Mirror **sum of a formula via subitems** (request `Material cost` ← line `Line cost`; PO `Subtotal` ← `Line total`) | ✅ 50, read through a probe formula and through `Total = {cost}+{tax}` = 55 |
| Formula over mirrors via two-way reflections (Catalogue `On hand` = In total − Out total) | ✅ 5 |
| Formula over a mirror of a subitems board (Catalogue `Available` = On hand − Reserved) | ✅ 0 (= 5 − 3 − 2) |
| Mirror of a formula, then formula over it (source board without subitems) | ✅ 5 |
| Mirror of a **formula** from a board that **has subitems** (Supplier `Total ordered` ← PO `Total`) | ⚠️ **Not readable through the API**: mirror `display_value` is empty and a probe formula returns `null` |
| Mirror of a mirror (Units `Material cost` ← request `Material cost`; Projects `Units material cost` ← Units, §5 #2/#8) | ⚠️ **Not readable through the API** (empty / `null`) |
| Mirror of **numbers** from a board that has subitems | Mirror shows 5, but a probe formula over it is still `null` |

**Conclusion.** No test showed that summing a formula *fails*: every chain the API can read returns the right value. Where the API returns empty or `null`, the source board has subitems, and the same probe returns `null` even for a plain numbers mirror. So the API can't read those values back; that is not evidence the mirrors are wrong. Per §10 Phase 5.2 the source columns stay as specified (no switch to numbers). **The UI must confirm** the test boards show Supplier Total ordered = 55, unit Material cost = 50 and project Units material cost = 50. This affects §9.7 verification: Material cost per request is readable (formula probe on the Requests board itself works), but Supplier Total ordered and the Projects/Units values need a UI check.

Note: a mirror with `function: sum` still returns the item list in `display_value` (e.g. "3, 2"); formulas read it as the sum.

### Phase 5.3 — Mirrors and formulas on demo boards

| Timestamp (UTC) | Phase | Mutation | Target | Note | Result |
|---|---|---|---|---|---|
| 2026-10-28T09:35:25Z | 5 | `create_column(mirror)` | 18437453024 | Materials Catalogue: mirror supplier_email via Default supplier -> Suppliers.Email  | {"create_column": {"id": "supplier_email", "title": "Supplier email", "type": "mirror"}} |
| 2026-10-28T09:35:26Z | 5 | `create_column(mirror)` | 18437453024 | Materials Catalogue: mirror in_total via ⚙️ Applied in -> Stock Movements.Qty sum | {"create_column": {"id": "in_total", "title": "⚙️ In total", "type": "mirror"}} |
| 2026-10-28T09:35:27Z | 5 | `create_column(mirror)` | 18437453024 | Materials Catalogue: mirror out_total via ⚙️ Applied out -> Stock Movements.Qty sum | {"create_column": {"id": "out_total", "title": "⚙️ Out total", "type": "mirror"}} |
| 2026-10-28T09:35:28Z | 5 | `create_column(formula)` | 18437453024 | Materials Catalogue: formula on_hand = {in_total} - {out_total} | {"create_column": {"id": "on_hand", "title": "On hand", "type": "formula"}} |
| 2026-10-28T09:35:29Z | 5 | `create_column(mirror)` | 18437453024 | Materials Catalogue: mirror reserved via ⚙️ Request lines -> Request lines.Qty reserved sum | {"create_column": {"id": "reserved", "title": "Reserved", "type": "mirror"}} |
| 2026-10-28T09:35:31Z | 5 | `create_column(formula)` | 18437453024 | Materials Catalogue: formula available = {on_hand} - {reserved} | {"create_column": {"id": "available", "title": "Available", "type": "formula"}} |
| 2026-10-28T09:35:32Z | 5 | `create_column(formula)` | 18437453024 | Materials Catalogue: formula stock_state = IF({stock_type}="Order-to-project","—",IF({available}<=0,"Out",IF({available}<{minimum_level},"Low","In"))) | {"create_column": {"id": "stock_state", "title": "Stock state", "type": "formula"}} |
| 2026-10-28T09:35:33Z | 5 | `create_column(formula)` | 18437453024 | Materials Catalogue: formula stock_value = {on_hand} * {last_price} | {"create_column": {"id": "stock_value", "title": "Stock value", "type": "formula"}} |
| 2026-10-28T09:35:34Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror uom via Product -> Materials Catalogue.UoM  | {"create_column": {"id": "uom", "title": "UoM", "type": "mirror"}} |
| 2026-10-28T09:35:36Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror on_hand via Product -> Materials Catalogue.On hand  | {"create_column": {"id": "on_hand", "title": "On hand", "type": "mirror"}} |
| 2026-10-28T09:35:37Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror available via Product -> Materials Catalogue.Available  | {"create_column": {"id": "available", "title": "Available", "type": "mirror"}} |
| 2026-10-28T09:35:38Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror supplier via Product -> Materials Catalogue.Default supplier  | {"create_column": {"id": "supplier", "title": "Supplier", "type": "mirror"}} |
| 2026-10-28T09:35:39Z | 5 | `create_column(formula)` | 18437453414 | Request lines: formula qty_outstanding = IF(OR({status}="Issued",{status}="Cancelled"),0,MAX(0,{qty_requested}-{qty_reserved})) | {"create_column": {"id": "qty_outstanding", "title": "Qty outstanding", "type": "formula"}} |
| 2026-10-28T09:35:40Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror qty_ordered via PO line -> PO lines.Qty ordered sum | {"create_column": {"id": "qty_ordered", "title": "Qty ordered", "type": "mirror"}} |
| 2026-10-28T09:35:41Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror qty_received via PO line -> PO lines.Qty received sum | {"create_column": {"id": "qty_received", "title": "Qty received", "type": "mirror"}} |
| 2026-10-28T09:35:42Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror po_unit_price via PO line -> PO lines.Unit price sum | {"create_column": {"id": "po_unit_price", "title": "PO unit price", "type": "mirror"}} |
| 2026-10-28T09:35:43Z | 5 | `create_column(mirror)` | 18437453414 | Request lines: mirror est_unit_price via Product -> Materials Catalogue.Last purchase price sum | {"create_column": {"id": "est_unit_price", "title": "Est. unit price", "type": "mirror"}} |
| 2026-10-28T09:35:44Z | 5 | `create_column(formula)` | 18437453414 | Request lines: formula line_cost = IF({qty_issued}>0,{qty_issued},{qty_requested}) * IF({po_unit_price}>0,{po_unit_price},{est_unit_price}) | {"create_column": {"id": "line_cost", "title": "Line cost", "type": "formula"}} |
| 2026-10-28T09:35:46Z | 5 | `create_column(mirror)` | 18437453027 | Material Requests: mirror po_status via Purchase Orders -> Purchase Orders.Status status | {"create_column": {"id": "po_status", "title": "PO status", "type": "mirror"}} |
| 2026-10-28T09:35:47Z | 5 | `create_column(mirror)` | 18437453027 | Material Requests: mirror material_cost via Subitems -> Request lines.Line cost sum | {"create_column": {"id": "material_cost", "title": "Material cost", "type": "mirror"}} |
| 2026-10-28T09:35:48Z | 5 | `create_column(mirror)` | 18437453449 | PO lines: mirror uom via Product -> Materials Catalogue.UoM  | {"create_column": {"id": "uom", "title": "UoM", "type": "mirror"}} |
| 2026-10-28T09:35:49Z | 5 | `create_column(mirror)` | 18437453449 | PO lines: mirror pack_size via Product -> Materials Catalogue.Pack size sum | {"create_column": {"id": "pack_size", "title": "Pack size", "type": "mirror"}} |
| 2026-10-28T09:35:50Z | 5 | `create_column(mirror)` | 18437453449 | PO lines: mirror supplier_part via Product -> Materials Catalogue.Supplier Part #  | {"create_column": {"id": "supplier_part", "title": "Supplier Part #", "type": "mirror"}} |
| 2026-10-28T09:35:51Z | 5 | `create_column(formula)` | 18437453449 | PO lines: formula packs = IF({pack_size}>0,ROUND({qty_ordered}/{pack_size},2),"") | {"create_column": {"id": "packs", "title": "Packs", "type": "formula"}} |
| 2026-10-28T09:35:53Z | 5 | `create_column(formula)` | 18437453449 | PO lines: formula line_total = {qty_ordered} * {unit_price} | {"create_column": {"id": "line_total", "title": "Line total", "type": "formula"}} |
| 2026-10-28T09:35:54Z | 5 | `create_column(mirror)` | 18437453028 | Purchase Orders: mirror supplier_email via Supplier -> Suppliers.Email  | {"create_column": {"id": "supplier_email", "title": "Supplier email", "type": "mirror"}} |
| 2026-10-28T09:35:55Z | 5 | `create_column(mirror)` | 18437453028 | Purchase Orders: mirror contact via Supplier -> Suppliers.Contact person  | {"create_column": {"id": "contact", "title": "Contact", "type": "mirror"}} |
| 2026-10-28T09:35:56Z | 5 | `create_column(mirror)` | 18437453028 | Purchase Orders: mirror subtotal via Subitems -> PO lines.Line total sum | {"create_column": {"id": "subtotal", "title": "Subtotal", "type": "mirror"}} |
| 2026-10-28T09:35:58Z | 5 | `create_column(formula)` | 18437453028 | Purchase Orders: formula total = {subtotal} + {tax_shipping} | {"create_column": {"id": "total", "title": "Total", "type": "formula"}} |
| 2026-10-28T09:35:59Z | 5 | `create_column(formula)` | 18437453028 | Purchase Orders: formula delivery_state = IF(AND({status}<>"Draft",{status}<>"Received",{status}<>"Closed",{status}<>"Cancelled",NOT(ISBLANK({expected_delivery})),DAYS({expected_delivery},TODAY())<0),"Overdue","") | {"create_column": {"id": "delivery_state", "title": "Delivery state", "type": "formula"}} |
| 2026-10-28T09:36:00Z | 5 | `create_column(mirror)` | 18437453018 | Suppliers: mirror total_ordered via Purchase Orders -> Purchase Orders.Total sum | {"create_column": {"id": "total_ordered", "title": "Total ordered", "type": "mirror"}} |
| 2026-10-28T09:36:01Z | 5 | `create_column(mirror)` | 18437453018 | Suppliers: mirror open_pos via Purchase Orders -> Purchase Orders.Status status | {"create_column": {"id": "open_pos", "title": "Open POs", "type": "mirror"}} |
| 2026-10-28T09:36:03Z | 5 | `create_column(mirror)` | 18437453030 | Stock Movements: mirror uom via Product -> Materials Catalogue.UoM  | {"create_column": {"id": "uom", "title": "UoM", "type": "mirror"}} |

Phase 5.3 result: 33 mirrors/formulas created exactly as §4 (read back: relation column, source column, `sum` / `allStatuses`, formula text). Every §4 column now exists on every demo board except the Phase 6 connects (`Material Requests.Unit / Project`, `Purchase Orders.Projects`). Sam's boards vs snapshot: **no change**.

Test folder 21780014 contents (all `ZZ-TEST-`, left in place for Omer's cleanup):
- ZZ-TEST- autonumber A — 18437453330
- ZZ-TEST- autonumber B — 18437453331
- ZZ-TEST- bootstrap parking — 18437453425
- ZZ-TEST- agg catalogue — 18437453723
- ZZ-TEST- agg requests — 18437453726
- ZZ-TEST- agg supplier — 18437453727
- ZZ-TEST- agg movements — 18437453734
- ZZ-TEST- agg projects — 18437453735
- ZZ-TEST- agg request lines (subitems) — 18437453790
- ZZ-TEST- agg units (subitems) — 18437453844

**Status: STOP at Gate 2.** Waiting for Omer's "go" on the 9 columns on Projects/Units.
| 2026-10-28T10:10:45Z | 5-verify | `create_item` | 18437453018 | ZZ-TEST-Supplier | {"create_item": {"id": "13404488723"}} |
| 2026-10-28T10:10:48Z | 5-verify | `create_item` | 18437453024 | ZZ-TEST-Product | {"create_item": {"id": "13404488615"}} |
| 2026-10-28T10:10:51Z | 5-verify | `create_item` | 18437453030 | ZZ-TEST-Opening in | {"create_item": {"id": "13404488795"}} |
| 2026-10-28T10:10:54Z | 5-verify | `create_item` | 18437453030 | ZZ-TEST-Manual out | {"create_item": {"id": "13404494207"}} |
| 2026-10-28T10:10:56Z | 5-verify | `create_item` | 18437453028 | ZZ-TEST-PO | {"create_item": {"id": "13404452029"}} |
| 2026-10-28T10:10:59Z | 5-verify | `create_subitem` | 18437453028 | ZZ-TEST-PO line | {"create_subitem": {"id": "13404493210"}} |
| 2026-10-28T10:11:01Z | 5-verify | `create_item` | 18437453027 | ZZ-TEST-Request | {"create_item": {"id": "13404448702"}} |
| 2026-10-28T10:11:05Z | 5-verify | `create_subitem` | 18437453027 | ZZ-TEST-Line A | {"create_subitem": {"id": "13404451993"}} |
| 2026-10-28T10:11:08Z | 5-verify | `create_subitem` | 18437453027 | ZZ-TEST-Line B | {"create_subitem": {"id": "13404462767"}} |


---

## Omer's feedback after Gate 2 report (chat, 2026-10-28)

- Test boards were not wanted: **test items go only on the new structure boards.** The `ZZ-TEST-` folder/boards stay in place (no deletes, rule 5) for Omer's cleanup; no more are created. DEVIATIONS D-03 superseded.
- Omer changed the demo boards in the UI. Read back by API:
  - Material Requests: `Production Calendar job` (`pc_job`) **deleted**; new **`Project \ Unit`** `board_relation_mm8j4n2b`: two-way, single, → Units 18412939439 + Projects 18412939430. Reflections: Projects `board_relation_mm8jqhv4` "link to Material Requests", Units `board_relation_mm8j9wgg` "link to Material Requests".
  - PO lines: `Project` (one-way) and `zz-unused – Owner` **deleted**; new **`Project \ Unit`** `board_relation_mm8jy91z`: two-way → Units + Projects (multi not set). Reflections: Projects `board_relation_mm8jbv88`, Units `board_relation_mm8jxknn` "link to Subitems of Purchase Orders".
  - Subitems columns added on Suppliers (`subtasks_mm8jb027` → 18437456750), Materials Catalogue (`subtasks_mm8jprg3` → 18437456753), Stock Movements (`subtasks_mm8j76fe` → 18437457028). Empty, default columns only. **Asked Omer whether intended.**
  - Units also has a new **`link to Stock Updates`** `board_relation_mm8j89fg` (two-way → Spot-nik Stock Updates 18427258261). Not created by this build; **reported to Omer**, untouched.
- `scripts/spec_columns.py` and `data/column-map.json` updated to the new structure.

### ZZ-TEST- verification data on the demo boards

Items (left in place, listed for cleanup):
- ZZ-TEST-bootstrap — `13404211573` (ZZ-TEST- bootstrap parking)
- ZZ-TEST-bootstrap — `13404234652` (ZZ-TEST- bootstrap parking)
- ZZ-TEST-Supplier — `13404488723` (Suppliers)
- ZZ-TEST-Product — `13404488615` (Materials Catalogue)
- ZZ-TEST-Opening in — `13404488795` (Stock Movements)
- ZZ-TEST-Manual out — `13404494207` (Stock Movements)
- ZZ-TEST-PO — `13404452029` (Purchase Orders)
- ZZ-TEST-PO line — `13404493210` (PO lines)
- ZZ-TEST-Request — `13404448702` (Material Requests)
- ZZ-TEST-Line A — `13404451993` (Request lines)
- ZZ-TEST-Line B — `13404462767` (Request lines)

Result (`data/zz-test-verification.json`): **all 13 formulas compute the expected value through the API.** Mirrors: 18 read correctly. Three more aren't readable directly but are proven by the formula on top of them: `Reserved` (API shows "4, 2"; `Available` = 11 proves 6), `PO Subtotal` (empty; `Total` = 78 proves 72), and `On hand` from the in/out mirrors. **Not readable by the API, UI check needed:** request line `On hand` (17) and `Available` (11), request `Material cost` (74), supplier `Total ordered` (78). All four are mirrors of a formula column.
