# MANUAL-STEPS — things the API can't do

Each entry: what, where, exact settings. **Status** is `Draft` (expected from the Phase 0 capability check, not yet confirmed), `Confirmed` (tried in the build and failed) or `Done` (completed by hand).

---

## M1 — Kanban view "By status" on Material Requests · Draft
- **Why manual:** the API's `ViewKind` has no kanban (TABLE, FORM, DASHBOARD, APP only).
- **Where:** board *Material Requests* (folder Inventory & Procurement (Demo)).
- **Steps:** Add view → Kanban → name `By status` → Kanban column: **Status** → show the subitems setting as default.
- **Settings:** card columns: Unit / Project, Needed by, Programmer, Material cost. Hide ⚙️ columns.

## M2 — Kanban view "By status" on Purchase Orders · Draft
- **Why manual:** as M1.
- **Where:** board *Purchase Orders*.
- **Steps:** Add view → Kanban → name `By status` → Kanban column: **Status**.
- **Settings:** card columns: Supplier, Projects, Expected delivery, Total, Delivery state.

## M3 — WorkForm "Manual stock update" on Stock Movements · Draft (try the API first in Phase 8)
- **Why possibly manual:** `create_form` always creates a new board, so it can't target Stock Movements. The `create_view(type: FORM)` + `create_form_question` route is unproven.
- **Where:** board *Stock Movements* → Add view → Form → name `Manual stock update`.
- **Description:** "Manual stock changes only. To take material for a job, use a material request. A manual out or a count that would cut into stock reserved for projects will be rejected."
- **Questions:**

| Question | Column | Required | Condition |
|---|---|---|---|
| Product | Product | yes | — |
| Movement type | Movement type | yes | Show only Manual in, Manual out, Stock count (hide Opening, Receipt, Issue to project). If label hiding isn't possible, rely on the description |
| Quantity | Qty | yes | Movement type = Manual in OR Manual out |
| Counted quantity | Counted qty | yes | Movement type = Stock count |
| Reason | Reason | yes | Movement type = Manual in OR Manual out |
| Note | Note | no | — |

- **Hidden:** Unit / Project (never shown). Status defaults to **Pending** (set the column default or a hidden question with default Pending).

## M4 — Dashboard widgets "by Supplier" · Draft (awaiting Omer's decision)
- **Why manual:** chart widgets created by the API can group the X axis only by status colour, group, person, board, name or date, not by a connect column (PO `Supplier`).
- **Where:** dashboard *Procurement Overview (Demo)*.
- **Widget 2, Open POs by supplier:** Chart (bar), source Purchase Orders, X axis = Supplier, Y = count of items, filter Status is not Received / Closed / Cancelled.
- **Widget 4, Spend by supplier:** Chart (bar), source Purchase Orders, X axis = Supplier, Y = sum of Total.
- Omer (Gate 1): try to build the charts through the API first (Phase 8). Also found: `create_widget(filter)` *"works only in board views"*, so dashboard widget filters (widgets 2, 3, 6) may need setting by hand too.

## M5 — Switch connect to two-way · Not needed
Phase 4 confirmed the API creates two-way and multi-board connects. Kept for Phase 6 in case Sam's boards behave differently. Used only if Phase 4 or 6 finds the API can't create a connect as two-way (spec §10 Phase 4.5). One entry per affected column: board, column, "Create a reflection column on the connected board" ON, expected reflection title.
