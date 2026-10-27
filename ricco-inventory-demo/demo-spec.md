# Demo Spec — Ricco Cabinetry · Native Inventory & Procurement

*Version 1.0 · 27 Oct 2026 · Owner: Omer (Kindaa) · Builder: Claude Code*
*Sources, in priority order: decisions in the 27 Oct spec session (this file) → `ricco-native-inventory-handover.md` → discovery call transcript (Yair ↔ Sam) → workspace export (workspace 15462830) → blueprint rev 1 (flows/risks only).*

Read `CLAUDE.md` before acting on anything in this file. Safety rules there override everything here.

---

## 0. What this demo is

A **native monday.com structure plus sample data** showing Sam's whole inventory and procurement flow. **No automations, no integrations, no Make scenarios, no webhooks** are active in the demo. Every flow is shown by sample records sitting at each stage, and a walkthrough script (§12) maps each step to the record that shows it.

All full-build logic is specified so the structure is ready for it (§11 and `AUTOMATIONS.md`), but none of it is built now.

### Decisions locked in the spec session

| # | Decision |
|---|---|
| D1 | Location: a **folder inside Sam's existing workspace "Project Manager" (15462830)**, account 34799434. |
| D2 | Spot-nik is out. Nothing in this build reads from, writes to, or depends on the Spot-nik boards. |
| D3 | The stock engine is **out of the demo**. Its runtime (Make, code or hybrid) is decided before the full build. The data model is built ready for it. |
| D4 | **One serialized stock process** owns every stock-changing operation. In Make that means a single scenario with sequential processing and a router. It writes only engine fields. Balances are **mirrors and formulas**, not engine-written numbers. |
| D5 | **On hand** = mirror sum of Applied *in* movements − mirror sum of Applied *out* movements. Movements count only once linked through the `⚙️ Applied in` or `⚙️ Applied out` connect columns, which the process sets on apply. Pending and Rejected movements are never linked. |
| D6 | **Reserved** = mirror sum of `Qty reserved` on request lines. **Available** = On hand − Reserved. **Available can never go negative**: any manual movement or stock count that would push it below zero is rejected. |
| D7 | Requests are created by a **Fillout form** (request plus lines). Programmers always pick from the catalogue and create a missing product from the connect column. **There are no free-text lines.** **✅ Materials complete** is a required confirmation on the form, a safeguard only: **no automation reads it.** Sending the form submits the request. Materials forgotten after submission go on a new request. |
| D8 | On submit, every line is compared with its product's current **Available**: all available → reserve it all (**From Stock**, Qty to order 0); part available → reserve that part and write the rest to **Qty to order** (**Partial**); none available → the whole quantity goes to **Qty to order** (**To Order**). Stock received against a project line is **reserved for that line on receipt**; surplus goes to free stock. |
| D9 | Requests link to a **Unit (Project subitem) or a whole Project** through one **two-way** connect column. Purchase Orders link to Projects two-way. |
| D10 | Manual movements (**Manual in / Manual out / Stock count**) never carry a project. Stock count takes the **counted quantity**; the process derives the difference. |
| D11 | All people columns use **Kindaa Support (103186497)** only. It is the only Kindaa user in the account. Never assign Sam or his staff. |
| D12 | Demo request and PO names start with **"DEMO –"**. Test items start with **"ZZ-TEST-"**. Nothing is deleted; cleanup is manual by Omer. |
| D13 | A **mock PO PDF**, watermarked "SAMPLE LAYOUT – PENDING RICCO TEMPLATE", is attached to one Sent PO. |
| D14 | A native **WorkForm "Manual stock update"** on Stock Movements is part of the demo. It is a form, not an automation. |

---

## 1. Scope

### In the demo
1. Folder **"Inventory & Procurement (Demo)"** with 5 boards: Suppliers, Materials Catalogue, Material Requests (+ request-line subitems), Purchase Orders (+ PO-line subitems), Stock Movements.
2. Every column, status label, connect, mirror and formula in §4.
3. The **9 approved columns** on Sam's Projects and Units boards (§5), created only after the STOP gate.
4. Groups and views (§6), the WorkForm (§7) and one dashboard (§8).
5. Sample data (§9) that reconciles exactly to the expected values in §9.7.
6. Mock PO PDF on PO-0003 (§10).
7. Walkthrough script (§12).

### Full build only (specified, not built)
- The stock process and nightly integrity check.
- Every automation in `AUTOMATIONS.md`: Fillout, auto-reserve, PO builder, receipt, readiness, issue, cancel/hold, low-stock alerts, notifications, edit guards.
- PO PDF generation from Sam's template, and emailing the supplier.
- Importing the material list from the programming software.
- A per-supplier quoted price list, and bin/rack locations.
- Loading the real catalogue and doing an opening physical count.
- Column locking with column permissions.
- Retiring the Spot-nik boards and removing `link to Stock Updates` (`board_relation_mm6vdxt9`) from Projects.
- Roles, seats and permissions for Sam's team.

### Not in this spec at all
- The 4 OptiSign screens on Production Calendar. They're a separate task and must not be built from this spec.

---

## 2. Conventions

| Topic | Rule |
|---|---|
| Folder | `Inventory & Procurement (Demo)` in workspace 15462830 |
| Board names | `Suppliers`, `Materials Catalogue`, `Material Requests`, `Purchase Orders`, `Stock Movements`. Don't use the name "Products"; the Spot-nik board 18427258253 already has it. |
| Currency / units | USD; imperial units (sheets 4×8, ft, gallons) |
| Dates | Given as offsets from the build day **T** (e.g. `T-14`). Convert at load time so "Overdue" logic holds whenever the demo is built. |
| People | Kindaa Support (103186497) in every people column |
| Item names | Requests: `DEMO – <Unit or Project name> – MR #<n>`. POs: `DEMO – PO-000<n> – <Supplier>`. Movements: `<Movement type> – <Product name>`. Lines: the product name. |
| Placeholders | `{{PRJ_A}}` etc. are real Sam items chosen in Phase 0 and approved by Omer (§9.1) |
| Formulas | Written below with `{Column Title}`. Replace each with the real `{column_id}` when creating the column. |
| `⚙️` prefix | Marks a technical column (reflections, helper mirrors, process-owned links). Hidden from the main views. |

---

## 3. Structure overview

```
Suppliers ◄──two-way── Materials Catalogue (Default supplier)
Suppliers ◄──two-way── Purchase Orders (Supplier)

Material Requests ──two-way──► Projects / Units (Unit / Project)            [Sam's boards]
Material Requests ──one-way──► Production Calendar (service job)            [Sam's board]
Material Requests ◄─two-way──► Purchase Orders (Purchase Orders)
  └ Request lines ──two-way──► Materials Catalogue (Product)  → feeds Reserved
  └ Request lines ◄─two-way──► PO lines (PO line)

Purchase Orders ──two-way──► Projects (Projects)                            [Sam's board]
  └ PO lines ──one-way──► Materials Catalogue (Product), Projects (Project)

Stock Movements ──one-way──► Materials Catalogue (Product)
Stock Movements ──two-way──► Materials Catalogue (⚙️ Applied in / ⚙️ Applied out) → feeds On hand
Stock Movements ──one-way──► Projects / Units, Request lines, PO lines
```

**The one rule:** nothing changes stock or reservations except the serialized stock process (full build). Users write movements and request lines; the process writes engine fields. In the demo all of these values are static sample data.

---

## 4. Boards and columns

"Written by" means who writes the value in the **full build**:
- **User**: entered by hand
- **Form**: filled by Fillout or the WorkForm
- **Process**: written by the stock process or a flow automation
- **Mirror / Formula**: computed by monday

### 4.1 Suppliers

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | | User | Supplier name |
| Contact person | text | | User | |
| Email | email | | User | |
| Phone | phone | | User | |
| Payment terms | text | | User | e.g. Net 30 |
| Categories supplied | dropdown (multi) | Sheet Goods, Edgeband, Hinges, Slides & Hardware, Accessories, Finish / Paint | User | |
| Active | status | Active (green), Inactive (grey) | User | |
| Products | reflection | from Catalogue `Default supplier` | — | Created by the two-way connect |
| Purchase Orders | reflection | from PO `Supplier` | — | Created by the two-way connect |
| Total ordered | mirror | via `Purchase Orders` → PO `Total`, **sum** | Mirror | Depends on the formula-aggregation test (§10, Phase 5) |
| Open POs | mirror | via `Purchase Orders` → PO `Status`, all statuses | Mirror | |

Groups: `Suppliers`.

### 4.2 Materials Catalogue

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | Convention: `<Material> <thickness/size> <finish>` | User | One product per size or variant |
| Category | status | Sheet Goods, Edgeband, Hinges, Slides & Hardware, Accessories, Finish / Paint | User | Purchaser sets it on new products |
| Stock type | status | Stocked (green), Order-to-project (blue) | User | Default for new products: Order-to-project |
| UoM | dropdown (single) | sheet, ft, each, pair, gallon, box | User | Stock unit; all quantities are in this unit |
| Pack size | numbers | | User | Supplier pack, in stock units (e.g. 300 for a roll) |
| Default supplier | connect → Suppliers | single, **two-way** | User | Required before a PO line can be built |
| Supplier email | mirror | via `Default supplier` → `Email` | Mirror | |
| Supplier Part # | text | | User | |
| Minimum level | numbers | | User | Low-stock threshold, compared against Available |
| Last purchase price | numbers | unit $ (left) | Process | Price per stock unit; updated on receipt. **Not a mirror**: mirrors can't take the latest value by date |
| ⚙️ Applied in | reflection | from Movements `⚙️ Applied in → Product` | — | |
| ⚙️ Applied out | reflection | from Movements `⚙️ Applied out → Product` | — | |
| ⚙️ In total | mirror | via `⚙️ Applied in` → Movements `Qty`, **sum** | Mirror | |
| ⚙️ Out total | mirror | via `⚙️ Applied out` → Movements `Qty`, **sum** | Mirror | |
| On hand | formula | `{⚙️ In total} - {⚙️ Out total}` | Formula | Same mirror-in-formula pattern as Transactions `formula_mkkreses` in Sam's account |
| ⚙️ Request lines | reflection | from request lines `Product` | — | |
| Reserved | mirror | via `⚙️ Request lines` → line `Qty reserved`, **sum** | Mirror | Lines that are issued or cancelled hold Qty reserved = 0 |
| Available | formula | `{On hand} - {Reserved}` | Formula | Never negative (guarded by the process) |
| Stock state | formula | `IF({Stock type}="Order-to-project","—",IF({Available}<=0,"Out",IF({Available}<{Minimum level},"Low","In")))` | Formula | Replaces a process-written status |
| Stock value | formula | `{On hand} * {Last purchase price}` | Formula | Indicative only; QuickBooks holds the books |
| Notes | long text | | User | |

Groups, in this order: **🆕 New – needs review** (must be the **top** group, because products created from a connect column land there), Sheet Goods, Edgeband, Hinges, Slides & Hardware, Accessories, Finish / Paint.

### 4.3 Material Requests (item)

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | `DEMO – <Unit/Project> – MR #<n>` | Form | |
| Request # | auto number | | — | |
| Status | status | Submitted (light blue), In Review (blue), Ordering (purple), Waiting for Delivery (orange), Ready for Production (light green), Issue Materials (dark orange), Issuing (yellow), Closed (green, done), On Hold (red), Cancelled (dark grey) | Process / User | |
| ✅ Materials complete | checkbox | | Form | Required confirmation on the form (safeguard). **No automation reads or depends on this column.** |
| Unit / Project | connect → **Projects (18412939430) + Subitems of Projects (18412939439)** | single, **two-way** | Form | Same pattern as Task Manager `board_relation_mm3att2b` |
| Production Calendar job | connect → Production Calendar (18433554480) | single, **one-way** | User | Service jobs only. Adds no column to Sam's board |
| Programmer | people | | Form | Kindaa Support in the demo |
| Purchaser | people | | Process | Kindaa Support |
| Inventory owner | people | | Process | Kindaa Support |
| Needed by | date | | Form | |
| Submitted on | date | | Process | |
| Source file | file | | Form | Material list exported from the programming software |
| Purchase Orders | connect → Purchase Orders | multi, **two-way** | Process | |
| PO status | mirror | via `Purchase Orders` → PO `Status`, all statuses | Mirror | |
| Material cost | mirror | via subitems → line `Line cost`, **sum** | Mirror | Depends on the aggregation test |
| Notes | long text | | User | |

Groups: **Active requests**, **Closed & cancelled**.

### 4.4 Request lines (subitems of Material Requests)

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | Product name | Form | |
| Product | connect → Materials Catalogue | single, **two-way** | Form | Missing products are created from this column |
| Qty requested | numbers | | Form | In stock units |
| UoM | mirror | via `Product` → `UoM` | Mirror | |
| On hand | mirror | via `Product` → `On hand` | Mirror | |
| Available | mirror | via `Product` → `Available` | Mirror | |
| Supplier | mirror | via `Product` → `Default supplier` | Mirror | |
| Decision | status | Pending (grey), From Stock (green), Partial (yellow), To Order (orange), Ordered (purple), Received (blue), Issued (dark green, done), Cancelled (dark grey) | Process | |
| Qty reserved | numbers | | Process | The reservation record; set to 0 on issue or cancel |
| Qty to order | numbers | | Process | Written at submit: Qty requested − Qty reserved. What the PO builder orders. Updated only if the purchaser releases a reservation |
| Qty outstanding | formula | `IF(OR({Decision}="Issued",{Decision}="Cancelled"),0,MAX(0,{Qty requested}-{Qty reserved}))` | Formula | Still not covered by stock or receipts; drives readiness |
| PO line | connect → PO lines | single, **two-way** | Process | |
| Qty ordered | mirror | via `PO line` → `Qty ordered` | Mirror | |
| Qty received | mirror | via `PO line` → `Qty received` | Mirror | |
| PO unit price | mirror | via `PO line` → `Unit price` | Mirror | |
| Est. unit price | mirror | via `Product` → `Last purchase price` | Mirror | |
| Qty issued | numbers | | User | Defaults to Qty requested at Issue Materials |
| Line cost | formula | `IF({Qty issued}>0,{Qty issued},{Qty requested}) * IF({PO unit price}>0,{PO unit price},{Est. unit price})` | Formula | |

Default subitem columns (Owner, Status, Date): see `CLAUDE.md` → "Default columns".

### 4.5 Purchase Orders (item)

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | `DEMO – PO-000<n> – <Supplier>` | Process | |
| PO # | auto number | | — | Displayed as PO-000n; format TBD with Sam |
| Status | status | Draft (grey), Approved (blue), Sent (purple), Partially Received (orange), Received (green), Closed (dark green, done), Cancelled (dark grey) | Process / User | |
| Supplier | connect → Suppliers | single, **two-way** | Process | |
| Supplier email | mirror | via `Supplier` → `Email` | Mirror | |
| Contact | mirror | via `Supplier` → `Contact person` | Mirror | |
| Projects | connect → **Projects (18412939430)** | multi, **two-way** | Process | |
| Material Requests | reflection | from Requests `Purchase Orders` | — | |
| Purchaser | people | | Process | Kindaa Support |
| Approved by | people | | User | Kindaa Support (approver TBD with Sam) |
| Order date | date | | User | |
| Expected delivery | date | | User | |
| Sent date | date | | Process | |
| PO document | file | | Process | Mock PDF on PO-0003 only |
| Subtotal | mirror | via subitems → `Line total`, **sum** | Mirror | Depends on the aggregation test |
| Tax / Shipping | numbers | unit $ | User | |
| Total | formula | `{Subtotal} + {Tax / Shipping}` | Formula | |
| Delivery state | formula | `IF(AND({Status}<>"Draft",{Status}<>"Received",{Status}<>"Closed",{Status}<>"Cancelled",NOT(ISBLANK({Expected delivery})),DAYS({Expected delivery},TODAY())<0),"Overdue","")` | Formula | Same pattern as Task Manager `⚙️Indication` |
| Notes to supplier | long text | | User | |

Groups: **Open POs**, **Closed & cancelled**.

### 4.6 PO lines (subitems of Purchase Orders)

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | Product name | Process | |
| Product | connect → Materials Catalogue | single, **one-way** | Process | |
| UoM | mirror | via `Product` → `UoM` | Mirror | |
| Pack size | mirror | via `Product` → `Pack size` | Mirror | |
| Supplier Part # | mirror | via `Product` → `Supplier Part #` | Mirror | |
| Qty ordered | numbers | | Process / User | **In stock units.** The purchaser rounds up to full packs |
| Packs | formula | `IF({Pack size}>0,ROUND({Qty ordered}/{Pack size},2),"")` | Formula | What the supplier sees |
| Unit price | numbers | unit $ | Process / User | Per stock unit |
| Line total | formula | `{Qty ordered} * {Unit price}` | Formula | |
| Qty received | numbers | | User | Cumulative, in stock units |
| Received date | date | | User | |
| Project | connect → Projects (18412939430) | single, **one-way** | Process | **Blank = stock replenishment** |
| Request line | reflection | from request lines `PO line` | — | |
| Line status | status | Open (grey), Partially Received (orange), Received (green, done), Cancelled (dark grey) | Process | |

### 4.7 Stock Movements

| Column | Type | Settings / labels | Written by | Notes |
|---|---|---|---|---|
| Name | name | `<Movement type> – <Product>` | Form / Process | |
| Movement # | auto number | | — | |
| Product | connect → Materials Catalogue | single, **one-way** | Form / Process | |
| UoM | mirror | via `Product` → `UoM` | Mirror | |
| Movement type | status | Opening (dark green), Receipt (green), Issue to project (blue), Manual in (light green), Manual out (orange), Stock count (purple) | Form / Process | Explicit; never inferred from a sign |
| Qty | numbers | always positive | Form / Process | For Stock count, the process writes the difference |
| Counted qty | numbers | | Form | Stock count only |
| Reason | dropdown (single) | Return, Found, Damage/Scrap, Sample, Other | Form | Required for Manual in/out |
| Note | long text | | Form | Required when Reason = Other |
| Status | status | Pending (grey), Applied (green), Rejected (red) | Process | |
| Rejection reason | text | | Process | |
| Qty before | numbers | | Process | On hand before applying |
| Qty after | numbers | | Process | On hand after applying |
| Applied at | date (with time) | | Process | |
| ⚙️ Applied in → Product | connect → Materials Catalogue | single, **two-way** | Process | Set only when Applied and the direction is in |
| ⚙️ Applied out → Product | connect → Materials Catalogue | single, **two-way** | Process | Set only when Applied and the direction is out |
| Unit / Project | connect → Projects + Subitems of Projects | single, **one-way** | Process | Receipts and issues only; never manual movements |
| Request line | connect → request lines | single, **one-way** | Process | |
| PO line | connect → PO lines | single, **one-way** | Process | |
| Created by | creation log | | — | |

**Direction by type.** In: Opening, Receipt, Manual in, and Stock count when counted > On hand. Out: Issue to project, Manual out, and Stock count when counted < On hand.

Groups: **Ledger**.

---

## 5. Approved changes on Sam's boards (STOP gate 2)

These are the **only** columns this build may add to boards outside the demo folder. They were approved in principle by Omer on 27 Oct, but Claude Code **must still stop and get explicit confirmation** before creating them (CLAUDE.md, rule 3).

| # | Board | Column | Type | Source |
|---|---|---|---|---|
| 1 | Subitems of Projects (Units) 18412939439 | Material Requests | reflection | Created by the Requests `Unit / Project` two-way connect |
| 2 | Units | Material cost | mirror | via #1 → Requests `Material cost`, sum |
| 3 | Units | Request status | mirror | via #1 → Requests `Status`, all statuses |
| 4 | Projects 18412939430 | Material Requests | reflection | Created by the same two-way connect (multi-board) |
| 5 | Projects | Purchase Orders | reflection | Created by the PO `Projects` two-way connect |
| 6 | Projects | Material cost | mirror | via #4 → Requests `Material cost`, sum (requests linked directly to the project) |
| 7 | Projects | Request status | mirror | via #4 → Requests `Status`, all statuses |
| 8 | Projects | Units material cost | mirror | via subitems `subtasks_mm3aqxk2` → Units `Material cost` (#2), sum. Same mirror-of-mirror pattern as `lookup_mm3rfs7n` |
| 9 | Projects | PO status | mirror | via #5 → PO `Status`, all statuses |

Optional, **not approved**: a Projects formula adding #6 + #8 into one total. Ask Omer first.

Nothing else on Projects, Units, Production Calendar, Task Manager or any Spot-nik board may change. That includes views, filters, groups, automations, column order, and existing columns such as `link to Stock Updates`.

---

## 6. Views (demo boards only)

| Board | View | Type | Definition |
|---|---|---|---|
| Suppliers | Main table | table | All columns |
| Materials Catalogue | Main table | table | Hide ⚙️ columns; key columns: Category, Stock type, UoM, On hand, Reserved, Available, Stock state, Minimum level, Default supplier |
| Materials Catalogue | Low & out | table | Filter: Stock state is Low or Out |
| Materials Catalogue | Reserved vs available | table | Columns: Name, UoM, On hand, Reserved, Available, Stock state; sorted by Reserved, descending |
| Material Requests | Main table | table | Subitems expanded; hide ⚙️ columns |
| Material Requests | By status | kanban | Grouped by Status |
| Purchase Orders | Main table | table | |
| Purchase Orders | By supplier | table | Grouped or sorted by Supplier |
| Purchase Orders | Overdue deliveries | table | Filter: Delivery state = Overdue |
| Purchase Orders | By status | kanban | Grouped by Status |
| Stock Movements | Ledger | table | Sorted by Movement #, ascending |
| Stock Movements | By product | table | Grouped or sorted by Product |
| Stock Movements | Rejected & pending | table | Filter: Status is Rejected or Pending |

If the API can't create views, record them in `MANUAL-STEPS.md` (CLAUDE.md, rule 9).

---

## 7. WorkForm — "Manual stock update" (Stock Movements)

A native monday WorkForm. It creates one Stock Movement item in Pending status.

| Question | Column | Required | Condition |
|---|---|---|---|
| Product | Product | yes | |
| Movement type | Movement type | yes | Show only Manual in, Manual out and Stock count, if the form supports hiding labels. Otherwise say so in the form description. |
| Quantity | Qty | yes | Movement type = Manual in or Manual out |
| Counted quantity | Counted qty | yes | Movement type = Stock count |
| Reason | Reason | yes | Movement type = Manual in or Manual out |
| Note | Note | no (required by the process when Reason = Other) | |

Form description: "Manual stock changes only. To take material for a job, use a material request. A manual out or a count that would cut into stock reserved for projects will be rejected."

Status defaults to Pending; Unit / Project is never shown. If the WorkForm can't be created through the API, add it to `MANUAL-STEPS.md`.

---

## 8. Dashboard — "Procurement Overview (Demo)"

Lives in the demo folder. Sources: the 5 demo boards. Projects is read-only and appears in widget 5 only; adding a board as a dashboard source doesn't change it.

| # | Widget | Source | Setup |
|---|---|---|---|
| 1 | Requests by status | Material Requests | Chart (bar) by Status |
| 2 | Open POs by supplier | Purchase Orders | Chart by Supplier; exclude Received, Closed, Cancelled |
| 3 | Overdue deliveries | Purchase Orders | Table; Delivery state = Overdue |
| 4 | Spend by supplier | Purchase Orders | Chart: sum of Total, by Supplier |
| 5 | Material cost per project | Projects | Table or chart: Material cost + Units material cost |
| 6 | Low & out stock | Materials Catalogue | Table; Stock state = Low or Out |
| 7 | Stock value | Materials Catalogue | Numbers: sum of Stock value |

If dashboards or widgets can't be created through the API, add them to `MANUAL-STEPS.md` with this table.

---

## 9. Sample data

### 9.1 Real items to pick (Phase 0, read-only, then STOP gate 1)

Claude Code reads Projects, Units and Production Calendar, proposes the following, and waits for Omer's approval:

| Placeholder | What to pick |
|---|---|
| `{{PRJ_A}}` | A Projects item, preferably *In Production*, with **at least 2 Units** |
| `{{PRJ_A_UNIT_2}}` | A Unit (subitem) of `{{PRJ_A}}` |
| `{{PRJ_B}}` | A different project, *In Production* or *In Design Process*, with at least 1 Unit |
| `{{PRJ_B_UNIT_1}}` | A Unit of `{{PRJ_B}}`, preferably Project Type = Pre-finished |
| `{{PRJ_C}}` | A third project with at least 1 Unit, preferably a Paint-type unit |
| `{{PRJ_C_UNIT_1}}` | A Unit of `{{PRJ_C}}` |
| `{{SVC_JOB}}` | An item in Production Calendar group **Installation - Service Job** (`group_mm7rz40h`) |

Avoid projects with Status = Done. The proposal lists name, ID, status and units for each pick.

### 9.2 Suppliers

All contact details are fictional (`.example` domains, 555-01xx numbers).

| Ref | Name | Contact | Email | Phone | Terms | Categories | Active |
|---|---|---|---|---|---|---|---|
| S1 | Pacific Panel Supply | Dana Whitfield | orders@pacificpanel.example | (555) 010-2101 | Net 30 | Sheet Goods | Active |
| S2 | Edge & Trim Distributors | Luis Romero | sales@edgetrim.example | (555) 010-2202 | Net 30 | Edgeband | Active |
| S3 | Hardware Source Co. | Priya Nair | orders@hardwaresource.example | (555) 010-2303 | Net 15 | Hinges, Slides & Hardware, Accessories | Active |
| S4 | Coastline Coatings | Mark Ellison | orders@coastlinecoatings.example | (555) 010-2404 | COD | Finish / Paint | Active |

### 9.3 Materials Catalogue

| Ref | Name | Group / Category | UoM | Stock type | Pack | Supplier | Part # | Min | Last price |
|---|---|---|---|---|---|---|---|---|---|
| P01 | MDF 3/4" 4x8 White Melamine | Sheet Goods | sheet | Stocked | 1 | S1 | PPS-MDF34-WM | 100 | 68.00 |
| P02 | MDF 3/4" 4x8 Raw (Paint Grade) | Sheet Goods | sheet | Stocked | 1 | S1 | PPS-MDF34-RAW | 25 | 52.00 |
| P03 | Plywood 3/4" 4x8 Maple Pre-finished | Sheet Goods | sheet | Stocked | 1 | S1 | PPS-PLY34-MPF | 15 | 95.00 |
| P04 | Plywood 1/4" 4x8 Maple Pre-finished | Sheet Goods | sheet | Stocked | 1 | S1 | PPS-PLY14-MPF | 10 | 38.00 |
| P05 | Edgeband White PVC 22mm | Edgeband | ft | Stocked | 300 | S2 | ET-PVC22-WH | 600 | 0.12 |
| P06 | Edgeband Maple Wood 22mm | Edgeband | ft | Order-to-project | 300 | S2 | ET-WD22-MP | 0 | 0.35 |
| P07 | Hinge 110° Soft-close Full Overlay | Hinges | each | Stocked | 50 | S3 | HS-H110-FO | 200 | 3.10 |
| P08 | Hinge Mounting Plate 0mm | Hinges | each | Stocked | 50 | S3 | HS-MP0 | 200 | 0.90 |
| P09 | Drawer Slide 21" Undermount Soft-close | Slides & Hardware | pair | Stocked | 10 | S3 | HS-UM21-SC | 40 | 24.50 |
| P10 | Drawer Slide 18" Undermount Soft-close | Slides & Hardware | pair | Order-to-project | 10 | S3 | HS-UM18-SC | 0 | 22.00 |
| P11 | Pull Handle 128mm Matte Black | Accessories | each | Order-to-project | 25 | S3 | HS-PH128-MB | 0 | 4.20 |
| P12 | Shelf Pin 5mm Nickel | Accessories | each | Stocked | 1000 | S3 | HS-SP5-NI | 500 | 0.04 |
| P13 | Primer White 1 gal | Finish / Paint | gallon | Stocked | 1 | S4 | CC-PRM-WH-1G | 10 | 32.00 |
| P14 | Pre-cat Lacquer Satin 1 gal | Finish / Paint | gallon | Stocked | 1 | S4 | CC-PCL-SAT-1G | 5 | 48.00 |
| P15 | Toe Kick 4" Black Melamine 8ft | **🆕 New – needs review**, Category blank | — | Order-to-project | — | — | — | — | — |

P15 shows a product created by the programmer from a request line: no supplier, UoM or price yet.

### 9.4 Material Requests and lines

All people columns = Kindaa Support. "Res" = Qty reserved. "To order" = Qty to order, as written at submit. "Issued" = Qty issued (blank unless shown). Every request has ✅ Materials complete ticked, because the form requires it.

**MR-1 · `DEMO – {{PRJ_A}} – MR #1`** · Status **Closed** · group Closed & cancelled · Unit / Project = `{{PRJ_A}}` (whole project) · Submitted T-28 · Needed by T-20

| Line | Product | Qty req | Decision | Res | To order | Issued | PO line |
|---|---|---|---|---|---|---|---|
| L1 | P01 | 30 | Issued | 0 | 0 | 30 | — |
| L2 | P05 | 400 | Issued | 0 | 0 | 400 | — |
| L3 | P07 | 60 | Issued | 0 | 0 | 60 | — |
| L4 | P08 | 60 | Issued | 0 | 0 | 60 | — |
| L5 | P09 | 12 | Issued | 0 | 0 | **10** | — |

Note on MR-1: "L5: 10 pairs used, 2 released back to stock."

**MR-2 · `DEMO – {{PRJ_B_UNIT_1}} – MR #2`** · Status **Ready for Production** · Unit / Project = `{{PRJ_B_UNIT_1}}` · Submitted T-14 · Needed by T+3 · Purchase Orders = PO-0001, PO-0002

| Line | Product | Qty req | Decision | Res | To order | PO line |
|---|---|---|---|---|---|---|
| L1 | P03 | 20 | From Stock | 20 | 0 | — |
| L2 | P04 | 8 | From Stock | 8 | 0 | — |
| L3 | P06 | 600 | Received | 600 | 600 | PO-0001 / L1 |
| L4 | P07 | 40 | From Stock | 40 | 0 | — |
| L5 | P08 | 40 | From Stock | 40 | 0 | — |
| L6 | P11 | 30 | Received | 30 | 30 | PO-0002 / L1 |

**MR-3 · `DEMO – {{PRJ_C_UNIT_1}} – MR #3`** · Status **Waiting for Delivery** · Unit / Project = `{{PRJ_C_UNIT_1}}` · Submitted T-10 · Needed by T+5 · Purchase Orders = PO-0003, PO-0004

| Line | Product | Qty req | Decision | Res | To order | PO line |
|---|---|---|---|---|---|---|
| L1 | P02 | 50 | From Stock | 50 | 0 | — |
| L2 | P13 | 20 | Ordered | 16 | 4 | PO-0003 / L1 |
| L3 | P10 | 16 | Ordered | 10 | 16 | PO-0004 / L1 (20 ordered as 2 packs, 10 received → 6 outstanding) |
| L4 | P14 | 6 | From Stock | 6 | 0 | — |

At submit, L2 was **Partial** (16 in stock, 4 to order) and L3 was **To Order** (none in stock). Both became Ordered once the PO lines were created.

**MR-4 · `DEMO – {{PRJ_A_UNIT_2}} – MR #4`** · Status **Issue Materials** · Unit / Project = `{{PRJ_A_UNIT_2}}` · Submitted T-21 · Needed by T-2 · Note: "Trigger for Issue Materials = production complete — **TBD with Sam**."

| Line | Product | Qty req | Decision | Res | To order | Issued (default) |
|---|---|---|---|---|---|---|
| L1 | P01 | 24 | From Stock | 24 | 0 | 24 |
| L2 | P05 | 300 | From Stock | 300 | 0 | 300 |
| L3 | P12 | 200 | From Stock | 200 | 0 | 200 |
| L4 | P07 | 30 | From Stock | 30 | 0 | 30 |

**MR-5 · `DEMO – {{PRJ_C}} – MR #5`** · Status **In Review** · Unit / Project = `{{PRJ_C}}` (whole project) · Submitted T-1 · Needed by T+14

| Line | Product | Qty req | Decision | Res | To order |
|---|---|---|---|---|---|
| L1 | P01 | 60 | From Stock | 60 | 0 |
| L2 | P15 | 6 | To Order | 0 | 6 |
| L3 | P09 | 24 | From Stock | 24 | 0 |
| L4 | P14 | 10 | **Partial** | 6 | 4 |

Note on MR-5: "L2 product is new — purchaser to complete supplier/UoM/price before ordering."

**MR-6 · `DEMO – Service – {{SVC_JOB}} – MR #6`** · Status **Ready for Production** · group Active requests · Unit / Project = *empty* · Production Calendar job = `{{SVC_JOB}}` · Submitted T-0 · Needed by T+10 · Note: "Service job — does it consume stock / need POs? **TBD with Sam**. Cost does not reach Projects."

| Line | Product | Qty req | Decision | Res | To order |
|---|---|---|---|---|---|
| L1 | P04 | 2 | From Stock | 2 | 0 |
| L2 | P07 | 4 | From Stock | 4 | 0 |

Everything on MR-6 was in stock at submit, so it went straight to Ready for Production with no purchaser step.

### 9.5 Purchase Orders and lines

All Purchaser and Approved by = Kindaa Support (Approved by stays blank on Draft).

| PO | Name | Status | Group | Supplier | Projects | Order | Expected | Sent | Tax/Ship |
|---|---|---|---|---|---|---|---|---|---|
| PO-0001 | DEMO – PO-0001 – Edge & Trim Distributors | Received | Closed & cancelled | S2 | `{{PRJ_B}}` | T-13 | T-6 | T-13 | 25 |
| PO-0002 | DEMO – PO-0002 – Hardware Source Co. | Received | Closed & cancelled | S3 | `{{PRJ_B}}` | T-13 | T-5 | T-13 | 15 |
| PO-0003 | DEMO – PO-0003 – Coastline Coatings | Sent | Open POs | S4 | `{{PRJ_C}}` | T-9 | **T-2 (overdue)** | T-9 | 40 |
| PO-0004 | DEMO – PO-0004 – Hardware Source Co. | Partially Received | Open POs | S3 | `{{PRJ_C}}` | T-9 | T+4 | T-9 | 30 |
| PO-0005 | DEMO – PO-0005 – Pacific Panel Supply | Draft | Open POs | S1 | — | — | — | — | 0 |

PO-0003 → PO document = mock PDF (§10, Phase 9).
PO-0005 → Notes to supplier: "Replenishment — MDF white below minimum."

| PO / Line | Product | Qty ordered | Unit price | Qty received | Received date | Project | Line status | Request line |
|---|---|---|---|---|---|---|---|---|
| PO-0001 / L1 | P06 | 600 | 0.35 | 600 | T-6 | `{{PRJ_B}}` | Received | MR-2 / L3 |
| PO-0002 / L1 | P11 | 50 | 4.20 | 50 | T-5 | `{{PRJ_B}}` | Received | MR-2 / L6 |
| PO-0003 / L1 | P13 | 4 | 32.00 | 0 | — | `{{PRJ_C}}` | Open | MR-3 / L2 |
| PO-0003 / L2 | P13 | 12 | 32.00 | 0 | — | *blank (replenishment)* | Open | — |
| PO-0004 / L1 | P10 | 20 | 22.00 | 10 | T-3 | `{{PRJ_C}}` | Partially Received | MR-3 / L3 |
| PO-0004 / L2 | P09 | 20 | 24.50 | 0 | — | *blank (replenishment)* | Open | — |
| PO-0005 / L1 | P01 | 100 | 68.00 | 0 | — | *blank (replenishment)* | Open | — |

PO-0002 / L1 shows the pack-rounding story: 30 needed, a box of 25 means 50 ordered; 30 reserved for MR-2, 20 free.

### 9.6 Stock Movements

Every row is Status **Applied**, except SM-23. "Link" says which applied connect is set. Applied at = the date shown.

| # | Name | Type | Product | Qty | Counted | Reason | Before | After | Link | Unit / Project | Request line | PO line | Date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SM-01 | Opening – P01 | Opening | P01 | 150 | | | 0 | 150 | in | | | | T-45 |
| SM-02 | Opening – P02 | Opening | P02 | 80 | | | 0 | 80 | in | | | | T-45 |
| SM-03 | Opening – P03 | Opening | P03 | 40 | | | 0 | 40 | in | | | | T-45 |
| SM-04 | Opening – P04 | Opening | P04 | 25 | | | 0 | 25 | in | | | | T-45 |
| SM-05 | Opening – P05 | Opening | P05 | 1500 | | | 0 | 1500 | in | | | | T-45 |
| SM-06 | Opening – P07 | Opening | P07 | 400 | | | 0 | 400 | in | | | | T-45 |
| SM-07 | Opening – P08 | Opening | P08 | 400 | | | 0 | 400 | in | | | | T-45 |
| SM-08 | Opening – P09 | Opening | P09 | 60 | | | 0 | 60 | in | | | | T-45 |
| SM-09 | Opening – P12 | Opening | P12 | 2000 | | | 0 | 2000 | in | | | | T-45 |
| SM-10 | Opening – P13 | Opening | P13 | 14 | | | 0 | 14 | in | | | | T-45 |
| SM-11 | Opening – P14 | Opening | P14 | 12 | | | 0 | 12 | in | | | | T-45 |
| SM-12 | Issue to project – P01 | Issue to project | P01 | 30 | | | 150 | 120 | out | `{{PRJ_A}}` | MR-1 / L1 | | T-20 |
| SM-13 | Issue to project – P05 | Issue to project | P05 | 400 | | | 1500 | 1100 | out | `{{PRJ_A}}` | MR-1 / L2 | | T-20 |
| SM-14 | Issue to project – P07 | Issue to project | P07 | 60 | | | 400 | 340 | out | `{{PRJ_A}}` | MR-1 / L3 | | T-20 |
| SM-15 | Issue to project – P08 | Issue to project | P08 | 60 | | | 400 | 340 | out | `{{PRJ_A}}` | MR-1 / L4 | | T-20 |
| SM-16 | Issue to project – P09 | Issue to project | P09 | 10 | | | 60 | 50 | out | `{{PRJ_A}}` | MR-1 / L5 | | T-20 |
| SM-17 | Manual in – P13 | Manual in | P13 | 2 | | Return | 14 | 16 | in | | | | T-18 |
| SM-18 | Manual out – P03 | Manual out | P03 | 2 | | Damage/Scrap | 40 | 38 | out | | | | T-16 |
| SM-19 | Stock count – P12 | Stock count | P12 | 150 | 1850 | | 2000 | 1850 | out | | | | T-15 |
| SM-20 | Receipt – P06 | Receipt | P06 | 600 | | | 0 | 600 | in | `{{PRJ_B_UNIT_1}}` | MR-2 / L3 | PO-0001 / L1 | T-6 |
| SM-21 | Receipt – P11 | Receipt | P11 | 50 | | | 0 | 50 | in | `{{PRJ_B_UNIT_1}}` | MR-2 / L6 | PO-0002 / L1 | T-5 |
| SM-22 | Receipt – P10 | Receipt | P10 | 10 | | | 0 | 10 | in | `{{PRJ_C_UNIT_1}}` | MR-3 / L3 | PO-0004 / L1 | T-3 |
| SM-23 | Manual out – P01 | Manual out | P01 | 50 | | Damage/Scrap | — | — | **none** | | | | T-1 |

SM-23: Status **Rejected**. Rejection reason: "Exceeds Available (36). Reserved stock can't be taken manually."
SM-18 Note: "Water damage, 2 sheets." SM-19 Note: "Quarterly count."

Product names in the Name column use the full product name, not the ref.

### 9.7 Expected values — verify after loading

**Materials Catalogue**

| Ref | On hand | Reserved | Available | Stock state |
|---|---|---|---|---|
| P01 | 120 | 84 | 36 | Low |
| P02 | 80 | 50 | 30 | In |
| P03 | 38 | 20 | 18 | In |
| P04 | 25 | 10 | 15 | In |
| P05 | 1100 | 300 | 800 | In |
| P06 | 600 | 600 | 0 | — |
| P07 | 340 | 74 | 266 | In |
| P08 | 340 | 40 | 300 | In |
| P09 | 50 | 24 | 26 | Low |
| P10 | 10 | 10 | 0 | — |
| P11 | 50 | 30 | 20 | — |
| P12 | 1850 | 200 | 1650 | In |
| P13 | 16 | 16 | 0 | Out |
| P14 | 12 | 12 | 0 | Out |
| P15 | 0 | 0 | 0 | — |

**Material cost per request** (Line cost sum)

| MR-1 | MR-2 | MR-3 | MR-4 | MR-5 | MR-6 |
|---|---|---|---|---|---|
| 2,573.00 | 2,700.00 | 3,880.00 | 1,769.00 | 5,148.00 | 88.40 |

MR-5 L2 (P15) has no price, so its line cost is 0. That's expected.

**Projects** (after the §5 columns exist)
- `{{PRJ_A}}`: Material cost 2,573.00; Units material cost includes 1,769.00 (from `{{PRJ_A_UNIT_2}}`).
- `{{PRJ_B}}`: Units material cost includes 2,700.00.
- `{{PRJ_C}}`: Material cost 5,148.00; Units material cost includes 3,880.00.

**Purchase Orders**

| PO | Subtotal | Total | Delivery state |
|---|---|---|---|
| PO-0001 | 210.00 | 235.00 | |
| PO-0002 | 210.00 | 225.00 | |
| PO-0003 | 512.00 | 552.00 | Overdue |
| PO-0004 | 930.00 | 960.00 | |
| PO-0005 | 6,800.00 | 6,800.00 | |

**Suppliers, Total ordered:** S1 6,800.00 · S2 235.00 · S3 1,185.00 · S4 552.00.

Any mismatch: stop, report it, and don't "fix" values by hand to force a match.

---

## 10. Build order

Each phase ends with a short entry in `BUILD-LOG.md`. **STOP** means: report to Omer and wait for an explicit "go".

### Phase 0 — Preflight (read-only)
1. Confirm the monday.com connector is available in the session. If raw API calls are needed, check that `MONDAY_API_TOKEN` is set; never print it.
2. Query `me` and confirm the acting user is **103186497 (Kindaa Support)** and the account is **34799434**. If not, STOP.
3. Check what the connector supports first, then the API, for the operations needed: create_folder, create_board, create_column (status/dropdown defaults, board_relation, mirror, formula), create_subitem, create_group, file upload, views, forms, dashboards. Record what's supported in `BUILD-LOG.md` and plan `MANUAL-STEPS.md` entries for the rest.
4. Confirm workspace 15462830 exists and no folder named `Inventory & Procurement (Demo)` exists yet. If it does, STOP and ask.
5. Snapshot the column list (id, title, type) of Projects, Units and Production Calendar into `snapshots/pre-build.json`. This is the baseline for every "nothing changed" check.
6. Read Projects, Units and Production Calendar items and propose the §9.1 picks.
7. **STOP gate 1:** Omer approves the picks.

### Phase 1 — Folder, boards, groups
1. Create the folder.
2. Create the 5 boards (public, in the folder) in this order: Suppliers → Materials Catalogue → Material Requests → Purchase Orders → Stock Movements.
3. Create the groups from §4. Make **🆕 New – needs review** the top group of the Catalogue.
4. Record the board IDs in CLAUDE.md "Live map".

### Phase 2 — Plain columns on the main boards
All columns from §4 that are text, numbers, status, dropdown, date, people, email, phone, file, checkbox, long text, auto number or creation log. Create status and dropdown labels as listed, then read back and verify each label set.

### Phase 3 — Subitem boards
1. Create the subitems column on Material Requests and Purchase Orders. If that isn't possible through the API, create one `ZZ-TEST-bootstrap` parent item with one subitem to bring the subitems board into existence. Leave the ZZ-TEST- items in place.
2. Record the subitem board IDs.
3. Add the plain columns from §4.4 and §4.6.

### Phase 4 — Connect columns inside the demo, plus one-way connects to Sam's boards
1. Demo ↔ demo connects, two-way as marked:
   - Catalogue `Default supplier`
   - PO `Supplier`
   - Requests ↔ POs
   - line `Product`
   - line `PO line`
   - Movements `⚙️ Applied in / out`
2. One-way, as marked:
   - PO line `Product`
   - Movements `Product`, `Request line` and `PO line`
3. One-way connects to Sam's boards, as marked: Requests `Production Calendar job`, PO line `Project`, Movements `Unit / Project`.
4. Re-read Sam's boards' columns and compare them with `snapshots/pre-build.json`. **Any new column = STOP.**
5. If the API can't create a connect as two-way, create it one-way, log it, and add "switch to two-way" to `MANUAL-STEPS.md`. Don't continue to any mirror that depends on that reflection until Omer confirms it's done.

### Phase 5 — Mirrors and formulas on demo boards
1. Run the **aggregation test** first, using `ZZ-TEST-` items on the demo boards only. Can a mirror **sum** a **formula** column (line `Line cost` → request `Material cost`; PO line `Line total` → PO `Subtotal`; PO `Total` → Supplier `Total ordered`)? Can a formula use a mirror (`On hand`)?
2. Log the result. If summing a formula doesn't work, change that source column to a plain `numbers` column, filled from §9, and record the deviation.
3. Create every mirror and formula in §4. Build mirrors in dependency order: Catalogue first, then lines, requests, PO lines, POs, Suppliers.

### Phase 6 — Columns on Sam's boards (STOP gate 2)
1. **STOP:** list the 9 columns from §5 and wait for Omer's explicit "go".
2. Create the Requests `Unit / Project` connect (two-way, Projects + Units) and the PO `Projects` connect (two-way).
3. Create mirrors #2, #3 on Units and #6, #7, #8, #9 on Projects.
4. Compare with the snapshot again. Exactly these 9 new columns may appear. Anything else = STOP.

### Phase 7 — Sample data
Load in this order, linking by **item ID**, never by name:
1. Suppliers
2. Catalogue
3. Movements, without links first
4. Requests (Unit / Project, Production Calendar job)
5. Request lines
6. POs (Supplier, Projects)
7. PO lines
8. Line ↔ PO line links
9. Request ↔ PO links
10. Movement links: applied, project, request line, PO line
11. Statuses

Then verify every value in §9.7 by reading the mirrors and formulas back through the API. Report the comparison table.

### Phase 8 — Views, WorkForm, dashboard
§6, §7 and §8 through the API where it's supported; otherwise `MANUAL-STEPS.md`.

### Phase 9 — Mock PO PDF
1. Generate a one-page PDF for **PO-0003**:
   - header "Ricco Cabinetry — Purchase Order" and the PO number
   - supplier block (S4)
   - both lines: product, part #, packs, qty, unit price, line total
   - subtotal, tax/shipping, total
   - order and expected dates
2. Add a diagonal watermark: **"SAMPLE LAYOUT – PENDING RICCO TEMPLATE"**. Use no logo.
3. Upload it to PO-0003 → `PO document`.

### Phase 10 — Handoff
Report to Omer:
- board and column map (fill in CLAUDE.md "Live map")
- §9.7 verification table
- deviations
- `MANUAL-STEPS.md`
- the list of `ZZ-TEST-` items for manual cleanup

No further writes after the report.

---

## 11. Full-build flow logic (reference; not built in the demo)

The detailed registry is `AUTOMATIONS.md`. The approved rules:

1. **Request (F1).** The programmer fills in a Fillout form: Unit or Project (or a Production Calendar job for service jobs), Needed by, Source file, plus lines (Product + Qty). The form won't send until the required **✅ Materials complete** confirmation is ticked. That checkbox is a safeguard only; **no automation reads it**. Required fields are enforced by the form, not by automations. Sending the form creates the request and its lines with Status **Submitted**. A missing product is created from the line's `Product` column and lands in 🆕 New – needs review as Order-to-project. Materials forgotten after sending go on a new request.
2. **Auto-reserve (F2), via the stock process.** Triggered by the new Submitted request, not by the checkbox. Each line is compared with its product's **current Available**, one line at a time; two lines for the same product see each other's reservations.
   - Available ≥ Qty requested → reserve it all; Qty to order = 0; Decision **From Stock**.
   - 0 < Available < Qty requested → reserve Available; Qty to order = the rest; Decision **Partial**.
   - Available = 0 → reserve nothing; Qty to order = Qty requested; Decision **To Order**.

   Then, if every line is From Stock → **Ready for Production** and notify the inventory owner. Otherwise → **In Review** and notify the purchaser.
3. **Purchaser review (F3, manual).** The purchaser can release a reservation (through the process, which adds the released quantity to Qty to order), adjust quantities, or complete a 🆕 product (supplier, UoM, price, stock type). Then sets **Ordering**.
4. **PO builder (F4).** Lines with Qty to order > 0 and no PO line yet are grouped by the product's default supplier. For each supplier: find its Draft PO (which can mix projects) or create one, add a PO line (Qty to order rounded up to full packs, last price, project, request line link), and set the line to Ordered. Lines whose product has no supplier are held and the purchaser is notified. When all lines are handled, the request goes to **Waiting for Delivery**. Approved → PDF (template TBD) → email (sender TBD) → **Sent**.
5. **Receipt (F5), via the stock process.** Triggered when Qty received changes on a PO line. A Receipt movement is created for the delta. The process applies it and, **in the same step**, adds up to the line's remaining need to the request line's `Qty reserved`; any surplus stays free. Then: update Last purchase price, roll up line and PO status, and when every request line is From Stock or Received, move the request to **Ready for Production** and notify.
6. **Issue (F6), via the stock process.** Production complete (trigger TBD) → **Issue Materials**, Qty issued defaults to requested, inventory owner notified. The owner corrects the quantities and sets **Issuing**. The process creates Issue movements, which draw from the line's reservation first, then from Available. It sets Qty reserved = 0 (releasing any remainder) and the line to Issued. When all are Applied, the request is **Closed**. On a rejection, the request returns to Issue Materials with the reason.
7. **Cancel / hold (F7).** Cancelled → release all reservations; open PO lines are *not* auto-cancelled and the purchaser is notified. On Hold → reservations kept, purchaser notified.
8. **Manual movements (F8), via the stock process.** Manual in/out or Stock count from the WorkForm. A Manual out or a count that would push Available below 0 → **Rejected**; notify the inventory owner and purchaser, naming the affected projects. No project link, ever.
9. **Low stock (F9).** When Stock state crosses into Low or Out, notify the purchaser once. They add a replenishment line (no project) to the supplier's Draft PO.
10. **Integrity check (F10), nightly.** Every Applied row has exactly 1 applied link; no Pending or Rejected row has one; the Qty before/after chain per product is unbroken; Reserved = sum of open lines' Qty reserved; no Pending older than 15 minutes. Alert Kindaa Support and the inventory owner on any failure.

**Stock process rules:**
- Single queue for every stock-changing operation.
- Validates before writing.
- Writes Qty before/after, the applied link and Status.
- After each apply, reads On hand back and **waits until it equals Qty after**, retrying for up to about 10 seconds; otherwise it stops the queue and alerts.
- Idempotent: an Applied movement is never re-applied.
- Applied rows are immutable; corrections are made with a reversing movement.
- In the full build, On hand, Qty, Type, Status and the applied links are locked by column permissions.

---

## 12. Walkthrough script (for presenting to Sam)

| # | Story | Show | Point out |
|---|---|---|---|
| 1 | Programmer sends the material list | MR-6 (Ready for Production) | The Fillout form (full build) creates the request and lines, picking from the catalogue only; ✅ Materials complete is a required confirmation before sending. Everything was in stock, so it went straight to Ready for Production. Service jobs link to Production Calendar — question for Sam |
| 2 | System checks stock and reserves | MR-5 (In Review) | Each line was compared with Available at submit: L1 and L3 fully reserved, L4 partly reserved with 4 to order, L2 all 6 to order. Catalogue P01: Reserved 84, Available 36, now Low. P15 sits in 🆕 New – needs review |
| 3 | Purchaser orders what's missing | PO-0005 (Draft), PO-0003 (Sent + mock PDF) | One PO per supplier can mix projects and stock replenishment (PO-0003 L2, blank project). The PDF layout waits for Sam's sample |
| 4 | Late delivery is visible | "Overdue deliveries" view, dashboard widget 3 | PO-0003 is past its expected date |
| 5 | Partial delivery | PO-0004, SM-22, MR-3 L3 | 10 of 20 received; those 10 are reserved for MR-3 only, and 6 more are still needed |
| 6 | Received for a job stays for that job | MR-2 (Ready for Production), P11 | 50 handles received (a box of 25 means 2 boxes): 30 reserved for the unit, 20 free |
| 7 | Production done → stock out | MR-4 (Issue Materials), MR-1 (Closed) | Inventory owner confirms actual quantities; MR-1 used 10 slides instead of 12, so 2 went back to stock (SM-16). The trigger is a question for Sam |
| 8 | Manual updates and counts | WorkForm, SM-17/18/19, SM-23 | Count by quantity counted; SM-23 rejected because it would take stock reserved for projects |
| 9 | Low stock | Catalogue "Low & out", PO-0004 L2, PO-0005 | Minimum levels are compared with Available, not On hand |
| 10 | Project costing | `{{PRJ_A}}`, `{{PRJ_B}}`, `{{PRJ_C}}` on Projects | Material cost and statuses now appear on his own Projects and Units |
| 11 | Overview | Dashboard | Requests, open POs, overdue, spend by supplier, cost per project, low stock |

Say clearly that the demo shows the **result** of each automatic step; nothing runs yet.

---

## 13. Placeholders and open questions for Sam

| Topic | Demo placeholder | Question |
|---|---|---|
| PO format | `PO-000n` auto number, mock PDF | Sample PO, numbering, approver, who emails it (monday or the purchaser) |
| Stock-out trigger | MR-4 at Issue Materials, marked TBD | What event means "production complete"? |
| Service jobs | MR-6 linked to the Production Calendar job, no project | Do service jobs use stock or need POs? |
| Roles | Kindaa Support everywhere | Who is programmer / purchaser / receiver / inventory owner; are they monday users? |
| Catalogue | 15 invented products | Real catalogue source and size; opening physical count |
| UoM / packs | Invented | Real units and pack sizes |
| Minimum levels | MDF 100 from the call; others invented | Levels per stocked item |
| Prices | Last price paid | Is that enough, or a quoted price list per supplier? |
| Material list | Typed in Fillout | Programming software name; can it export CSV/Excel? |
| Fillout | Not connected | Confirm the form can create a missing catalogue item, or keep that on the board |
| Spot-nik boards | Untouched | Where do his Products-board "item created / archived → webhook" automations point? |

---

## 14. Known uncertainties for the builder

Verify these with the connector first, then the API. Log the result and never work around them silently:
- Whether the connector or API can create **two-way** and **multi-board** connect columns.
- Whether the API can create **mirror** columns, and with which aggregation (sum / all statuses).
- Status label creation and colors through the API.
- Creating views, WorkForms and dashboards through the API.
- Mirror **sum** over formula columns (Phase 5 test).
- Default columns monday adds to new boards and subitem boards.
