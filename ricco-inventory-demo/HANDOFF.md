# Handoff — Ricco Cabinetry · Inventory & Procurement Demo

*Built 2026-10-28 by Claude Code through the monday API (proxy-injected credential, API version 2026-10, acting user Kindaa Support 103186497, account 34799434). No automations, integrations, webhooks or Make scenarios were created. Every write is in `BUILD-LOG.md` and `logs/write-log.jsonl`.*

## 1. What exists

| Object | ID |
|---|---|
| Folder `Inventory & Procurement (Demo)` | 21780002 |
| Suppliers | 18437453018 |
| Materials Catalogue | 18437453024 |
| Material Requests | 18437453027 |
| ↳ Request lines (subitems) | 18437453414 |
| Purchase Orders | 18437453028 |
| ↳ PO lines (subitems) | 18437453449 |
| Stock Movements | 18437453030 |
| Dashboard `Procurement Overview (Demo)` | 40200086 (widgets: Requests by status 732648339, Open POs by supplier 732648364, Spend by supplier 732648385, Material cost per project 732648406, Stock value 732648409) |
| WorkForm `Manual stock update` | form view 288954194 on Stock Movements |
| Table views | Stock Movements: Rejected & pending 288954103, Ledger 288954126, By product 288954129 · Catalogue: Low & out 288954133, Reserved vs available 288954147 · POs: By supplier 288954135, Overdue deliveries 288954136 |

Full title → column ID maps: `data/column-map.json`. Item IDs for every sample record (S1–S4, P01–P15, SM-01…SM-23, MR-1…MR-5 and their lines, PO-0001…PO-0005 and their lines): `data/id-map.json` → `items`.

**Sam's boards — what changed** (only these; checked against `snapshots/pre-build.json`, final state in `snapshots/post-phase-6.json`):

| Board | Column | ID | Origin |
|---|---|---|---|
| Projects | Material Requests (reflection) | `board_relation_mm8jqhv4` | Omer's `Project \ Unit` connect on Material Requests; renamed by the build |
| Projects | PO lines (reflection) | `board_relation_mm8jbv88` | Omer's `Project \ Unit` connect on PO lines; renamed |
| Projects | Material cost (mirror, sum) | `lookup_mm8jr37y` | Phase 6 |
| Projects | Request status (mirror, all statuses) | `lookup_mm8j7963` | Phase 6 |
| Projects | Units material cost (mirror of Units Material cost, sum) | `lookup_mm8jvw8q` | Phase 6 |
| Projects | PO status (mirror of PO lines' Line status) | `lookup_mm8jn862` | Phase 6 |
| Units | Material Requests (reflection) | `board_relation_mm8j9wgg` | Omer's connect; renamed |
| Units | PO lines (reflection) | `board_relation_mm8jxknn` | Omer's connect; renamed |
| Units | Material cost (mirror, sum) | `lookup_mm8j6ayp` | Phase 6 |
| Units | Request status (mirror, all statuses) | `lookup_mm8jz4rt` | Phase 6 |
| Projects | ~~link to Stock Updates~~ `board_relation_mm6vdxt9` | — | **Deleted in the UI by the Kindaa Support account, 2026-10-28 11:03 UTC** (activity log), not by the build |

Real items linked by the sample data: Sal Fabbri `12644564714` / Laundry Room `12644695770`, Rivanti `12188627230` / Wall Panel `12188559043`, Menatwork 139 Hamilton `12738591802` / Kitchen `12882328030`.

## 2. §9.7 verification (MR-6 excluded, D-08)

`data/verification-phase7.json`: **89 checks, 0 mismatches.**

| Area | Result | How it was read |
|---|---|---|
| Catalogue P01–P15: On hand / Available / Stock state | all match | API (formulas) |
| Catalogue Reserved | all match (P04 = 8, P07 = 70 after removing MR-6) | derived: On hand − Available |
| Material cost MR-1…MR-5 (2,573 / 2,700 / 3,880 / 1,769 / 5,148) | all match | derived: Σ line `Line cost` (the mirror itself isn't API-readable) |
| PO Subtotal / Total / Delivery state (PO-0003 Overdue) | all match | Total and Delivery state from the API; Subtotal = Total − Tax |
| Supplier Total ordered (6,800 / 235 / 1,185 / 552) | all match | derived: Σ PO Totals (the mirror isn't API-readable) |
| Stock value (demo items) | 21,399.00 | API (formula) |

**UI check still needed** (the API can't read mirrors of formulas or mirror chains):
- Projects → Sal Fabbri: Material cost **2,573**, Units material cost **1,769**
- Projects → Rivanti: Units material cost **2,700**
- Projects → Menatwork 139 Hamilton: Material cost **5,148**, Units material cost **3,880**
- Suppliers → Total ordered; Material Requests → Material cost; request lines → On hand / Available (display only)

## 3. Deviations — `DEVIATIONS.md`

D-01 API through the proxy-injected credential (approved) · D-02 repo subfolder · D-03 test boards (superseded; Omer deleted them) · D-04 bootstrap items (parked, then deleted with the test folder) · D-05 column positions · D-06 Omer's `Project \ Unit` connects replace `Unit / Project`, `Production Calendar job` and the PO line `Project` · D-07 no PO header `Projects`; #9 mirrors PO line status · D-08 MR-6 dropped.

Also changed by Omer in the UI and kept: Request lines `Line cost` → `formula_mm8jjeek`, PO lines `Line total` → `formula_mm8j7946` (mirrors re-pointed); Catalogue `PO Line` + `Average Unit Price`; subitems columns on Suppliers / Catalogue / Stock Movements; `zz-unused` columns deleted.

## 4. Manual steps — `MANUAL-STEPS.md`

| # | What |
|---|---|
| M1 / M2 | Kanban "By status" views on Material Requests and Purchase Orders |
| M3 | WorkForm: make **Product** visible and required; Status default **Pending**; (optional) hide the Opening / Receipt / Issue labels |
| M4 | Check that dashboard widgets 2 and 4 group by Supplier; add the widget 2 filter (not Received / Closed / Cancelled) |
| M6 | Hide ⚙️ columns on the default Main Table (Catalogue, Stock Movements); expand subitems on the Requests Main Table |
| M7 | Sort "Reserved vs available" by Reserved ↓ |
| M8 | Dashboard table widgets 3 (Overdue deliveries) and 6 (Low & out stock) |

## 5. Items to clean up

`ZZ-TEST-` items created by the build (all on demo boards):

| Item | ID | Board |
|---|---|---|
| ZZ-TEST-Supplier | 13404488723 | Suppliers |
| ZZ-TEST-Product | 13404488615 | Materials Catalogue |
| ZZ-TEST-Opening in | 13404488795 | Stock Movements |
| ZZ-TEST-Manual out | 13404494207 | Stock Movements |
| ZZ-TEST-PO | 13404452029 | Purchase Orders |
| ZZ-TEST-PO line | 13404493210 | PO lines |
| ZZ-TEST-Request | 13404448702 | Material Requests |
| ZZ-TEST-Line A | 13404451993 | Request lines |
| ZZ-TEST-Line B | 13404462767 | Request lines |

Items on the demo boards that weren't created by the build: `.` (Suppliers 13404358218, Catalogue 13404393020, Requests 13404361009, POs 13404357745, Request lines 13404383068, PO lines 13404413739), `2` (POs 13404357962), `1` (Movements 13404426554), `ZZ-TEST-Request (copy)` 13404494829 with 2 lines, `ZZ-TEST-PO (copy)` 13404497478.

All of these appear in the dashboard and take Request # / PO # / Movement # numbers ahead of the DEMO items: auto numbers aren't API-readable, so check them in the UI after cleanup.

## 6. Walkthrough notes (spec §12)

- Step 1 (MR-6 service job) is out of the demo; start with MR-5.
- Step 3: PO-0003 has the mock PDF in `PO document`.
- Step 10: Projects show Material cost, Units material cost, Request status and PO status (the PO status comes from PO line statuses).
