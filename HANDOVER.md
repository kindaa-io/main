# Elevation Phase 2 – session handover

**Written:** 3 Nov 2026 · **Branch:** `claude/nifty-sagan-exnzn7` · **Client:** Elevation Academy (monday account 183643), workspace 13463480 "Elevation - CRM" · **Partner:** Kindaa

Phases 1–9 of the build pack are built and tested. The next session handles the **client's rejects** of this build.
Read this file, then `scan/column-map.json` (every column/scenario ID, action and note), then re-read the live account before changing anything — people edit the boards and scenarios between sessions (see "Things that changed under us").

The original build pack (`elevation-phase2-build-pack.md`, 21 Oct) is **not in this repo**; the user pasted it into the first session. Ask for it if a rule from it is needed. Where it conflicts with the decisions below, **the decisions win**.

---

## 1. Access (how this session reached the systems)

| System | How | Notes |
|---|---|---|
| monday.com | GraphQL `https://api.monday.com/v2` via the session's proxy-injected credentials (no token in code) | The monday **MCP never connected** (proxy tunnel 403). Acts as user "Kindaa support" (111441380). |
| Make.com | REST `https://eu1.make.com/api/v2` via proxy-injected credentials | **eu1**, not eu2 (eu2 returned 401, later blocked). Org "Elevation" 630631, team 387027, folder 381378, monday connection 3107441 ("Ariella's Monday connection"). Authenticated as Yair Ben Ivgi. No Make MCP. |
| Claude Docs | Meeting plan doc: https://claude.ai/artifact/1Ug1LMijkeq7nKcQ4ABkx7 | 60-min demo plan, decisions list, expected figures. |

**Permissions in Claude Code:** the auto-mode classifier blocked live-board writes until a project rule allowed the build script (`.claude/settings.local.json`, not committed — a new session must re-create a rule or get approval). It also **blocked committing Make blueprints and the backfill record to this repo** ("out-of-place publication"); those stayed in the old session's scratchpad and are lost. Blueprints can be re-read from Make at any time.

**Build script:** all changes were made by one script (`phase2.py`, steps `p3`…`p8`, `fix2`, `m3_*`, `mk_*`, `backfill_*`), logged per mutation. It lived in the old scratchpad. `tools/elevation_build.py` is a copy if it could be committed; otherwise rebuild helpers from the API notes in section 8.

---

## 2. Boards

| Board | ID | Notes |
|---|---|---|
| ⚙️ Pricing Parameters (new) | 18436459887 | 1 group "Versions" (`topics`). Items: v1 – Oct 2026 `13348993282` (**Active**), "test" `13441112751` (Archived — created by someone else, archived by scenario #05), "TEST copy of v1 (Kindaa)" `13441128594` (Archived, test) |
| Opportunity | 18390568735 | groups `topics` Active Deals, `closed`, `group_mm69150s` |
| Line items (Subitems of Opportunity) | 18390568739 | |
| Catalog | 18433874513 | 34 products; LS level, hourly rate, Back office H, Training Weeks **empty on all** |
| Cohorts | 18403700733 | new cohorts go to group `group_mm2k46ga` |
| Projects | 18390568732 | |
| Accounts | 18390568736 | not changed |

## 3. Decisions log (overrides the build pack)

| Date | Decision |
|---|---|
| 21 Oct | Read-only scan approved list; Make not checked then. |
| 21 Oct | Keep level columns `opp_admission_level`, `opp_mkt_level`, `opp_branding_level`, checkboxes `opp_customer_mgmt`, `boolean_mm88cbqy` (no status merge). |
| 21 Oct | Every service = status **Low / High / Not Sold** (new label idx 2, grey): Admission (`opp_admission_level`), Marketing (`opp_mkt_level`), Website Build (`op_website`, new), Branding Setup (`opp_branding_level`), Event (`opp_event_level`), Ongoing Course Support (`opp_support_level`), Customer Mgmt (`color_mm88m6bm`). `color_mm66cssh` "Screening/Admission?" and `color_mm66x3y2` "Marketing?" left unchanged. |
| 21 Oct | Admission logic: Low/High = sold; Not Sold = 0; empty level + `color_mm66cssh`="Yes" → Low. "No" was approved as = Not Sold, **but the built formula lets the level win** (see open item 1). Ongoing / Customer Mgmt / Event: empty → Low. Marketing hours driven by `opp_mkt_level` (empty → 0); budget stays in `opp_mkt_budget`. |
| 21 Oct | Catalog Training Weeks = new editable Number on Catalog, copied to the line (`li_months`). |
| 21 Oct | Old checkboxes renamed "(old)" — **then deleted outside our scripts** (17:42 UTC, Kindaa support account): `opp_branding_setup`, `boolean_mm88cbqy`, `opp_customer_mgmt`. All were empty. |
| 22 Oct | LS sum: keep `lookup_mm894g60` ("Σ LS Hours (lines)"), deleted `lookup_mm88cm47` + `li_total_hours`. |
| 22 Oct | Projects: 6 broken hour mirrors deleted and recreated as `prj_tot_pm/ops/learning/career/auto/design`. |
| 22 Oct | **Branding dropped** from Design hours (columns kept, not priced). |
| 26 Oct | Readiness gate built **OFF**; Project field mapping approved with "create missing labels"; M1 backfill by script; safe testing on TEST KINDAA. No new monday columns for the Make work. |
| 2 Nov | Scenario #05: only one Active pricing version. |

## 4. What is built (details and IDs: `scan/column-map.json`)

- **Pricing Parameters:** `prm_status` (1 Active / 0 Archived), `prm_effective`, 38 numbers (`prm_*`), v1 values = build pack §2.1.
- **Opportunity:** `op_prm_version` (→ Pricing Parameters) + 38 mirrors `opm_*`; `op_website`, `op_cm_weeks`; 9 rate formulas `op_r_*`; Σ mirrors `op_sum_bo/live/self/trn`, `op_li_count`, renamed `lookup_mm89*` (Σ PM/OPS/Career/Automation/Design), `lookup_mm894g60` (Σ LS); re-pointed `opp_participants` (Σ `li_part_t`), `opp_expert_hours` (Σ `li_expert`); formulas `op_ev_pm/ops`, `op_cm_pm/ops`, `op_tot_pm/ops/learning/expert/career/auto/design`, `op_n_cohorts`, `op_n_participants`.
- **Line items:** numbers `li_pweeks`, `li_placement_pct`, `li_ls_base`, `li_expert`, `li_bo`; mirror `li_trn_cohort`; 9 `li_r_*` mirrors via `li_parent_opp`; formulas `li_pm_c/ops_c/car_c`, `li_part_t/live_t/self_t/trn_t/bo_t`, `li_one`; repurposed `formula_mm89hfy4/qcd4/b2z4/897s4c/fxr7` (PM/OPS/Career/Automation/Design totals), `formula_mm89sm5r` (LS Hours line); `li_check` rewritten (`li_ready` reads it); renames `li_months` "Training Weeks", `li_cohort_months` "Total Training Weeks", `li_participants` "Participants / Cohort".
- **Catalog:** `cat_ls_hours` → "LS Base Hours" formula High 28 / Low 4; `cat_training_weeks` (Number).
- **Cohorts:** 14 mirrors `co_*` ("(planned)" where an operational column exists).
- **Projects:** `prj_tot_*` (6), `prj_expert`, re-pointed + renamed `lookup_mm8825n1` "Number of Cohorts", `lookup_mm88t3m5` "Total Participants", `prj_deal_amount` → "Total Contract Value".
- **Deleted (backups in `backup/`):** `color_mm886byb`, `li_bo_hours`, `li_expert_hours`, `co_months`, `lookup_mm88cm47`, `li_total_hours`, 6 old `prj_*` hour mirrors.
- **Views "new columns" / "modified columns":** Opportunity 287762127 / 287762146 (item + line-item level), Catalog 287770585 / 287770602, Cohorts 287770627 / 287770641, Projects 287770648 / 287770664. Keep them updated with every change.

## 5. Make scenarios (all in folder 381378, connection 3107441)

| # | ID | Trigger | Does |
|---|---|---|---|
| #01 M3 | 7213714 | Deal Stage → Closed Won (hook 3652738) | Extended 26 Oct on top of a 25-Oct edit by someone else: module 60 GraphQL line-item query, 61 SetVariables (`readiness_gate`="off"), project mapping in 46 (Participants, Vertical, Timeline, Placements, Program, PM; create labels), router 49 → contacts chain + cohort branch (70 iterator → 71 repeater × Quantity → 72/73 `create_item` in `group_mm2k46ga` linking Project/Opportunity/Source Line Item/Catalog), Matching Needed filter added to route 1 (was missing), gate-fail route 80/81 idle. Orphan modules 45/47 exist on its canvas. |
| #02 M1 | 8189159 | Opportunity created (hook 3980742) | Link Active pricing version; Margin 40, Ongoing / Customer Mgmt Low when empty. |
| #03 M2a | 8189111 | Line item created (hook 3980717) | Link parent; Quantity 1; copy rate / weeks / LS base / expert / BO from Catalog where empty. |
| #04 M2b | 8189131 | Subitem column changed, filtered to `li_catalog_item` (hook 3980729) | Overwrite those five fields from the new Catalog product. |
| #05 | 8326233 | Pricing `prm_status` changed (hook 4024431) | When a version becomes Active, set all other Active versions to Archived. |

Backfill (26 Oct): the open Opportunities without a version were linked to v1 (30); closed deals left unlinked.

## 6. Test data currently live (not archived, on purpose)

- Opportunity **TEST KINDAA** `13349045463` (pipeline B2B, stage Discovery Call at last read; Admission High, Marketing Low, Ongoing High, Cust Mgmt Low, CM weeks 20, 2 Low events, Website Low, Learning manual 5, Dev Live 10 / Self 6; `color_mm66cssh`="No" set by someone).
  Lines: A `13349455069` (3 × 5 wk, placement 25 wk), B `13349515700` (1 × 3 wk), C `13385996005` (edited by someone: 50 participants, 8 wk, rate 250).
- Test Project "TEST KINDAA" `13386043686` + cohorts `13386052802`, `13386024491`, `13386047557`, `13386023950`, `13386043710`.
- Opportunity "TEST KINDAA M1" `13386031587`. Pricing item "TEST copy of v1 (Kindaa)" `13441128594`.
- Archived earlier tests: project `13384891797` + 4 cohorts, `13384987487`, `13384917176`.

## 7. Open items / known issues

1. **Admission "No" vs level:** TEST KINDAA has `color_mm66cssh`="No" with level High; formulas charge High. Agreed rule was "No" = Not Sold → one formula change (`ADM_SOLD` + every `adm(...)` use) if the client confirms.
2. **Formulas read "null" via API since 2 Nov** for every formula on Opportunity (even pre-existing ones). Probably monday-side; verify in UI.
3. API reads **blank** for mirrors of formula columns (cohort PM/OPS/Career planned, subitem Σ mirrors); formulas using them compute correctly. Confirm in the UI.
4. Readiness gate OFF until the Catalog has LS levels (every line shows "Missing: Catalog/LS Level").
5. Cohort names repeat across lines with the same product ("… – 1").
6. M2b overwrites with empty Catalog values (clears typed rate/BO/weeks).
7. Price List / COGS / Cost Rates: Nofar, not started. Branding columns kept, unpriced.
8. UI-only: restrict Pricing Parameters editing to Nofar (sales view only); collapse the ⚙️ parameter columns.

## 8. API notes that cost time

- `create_column` on API **2025-04** cannot create `board_relation` / `mirror`, and **stores an empty formula** → use **2025-10**; set formulas with `update_column(settings:{formula})` (settings is an object, needs `revision`).
- `update_status_column` needs a colour on every label (existing ones too).
- Re-pointing an existing mirror with `update_column` fails when its current source column is gone (`notices.column.settings.update.error`); works otherwise.
- Make hooks: `POST /hooks` with **flat** params (`__IMTCONN__`, `boardId`, `updateType`, `config`) — Make registers the monday webhook itself. Types: `monday4` create_item / create_subitem, `monday3` change_specific_column_value / change_subitem_column_value.
- Make GraphQL module: `monday:ExecuteGraphQLQueryV2`, mapper `{method:"POST", queryBody, variables:[{key,value}], variablesDataSource:"array"}`; output `{{N.body.data...}}` (1-based indexes).
- Validate a changed blueprint as an inactive draft copy (trigger hook removed) before patching a live scenario; blueprint module IDs must be unique including canvas orphans.

## 9. Things that changed under us (re-read before acting)

- Scenario 7213714 was edited by someone on 25 Oct (Matching Needed router) — built on that version.
- `connect_boardsjf9cld` "Active Project" was added to Opportunity by someone.
- The three "(old)" checkboxes were deleted by someone.
- TEST KINDAA inputs, Line C values and a Pricing item "test" were changed/added by someone.
