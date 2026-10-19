# Phase 0 findings (read-only): Spot-nik Inventory engine

Run on 2026-10-19. All calls were GraphQL **queries**: no mutation was sent.
Source: account **Ricco cabinetry** (34799434), workspace **Project Manager** (15462830), read as user *Kindaa support* (103186497).
`api.monday.com` is blocked by this container's network policy, so `phase0.py` could not run directly. The same queries went through the monday MCP read-only tool, which rejects mutations before sending them.

## 0. Environment warning
- **No sandbox install exists.** The Kindaa account (18427868) has no Products/Transactions/Stock Updates boards. The only install is in the Ricco cabinetry workspace, next to *Projects*, *Production Calendar* and *Task Manager*. Board owner Sam = sam@riccocabinetry.ca. **This is the client's production install.** `config.json` holds these IDs with `confirmed_by_user: false`, and the client refuses every mutation until that flag is set.
- Writing tests here has side effects beyond test items. See section 5.

## 1. Board / column map (titles → IDs; never hardcoded in tests, resolved via `col_map()`)
| Board | ID | Key columns |
|---|---|---|
| Products | 18427258253 | Current Quantity `numbers03` (numbers) · Minimum Level `dup__of_low_stock_level__1` · Out of stock level `numbers7` · Stock Status `status__1` (0 Low Stock / 1 In Stock / 2 Out Of Stock) · Price per unit `numbers4__1` · Stock Value `numbers0__1` (**plain numbers, not formula**) · Transactions `connect_boards6__1` · Current Quantity Mirror `mirror__1` (mirrors **Transactions.Amount**, i.e. a ledger sum) · Last Updated `last_updated5` · groups MDF `topics`, Kits `group_mkrmbgxg` |
| Transactions | 18427258255 | Transaction Type `status_1` (0 Add to Stock / 1 Take Out of Stock / 6 Entry Stock) · Amount `numbers__1` · Quantity Before `numbers87__1` · Quantity After `numeric_mksv64bk` · Products `link_to_products__1` (single) · Current Quantity mirror `lookup_mkw45cah` · Price Per Unit mirror · Transaction Value formula · Transaction Date `date4` · Transaction Owner `people7` · Stock Update ID `action_id6__1` (text) · Transaction ID (item_id) · Comment · groups Purchase `topics`, Production Form `group_mm6dapdf`, Inventory Adjustment `group_mm6d4z9y` |
| Stock Updates | 18427258261 | Action Owner `people7` · Transaction Date `date4` · Stock Update ID (item_id) · Comment · "Compnay" text · Projects (connect, added 2026-09-03 by Kindaa support) · group Activities `topics` |
| Stock Updates subitems | 18427258274 | Product name `text__1` (text) · Amount `numbers__1` · Quantity Before `amount_insert_to_stock__1` · Quantity After `numeric_mksgyvq7` · Transaction Type `transaction_type9__1` (1 Add / 2 Take Out; **no Entry Stock label**) |
| Products subitems | 18427258269 | Products (connect) · Numbers of items. Out of scope |

Brief vs reality: "Kits" is a **group** on Products. The subitem board is a separate kit-components board.

## 2. Webhooks: which events trigger the engine
| Board | `app_webhooks_only: true` | without flag |
|---|---|---|
| Products | none | `create_item`, `item_archived`, `item_restored`, `item_deleted` (ids 625236924-927) |
| Transactions, Stock Updates, both subitem boards | none | none |

The four Products webhooks belong to native "When an item is …, send a webhook" automations owned by Sam. The endpoint URL isn't readable through the API (config `{}`). Caveat: `app_webhooks_only` only returns webhooks created by the *calling* app, so a webhook belonging to another app would not show. **No webhook fires on Transactions or Stock Updates**, so no external service is listening to transaction creation.

## 3. The engine is board automations, not an app backend
Every automation is a template copy (`duplicateSourceAutomationId`) created 2026-08-19 14:48 and owned by **Sam (102616219)**. Calculations run through a third-party "column calc" app, appId **153189** (`app_recipe`). Activity logs show these writes as **user_id -4** (automation) or as **Sam**.

**Stock Updates board** (UI path)
1. When a subitem is created and Amount > 0, set subitem Type = Add to Stock. If Amount < 0, set it to Take Out of Stock.
2. When subitem Transaction Type changes to *anything*, **create a Transactions item** with: name = subitem name, Type = subitem Type, Stock Update ID = item id, Amount, Date / Owner / Comment from the parent. Group = Purchase. Quantity Before/After are *not* mapped.

**Transactions board** (the real ledger trigger)
3. On item created, **connect to Products where Name = Name** (static recipe 229, "first match", action *append*). **The product is matched by item name.**
4. On item created: Amount > 0 → Type = Add to Stock. Amount < 0 → Type = Take Out of Stock. (This overwrites whatever Type was sent.)
5. When the Products link changes, Quantity Before = cast(mirror Current Quantity).
6. When the Products link changes, Quantity After = mirror Current Quantity + Amount.
7. When Quantity After changes, copy Quantity After → Products.Current Quantity via the link.
8. On item created, set default `numbers6__1 = -1`. That column no longer exists.

**Products board**
9. When Current Quantity changes: Stock Status (In / Low / Out vs Minimum Level and Out of stock level), Stock Value = CQ × Price, Stock Volume (refers to missing columns). Matching "item created" and "Minimum / Out-of-stock level changed" variants exist.
10. When Stock Status changes to Low or Out, **notify all board subscribers**.
11. Two monday-AI "categorize" automations (app 149695) also write Stock Status from Minimum Level, on create and on change.
12. On create: QR code to a file column (`file_mkw0n21g`, which no longer exists) and default values (`numbers68`, which no longer exists).

### Golden run observed (UI Update Stock, 2026-09-03, +2 on "3/4 Plumcreek MDF White Face Down")
| t (s) | Actor | Write |
|---|---|---|
| 0.0 | Kindaa support (UI) | Stock Update item "Update Stock" created (Owner, Date) |
| 2.2 | Kindaa support (UI) | Subitem created: Product name, Amount 2, **Before 0, After 2 computed by the UI** |
| 7.5 | automation (-4) | Subitem Type = Add to Stock |
| 12.7 | automation (-4), creator shows **Sam** | Transactions item created: name, Type, Amount 2, Stock Update ID, Date, Owner |
| 19.2 | automation (-4) | Transaction ↔ Product linked (name match) |
| 24.5 | Sam (calc app) | Transaction Quantity Before 0 / After 2 |
| 28.8 | Sam (calc app) | Product Current Quantity 0 → 2 |
| 32.9-33.8 | Sam (calc app) | Stock Value 0 → 14, Stock Status Out → Low |

End to end ≈ **34 s**. Record counts: Transactions has 5 items, 3 of them template seed data from 2026-08-19 (Stock Update ID 10969229281, dated 2027). Stock Updates has 2 items (1 real, 1 empty "." item).

### Inferred golden format for an API caller (to be confirmed in Phase 1/2)
Create **one Transactions item** where **item name = exact product name**, Amount = **signed** (negative for out), Transaction Date, Owner, and optionally the Products link. The Stock Updates header and subitem are only the UI's input path: they spawn the Transactions item through automation 2.

## 4. Risks in the automation design (not yet tested; each maps to a Phase 2 test)
- **Name-based product match** (3): renamed, duplicated or trailing-space product names give a wrong link or no link, and then no stock change. *Silent.* (2.4, 2.13)
- **Type derived from the Amount sign** (4): "Take Out of Stock" with a positive Amount gets re-typed Add and *increases* stock. *Silent wrong number.* Entry Stock has no logic, so a positive Entry Stock becomes additive Add. Amount 0 gets no type, but the After/CQ copy still runs. (2.5, 2.7, 2.8)
- **Read-modify-write through a mirror** (5-7): After = mirror(CQ) + Amount, written back to CQ. Parallel transactions on one product can read the same CQ, so lost updates are likely. (3.1-3.4)
- **No negative-stock guard** in any automation. (2.6)
- **No trigger on Amount edit or on archive** in Transactions, so edits and archives are probably not reflected. (2.10, 2.11)
- **CQ is incremental, not recomputed from the ledger.** Existing data already drifts:

| Product | Current Quantity | Ledger sum (Current Quantity Mirror) |
|---|---|---|
| 3/4 MDF White Back | 0 | 10 |
| 1-3/4 Paintable tape 1mm | (empty) | -40 |
| New employee kit | 5 | 2 |
| 3/4 Plumcreek MDF White Face Down | 2 | 2 ✓ |

- **Broken automations already failing in production:** 10 of the 62 Products-board runs since 2026-08-15 failed with "The second column wasn't found" (missing volume column) or "Column is empty" ×3, and the AI categorize runs failed with "No results – the provided text is not detailed enough". Two engines (calc app and AI) write Stock Status, so they can conflict.
- **Single point of failure:** every automation runs on Sam's auth (`auth.monday 25949888`). If Sam is deactivated or the calc app is uninstalled, the engine stops.
- A Products-board integration run happened at **2026-10-19 12:25:57 UTC** during this session. It was not caused by us: every call was a read.

## 5. Side effects of any write test on this (production) install
- Low/Out-of-stock **notifications go to all Products board subscribers**, i.e. real client users. Test 2.14 and any drive to 0 will trigger them.
- Creating or archiving `ZZ-TEST-A/B` fires the **create/archive webhooks to an unknown external endpoint** (maybe the client's other integrations).
- Each run uses **automation actions from the client's monthly quota** (≈7-9 actions per transaction).
- The "Current Quantity Mirror" sums and the dashboards (Inventory Administration, Warehouse) will show test rows until they are archived.
- Phase 2/3 writes would have to go through the monday MCP write tool (since `api.monday.com` is blocked here), unless you allow `api.monday.com` in the environment's network settings. With MCP, the Python prefix guard can't sit in the transport path, so I'd apply the same checks by hand before every call. Allowing the host is the safer option.
