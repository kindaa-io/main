# Elevation Phase 2: Prompt 0 scan report

**Workspace:** 13463480 (Elevation - CRM), account 183643 Elevation Academy · **Scan date:** 21 Oct 2026 · **Mode:** read-only (only GraphQL `query` calls; the helper scripts refuse any request containing `mutation`). Nothing in the account was changed.

**Status:** the column plan in this report includes the decisions made in chat on 21 Oct (see "Decisions applied"). No execution phase (§6) has started.

### How the scan was done
- **monday.com:** the monday MCP server **failed to connect** (proxy tunnel 403). All reads went through the session's proxy-authenticated monday GraphQL API (`api.monday.com/v2`, API-Version 2025-04), signed in as *Kindaa support* (user 111441380). All six boards were readable.
- **Make: NOT CHECKED.** No Make MCP was connected, and the Make REST API (`eu2.make.com`) returned 401 on every endpoint. No scenario blueprints were searched for column or board IDs, so every "no dependents" below means *no monday-side dependents*.
- **Items:** every item on Opportunity, Line items, Catalog, Projects and Accounts was fetched with full `items_page` pagination (no sampling). **Cohorts item data was NOT counted:** the board errors on whole-row reads ("upstream request failed"), and the column-by-column fallback was stopped at the user's request. Cohorts *column definitions* were fully read.
- **Dependents:** formula `{id}` references, mirror sources and relation columns were parsed for all 50 boards in the workspace. Webhooks were read for every board. View filters and sorts are **not exposed** by the API (every view returns `settings_str = {}`), and native automations have no API, so both are on the UI-check list.


## Access check

| Board | ID | Read OK | Items (paginated, all) | Columns |
|---|---|---|---|---|
| Opportunity | 18390568735 | ✅ | 1233 | 165 |
| Line items | 18390568739 | ✅ | 1 | 27 |
| Catalog | 18433874513 | ✅ | 34 | 44 |
| Cohorts | 18403700733 | ✅ | 350 (values not counted) | 171 |
| Projects | 18390568732 | ✅ | 494 | 67 |
| Accounts | 18390568736 | ✅ | 5374 | 28 |

All six boards are active and in workspace 13463480. **Cohorts: 350 items, values not counted.** The line-items board holds **one** item, and it is test data (see Test data).

## Counts by action

| Board | KEEP | RENAME | REPURPOSE | CONVERT | CREATE | DELETE | UPDATE | LEAVE | ASK | NOT FOUND |
|---|---|---|---|---|---|---|---|---|---|---|
| ⚙️ Pricing Parameters (new board) | 0 | 0 | 0 | 0 | 41 | 0 | 0 | 0 | 0 | 0 |
| Opportunity (18390568735) | 15 | 3 | 11 | 0 | 68 | 2 | 0 | 2 | 0 | 1 |
| Line items (18390568739) | 10 | 3 | 6 | 3 | 21 | 3 | 2 | 2 | 0 | 1 |
| Catalog (18433874513) | 5 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 2 |
| Cohorts (18403700733) | 4 | 0 | 0 | 0 | 14 | 1 | 0 | 0 | 0 | 0 |
| Projects (18390568732) | 2 | 1 | 8 | 0 | 1 | 0 | 0 | 2 | 0 | 0 |

Counts are after the 21-Oct decisions. Opportunity CREATE includes the 38 `opm_*` mirrors. "NOT FOUND" means a pack ID that doesn't exist live (nothing to do). UPDATE = formula change on an existing formula column.

## Discrepancies: live account vs build pack

| # | Board | Pack says | Live account |
|---|---|---|---|
| 1 | Opportunity | `formula_mm884cg8` ⚙️Line Items Count exists → RENAME | Doesn't exist anywhere in the workspace. Nothing counts line items. → CREATE (decided) |
| 2 | Opportunity | `color_mm885xtx` "I approve" → DELETE | Doesn't exist. Nothing to delete |
| 3 | Opportunity | Branding Setup may be a status | `opp_branding_setup` is a **checkbox**. There's also a status `opp_branding_level` (Low/High) the pack doesn't mention |
| 4 | Opportunity | Customer Management = `color_mm88m6bm` | Two columns: `color_mm88m6bm` (Low/High) **and** checkbox `opp_customer_mgmt` ("Checked by default"), which the pack doesn't mention |
| 5 | Opportunity | Content Dev Live/Self → CREATE | Already exist: `opp_cd_live_hours`, `opp_cd_self_hours` ("RR Content Dev – …") → RENAME |
| 6 | Opportunity | `op_sum_pm/_ops/_car/_auto/_des` → CREATE | Placeholder Σ mirrors already exist (`lookup_mm89667w`, `…s51s`, `…k0tq`, `…ydqn`, `…qv7b`) → REPURPOSE (approved) |
| 7 | Opportunity | `opp_expert_hours` → KEEP | It sums `li_expert_hours`, a **mirror** due for deletion → must be re-pointed (approved) |
| 8 | Opportunity | `opp_cohort_months` → rename + re-point | It already sums weeks × quantity (`li_cohort_months` = `{li_months}*{li_qty}`) → rename only |
| 9 | Opportunity | Admission/Marketing data needs migration | 67 Admission and 36 Marketing deals are "Yes" with **no level**. All level columns are empty on all 1,233 deals |
| 10 | Opportunity | (implied) test data = Kindaa-created | **1,220 of 1,233 deals were created by the Kindaa support user on 2026-08-27** (HubSpot import). That's real data, so creator can't be used as a test marker |
| 11 | Line items | Spec custom IDs `li_quantity`, `li_parent`, `li_placement`, `li_weeks`, `li_ls_hours`, `li_backoffice`, `li_expert_hours` | Live: `li_qty`, `li_parent_opp`, `li_placements`, `li_months`; **no** `li_ls_hours` or `li_backoffice` (the LS and Back Office mirrors are `li_total_hours` and `li_bo_hours`) |
| 12 | Line items | `li_total_hours` = Total Training Hours / Cohort (mirror of Live+Self) | `li_total_hours` is the **LS-hours mirror** (of `cat_ls_hours`, title "NUMBERS Learning Service Hours"). No total-training-hours mirror exists → CREATE one with a new ID |
| 13 | Line items | `li_placement_pct` exists → KEEP | **Doesn't exist** → CREATE |
| 14 | Line items | LS Base / Expert / Back Office may already be Numbers (meeting 42:04) | All three are **still mirrors** (titles start with "NUMBERS", but the type is mirror) → CONVERT |
| 15 | Line items | "Training Months" has test values to clear | `li_months` is already titled "CATALOG Training Weeks"; the only item has no value → rename only |
| 16 | Line items | "Cohort Months" formula needs a new formula | `li_cohort_months` "Cohort-Weeks Total" already = weeks × quantity → rename only |
| 17 | Line items | PM/OPS/Career/Automation/Design totals and LS line → CREATE | Placeholder formulas exist (`formula_mm89*`, all `"0"`) → REPURPOSE (approved) |
| 18 | Line items | `li_ready` is a standalone formula | `li_ready` = `IF({li_check}="Complete",1,0)`: it depends on the helper `li_check` and returns 1/0, not ✅ |
| 19 | Line items | Default Owner/Status/Date columns → DELETE candidates | Not present |
| 20 | Catalog | `cat_ls_hours` holds values 58/34 that Nofar can edit | It's a **formula** `IF(level=High,58,IF(level=Low,34,0))`. Changing it to 28/4 means editing the formula. **`cat_ls_level` is empty on all 34 products**, so LS/Expert hours show 0 everywhere |
| 21 | Catalog | `numeric_mm882ygh`, `numeric_mm88zbdm` (PM Hours, dup.) → DELETE | Don't exist |
| 22 | Catalog | Training Weeks may exist | No Number column. An unfinished `formula_mm8adqz8` "Training week # (Formula)" has an empty formula → new Number column (decided) |
| 23 | Catalog | Training Hour Rate: "Nofar fills empty values" | The rate (`numeric_mm7tp9h8`) **and** Back office H (`numeric_mm7t4zmq`) are empty on **all 34** products |
| 24 | Projects | Total Contract Value, Number of Cohorts, Total Participants → CREATE | All exist: `prj_deal_amount` (Σ deal_value), `lookup_mm8825n1` and `lookup_mm88t3m5`. The last two mirror a mirror and show blank on all 494 projects → RENAME / re-point |
| 25 | Projects | 8 broken mirrors | Confirmed. They display non-existent Opportunity IDs (`opp_pm_hours_b`, `opp_ops_hours_b`, `opp_ls_hours_b`, `<opp_career_total>`, `<opp_automation_total>`, `<opp_design_total>`, `<opp_pricelist_total>`, `<opp_cogs_total>`). Empty on all 494 |
| 26 | Workspace | — | No ⚙️ Pricing Parameters or Cost Rates board exists |


## Phase 1 blockers and open decisions

**Phase 1 (create the Pricing Parameters board): nothing blocks it** once this plan is approved. The board doesn't exist, and nothing depends on it yet.

Open items for later phases (they don't block Phase 1):
1. **Marketing hours (Phase 2–3):** with "Marketing = budget only", should the §2.1 Marketing & Branding Setup hours (`prm_mkt_*`, used in PM/OPS per cohort) still be created, and what drives them (`opp_mkt_level`?), or are they dropped? Until this is answered, the rates exclude Marketing.
2. **Admission "No" (Phase 3):** the formula assumes the existing label "No" means the same as the new "Not Sold". Please confirm.
3. **Make (Phases 2, 8, 9):** blueprints not checked. Before any delete or label change, search the scenarios for the IDs on the UI-check list. Two Opportunity webhooks (create_item; Deal Stage = Closed Won) are probably Make and are where M1/M3 will plug in.
4. **Catalog data (Phase 4 test):** `cat_ls_level`, the hourly rate and Back office H are empty on all 34 products, so every line item will read "not ready" until Nofar fills them.
5. **Cohorts `co_months` (Phase 8):** delete approved on condition. Count and back it up first.
6. **API capability (Phases 3–7):** re-pointing a mirror and editing a formula both need `update_column` (or the UI). Check this on one throwaway column first. If the API can't re-point mirrors, the re-points become UI steps.

### Decisions applied (chat, 21 Oct)
- **Admission:** add the new label **"Not Sold"** to `color_mm66cssh` (keep No/Yes). Level stays in `opp_admission_level`. Logic: Low/High = sold, unless the flag says Not Sold; "Yes" with no level = Low.
- **Marketing:** budget column (`opp_mkt_budget`) only. `color_mm66x3y2` isn't changed.
- **Ongoing / Customer Management:** add "Not Sold" to `opp_support_level` and `color_mm88m6bm`. Formulas read these columns (empty = Low).
- **Kept (no delete):** `opp_admission_level`, `opp_mkt_level`, `opp_branding_level`, `opp_customer_mgmt`, `boolean_mm88cbqy`.
- **Deleted (approved):** `color_mm886byb`, `lookup_mm894g60`, `li_total_hours`, `li_expert_hours`, `li_bo_hours`, `co_months` (conditional).
- **Created (decided):** Line Items Count (+ line-item counter), a Catalog Training Weeks Number, Projects Total Expert Hours.
- **Repurposes:** all others approved as listed.


## Per-board mapping (logical key → live column)

Data = non-empty items / all items (formulas and mirrors count their displayed value). `pack:` shows the pack's action where the scan proposes a different one.


### ⚙️ Pricing Parameters (new board)

All 41 entries are CREATE: the board, `prm_status`, `prm_effective` and the 38 number columns from §3.1. No such board exists in the workspace. Full list in `column-map.json`.


### Opportunity (18390568735)

The 38 `opm_*` mirrors (all CREATE via `op_prm_version`) are listed in `column-map.json` and left out of this table.

| Key | Live ID | Live title [type] | Action | Data | Dependents | Notes |
|---|---|---|---|---|---|---|
| `op_prm_version` | — | — | CREATE | — | — | Target board does not exist yet (Phase 1). |
| `op_admission` | `color_mm66cssh` | Screening/Admission? [status] | REPURPOSE (pack: REPURPOSE (Not Sold / Low Touch / High Touch)) | 142/1233 | none found | DECIDED 21-Oct: add a NEW label 'Not Sold' (new index). Keep 'No' (idx 0) and 'Yes' (idx 1) unchanged; no merge, no data migration. Formula logic: Not Sold if this column = 'Not Sold' (assumed also 'No'); else High if opp_admission_level = High; else Low if opp_admission_level = Low, or if this column = 'Yes' with no level; else (both empty) Not Sold. |
| `op_admission_level` | `opp_admission_level` | Admission Level [status] | KEEP (pack: DELETE after migration) | 0/1233 | none found | DECIDED 21-Oct: KEEP. This is the level source for Admission (Low/High). Empty on all 1,233 items. |
| `op_marketing` | `color_mm66x3y2` | Marketing? [status] | KEEP (pack: REPURPOSE) | 142/1233 | none found | DECIDED 21-Oct: Marketing is captured by the budget column only. This status is not changed. |
| `op_mkt_budget` | `opp_mkt_budget` | Marketing Budget (₪) [numbers] | KEEP (pack: (not in pack)) | 0/1233 | Projects:`prj_mkt_budget` (mirror) | DECIDED 21-Oct: the only Marketing input. Mirrored by Projects prj_mkt_budget. |
| `op_mkt_level` | `opp_mkt_level` | Marketing Level [status] | KEEP (pack: DELETE after migration) | 0/1233 | none found | DECIDED 21-Oct: KEEP (not deleted). OPEN: whether Marketing setup hours (prm_mkt_*) still apply and read this level, or are dropped because Marketing = budget only. |
| `op_ongoing` | `opp_support_level` | Ongoing Course Support Level [status] | REPURPOSE | 0/1233 | none found | Found by title 'Ongoing Course Support Level' (custom ID opp_support_level), labels {0:Low,1:High}. Add NEW label 'Not Sold'. Formulas read this column: Low/High = sold, Not Sold = 0, empty = Low (decision 21-Oct). The checkbox boolean_mm88cbqy is kept but not read. |
| `op_cust_mgmt` | `color_mm88m6bm` | Customer Management Level [status] | REPURPOSE | 0/1233 | none found | Labels {0:Low,1:High}. Add NEW label 'Not Sold'. Formulas read this column: Low/High = sold, Not Sold = 0, empty = Low. The checkbox opp_customer_mgmt is kept but not read. |
| `op_website` | — | — | CREATE (pack: VERIFY / CREATE) | — | — | No website column found on Opportunity. |
| `op_branding` | `opp_branding_setup` | Branding Setup [checkbox] | KEEP (pack: VERIFY (repurpose if status)) | 0/1233 | none found | Existing 'Branding Setup' is a CHECKBOX, so per pack: don't convert, formula reads the checkbox. Optional RENAME to 'Branding'. Separate status opp_branding_level (Low/High) is not in the target schema (D2) -> see unmatched list. |
| `op_event_level` | `opp_event_level` | Event Level [status] | KEEP (pack: VERIFY / KEEP) | 0/1233 | none found | Labels {0:Low,1:High} |
| `op_events_n` | `opp_events` | Number of Events [numbers] | KEEP (pack: VERIFY / KEEP) | 0/1233 | none found |  |
| `op_learning_manual` | `opp_learning_manual` | Learning Hours – Manual [numbers] | KEEP (pack: VERIFY / KEEP) | 0/1233 | none found |  |
| `op_dev_live` | `opp_cd_live_hours` | RR Content Dev – Live Hours [numbers] | RENAME (pack: CREATE (unless found)) | 0/1233 | none found | Found: 'RR Content Dev – Live Hours'. |
| `op_dev_self` | `opp_cd_self_hours` | RR Content Dev – Self Hours [numbers] | RENAME (pack: CREATE (unless found)) | 0/1233 | none found | Found: 'RR Content Dev – Self Hours'. |
| `op_cm_weeks` | — | — | CREATE (pack: CREATE (pending Q1)) | — | — |  |
| `op_margin` | `opp_margin` | Margin % [numbers] | KEEP | 0/1233 | Projects:`prj_margin` (mirror) | Unit %. Description already says 'Default 40'. |
| `op_r_pm_cohort` | — | — | CREATE | — | — |  |
| `op_r_ops_cohort` | — | — | CREATE | — | — |  |
| `op_r_pm_week` | — | — | CREATE | — | — |  |
| `op_r_ops_week` | — | — | CREATE | — | — |  |
| `op_r_car_cohort` | — | — | CREATE | — | — |  |
| `op_r_car_week` | — | — | CREATE | — | — |  |
| `op_r_auto_cohort` | — | — | CREATE | — | — |  |
| `op_r_des_cohort` | — | — | CREATE | — | — |  |
| `op_r_ls_per_cohort` | — | — | CREATE | — | — |  |
| `opp_cohorts` | `opp_cohorts` | Number of Cohorts [mirror] | KEEP | 1/1233 | Projects:`lookup_mm8825n1` (mirror) | Σ li_qty via subitems |
| `opp_li_ready` | `opp_li_ready` | ⚙️Line Items Ready [mirror] | KEEP | 0/1233 | none found | Σ li_ready (li_ready returns 1/0, not ✅). |
| `opp_verticals` | `opp_verticals` | Verticals [mirror] | KEEP | 1/1233 | none found |  |
| `opp_expert_hours` | `opp_expert_hours` | Total Expert Hours [mirror] | REPURPOSE (pack: KEEP) | 0/1233 | none found | Currently Σ li_expert_hours, which is itself a MIRROR (old version, to be deleted). Must be re-pointed to the new li_expert Number column before the old mirror is deleted. |
| `opp_participants` | `opp_participants` | Total Participants [mirror] | REPURPOSE | 0/1233 | Projects:`lookup_mm88t3m5` (mirror) | Currently Σ li_participants -> re-point to li_part_t. |
| `opp_cohort_months` | `opp_cohort_months` | Total Cohort-Months [mirror] | RENAME (pack: RENAME + re-point) | 0/1233 | none found | Currently Σ li_cohort_months, whose formula is already {li_months}*{li_qty} (weeks × qty). If li_weeks_t = li_cohort_months (see line items) no re-point is needed: rename only. ID keeps 'months' in its name but holds weeks. |
| `lookup_mm88cm47` | `lookup_mm88cm47` | Learning Services Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/1233 | none found | Currently Σ li_total_hours (= mirror of cat_ls_hours). Re-point to li_ls_line. |
| `op_sum_pm` | `lookup_mm89667w` | PM [mirror] | REPURPOSE (pack: CREATE) | 0/1233 | none found | Placeholder Σ mirror already exists (lookup_mm89667w) summing a line-item placeholder formula that is '0'. Proposed: re-point to li_pm_t instead of creating a new column. Needs approval (deviates from pack). |
| `op_sum_ops` | `lookup_mm89s51s` | OPS [mirror] | REPURPOSE (pack: CREATE) | 0/1233 | none found | Placeholder Σ mirror already exists (lookup_mm89s51s) summing a line-item placeholder formula that is '0'. Proposed: re-point to li_ops_t instead of creating a new column. Needs approval (deviates from pack). |
| `op_sum_car` | `lookup_mm89k0tq` | Career [mirror] | REPURPOSE (pack: CREATE) | 0/1233 | none found | Placeholder Σ mirror already exists (lookup_mm89k0tq) summing a line-item placeholder formula that is '0'. Proposed: re-point to li_car_t instead of creating a new column. Needs approval (deviates from pack). |
| `op_sum_auto` | `lookup_mm89ydqn` | Automation [mirror] | REPURPOSE (pack: CREATE) | 0/1233 | none found | Placeholder Σ mirror already exists (lookup_mm89ydqn) summing a line-item placeholder formula that is '0'. Proposed: re-point to li_auto_t instead of creating a new column. Needs approval (deviates from pack). |
| `op_sum_des` | `lookup_mm89qv7b` | Design [mirror] | REPURPOSE (pack: CREATE) | 0/1233 | none found | Placeholder Σ mirror already exists (lookup_mm89qv7b) summing a line-item placeholder formula that is '0'. Proposed: re-point to li_des_t instead of creating a new column. Needs approval (deviates from pack). |
| `op_sum_bo` | — | — | CREATE | — | — |  |
| `op_sum_live` | — | — | CREATE | — | — |  |
| `op_sum_self` | — | — | CREATE | — | — |  |
| `op_sum_trn` | — | — | CREATE | — | — |  |
| `op_ev_pm` | — | — | CREATE | — | — |  |
| `op_ev_ops` | — | — | CREATE | — | — |  |
| `op_cm_pm` | — | — | CREATE | — | — |  |
| `op_cm_ops` | — | — | CREATE | — | — |  |
| `op_tot_pm` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_ops` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_learning` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_expert` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_career` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_auto` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_tot_design` | — | — | CREATE | — | — | Confirmed: the D1 formulas never existed (Projects mirrors point to non-existent opp_pm_hours_b, opp_ops_hours_b, opp_ls_hours_b, <opp_career_total>, …). |
| `op_n_cohorts` | — | — | CREATE | — | — |  |
| `op_n_participants` | — | — | CREATE | — | — |  |
| `line_items_count` | — | — | CREATE (pack: RENAME formula_mm884cg8) | — | — | formula_mm884cg8 does not exist on any board in the workspace. Nothing counts line items today. M3's gate ('every li_ready = ✅') needs a count to compare against Σ li_ready. Note: a formula can't count subitems; needs a Σ mirror of a constant-1 formula on the line item. DECIDED 21-Oct: create it as a Σ mirror of line-item li_one (formula = 1). |
| `i_approve` | — | — | NOT FOUND (pack: DELETE color_mm885xtx) | — | — | color_mm885xtx does not exist. Nothing to delete. |
| `opp_ls_level_old` | `color_mm886byb` | Learning Services Level [status] | DELETE | 0/1233 | none found | APPROVED 21-Oct. Level lives in Catalog. Empty, no column dependents. |
| `opp_ongoing_checkbox` | `boolean_mm88cbqy` | Ongoing Course Support [checkbox] | KEEP (pack: DELETE) | 0/1233 | none found | DECIDED 21-Oct: KEEP. Not read by formulas. Empty on all items. |
| `opp_customer_mgmt_checkbox` | `opp_customer_mgmt` | Customer Management [checkbox] | KEEP (pack: (not in pack)) | 1/1233 | none found | DECIDED 21-Oct: KEEP. Not read by formulas. |
| `opp_branding_level` | `opp_branding_level` | Branding Level [status] | KEEP (pack: (not in pack)) | 0/1233 | none found | DECIDED 21-Oct: KEEP. Not read by formulas (D2: Branding is single option via opp_branding_setup). |
| `nofar_pricelist_sum` | `lookup_mm896pxy` | Price List [mirror] | LEAVE (pack: Nofar) | 0/1233 | none found | Σ of line-item placeholder formula_mm89j9nx ('0'). Leave for Nofar. |
| `nofar_cogs_sum` | `lookup_mm893200` | COGS [mirror] | LEAVE (pack: Nofar) | 0/1233 | none found | Σ of line-item placeholder formula_mm898xd6 ('0'). Leave for Nofar. |
| `opp_learning_sum_placeholder` | `lookup_mm894g60` | Learning [mirror] | DELETE (pack: (not in pack)) | 0/1233 | none found | DECIDED 21-Oct: DELETE. Σ of placeholder formula_mm89sm5r; duplicates lookup_mm88cm47 once that is re-pointed to li_ls_line. Empty, no dependents. Delete AFTER formula_mm89sm5r is repurposed (it is this mirror's source). |

### Line items (18390568739)

| Key | Live ID | Live title [type] | Action | Data | Dependents | Notes |
|---|---|---|---|---|---|---|
| `li_catalog` | `li_catalog_item` | Catalog Item [board_relation] | KEEP | 1/1 (test 1) | Subitems of Opportunity:`li_ls_level` (mirror relation); Subitems of Opportunity:`li_live_hours` (mirror relation); Subitems of Opportunity:`li_self_hours` (mirror relation); Subitems of Opportunity:`li_bo_hours` (mirror relation); Subitems of Opportunity:`li_expert_hours` (mirror relation); Subitems of Opportunity:`li_total_hours` (mirror relation); +2 more | Custom ID differs from spec (li_catalog_item). |
| `li_parent` | `li_parent_opp` | ⚙️Parent Opportunity [board_relation] | KEEP (pack: KEEP/VERIFY) | 0/1 | none found | Custom ID li_parent_opp. Connect -> Opportunity, single item. Empty on the only line item (M2 not live). |
| `li_quantity` | `li_qty` | Quantity (Cohorts) [numbers] | KEEP | 1/1 (test 1) | Cohorts:`lookup_mm88v28p` (mirror); Subitems of Opportunity:`li_cohort_months` (formula); Subitems of Opportunity:`li_check` (formula); Opportunity:`opp_cohorts` (mirror) | Custom ID li_qty; live title 'Quantity (Cohorts)'. |
| `li_participants` | `li_participants` | Participants [numbers] | RENAME (pack: KEEP (rename)) | 0/1 | Subitems of Opportunity:`li_check` (formula); Opportunity:`opp_participants` (mirror) |  |
| `li_rate` | `li_rate` | Training Hour Rate (₪) [numbers] | KEEP | 1/1 (test 1) | none found | Live title 'Training Hour Rate (₪)', ₪ unit. Catalog source (numeric_mm7tp9h8) is empty on all 34 products. |
| `li_weeks` | `li_months` | CATALOG Training Weeks [numbers] | RENAME (pack: REPURPOSE 'Training Months') | 0/1 | Subitems of Opportunity:`li_cohort_months` (formula); Subitems of Opportunity:`li_check` (formula) | Live title is already 'CATALOG Training Weeks' (weeks), so only the 'CATALOG ' prefix goes. The only line item has no value: nothing to clear or convert. ID li_months holds WEEKS. |
| `li_pweeks` | — | — | CREATE (pack: CREATE (or repurpose empty number)) | — | — | No spare Number column on the board: the 4 number columns are all in use. |
| `li_placement` | `li_placements` | Includes Placements [checkbox] | KEEP | 1/1 (test 1) | none found | Custom ID li_placements; title 'Includes Placements'. |
| `li_placement_pct` | — | — | CREATE (pack: KEEP) | — | — | DOES NOT EXIST on line items. Must be created (Cohorts mirror depends on it). |
| `li_ls_level` | `li_ls_level` | Learning Services Level [mirror] | KEEP | 0/1 | none found | Mirror of cat_ls_level. Catalog value is empty for all 34 products. |
| `li_live` | `li_live_hours` | Live Training Hours [mirror] | KEEP | 1/1 (test 1) | none found | Mirror of Catalog numeric_mm7tv0sp. |
| `li_self` | `li_self_hours` | Self Training Hours [mirror] | KEEP | 1/1 (test 1), non-zero 0 | none found | Mirror of Catalog numeric_mm7t38zg. |
| `li_vertical` | `li_vertical` | Vertical [mirror] | KEEP | 1/1 (test 1) | Opportunity:`opp_verticals` (mirror) |  |
| `li_content_status` | `li_content_status` | Content Status [mirror] | KEEP | 1/1 (test 1) | none found |  |
| `li_total_hours` | — | — | CREATE (pack: RENAME li_total_hours) | — | — | MISMATCH: the column with ID li_total_hours is a mirror of cat_ls_hours (title 'NUMBERS Learning Service Hours'). It is the LS mirror, not total training hours. No Live+Self total mirror exists. Create a mirror of Catalog numeric_mm7thk2x 'Total Hours (Live & Self)'. |
| `li_ls_base` | — | — | CONVERT (pack: CONVERT from li_ls_hours (or RENAME)) | — | — | The source is li_total_hours (there is no li_ls_hours). Still a MIRROR (of cat_ls_hours), not converted to Number. Data to copy: 1 item, empty value. |
| `li_expert` | — | — | CONVERT (pack: CONVERT from li_expert_hours (or RENAME)) | — | — | li_expert_hours is still a MIRROR (of cat_expert_hours). Data: empty. |
| `li_bo` | — | — | CONVERT (pack: CONVERT from li_backoffice (or RENAME)) | — | — | The source ID is li_bo_hours (there is no li_backoffice). Still a MIRROR (of Catalog numeric_mm7t4zmq, which is empty on all 34 products). Data: empty. |
| `li_r_pm_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_ops_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_pm_week` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_ops_week` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_car_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_car_week` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_auto_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_des_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_r_ls_per_cohort` | — | — | CREATE | — | — | via li_parent_opp |
| `li_pm_c` | — | — | CREATE | — | — |  |
| `li_ops_c` | — | — | CREATE | — | — |  |
| `li_car_c` | — | — | CREATE | — | — |  |
| `li_ls_line` | `formula_mm89sm5r` | Learning [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm894g60` (mirror) | Placeholder formula 'Learning' = '0' exists; proposed reuse. Needs approval (deviates from pack). |
| `li_weeks_t` | `li_cohort_months` | Cohort-Weeks Total [formula] | RENAME (pack: REPURPOSE 'Cohort Months' (rename + new formula)) | 1/1 (test 1), non-zero 0 | Opportunity:`opp_cohort_months` (mirror) | Live title 'Cohort-Weeks Total'. Formula is already {li_months}*{li_qty}, i.e. Training Weeks × Quantity, so only a rename is needed. Referenced by opp_cohort_months. |
| `li_part_t` | — | — | CREATE | — | — |  |
| `li_live_t` | — | — | CREATE | — | — |  |
| `li_self_t` | — | — | CREATE | — | — |  |
| `li_trn_t` | — | — | CREATE | — | — |  |
| `li_bo_t` | — | — | CREATE | — | — |  |
| `li_pm_t` | `formula_mm89hfy4` | PM [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm89667w` (mirror) | Placeholder formula 'PM' = '0' already exists and is summed by Opportunity lookup_mm89667w. Proposed: update its formula instead of creating a new column. Needs approval (deviates from pack). |
| `li_ops_t` | `formula_mm89qcd4` | OPS [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm89s51s` (mirror) | Placeholder formula 'OPS' = '0' already exists and is summed by Opportunity lookup_mm89s51s. Proposed: update its formula instead of creating a new column. Needs approval (deviates from pack). |
| `li_car_t` | `formula_mm89b2z4` | Career [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm89k0tq` (mirror) | Placeholder formula 'Career' = '0' already exists and is summed by Opportunity lookup_mm89k0tq. Proposed: update its formula instead of creating a new column. Needs approval (deviates from pack). |
| `li_auto_t` | `formula_mm897s4c` | Automation [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm89ydqn` (mirror) | Placeholder formula 'Automation' = '0' already exists and is summed by Opportunity lookup_mm89ydqn. Proposed: update its formula instead of creating a new column. Needs approval (deviates from pack). |
| `li_des_t` | `formula_mm89fxr7` | Design [formula] | REPURPOSE (pack: CREATE) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm89qv7b` (mirror) | Placeholder formula 'Design' = '0' already exists and is summed by Opportunity lookup_mm89qv7b. Proposed: update its formula instead of creating a new column. Needs approval (deviates from pack). |
| `li_ready` | `li_ready` | ⚙️Line Item Ready [formula] | UPDATE (pack: UPDATE formula) | 1/1 (test 1), non-zero 0 | Opportunity:`opp_li_ready` (mirror) | Live: IF({li_check}="Complete",1,0). Returns 1/0. Depends on helper li_check (not in pack), which checks only qty, participants and months. Either update both or inline li_check. |
| `li_check` | `li_check` | Line Item Check [formula] | UPDATE (pack: (not in pack)) | 1/1 (test 1) | Subitems of Opportunity:`li_ready` (formula) | APPROVED 21-Oct: update together with li_ready. Its 'Missing: …' text feeds M3's owner notification. |
| `li_one` | — | — | CREATE (pack: (not in pack)) | — | — | DECIDED 21-Oct: formula = 1; summed by Opportunity ⚙️Line Items Count for the M3 gate (Σ li_ready = count). |
| `subitem_defaults` | — | — | NOT FOUND (pack: DELETE candidates) | — | — | The board has no default Owner/Status/Date columns. Nothing to delete. |
| `old_ls_mirror` | `li_total_hours` | NUMBERS Learning Service Hours [mirror] | DELETE (pack: DELETE after CONVERT) | 0/1 | Opportunity:`lookup_mm88cm47` (mirror) | Old LS mirror. Dependent: Opportunity lookup_mm88cm47 (Σ). Re-point it first. |
| `old_expert_mirror` | `li_expert_hours` | NUMBERS Content Expert Hours [mirror] | DELETE (pack: DELETE after CONVERT) | 0/1 | Opportunity:`opp_expert_hours` (mirror) | Dependent: Opportunity opp_expert_hours (Σ). Re-point it first. |
| `old_bo_mirror` | `li_bo_hours` | NUMBERS Back Office Hours [mirror] | DELETE (pack: DELETE after CONVERT) | 0/1 | none found | No column dependents. |
| `nofar_pricelist` | `formula_mm89j9nx` | Price List [formula] | LEAVE (pack: Nofar) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm896pxy` (mirror) | Placeholder '0'. |
| `nofar_cogs` | `formula_mm898xd6` | COGS [formula] | LEAVE (pack: Nofar) | 1/1 (test 1), non-zero 0 | Opportunity:`lookup_mm893200` (mirror) | Placeholder '0'. |

### Catalog (18433874513)

| Key | Live ID | Live title [type] | Action | Data | Dependents | Notes |
|---|---|---|---|---|---|---|
| `cat_ls_hours` | `cat_ls_hours` | Learning Services Hours [formula] | REPURPOSE (pack: REPURPOSE (rename; values 28/4)) | 34/34, non-zero 0 | Subitems of Opportunity:`li_total_hours` (mirror) | It's a FORMULA: IF({cat_ls_level}="High",58,IF(…="Low",34,0)), not a Number. Nofar can't type values into it. Changing to 28/4 = editing the formula (same type, allowed). Per-product values would need CONVERT to Number. All 34 products show 0 because cat_ls_level is empty. |
| `cat_expert_hours` | `cat_expert_hours` | Content Expert Hours [formula] | KEEP | 34/34, non-zero 0 | Subitems of Opportunity:`li_expert_hours` (mirror) | Formula IF(High,9,0): matches D4. |
| `cat_ls_level` | `cat_ls_level` | Learning Services Level [status] | KEEP | 0/34 | Catalog:`cat_ls_hours` (formula); Catalog:`cat_expert_hours` (formula); Cohorts:`co_ls_level` (mirror); Subitems of Opportunity:`li_ls_level` (mirror) | EMPTY on all 34 products. Description still says 34/58 (update when values change). |
| `cat_training_weeks` | — | — | CREATE (pack: VERIFY / repurpose Months / CREATE) | — | — | DECIDED 21-Oct: new editable Number column on Catalog; M2 copies it into line-item li_months (editable). No Months column exists. The unfinished 'Training week # (Formula)' formula_mm8adqz8 (empty formula) and the empty 'Classes per week' / 'Hours per class' columns are left as they are. |
| `cat_rate` | `numeric_mm7tp9h8` | מחיר שעתי מומלץ- LIVE [numbers] | KEEP (pack: KEEP; Nofar fills) | 0/34 | none found | Empty on ALL 34 products. |
| `cat_bo` | `numeric_mm7t4zmq` | Back office H [numbers] | KEEP (pack: (implied)) | 0/34 | Subitems of Opportunity:`li_bo_hours` (mirror) | Source for li_bo. Empty on ALL 34 products. |
| `cat_total_hours` | `numeric_mm7thk2x` | Total Hours (Live & Self) [numbers] | KEEP (pack: (implied)) | 34/34 | none found | Source for the Total Training Hours mirrors (line items and Cohorts). A NUMBER, not a formula: equals Live + Self in the current data. |
| `cat_pm_hours` | — | — | NOT FOUND (pack: DELETE numeric_mm882ygh) | — | — | Does not exist. Nothing to delete. |
| `cat_pm_hours_dup` | — | — | NOT FOUND (pack: DELETE numeric_mm88zbdm) | — | — | Does not exist. Nothing to delete. |
| `cat_consulting` | `numeric_mm7tw5ja` | Consulting [numbers] | LEAVE (pack: VERIFY: flag, don't touch) | 34/34 | none found | Values 0 or 15. 'Training hours- total' (numeric_mm7t4es2) = Live + Consulting. |

### Cohorts (18403700733)

| Key | Live ID | Live title [type] | Action | Data | Dependents | Notes |
|---|---|---|---|---|---|---|
| `co_source_li` | `board_relation_mm88gj2b` | Source Line Item ID [board_relation] | KEEP | not counted | Cohorts:`lookup_mm88v28p` (mirror relation) |  |
| `co_catalog_item` | `co_catalog_item` | Catalog Item [board_relation] | KEEP | not counted | Cohorts:`co_ls_level` (mirror relation) |  |
| `co_ls_level` | `co_ls_level` | Learning Services Level [mirror] | KEEP | not counted | none found |  |
| `co_months` | `co_months` | Training Months [numbers] | DELETE (pack: DELETE after (unless real data)) | not counted | none found | APPROVED 21-Oct, CONDITIONAL: data NOT COUNTED (Cohorts scan stopped at the user's request). Count + backup before deleting; if it holds real data, stop and report. |
| `co_count_opp` | `lookup_mm88v28p` | Cohort Count (Opportunity) [mirror] | KEEP (pack: (not in pack)) | not counted | none found | Mirror of li_qty via the Source Line Item. Not in the pack. |
| `co_rate` | — | — | CREATE | — | — | Mirror of li_rate via board_relation_mm88gj2b. |
| `co_weeks` | — | — | CREATE | — | — | Mirror of li_weeks via board_relation_mm88gj2b. |
| `co_participants` | — | — | CREATE | — | — | Mirror of li_participants via board_relation_mm88gj2b. |
| `co_placement` | — | — | CREATE | — | — | Mirror of li_placement via board_relation_mm88gj2b. |
| `co_placement_pct` | — | — | CREATE | — | — | Mirror of li_placement_pct via board_relation_mm88gj2b. |
| `co_pweeks` | — | — | CREATE | — | — | Mirror of li_pweeks via board_relation_mm88gj2b. |
| `co_bo` | — | — | CREATE | — | — | Mirror of li_bo via board_relation_mm88gj2b. |
| `co_expert` | — | — | CREATE | — | — | Mirror of li_expert via board_relation_mm88gj2b. |
| `co_pm` | — | — | CREATE | — | — | Mirror of li_pm_c via board_relation_mm88gj2b. |
| `co_ops` | — | — | CREATE | — | — | Mirror of li_ops_c via board_relation_mm88gj2b. |
| `co_car` | — | — | CREATE | — | — | Mirror of li_car_c via board_relation_mm88gj2b. |
| `co_live` | — | — | CREATE | — | — | Mirror of Catalog via co_catalog_item. |
| `co_self` | — | — | CREATE | — | — | Mirror of Catalog via co_catalog_item. |
| `co_trn` | — | — | CREATE | — | — | Mirror of Catalog via co_catalog_item. |

### Projects (18390568732)

| Key | Live ID | Live title [type] | Action | Data | Dependents | Notes |
|---|---|---|---|---|---|---|
| `prj_pm_hours` | `prj_pm_hours` | Total PM Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_pm. |
| `prj_ops_hours` | `prj_ops_hours` | Total OPS Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_ops. |
| `prj_learning_hours` | `prj_learning_hours` | Total Learning Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_learning. |
| `prj_career_hours` | `prj_career_hours` | Career Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_career. |
| `prj_auto_hours` | `prj_auto_hours` | Automation Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_auto. |
| `prj_design_hours` | `prj_design_hours` | Design Hours [mirror] | REPURPOSE (pack: REPURPOSE (re-point)) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Re-point to op_tot_design. |
| `prj_pricelist` | `prj_pricelist` | Price List (₪) [mirror] | LEAVE (pack: re-point after Nofar builds Price List / COGS) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Leave until Nofar's Opportunity Price List / COGS columns exist, then re-point. |
| `prj_cogs` | `prj_cogs` | COGS (₪) [mirror] | LEAVE (pack: re-point after Nofar builds Price List / COGS) | 0/494 | none found | Broken: displays a non-existent Opportunity column. Leave until Nofar's Opportunity Price List / COGS columns exist, then re-point. |
| `prj_contract_value` | `prj_deal_amount` | Deal Amount [mirror] | RENAME (pack: CREATE) | 474/494, non-zero 469 | none found | ALREADY EXISTS: 'Deal Amount' = Σ deal_value via board_relation_mm7y54c8. Rename instead of creating. |
| `prj_n_cohorts` | `lookup_mm8825n1` | Number of Sold Cohorts [mirror] | REPURPOSE (pack: CREATE) | 0/494 | none found | ALREADY EXISTS: 'Number of Sold Cohorts' = Σ opp_cohorts, a mirror of a mirror. Re-point to op_n_cohorts. |
| `prj_n_participants` | `lookup_mm88t3m5` | Total Participents [mirror] | REPURPOSE (pack: CREATE) | 0/494 | none found | ALREADY EXISTS: 'Total Participents' (typo) = Σ opp_participants, a mirror of a mirror. Re-point to op_n_participants and fix the typo. |
| `prj_expert` | — | — | CREATE (pack: Optional) | — | — | DECIDED 21-Oct: create. Σ op_tot_expert via board_relation_mm7y54c8. |
| `prj_margin` | `prj_margin` | Margin % [mirror] | KEEP (pack: (not in pack)) | 0/494 | none found | Average of opp_margin. |
| `prj_mkt_budget` | `prj_mkt_budget` | Marketing Budget (₪) [mirror] | KEEP (pack: (not in pack)) | 0/494 | none found | Σ opp_mkt_budget. |

## DELETE candidates with risk tags

Approved list. Every delete exports a backup to `backup/<board>_<col>.json` first, and runs only after the prerequisites in its row are done.

| Board | ID | Title | Data | Column dependents | Risk | Prerequisite |
|---|---|---|---|---|---|---|
| Opportunity | `color_mm886byb` | Learning Services Level | 0/1233 | none | LOW* | — |
| Opportunity | `lookup_mm894g60` | Learning (Σ placeholder) | 0/1233 | none | LOW* | after `formula_mm89sm5r` is repurposed |
| Line items | `li_total_hours` | NUMBERS Learning Service Hours (mirror) | 0/1 | Opportunity `lookup_mm88cm47` | HIGH → LOW | LS Base Number created; `lookup_mm88cm47` re-pointed |
| Line items | `li_expert_hours` | NUMBERS Content Expert Hours (mirror) | 0/1 | Opportunity `opp_expert_hours` | HIGH → LOW | Expert Number created; `opp_expert_hours` re-pointed |
| Line items | `li_bo_hours` | NUMBERS Back Office Hours (mirror) | 0/1 | none | LOW* | Back Office Number created |
| Cohorts | `co_months` | Training Months | **not counted** | none | UNKNOWN | count + backup; stop if real data |

\* LOW assumes a clean Make and native-automation check (not possible from here).

**Kept by decision (were DELETE in the pack):** `opp_admission_level`, `opp_mkt_level`, `boolean_mm88cbqy`, plus `opp_customer_mgmt` and `opp_branding_level` (not in the pack).
**Pack deletions that don't exist:** `color_mm885xtx`, `numeric_mm882ygh`, `numeric_mm88zbdm`, the default subitem Owner/Status/Date columns.


## Unmatched columns: Opportunity and line items

Every existing column not matched to a §3 key. Recommendation: DELETE-LOW / DELETE-MED / KEEP-unrelated / ASK. Columns outside the pricing build (pre-existing CRM, HubSpot import, ILS reporting) are KEEP-unrelated even when they're empty. Clearing them is out of scope for this job.


### Opportunity (18390568735)

| ID | Title | Type | Data | Dependents | Recommendation |
|---|---|---|---|---|---|
| `subitems` | Cohorts | subtasks | 0/1233 | Opportunity:`opp_cohorts` (mirror relation); Opportunity:`lookup_mm88cm47` (mirror relation); Opportunity:`opp_participants` (mirror relation); Opportunity:`opp_cohort_months` (mirror relation); +11 more | KEEP-unrelated |
| `multiple_person_mkyzs737` | Owner | people | 778/1233 (test 1) | Opportunity:`formula_mm83qb6n` (formula); Opportunity:`formula_mm83qdd6` (formula); Opportunity:`formula_mm834d5g` (formula); Opportunity:`formula_mm83ec6y` (formula); +3 more | KEEP-unrelated |
| `color_mkyzchms` | Deal Stage | status | 1233/1233 (test 1) | Opportunity:`formula_mm6m9g2p` (formula); Opportunity:`formula_mm6mh3bh` (formula); Opportunity:`formula_mm6m7p7q` (formula); Opportunity:`formula_mm81z8ms` (formula); +14 more | KEEP-unrelated |
| `formula_mm6rjta6` | Days in current stage | formula | 36/1233 | none found | KEEP-unrelated |
| `color_mkyd5d32` | Pipeline | status | 1233/1233 (test 1) | Projects:`lookup_mm82bs7e` (mirror) | KEEP-unrelated |
| `boolean_mm6qkfvk` | Sales Committed | checkbox | 14/1233 | none found | KEEP-unrelated |
| `dropdown_mm6cacm6` | Program | dropdown | 22/1233 | none found | KEEP-unrelated |
| `date_mm66d80a` | Followup Date | date | 0/1233 | none found | KEEP-unrelated |
| `dropdown_mm63v6v9` | Deal Type | dropdown | 1232/1233 (test 1) | none found | KEEP-unrelated |
| `board_relation_mm1b747v` | Account | board_relation | 863/1233 (test 1) | Opportunity:`lookup_mm66ybeg` (mirror relation); Opportunity:`lookup_mm6ds2pw` (mirror relation); Opportunity:`lookup_mm6ge3xc` (mirror relation) | KEEP-unrelated |
| `lookup_mm66ybeg` | Industry | mirror | 718/1233 (test 1) | none found | KEEP-unrelated |
| `lookup_mm6ds2pw` | Contacts | mirror | 703/1233 (test 1) | none found | KEEP-unrelated |
| `date_mkyzvjr` | Last Contacted | date | 740/1233 | none found | KEEP-unrelated |
| `deal_value` | Amount | numbers | 1233/1233 (test 1) | Opportunity:`formula_mm6m9g2p` (formula); Opportunity:`formula_mm81zd7j` (formula); Opportunity:`formula_mm8167c0` (formula); Projects:`prj_deal_amount` (mirror) | KEEP-unrelated |
| `formula_mm6m9g2p` | Weighted Amount | formula | 1233/1233 (test 1), non-zero 499 | none found | KEEP-unrelated |
| `color_mm6gsmdt` | Currency | status | 1233/1233 (test 1) | Opportunity:`formula_mm81zd7j` (formula); Opportunity:`formula_mm8167c0` (formula) | KEEP-unrelated |
| `color_mm6697sr` | Expected Payment Terms | status | 44/1233 | none found | KEEP-unrelated |
| `long_text_mm69w6tq` | What was sold? | long_text | 102/1233 | none found | KEEP-unrelated |
| `text_mm1jf2fj` | Link to budget board | text | 143/1233 | none found | KEEP-unrelated |
| `link_mm664x3p` | Link to sales presentation (internal) | link | 138/1233 | none found | KEEP-unrelated |
| `link_mm6kgma8` | Link to Elevation’s order form | link | 16/1233 | none found | KEEP-unrelated |
| `file_mm66qc04` | Signed Contract/Purchase Order | file | 0/1233 | none found | KEEP-unrelated |
| `lookup_mm6ge3xc` | Source | mirror | 719/1233 (test 1) | none found | KEEP-unrelated |
| `dropdown_mm66r5r8` | Target Audience | dropdown | 142/1233 | none found | KEEP-unrelated |
| `text_mm66fs1h` | Target Audience - comments | text | 39/1233 | none found | KEEP-unrelated |
| `numeric_mkyz8mxm` | Deal Score | numbers | 0/1233 | none found | KEEP-unrelated |
| `deal_close_probability` | Close Probability | numbers | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `color_mm665sx7` | Cohort flow | status | 19/1233 | none found | KEEP-unrelated |
| `long_text_mm66y9zh` | Additional Links | long_text | 4/1233 | none found | KEEP-unrelated |
| `color_mm1b9xkn` | Lost Reason | status | 1/1233 | none found | KEEP-unrelated |
| `file_mm668ew2` | Other Files | file | 0/1233 | none found | KEEP-unrelated |
| `text_mm1jderw` | Additional Partners (optional) | text | 15/1233 | none found | KEEP-unrelated |
| `color_mm663pkq` | Training Format | status | 135/1233 | none found | KEEP-unrelated |
| `color_mm669n5d` | Training Model | status | 95/1233 | none found | KEEP-unrelated |
| `text_mm1j1305` | Training model - if other | text | 22/1233 | none found | KEEP-unrelated |
| `numeric_mm66xkfx` | Approx. overall number of participants | numbers | 162/1233 | none found | KEEP-unrelated |
| `numeric_mm6kk1kf` | Expected number of cohorts | numbers | 137/1233 | none found | KEEP-unrelated |
| `timerange_mm66c6q6` | Approx. Program Timeline- delete | timeline | 26/1233 | none found | ASK: title says '- delete' (26 values). Outside this job |
| `text_mm1jgay4` | Expected Start date | text | 116/1233 | none found | KEEP-unrelated |
| `date_mm7yfjxw` | Expected Start date | date | 107/1233 | none found | KEEP-unrelated |
| `numeric_mm7xtxtm` | Project duration (Months) | numbers | 0/1233 | none found | KEEP-unrelated |
| `numeric_mm66zj7` | Expected number of training hours (overall) | numbers | 136/1233 | none found | KEEP-unrelated |
| `color_mm66nae7` | Content Language | status | 142/1233 | none found | KEEP-unrelated |
| `color_mm66m9w1` | Content Delivery Language | status | 142/1233 | none found | KEEP-unrelated |
| `text_mm1j5kac` | Preferred trainer? | text | 87/1233 | none found | KEEP-unrelated |
| `dropdown_mm66x1zh` | Business objective/s | dropdown | 142/1233 | none found | KEEP-unrelated |
| `dropdown_mm66j07v` | Business objective/s - Internal Prioritization | dropdown | 44/1233 | none found | KEEP-unrelated |
| `dropdown_mm6kd4k9` | KPI | dropdown | 131/1233 | none found | KEEP-unrelated |
| `color_mm66v3pr` | Career team needed? | status | 135/1233 | none found | KEEP-unrelated (deal-level career info; overlaps the line-item 'Includes Placement', D11) |
| `color_mm6tx1t1` | Placements | status | 12/1233 | none found | KEEP-unrelated (overlaps the line-item placement flag) |
| `numeric_mm6kkv3f` | Placement duration | numbers | 10/1233 | none found | KEEP-unrelated (deal-level placement duration, months) |
| `numeric_mm66n56h` | Placement percent | numbers | 35/1233 | none found | KEEP-unrelated (deal-level placement %; the line item gets its own) |
| `color_mm6t3pr0` | Impact measurement | status | 0/1233 | none found | KEEP-unrelated |
| `text_mm1jw7qz` | Additional requests by client? | text | 39/1233 | none found | KEEP-unrelated |
| `long_text_mm66c3wg` | Any additional information? | long_text | 92/1233 | none found | KEEP-unrelated |
| `text_mm1j2shf` | Expected Payment Milestones | text | 126/1233 | none found | KEEP-unrelated |
| `board_relation_mm6929h0` | Financial Focal Point | board_relation | 2/1233 | Opportunity:`lookup_mm69tx34` (mirror relation); Opportunity:`lookup_mm696k1x` (mirror relation) | KEEP-unrelated |
| `lookup_mm69tx34` | Email of financial focal point | mirror | 2/1233 | none found | KEEP-unrelated |
| `lookup_mm696k1x` | Phone number of financial focal point | mirror | 0/1233 | none found | KEEP-unrelated |
| `multiple_person_mm66jz8e` | Learning | people | 11/1233 | none found | KEEP-unrelated |
| `multiple_person_mm66vf` | PM | people | 701/1233 (test 1) | none found | KEEP-unrelated |
| `date_mkyzbn51` | Close Date | date | 1232/1233 (test 1) | Accounts:`lookup_mm656fcb` (mirror); Opportunity:`formula_mm6mh3bh` (formula); Opportunity:`formula_mm6m7p7q` (formula); Opportunity:`formula_mm8178tp` (formula); +14 more | KEEP-unrelated |
| `date_mkyzavat` | Create Date | date | 1232/1233 (test 1) | none found | KEEP-unrelated |
| `board_relation_mkydsrf1` | Project | board_relation | 472/1233 | none found | KEEP-unrelated |
| `color_mm6ms3fd` | ⚙️Current Deal Stage | status | 36/1233 | none found | KEEP-unrelated |
| `board_relation_mm1gqact` | Cohorts | board_relation | 0/1233 | none found | KEEP-unrelated |
| `pulse_updated_mm664maq` | Last updated | last_updated | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `custom_mkrmrgz6` | Activities timeline | unsupported | 0/1233 | none found | KEEP-unrelated |
| `numeric_mm6g3f6j` | Total days in "Discovery Call & Identification" | numbers | 1224/1233 (test 1) | none found | KEEP-unrelated |
| `numeric_mm6g35jh` | Total days in "Proposal Sent & Tenders Prepared" | numbers | 1221/1233 (test 1) | none found | KEEP-unrelated |
| `numeric_mm6g7652` | Total days in "Proposal Approved" | numbers | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `numeric_mm6gyr4q` | Total days in "Price Offer & Tenders Sent" | numbers | 1221/1233 (test 1) | none found | KEEP-unrelated |
| `numeric_mm6g6ntg` | Total days in "Price Offer Signed & Tenders Approved" | numbers | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm6mh3bh` | Total days in "Closed Won" | formula | 1233/1233 (test 1), non-zero 475 | none found | KEEP-unrelated |
| `formula_mm6m7p7q` | Total days in "Closed Lost" | formula | 1233/1233 (test 1), non-zero 729 | none found | KEEP-unrelated |
| `date_mm6db97w` | ⚙️Last Stage Change | date | 36/1233 | Opportunity:`formula_mm6rjta6` (formula) | KEEP-unrelated |
| `text_mm6gqa7x` | ⚙️Hubspot_id | text | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `text_mm6jeh2w` | ⚙️Hubspot original status | text | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `text_mm6mnd66` | ⚙️Hubspot original pipeline | text | 1220/1233 (test 1) | none found | KEEP-unrelated |
| `color_mm6rd6v2` | PO Attched? | status | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `deal_contact` | Contacts | board_relation | 6/1233 | none found | KEEP-unrelated |
| `dropdown_mm6re20f` | Customer Industry | dropdown | 20/1233 | none found | KEEP-unrelated |
| `numeric_mm817h9j` | ILS Equivalent | numbers | 0/1233 | Opportunity:`formula_mm81zd7j` (formula); Opportunity:`formula_mm8167c0` (formula) | KEEP-unrelated |
| `formula_mm81zd7j` | Reporting Amount ILS | formula | 1233/1233 (test 1), non-zero 1124 | Opportunity:`formula_mm81z8ms` (formula); Opportunity:`formula_mm81efv6` (formula); Opportunity:`formula_mm832296` (formula); Opportunity:`formula_mm83k8b5` (formula); +7 more | KEEP-unrelated |
| `formula_mm81z8ms` | Won Sales ILS | formula | 0/1233 | Opportunity:`formula_mm81zhjc` (formula); Opportunity:`formula_mm814cfs` (formula); Opportunity:`formula_mm81pgwd` (formula); Opportunity:`formula_mm81gvtt` (formula); +2 more | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm81efv6` | Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 29 | Opportunity:`formula_mm8178tp` (formula); Opportunity:`formula_mm81pedz` (formula); Opportunity:`formula_mm81qcrj` (formula); Opportunity:`formula_mm81bt9z` (formula); +3 more | KEEP-unrelated |
| `formula_mm81sqw6` | Won Missing Close Date | formula | 0/1233 | none found | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm8167c0` | ILS Readiness Check (Unverified) | formula | 1233/1233 (test 1), non-zero 5 | none found | KEEP-unrelated |
| `formula_mm81zhjc` | Q4 2026 Won ILS | formula | 0/1233 | Opportunity:`formula_mm81x88q` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm8178tp` | Q4 2026 Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 27 | Opportunity:`formula_mm81x88q` (formula) | KEEP-unrelated |
| `formula_mm81x88q` | Q4 2026 Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm814cfs` | 2027 Annual Won ILS | formula | 0/1233 | Opportunity:`formula_mm81f6ry` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm81pedz` | 2027 Annual Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 2 | Opportunity:`formula_mm81f6ry` (formula) | KEEP-unrelated |
| `formula_mm81f6ry` | 2027 Annual Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm81pgwd` | Q1 2027 Won ILS | formula | 0/1233 | Opportunity:`formula_mm81ga1h` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm81qcrj` | Q1 2027 Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 2 | Opportunity:`formula_mm81ga1h` (formula) | KEEP-unrelated |
| `formula_mm81ga1h` | Q1 2027 Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm81gvtt` | Q2 2027 Won ILS | formula | 0/1233 | Opportunity:`formula_mm814stx` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm81bt9z` | Q2 2027 Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 0 | Opportunity:`formula_mm814stx` (formula) | KEEP-unrelated |
| `formula_mm814stx` | Q2 2027 Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm81yh6w` | Q3 2027 Won ILS | formula | 0/1233 | Opportunity:`formula_mm81tn7a` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm81x93h` | Q3 2027 Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 0 | Opportunity:`formula_mm81tn7a` (formula) | KEEP-unrelated |
| `formula_mm81tn7a` | Q3 2027 Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm81rswk` | Q4 2027 Won ILS | formula | 0/1233 | Opportunity:`formula_mm81zcp3` (formula) | KEEP-unrelated (broken ref to deleted date_mm816c6c; flag to client) |
| `formula_mm813z4` | Q4 2027 Weighted Open ILS | formula | 1233/1233 (test 1), non-zero 0 | Opportunity:`formula_mm81zcp3` (formula) | KEEP-unrelated |
| `formula_mm81zcp3` | Q4 2027 Forecast ILS | formula | 0/1233 | none found | KEEP-unrelated |
| `formula_mm832296` | 2026 Closed Won ILS (Expected Date) | formula | 1233/1233 (test 1), non-zero 42 | Opportunity:`formula_mm83cfm6` (formula); Opportunity:`formula_mm83qb6n` (formula); Opportunity:`formula_mm834d5g` (formula); Opportunity:`formula_mm8342za` (formula) | KEEP-unrelated |
| `formula_mm83k8b5` | Q1 2026 Closed Won ILS (Expected Date) | formula | 1233/1233 (test 1), non-zero 16 | Opportunity:`formula_mm83yeej` (formula) | KEEP-unrelated |
| `formula_mm83yeej` | Q1 2026 Company Attainment % | formula | 1233/1233 (test 1), non-zero 16 | none found | KEEP-unrelated |
| `formula_mm837df5` | Q2 2026 Closed Won ILS (Expected Date) | formula | 1233/1233 (test 1) | Opportunity:`formula_mm8321h5` (formula) | KEEP-unrelated |
| `formula_mm8321h5` | Q2 2026 Company Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83p93r` | Q3 2026 Closed Won ILS (Expected Date) | formula | 1233/1233 (test 1) | Opportunity:`formula_mm83ate0` (formula) | KEEP-unrelated |
| `formula_mm83ate0` | Q3 2026 Company Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83esbd` | Q4 2026 Closed Won ILS (Expected Date) | formula | 1233/1233 (test 1) | Opportunity:`formula_mm83ndz` (formula); Opportunity:`formula_mm83qdd6` (formula); Opportunity:`formula_mm83ec6y` (formula); Opportunity:`formula_mm83e8qn` (formula) | KEEP-unrelated |
| `formula_mm83ndz` | Q4 2026 Company Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83cfm6` | 2026 Company Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83f9br` | Q4 2026 Open Pipeline ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83qb6n` | Tomer 2026 Annual Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83qdd6` | Tomer Q4 2026 Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm834d5g` | Nir 2026 Annual Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83ec6y` | Nir Q4 2026 Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm8342za` | Yariv 2026 Annual Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83e8qn` | Yariv Q4 2026 Attainment % | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83t4jq` | Current Quarter Closed Won ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm83x54t` | Current Quarter Company Target ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm837by` | Salesperson Reporting Group | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `text_mm88x4s7` | ⚙️New Program Option | text | 0/1233 | none found | ASK: duplicate of ✨New Program Option, empty |
| `short_textq6oy0o42` | ✨New Program Option | text | 1/1233 | none found | ASK: duplicate of ⚙️New Program Option; only value is 'testtest' (test data) |
| `formula_mm8bhjrw` | Current Quarter Open Pipeline ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm8byp30` | Current Quarter Weighted Open Pipeline ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |
| `formula_mm8bgj3x` | All Open Pipeline ILS | formula | 1233/1233 (test 1) | none found | KEEP-unrelated |

### Line items (18390568739)

| ID | Title | Type | Data | Dependents | Recommendation |
|---|---|---|---|---|---|

## Dependency graph (pricing columns)

Monday-side dependents of the columns this plan touches (formula references, mirrors on any of the 50 workspace boards, webhooks):

| Column | Depended on by |
|---|---|
| Line items `li_qty` | `li_cohort_months`, `li_check` (formulas); Opportunity `opp_cohorts` (Σ); Cohorts `lookup_mm88v28p` |
| Line items `li_months` | `li_cohort_months`, `li_check` |
| Line items `li_participants` | `li_check`; Opportunity `opp_participants` (Σ) |
| Line items `li_check` → `li_ready` → Opportunity `opp_li_ready` (Σ) | chain |
| Line items `li_cohort_months` | Opportunity `opp_cohort_months` (Σ) |
| Line items `li_total_hours` | Opportunity `lookup_mm88cm47` (Σ) |
| Line items `li_expert_hours` | Opportunity `opp_expert_hours` (Σ) |
| Line items `formula_mm89*` (8) | Opportunity `lookup_mm89*` (8 Σ mirrors), one each |
| Catalog `cat_ls_level` | `cat_ls_hours`, `cat_expert_hours`; line-item `li_ls_level`; Cohorts `co_ls_level` |
| Catalog `cat_ls_hours` / `cat_expert_hours` / `numeric_mm7t4zmq` | line-item `li_total_hours` / `li_expert_hours` / `li_bo_hours` |
| Opportunity `opp_participants`, `opp_cohorts` | Projects `lookup_mm88t3m5`, `lookup_mm8825n1` (mirror-of-mirror; blank) |
| Opportunity `deal_value` | Opportunity formulas `formula_mm6m9g2p`, `formula_mm81zd7j`, `formula_mm8167c0`; Projects `prj_deal_amount` |
| Opportunity `opp_margin`, `opp_mkt_budget` | Projects `prj_margin`, `prj_mkt_budget` |
| Opportunity `color_mm66cssh`, `color_mm66x3y2`, `color_mm88m6bm`, `opp_support_level`, all level columns, `color_mm886byb` | **no monday-side dependents found.** Make not checked. Projects has similar statuses ("Admission" `color_mm6tmsqv`, "Marketing" `color_mm7yntdf`) that are likely filled by the Closed Won → Project automation: UI/Make check |
| Cohorts `co_months` | none |

**Webhooks** (likely Make or integrations): Opportunity `create_item` (655003206) and Deal Stage `color_mkyzchms` → index 6 Closed Won (632054786). Cohorts: `create_item` ×2, `color_mm2kwwtg`, `date_mm2m40dv`, `date_mm2mqd70`. The line-items, Catalog, Projects and Accounts boards have none.

**Other boards linking to the target boards:** Customer Contacts (→ Opportunity, Projects, Accounts); ARCHIVE Opportunity (→ Cohorts, Projects; it reuses the Opportunity relation IDs); Participants, Classes, Budgets and Enrollments (→ Cohorts; ~120 mirrors of operational Cohorts columns, none of them pricing columns).

**Pre-existing broken references (outside scope, FYI):** 8 Opportunity ILS formulas (`formula_mm81z8ms`, `formula_mm81sqw6`, `formula_mm81zhjc`, `formula_mm814cfs`, `formula_mm81pgwd`, `formula_mm81gvtt`, `formula_mm81yh6w`, `formula_mm81rswk`) reference a deleted column `date_mm816c6c`.


## Status migration preview (§4.3)

| Service | Flag column | Level column | How the formulas will read today's data (all 1,233 Opportunities) |
|---|---|---|---|
| Admission | `color_mm66cssh` | `opp_admission_level` | Not Sold: 1166; Low (Yes, no level): 67 |
| Ongoing Course Support | `boolean_mm88cbqy` | `opp_support_level` | Low (empty level): 1233 |
| Customer Management | `opp_customer_mgmt` | `color_mm88m6bm` | Low (empty level): 1233 |

**Under the 21-Oct decision no data is migrated.** `color_mm66cssh` only gains a new "Not Sold" label, and the level columns stay as they are. The table shows how the agreed formula logic will read today's data. Because every level column is empty, every "Yes" falls back to **Low** (decision: "do low").

#### Admission items with flag = Yes (read as Low until a level is set)

| Service | Item ID | Item | Deal Stage | Flag | Level | Proposed |
|---|---|---|---|---|---|---|
| Admission | 12913781810 | Dell foundation- Neshota | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913781822 | schusterman-Beatzmi- Tech Troop | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913774478 | Palestinian Internship Program - Fullstack Oct 23 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913750299 | Strauss Food Entrepreneurship | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913800025 | Hayozma + Negev Talent - Tech Onboarding | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913759987 | WOO (Bonim Atid) - 2026 Expansion | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913715658 | preTech - Keren Rashi | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788980 | Atufot - UI UX (south) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913789016 | IDF WOO - Program | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913770578 | Ofakim Muni - Pretech + CCNA | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913782025 | JAFI - CCNA Karmiel | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913758975 | Appleseeds/Salesforce - CRM | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788781 | Hizdamnut - SF Admin | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913789821 | Sapir College - Devops & Project Management | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786210 | Kav Mashve 23-24 - Arabs reskill to Recruitment *2 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788084 | Jewish Agency - Project Mng | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913727134 | Merit spread-Tmura (Riskified) Neshota mil wives | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913780863 | East Negev Tender - Pilot Cohort | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913761133 | Google Africa - Shopping/Accelherate | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913714488 | Appleseeds - QA+Data | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913729499 | Seminar Python Bootcamp (Israel Tik) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913715654 | Rashi Bedarka (W2W) - Data | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913715655 | Place IL - Cohort 3 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913750643 | Itworks Frontend 2nd round | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913750646 | Joint & Ministry of Tourism - Online outreach workshops for guides | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788957 | IIA - Bedouin Program - Matching | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788962 | Wix - Shopping IL (Website Build) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788963 | Jerusalem Muni - Preparation for technological interviews | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913685171 | Old Seminar Jerusalem - Python Bootcamp N.02 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913718165 | Hayozma South - Account Mng | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913718171 | HaYozma - Data (Center) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913789020 | Negev Talent - 2nd cohort - Sales Training | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913770576 | Beer Sheva Muni - Data Analyst Reskill | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913770582 | PreTech- Rayan Beatzmi | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913754359 | Pretech - Rayan Alfanar (North) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913754361 | Place IL - 5th Cohort | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788780 | Tech Troop- Aharai | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913727136 | Hayozma - Lamerhak BI | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913719618 | Haimash/IDF - Digital Marketing (PPC & AI) - Cohort 2 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913757816 | Pais (Shopping New Version) | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913757821 | Jewish Agency - Project 2nd Cohort | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913757839 | Hayozma/Tnufa  - Reskill Course | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913740788 | Negev Talent - SMB's training | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913730529 | Kinneret College - AI for Reservists | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913781811 | Neshota- The day after fund- upskill 2025 q4 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913781827 | Alfanar - Pretech 2 groups | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913750313 | AI Workshops for Miluim- Employment Service & Malam | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913759988 | JAFI - Project Mng Feb 26 | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913685474 | 255- Hostages families | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913685478 | JLM - Pretech 2 Groups | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913718499 | JAFI - Project Mng Ibim | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786649 | Pretech - with Achva College | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786653 | Beshvil HaZafon - Pais + Walla | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786655 | Pretech Negev Talent | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913782028 | WOO Extension - 2 Financial Workshops | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913782053 | I4Valley - AI for Developers | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913782055 | Beshvil Hatzafon - Pais+Ruah HaGalil | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 13111633987 | Momentum- released soldiers workshops | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786647 | Beatzmi & Shusterman - Budget Extension | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786022 | IIA + I4Valley | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913786030 | Sherut Taasuka - Short Courses | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913759986 | Government Matching for DellFoundation- Israeli Employment Services | Closed Won | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913781820 | Hayozma - CCNA | Closed Lost | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913780431 | ItWorks & IIA - Data Analysis Women 4 (5/23) | Closed Lost | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913788740 | AWS Restart Matching | Closed Lost | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913729496 | Sigma - Data Program | Closed Lost | Yes | (empty) | Low (Yes, no level) |
| Admission | 12913790004 | Wolf Seminar - Devops Bootcamp | Closed Lost | Yes | (empty) | Low (Yes, no level) |

Admission items with flag = No are read as Not Sold: 75. Items with both columns empty are also Not Sold. Ongoing and Customer Management levels are empty on every deal, so all of them read as Low until set (M1 will preset new deals). Marketing has no level logic (budget only). Full rows: `scan/migration-preview.json`.


## Test data

Rule: item name matches test/בדיקה/טסט/dummy, **or** the item was created by a Kindaa user on/after 2026-10-01 (the build period). The 2026-08-27 bulk import by the Kindaa API user (1,220 Opportunities) is real data and isn't flagged. Name matches are candidates only: e.g. Opportunity 12913775378 "Zalando - UI automation testing for apps" is a real deal, and several Accounts matches are real companies (e.g. "qa-testlab.com").

- **Opportunity**: 1 test item(s): 12913775378 "Zalando - UI automation testing for apps". Kindaa-created by date: {'2026-08-27': 1220}.
- **Line items**: 1 test item(s): 13334326395 "1". Kindaa-created by date: {'2026-10-20': 1}.
- **Catalog**: 0 test item(s). Kindaa-created by date: none.
- **Cohorts**: 0 test item(s). Kindaa-created by date: none.
- **Projects**: 0 test item(s). Kindaa-created by date: none.
- **Accounts**: 22 test item(s): 12882585421 "TestMe", 12882616972 "qa-testlab.com", 12882924368 "Test", 12882931242 "test4.com", 12882931262 "test5.com", 12882931263 "Test6", 12882931264 "test7.com", 12882931265 "test8.cm", 12882931266 "test10.com", 12882931267 "Test12 - Show Equipment", 12883007857 "elevationtest.ac", 12883057308 "test11.co.il" …. Kindaa-created by date: none.

## UI-check list (no API access)

Check these in the monday UI (automations center, view settings, dashboards) and in Make before the matching phase:

- **Opportunity:** automations reading or writing `color_mm66cssh`, `color_mm66x3y2`, `color_mm88m6bm`, `opp_support_level`, `color_mm886byb`, `boolean_mm88cbqy`, `opp_customer_mgmt`; the Closed Won → Project automation (spec C5.1), which may copy Admission/Marketing to Projects `color_mm6tmsqv` / `color_mm7yntdf`; filters, sorts and columns in the 5 views (By Deal Stage, Forecasting, Sales Reporting | By Salesperson, Sales Reporting | Foreign deals review, **\*Sales – Pricing\***); dashboards and widgets using the `lookup_mm89*` sums or `lookup_mm894g60`.
- **Line items:** any automation on subitems (create, catalog change); views on the parent's subitem view showing `li_total_hours`, `li_expert_hours`, `li_bo_hours`.
- **Catalog:** the "By Vertical" view; who edits `cat_ls_level` (D10 security).
- **Cohorts:** automations or forms touching `co_months`; the "Add Cohort" and "Add Event" forms; 17 table views (any column-visibility settings for the new mirrors).
- **Projects:** "Table" and "PM" views showing `prj_*`, `lookup_mm8825n1`, `lookup_mm88t3m5`.
- **Make:** grep every scenario blueprint in the Elevation team for: board IDs 18390568735, 18390568739, 18433874513, 18403700733, 18390568732; and column IDs `color_mm66cssh`, `color_mm66x3y2`, `color_mm88m6bm`, `opp_support_level`, `color_mm886byb`, `lookup_mm894g60`, `li_total_hours`, `li_expert_hours`, `li_bo_hours`, `li_months`, `li_cohort_months`, `li_ready`, `li_check`, `formula_mm89*`, `lookup_mm89*`, `cat_ls_hours`, `co_months`, `board_relation_mm88gj2b`, `co_catalog_item`, `prj_*`, `lookup_mm8825n1`, `lookup_mm88t3m5`.

