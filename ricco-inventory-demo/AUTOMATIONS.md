# AUTOMATIONS.md — Ricco Cabinetry · Inventory & Procurement

Registry of every automation for the **full build**. **Demo phase: none of these are built or active.**

When an automation is built:
- fill in its Runtime and ID fields
- change its Status
- add the date and builder to its change log

The stock process runtime (Make, code or hybrid) is decided before the full build. One rule holds whichever runtime is chosen: **every stock-changing operation goes through A03**, one item at a time.

**Status values:** `Planned` · `Blocked – TBD with Sam` · `In build` · `Active` · `Paused` · `Retired`

**Runtime values:** `Native monday automation` · `Make (scenario ID)` · `Code (path)` · `Fillout` · `TBD`

---

## Summary

| ID | Name | Trigger | Runtime | Status |
|---|---|---|---|---|
| A01 | Material request form | Fillout submission | Fillout | Planned |
| A03 | **Stock process** (single queue) | Operations from A04, A10, A13, A14, A15 | TBD (Make sequential / code) | Planned |
| A04 | Auto-reserve on submit | Request created by the form (Status = Submitted) | TBD (enqueues to A03) | Planned |
| A06 | New product intake | Item created in Catalogue group 🆕 New – needs review | Native / TBD | Planned |
| A07 | PO builder | Request → Ordering | TBD | Planned |
| A08 | PO approval → PDF | PO → Approved | TBD | Blocked – TBD with Sam (template) |
| A09 | PO send to supplier | PDF attached / PO → Sent | TBD | Blocked – TBD with Sam (sender) |
| A10 | Receipt | PO line `Qty received` changed | TBD (enqueues to A03) | Planned |
| A11 | Request readiness | Request line Decision changed | TBD | Planned |
| A12 | Production complete → Issue Materials | TBD event | TBD | Blocked – TBD with Sam (trigger) |
| A13 | Issue materials | Request → Issuing | TBD (enqueues to A03) | Planned |
| A14 | Cancel / hold request | Request → Cancelled / On Hold | TBD (enqueues to A03 on cancel) | Planned |
| A15 | Manual movement intake | Stock Movement created (WorkForm/board) | TBD (enqueues to A03) | Planned |
| A16 | Low-stock alert | Catalogue `Stock state` → Low / Out | TBD | Planned |
| A17 | Nightly integrity check | Schedule, daily | TBD | Planned |
| A18 | Applied-movement edit guard | Change/archive on an Applied movement | TBD | Planned |

---

*IDs A02 (submit on ✅) and A05 (reopen on un-ticking ✅) were removed on 27 Oct 2026: ✅ Materials complete is a form-only safeguard and no automation depends on it. Remaining IDs are kept unchanged.*

## Entries

### A01 — Material request form
| Field | Value |
|---|---|
| Trigger | Programmer submits the Fillout form |
| Boards / columns | Material Requests: Name, Unit / Project, Needed by, Source file, Programmer; request lines: Name, Product, Qty requested |
| Runtime / ID | Fillout · form ID: TBD |
| Purpose | Create the request (Status = Submitted) and all its lines in one submission |
| Logic | The form requires: Unit / Project (or a Production Calendar job for service jobs), at least 1 line, and the **✅ Materials complete** confirmation. The form won't send without them; this is enforced by the form, not by an automation. On sending: request created with Status **Submitted**, Submitted on = today, ✅ stored as a record; one subitem per material with Product picked from the Catalogue. A missing product is created from the Product connect, so it lands in 🆕 New – needs review. No free text. |
| Depends on | Catalogue, Unit / Project connect; hands off to A04 |
| Status | Planned |
| Notes | **✅ Materials complete is a safeguard only. No automation reads it or triggers on it.** Materials forgotten after sending go on a new request. Confirm Fillout can create a missing connected item from the form; if not, the programmer creates the product on the Catalogue before filling the form. |
| Change log | — |

### A03 — Stock process (single serialized queue)
| Field | Value |
|---|---|
| Trigger | Operation requests from A04, A10, A13, A14, A15. **Nothing else may change stock or reservations.** |
| Boards / columns | Stock Movements: Movement type, Qty, Counted qty, Status, Rejection reason, Qty before, Qty after, Applied at, ⚙️ Applied in → Product, ⚙️ Applied out → Product. Request lines: Qty reserved, Qty to order, Decision. Catalogue: On hand, Reserved, Available (read only), Last purchase price. |
| Runtime / ID | TBD. Make: **one** scenario, sequential processing on, router per operation. Code: a queue with concurrency 1. |
| Purpose | Apply every stock and reservation change one at a time, with validation and an audit trail |
| Operations | `RESERVE` (line, qty ≤ Available) · `RELEASE` (line, qty ≤ line's Qty reserved; when the purchaser releases to order fresh, the released qty is added to Qty to order) · `OPENING` (in) · `RECEIPT` (in; same step adds up to the line's remaining need to Qty reserved, surplus stays free) · `ISSUE` (out; takes from the line's reservation first, then Available; then sets Qty reserved = 0) · `MANUAL_IN` (in) · `MANUAL_OUT` (out; qty ≤ Available) · `STOCK_COUNT` (delta = counted − On hand; reject if counted < Reserved) |
| Apply steps | 1) Skip if the movement is already Applied (idempotent). 2) Validate. 3) Write Qty before = On hand and Qty after. 4) Set the applied link (in or out) and Status = Applied, plus Applied at. 5) **Read-after-write:** re-read On hand until it equals Qty after (retry up to about 10 seconds); on timeout stop the queue and alert. 6) For reserve, release and issue operations, update the line's Qty reserved and Decision. |
| On reject | Status = Rejected and Rejection reason set; no link; notify the creator and inventory owner (and purchaser when reservations are involved, naming the affected projects) |
| Guarantee | Available never goes below 0 |
| Depends on | Mirrors: ⚙️ In total, ⚙️ Out total, Reserved; formulas: On hand, Available |
| Status | Planned |
| Notes | The runtime decision is open. Whatever it is, it must be the only writer of engine fields. Engine columns get locked with column permissions. |
| Change log | — |

### A04 — Auto-reserve on submit
| Field | Value |
|---|---|
| Trigger | A request is created by the form (A01) with Status = Submitted. **Not** the ✅ checkbox. |
| Boards / columns | Request lines: Product, Qty requested, Qty reserved, Qty to order, Decision; Catalogue: Available (read); Material Requests: Status, Purchaser, Inventory owner |
| Runtime / ID | TBD (enqueues `RESERVE` to A03) |
| Purpose | Compare every line with current stock, reserve what's available, and write the rest for ordering |
| Logic | For each line, in order, through A03 (each line sees the reservations made before it, including earlier lines for the same product): **Available ≥ Qty requested** → reserve all, Qty to order = 0, Decision **From Stock**. **0 < Available < Qty requested** → reserve Available, Qty to order = Qty requested − Available, Decision **Partial**. **Available = 0** → reserve nothing, Qty to order = Qty requested, Decision **To Order**. When all lines are done: every line From Stock → request **Ready for Production**, notify the inventory owner; otherwise → **In Review**, send the purchaser a summary (lines and quantities to order). |
| Depends on | A01, A03 |
| Status | Planned |
| Notes | Products in 🆕 New – needs review have Available = 0, so they always go To Order. |
| Change log | — |

### A06 — New product intake
| Field | Value |
|---|---|
| Trigger | Item created in Catalogue group 🆕 New – needs review |
| Boards / columns | Materials Catalogue: Stock type, Default supplier, UoM, Pack size, Last purchase price, Category |
| Runtime / ID | Native monday automation / TBD |
| Purpose | Make sure new products are completed before ordering |
| Logic | Set Stock type = Order-to-project and notify the purchaser. Once supplier, UoM, pack size and category are filled, the purchaser moves it to its category group. |
| Status | Planned |
| Change log | — |

### A07 — PO builder
| Field | Value |
|---|---|
| Trigger | Request Status → Ordering |
| Boards / columns | Request lines: Qty to order, Product, PO line, Decision; Catalogue: Default supplier, Pack size, Last purchase price; Purchase Orders: Supplier, Status, Projects; PO lines: all |
| Runtime / ID | TBD |
| Purpose | Turn uncovered lines into Draft PO lines per supplier |
| Logic | For each line with Qty to order > 0 and no PO line yet: supplier = the product's default supplier (if missing → hold the line and notify the purchaser). Find that supplier's **Draft** PO (any project) or create one. Add a PO line: qty = Qty to order rounded up to full packs, unit price = Last purchase price, Project = the request's project (or the unit's parent), link the request line. Line Decision → Ordered; add the project to the PO's Projects and the PO to the request's Purchase Orders. All lines handled → request **Waiting for Delivery**. |
| Status | Planned |
| Change log | — |

### A08 — PO approval → PDF
| Field | Value |
|---|---|
| Trigger | PO Status → Approved |
| Boards / columns | Purchase Orders: all header fields, PO document; PO lines |
| Runtime / ID | TBD |
| Purpose | Generate the PO document |
| Logic | Render the PDF from Sam's template and attach it to PO document. |
| Status | Blocked – TBD with Sam (sample PO, numbering, approver) |
| Change log | — |

### A09 — PO send to supplier
| Field | Value |
|---|---|
| Trigger | PDF attached on an Approved PO (or a manual "Send" action) |
| Boards / columns | Purchase Orders: Supplier email, PO document, Status, Sent date |
| Runtime / ID | TBD |
| Purpose | Send the PO to the supplier |
| Logic | Email the supplier with the PDF; Status → Sent; Sent date = today. |
| Status | Blocked – TBD with Sam (sent from monday vs by the purchaser) |
| Change log | — |

### A10 — Receipt
| Field | Value |
|---|---|
| Trigger | PO line `Qty received` increases |
| Boards / columns | PO lines: Qty received, Received date, Line status, Product, Project, Request line; Stock Movements; Catalogue: Last purchase price; Purchase Orders: Status |
| Runtime / ID | TBD (enqueues `RECEIPT` to A03) |
| Purpose | Put received goods into stock, reserved for their job |
| Logic | Delta = new − previously received. Create a Receipt movement (Qty = delta, Product, Unit/Project, Request line, PO line). A03 applies it and reserves up to the line's remaining need; the surplus is free. Update Last purchase price = Unit price. Line status → Partially Received or Received; PO status rolls up. If received > ordered, flag it to the purchaser. |
| Depends on | A03, A11 |
| Status | Planned |
| Change log | — |

### A11 — Request readiness
| Field | Value |
|---|---|
| Trigger | Request line Decision or Qty reserved changes |
| Boards / columns | Request lines: Decision, Qty outstanding; Material Requests: Status |
| Runtime / ID | TBD |
| Purpose | Move a request to Ready for Production when everything is covered |
| Logic | A line becomes Received when its Qty outstanding = 0 after receipts. When all lines are From Stock or Received → request **Ready for Production**; notify the inventory owner and production. |
| Status | Planned |
| Change log | — |

### A12 — Production complete → Issue Materials
| Field | Value |
|---|---|
| Trigger | **TBD with Sam**: e.g. Production Calendar Assembly item Done, or a Projects/Units status |
| Boards / columns | Material Requests: Status, Inventory owner; request lines: Qty issued |
| Runtime / ID | TBD |
| Purpose | Start the stock-out step |
| Logic | Request → **Issue Materials**; Qty issued = Qty requested on each line; notify the inventory owner. |
| Status | Blocked – TBD with Sam |
| Notes | Production Calendar's `Project` is a text column. Don't match it to requests by name; the link must be by item ID. |
| Change log | — |

### A13 — Issue materials
| Field | Value |
|---|---|
| Trigger | Request Status → Issuing (set by the inventory owner after correcting Qty issued) |
| Boards / columns | Request lines: Qty issued, Qty reserved, Decision; Stock Movements; Material Requests: Status, Notes |
| Runtime / ID | TBD (enqueues `ISSUE` to A03) |
| Purpose | Take used materials out of stock and close the request |
| Logic | One Issue movement per line (Qty = Qty issued, Unit/Project, Request line). A03 takes from the reservation first, then Available, then sets Qty reserved = 0 (the remainder is released) and Decision = Issued. All Applied → request **Closed**. Any Rejected → request back to Issue Materials with the reason; notify. |
| Depends on | A03 |
| Status | Planned |
| Change log | — |

### A14 — Cancel / hold request
| Field | Value |
|---|---|
| Trigger | Request Status → Cancelled, or → On Hold |
| Boards / columns | Request lines: Qty reserved, Decision; PO lines (read) |
| Runtime / ID | TBD (enqueues `RELEASE` to A03 on cancel) |
| Purpose | Free stock from cancelled jobs |
| Logic | Cancelled → release every line's reservation, Decision = Cancelled; open PO lines are **not** auto-cancelled; notify the purchaser (later receipts for those lines go to free stock). On Hold → keep reservations; notify the purchaser. |
| Status | Planned |
| Change log | — |

### A15 — Manual movement intake
| Field | Value |
|---|---|
| Trigger | Stock Movement created with type Manual in, Manual out or Stock count (WorkForm or board) |
| Boards / columns | Stock Movements: all user fields |
| Runtime / ID | TBD (enqueues `MANUAL_IN` / `MANUAL_OUT` / `STOCK_COUNT` to A03) |
| Purpose | Apply manual changes safely |
| Logic | Validate: Product set; Qty > 0 (or Counted qty ≥ 0 for counts); Reason set for in/out; Note when Reason = Other; **no Unit/Project**. Then A03 applies or rejects. A Manual out or count that would push Available below 0 → Rejected; notify the inventory owner and purchaser. |
| Depends on | A03 |
| Status | Planned |
| Change log | — |

### A16 — Low-stock alert
| Field | Value |
|---|---|
| Trigger | Catalogue `Stock state` changes into Low or Out |
| Boards / columns | Materials Catalogue: Stock state, Available, Minimum level, Default supplier |
| Runtime / ID | TBD |
| Purpose | Prompt replenishment |
| Logic | Notify the purchaser once per crossing. The purchaser adds a replenishment line (no project) to the supplier's Draft PO. |
| Notes | Stock state is a formula; a native "status changes" trigger won't fire on it. A scheduled check or the A03 post-apply step must detect the crossing. |
| Status | Planned |
| Change log | — |

### A17 — Nightly integrity check
| Field | Value |
|---|---|
| Trigger | Daily schedule (night, Sam's time zone) |
| Boards / columns | Stock Movements, request lines, Materials Catalogue |
| Runtime / ID | TBD |
| Purpose | Detect drift or tampering |
| Checks | Every Applied movement has exactly 1 applied link · no Pending or Rejected movement has one · the Qty before/after chain per product is unbroken and ends at On hand · Reserved = sum of open lines' Qty reserved · Available ≥ 0 · no Pending movement older than 15 minutes |
| On failure | Alert Kindaa Support and the inventory owner with details. Never auto-correct. |
| Status | Planned |
| Change log | — |

### A18 — Applied-movement edit guard
| Field | Value |
|---|---|
| Trigger | Any change to Qty, Movement type, Product, Status or the applied links on an Applied movement; or an archive/delete of an Applied movement |
| Boards / columns | Stock Movements |
| Runtime / ID | TBD |
| Purpose | Applied movements are immutable; corrections use a reversing movement |
| Logic | Alert Kindaa Support and the inventory owner with old and new values. Don't silently revert. Column permissions are the first line of defence. |
| Status | Planned |
| Change log | — |

---

## Demo phase

| | |
|---|---|
| Automations active | **None** |
| Integrations active | **None** (Fillout not connected) |
| Make scenarios | **None** |
| Native board automations created | **None** |
