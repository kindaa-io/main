# Phase 2: Opportunity inputs (statuses, renames, Website Build, CM Weeks, pricing link + 38 mirrors) and the
# formula-over-mirror gate on test item 13349045463. Every mutation is logged; stops at the first API error.
import json, os, subprocess, sys, time
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # relative paths (raw/, logs) resolve next to the script
OPP, PRM_BOARD, PRM_ITEM, TEST_ITEM = 18390568735, 18436459887, 13348993282, 13349045463
LOG = open("phase2_mutations.log", "a")
STEP = sys.argv[1] if len(sys.argv) > 1 else "all"

def gql(q, v=None, ver="2025-04"):
    body = json.dumps({"query": q, "variables": v or {}})
    r = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.monday.com/v2", "-H", "Content-Type: application/json",
                        "-H", f"API-Version: {ver}", "--data-binary", "@-"], input=body, capture_output=True, text=True)
    d = json.loads(r.stdout)
    if q.lstrip().startswith("mutation"):
        LOG.write(json.dumps({"t": time.strftime("%H:%M:%S"), "ver": ver, "q": q, "v": v, "resp": d}, ensure_ascii=False) + "\n"); LOG.flush()
    if d.get("errors") or d.get("error_code"):
        raise SystemExit("API error: " + json.dumps(d, ensure_ascii=False)[:1200])
    return d["data"]

def rename(cid, title):
    r = gql("mutation($b:ID!,$c:String!,$t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id title } }",
            {"b": OPP, "c": cid, "t": title})["change_column_title"]
    print("renamed", r["id"], "->", r["title"])

EXISTING = set()
def create(cid, title, ctype, description, defaults=None, ver="2025-04"):
    if not EXISTING:
        EXISTING.update(c["id"] for c in gql("query($b:[ID!]) { boards(ids:$b) { columns { id } } }", {"b": [OPP]})["boards"][0]["columns"])
    if cid in EXISTING:
        print("exists, skipped", cid); return None
    EXISTING.add(cid)
    v = {"b": OPP, "id": cid, "t": title, "d": description}
    if defaults is not None: v["def"] = json.dumps(defaults)
    q = "mutation($b:ID!,$id:String!,$t:String!,$d:String%s) { create_column(board_id:$b, id:$id, title:$t, column_type:%s, description:$d%s) { id title type } }" % (
        ",$def:JSON" if defaults is not None else "", ctype, ", defaults:$def" if defaults is not None else "")
    r = gql(q, v, ver=ver)["create_column"]; print("created", r["id"], r["title"], r["type"]); return r

def col_state(cid):
    return gql('query($b:[ID!],$c:[String!]) { boards(ids:$b) { columns(ids:$c) { id title revision settings } } }',
               {"b": [OPP], "c": [cid]}, ver="2025-10")["boards"][0]["columns"][0]

def set_status_labels(cid, title):
    """Keep existing labels (same ids/indexes), add 'Not Sold' at index 2 (grey), set title."""
    c = col_state(cid)
    # The API wants a color on every label; keep each existing label's current color (by hex).
    HEX = {"#fdab3d": "working_orange", "#00c875": "done_green", "#c4c4c4": "american_gray", "#df2f4a": "stuck_red", "#e2445c": "stuck_red"}
    labels = []
    for l in c["settings"]["labels"]:
        if l.get("hex", "").lower() not in HEX: raise SystemExit(f"Unknown color {l} on {cid}; not changing it")
        labels.append({"id": l["id"], "label": l["label"], "index": l["index"], "color": HEX[l["hex"].lower()]})
    if not any(l["label"] == "Not Sold" for l in labels):
        labels.append({"label": "Not Sold", "index": 2, "color": "american_gray"})
    else:
        labels = [dict(l, color="american_gray") if l["label"] == "Not Sold" else l for l in labels]
    r = gql("mutation($b:ID!,$c:String!,$t:String!,$rev:String!,$s:UpdateStatusColumnSettingsInput!) { update_status_column(board_id:$b, id:$c, title:$t, revision:$rev, settings:$s) { id title } }",
            {"b": OPP, "c": cid, "t": title, "rev": c["revision"], "s": {"labels": labels}}, ver="2025-10")["update_status_column"]
    print("status", r["id"], "->", r["title"])

PRM = [c for c in json.load(open("raw/phase1_readback.json"))["data"]["boards"][0]["columns"] if c["type"] == "numbers"]
assert len(PRM) == 38

if STEP in ("all", "inputs"):
    # 1. Old checkboxes get "(old)" so the new status titles are unique.
    rename("opp_branding_setup", "Branding Setup (old)")
    rename("boolean_mm88cbqy", "Ongoing Course Support (old)")
    rename("opp_customer_mgmt", "Customer Management (old)")
    # 2. Six existing level columns -> Low / High / Not Sold, with the requested titles.
    for cid, title in [("opp_admission_level", "Admission"), ("opp_mkt_level", "Marketing"), ("opp_branding_level", "Branding Setup"),
                       ("opp_event_level", "Event"), ("opp_support_level", "Ongoing Course Support"), ("color_mm88m6bm", "Customer Mgmt")]:
        set_status_labels(cid, title)
    # 3. Content-dev renames.
    rename("opp_cd_live_hours", "Content Dev Hours – Live")
    rename("opp_cd_self_hours", "Content Dev Hours – Self")
    # 4. New inputs.
    create("op_website", "Website Build", "status", "Low: 52 h, High: 68 h design (once per deal). Not Sold: 0.",
           {"labels": {"0": "Low", "1": "High", "2": "Not Sold"}})
    set_status_labels("op_website", "Website Build")   # grey 'Not Sold', same as the other six
    create("op_cm_weeks", "Customer Mgmt Weeks", "numbers", "Weeks of customer management (× monthly rate ÷ Weeks per Month).")

if STEP in ("all", "pricing"):
    # 5. Link to the Pricing Parameters version + 38 hidden mirrors.
    create("op_prm_version", "⚙️Pricing Version", "board_relation", "Set at creation to the Active Pricing Parameters version (D6). Don't change on existing deals.",
           {"boardIds": [PRM_BOARD], "allowMultipleItems": False, "allowCreateReflectionColumn": False}, ver="2025-10")
    for c in PRM:
        create("opm_" + c["id"][4:], "⚙️" + c["title"], "mirror", "Mirror of Pricing Parameters " + c["id"] + ".",
               {"relation_column": {"op_prm_version": True}, "displayed_linked_columns": [{"board_id": str(PRM_BOARD), "column_ids": [c["id"]]}]}, ver="2025-10")
        if os.environ.get("ONLY_ONE"): break

if STEP in ("all", "gate"):
    # 6. Gate: link the test deal to v1, Admission High + Marketing Low, create op_r_pm_cohort, expect 26.
    cv = {"op_prm_version": {"item_ids": [PRM_ITEM]}, "opp_admission_level": {"label": "High"}, "opp_mkt_level": {"label": "Low"}}
    gql("mutation($b:ID!,$i:ID!,$cv:JSON!) { change_multiple_column_values(board_id:$b, item_id:$i, column_values:$cv) { id } }",
        {"b": OPP, "i": TEST_ITEM, "cv": json.dumps(cv)})
    print("test item linked + levels set")
    f = ('{opm_setup_pm}'
         ' + IF({opp_admission_level}="Not Sold", 0, IF({opp_admission_level}="High", {opm_adm_hi_pm},'
         ' IF(OR({opp_admission_level}="Low", AND({opp_admission_level}="", {color_mm66cssh}="Yes")), {opm_adm_lo_pm}, 0)))'
         ' + IF({opp_mkt_level}="High", {opm_mkt_hi_pm}, IF({opp_mkt_level}="Low", {opm_mkt_lo_pm}, 0))')
    create("op_r_pm_cohort", "⚙️PM / Cohort", "formula", "Setup PM + Admission PM (level) + Marketing PM (level), per cohort. §2.3.", {"formula": f})

def set_formula(cid, formula):
    """create_column on 2025-04 drops the formula text; write it with update_column (2025-10)."""
    c = col_state(cid)
    r = gql("mutation($b:ID!,$c:String!,$rev:String!,$s:JSON!) { update_column(board_id:$b, id:$c, revision:$rev, settings:$s, column_type:formula) { id title } }",
            {"b": OPP, "c": cid, "rev": c["revision"], "s": {"formula": formula}}, ver="2025-10")["update_column"]
    print("formula set", r["id"])

PM_COHORT = ('{opm_setup_pm}'
     ' + IF({opp_admission_level}="Not Sold", 0, IF({opp_admission_level}="High", {opm_adm_hi_pm},'
     ' IF(OR({opp_admission_level}="Low", AND({opp_admission_level}="", {color_mm66cssh}="Yes")), {opm_adm_lo_pm}, 0)))'
     ' + IF({opp_mkt_level}="High", {opm_mkt_hi_pm}, IF({opp_mkt_level}="Low", {opm_mkt_lo_pm}, 0))')
if STEP == "fix_formula":
    set_formula("op_r_pm_cohort", PM_COHORT)

# Views. Keep these lists current as later phases add or modify columns (item level = Opportunity, subitem level = line items).
NEW_ITEM = ["op_website", "op_cm_weeks", "op_prm_version"] + ["opm_" + c["id"][4:] for c in PRM] + ["op_r_pm_cohort"]
MOD_ITEM = ["opp_admission_level", "opp_mkt_level", "opp_branding_level", "opp_event_level", "opp_support_level", "color_mm88m6bm",
            ] + ["opp_cd_live_hours", "opp_cd_self_hours"]   # the 3 "(old)" checkboxes were deleted outside this script on 21-Oct
NEW_SUB, MOD_SUB = [], []
LINE_ITEMS = 18390568739

def view_settings(item_cols, sub_cols):
    opp_cols = [c["id"] for c in gql("query($b:[ID!]) { boards(ids:$b) { columns { id } } }", {"b": [OPP]})["boards"][0]["columns"]]
    li_cols = [c["id"] for c in gql("query($b:[ID!]) { boards(ids:$b) { columns { id } } }", {"b": [LINE_ITEMS]})["boards"][0]["columns"]]
    keep = {"name", "subitems"} | set(item_cols)
    missing = [c for c in item_cols if c not in opp_cols] + [c for c in sub_cols if c not in li_cols]
    if missing: raise SystemExit("columns not on board: %s" % missing)
    order = ["name"] + item_cols + (["subitems"] if "subitems" in opp_cols else [])
    return {"columns": {
        "column_properties": [{"column_id": c, "visible": c in keep} for c in opp_cols],
        "subitems_column_properties": [{"column_id": c, "visible": c == "name" or c in sub_cols} for c in li_cols],
        "column_order": json.dumps(order)}}

def upsert_view(name, item_cols, sub_cols):
    views = gql("query($b:[ID!]) { boards(ids:$b) { views { id name type } } }", {"b": [OPP]}, ver="2025-10")["boards"][0]["views"]
    existing = [v for v in views if v["name"] == name]
    s = view_settings(item_cols, sub_cols)
    if existing:
        r = gql("mutation($v:ID!,$b:ID!,$s:TableViewSettingsInput!) { update_view_table(view_id:$v, board_id:$b, settings:$s) { id name } }",
                {"v": existing[0]["id"], "b": OPP, "s": s}, ver="2025-10")["update_view_table"]
        print("view updated", r["id"], r["name"])
    else:
        r = gql("mutation($b:ID!,$n:String!,$s:TableViewSettingsInput!) { create_view_table(board_id:$b, name:$n, settings:$s) { id name } }",
                {"b": OPP, "n": name, "s": s}, ver="2025-10")["create_view_table"]
        print("view created", r["id"], r["name"])

if STEP == "views":
    upsert_view("new columns", NEW_ITEM, NEW_SUB)
    upsert_view("modified columns", MOD_ITEM, MOD_SUB)

# ============================== Phases 3-8 (approved 21-Oct) ==============================
LI, CAT, COH, PRJ = 18390568739, 18433874513, 18403700733, 18390568732
RESULTS = "phase3to8_results.json"
def B(x): return "{" + x + "}"

def colstate_b(board, cid):
    cs = gql('query($b:[ID!],$c:[String!]) { boards(ids:$b) { columns(ids:$c) { id title type revision settings } } }',
             {"b": [board], "c": [cid]}, ver="2025-10")["boards"][0]["columns"]
    return cs[0] if cs else None

def mk(board, cid, title, ctype, desc, defaults=None):
    if colstate_b(board, cid):
        print("exists, skipped", board, cid); return False
    v = {"b": board, "id": cid, "t": title, "d": desc}
    if defaults is not None: v["def"] = defaults
    q = "mutation($b:ID!,$id:String!,$t:String!,$d:String%s) { create_column(board_id:$b, id:$id, title:$t, column_type:%s, description:$d%s) { id title type } }" % (
        ",$def:JSON" if defaults is not None else "", ctype, ", defaults:$def" if defaults is not None else "")
    r = gql(q, v, ver="2025-10")["create_column"]; print("created", board, r["id"], r["title"], r["type"]); return True

def upd_settings(board, cid, ctype, settings):
    c = colstate_b(board, cid)
    if c["settings"] == settings: print("unchanged", cid); return
    gql("mutation($b:ID!,$c:String!,$rev:String!,$s:JSON!) { update_column(board_id:$b, id:$c, revision:$rev, settings:$s, column_type:%s) { id } }" % ctype,
        {"b": board, "c": cid, "rev": c["revision"], "s": settings}, ver="2025-10")
    after = colstate_b(board, cid)["settings"]
    for k, v in settings.items():
        if after.get(k) != v: raise SystemExit(f"settings did not stick on {cid}: {k} = {after.get(k)!r}, wanted {v!r}")
    print("settings set", board, cid)

def retitle(board, cid, title):
    c = colstate_b(board, cid)
    if c["title"] == title: print("title ok", cid); return
    gql("mutation($b:ID!,$c:String!,$t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id } }", {"b": board, "c": cid, "t": title})
    print("renamed", board, cid, "->", title)

def describe(board, cid, text):
    gql("mutation($b:ID!,$c:String!,$v:String!) { change_column_metadata(board_id:$b, column_id:$c, column_property:description, value:$v) { id } }",
        {"b": board, "c": cid, "v": text}); print("description set", board, cid)

def formula(board, cid, title, desc, f):
    mk(board, cid, title, "formula", desc); upd_settings(board, cid, "formula", {"formula": f})

def mirror(board, cid, title, desc, rel, tboard, tcol, fn=None):
    s = {"relation_column": {rel: True}, "displayed_linked_columns": [{"board_id": str(tboard), "column_ids": [tcol]}]}
    if fn: s["function"] = fn
    mk(board, cid, title, "mirror", desc, s)
    c = colstate_b(board, cid)
    got = c["settings"].get("displayed_linked_columns"); 
    if got != s["displayed_linked_columns"] or (fn and c["settings"].get("function") != fn):
        upd_settings(board, cid, "mirror", s)

PENDING = "pending_ui_repoints.json"
def repoint(board, cid, rel, tboard, tcol, fn=None):
    """API refuses to change an existing mirror's source (notices.column.settings.update.error). Record it for the UI instead."""
    s = {"relation_column": {rel: True}, "displayed_linked_columns": [{"board_id": str(tboard), "column_ids": [tcol]}]}
    if fn: s["function"] = fn
    try:
        upd_settings(board, cid, "mirror", s); return True
    except SystemExit as e:
        p = json.load(open(PENDING)) if os.path.exists(PENDING) else {}
        p[f"{board}:{cid}"] = {"board": board, "column": cid, "title": colstate_b(board, cid)["title"], "via": rel, "should_show": f"{tboard}:{tcol}", "function": fn, "error": str(e)[:160]}
        json.dump(p, open(PENDING, "w"), ensure_ascii=False, indent=1)
        print("RE-POINT REFUSED by API, queued for UI:", board, cid, "->", tcol); return False

def setvals(board, item, cv):
    gql("mutation($b:ID!,$i:ID!,$cv:JSON!) { change_multiple_column_values(board_id:$b, item_id:$i, column_values:$cv) { id } }",
        {"b": board, "i": item, "cv": json.dumps(cv)}); print("values set on", item)

def read_vals(item_ids, cols):
    d = gql("query($i:[ID!],$c:[String!]) { items(ids:$i) { id name column_values(ids:$c) { id text ... on FormulaValue { display_value } ... on MirrorValue { display_value } } } }",
            {"i": item_ids, "c": cols}, ver="2025-10")["items"]
    return {it["id"]: {cv["id"]: (cv.get("display_value") if cv.get("display_value") is not None else cv.get("text")) for cv in it["column_values"]} for it in d}

def check(label, item, vals, expected, tol=0.01):
    bad = []
    for k, e in expected.items():
        v = vals[item].get(k)
        try: ok = abs(float(v) - e) <= tol
        except (TypeError, ValueError): ok = False
        if not ok: bad.append((k, v, e))
    print(f"CHECK {label}: {len(expected) - len(bad)}/{len(expected)} ok", "" if not bad else f"MISMATCH {bad}")
    return bad

# ---- level helpers (Opportunity) ----
ADM_SOLD = 'OR({opp_admission_level}="High", {opp_admission_level}="Low", AND({opp_admission_level}="", {color_mm66cssh}="Yes"))'
def adm(lo, hi): return f'IF({B("opp_admission_level")}="High", {B(hi)}, IF({ADM_SOLD}, {B(lo)}, 0))'
def mkt(lo, hi): return f'IF({B("opp_mkt_level")}="High", {B(hi)}, IF({B("opp_mkt_level")}="Low", {B(lo)}, 0))'
def low_default(col, lo, hi): return f'IF({B(col)}="High", {B(hi)}, IF({B(col)}="Not Sold", 0, {B(lo)}))'   # empty -> Low

RATES = {   # op_r_* : (title, formula, description)
 "op_r_pm_cohort": ("⚙️PM / Cohort", f'{B("opm_setup_pm")} + {adm("opm_adm_lo_pm","opm_adm_hi_pm")} + {mkt("opm_mkt_lo_pm","opm_mkt_hi_pm")}', "Setup + Admission + Marketing PM hours per cohort. §2.3."),
 "op_r_ops_cohort": ("⚙️OPS / Cohort", f'{B("opm_setup_ops")} + {adm("opm_adm_lo_ops","opm_adm_hi_ops")} + {mkt("opm_mkt_lo_ops","opm_mkt_hi_ops")}', "Setup + Admission + Marketing OPS hours per cohort. §2.3."),
 "op_r_pm_week": ("⚙️PM / Week", f'{low_default("opp_support_level","opm_ong_lo_pm_m","opm_ong_hi_pm_m")} / {B("opm_wk_per_month")}', "Ongoing Course Support PM per week (monthly ÷ weeks per month). Not Sold = 0, empty = Low."),
 "op_r_ops_week": ("⚙️OPS / Week", f'{low_default("opp_support_level","opm_ong_lo_ops_m","opm_ong_hi_ops_m")} / {B("opm_wk_per_month")}', "Ongoing Course Support OPS per week. Not Sold = 0, empty = Low."),
 "op_r_car_cohort": ("⚙️Career / Cohort", f'{B("opm_car_adm")} + {B("opm_car_ws")} + {B("opm_car_sup")}', "Career admission + workshops + support per cohort (applied on lines with placement)."),
 "op_r_car_week": ("⚙️Career / Week", B("opm_car_wk"), "Career support per placement-support week."),
 "op_r_auto_cohort": ("⚙️Automation / Cohort", f'IF({ADM_SOLD}, {B("opm_auto")}, 0)', "Automation hours per cohort, only when Admission is sold."),
 "op_r_des_cohort": ("⚙️Design / Cohort", B("opm_des_tpl"), "Design templates per cohort."),
 "op_r_ls_per_cohort": ("⚙️LS / Cohort", B("opm_ls_per_cohort"), "LS hours added per cohort on each line."),
}
WK = 4.2
EXP_RATES = {"op_r_pm_cohort": 26, "op_r_ops_cohort": 56, "op_r_pm_week": 12 / WK, "op_r_ops_week": 25 / WK, "op_r_car_cohort": 107.5,
             "op_r_car_week": 14, "op_r_auto_cohort": 8, "op_r_des_cohort": 12, "op_r_ls_per_cohort": 2.5}
TEST_OPP_INPUTS = {"opp_support_level": {"label": "High"}, "color_mm88m6bm": {"label": "Low"}, "op_cm_weeks": "20",
                   "opp_event_level": {"label": "Low"}, "opp_events": "2", "opp_branding_level": {"label": "Low"},
                   "op_website": {"label": "Low"}, "opp_learning_manual": "5", "opp_cd_live_hours": "10", "opp_cd_self_hours": "6"}

if STEP == "p3":
    setvals(OPP, TEST_ITEM, TEST_OPP_INPUTS)     # §8 Opportunity inputs on the test deal
    for cid, (t, f, d) in RATES.items():
        formula(OPP, cid, t, d, f)
    v = read_vals([TEST_ITEM], list(RATES))
    check("Opportunity rates (§8)", str(TEST_ITEM), v, EXP_RATES)

# ---- Phase 4: line items (Opportunity subitems board) ----
LI_NUMBERS = [("li_pweeks", "Placement Support Weeks", "Weeks of placement support (שבועות ליווי להשמה). Required when Includes Placements is checked."),
              ("li_placement_pct", "Placement %", "Placement target %. Required when Includes Placements is checked."),
              ("li_ls_base", "LS Base Hours", "Copied from Catalog LS Base Hours (editable). Replaces the old mirror li_total_hours."),
              ("li_expert", "Content Expert Hours", "Copied from Catalog Content Expert Hours (editable). Not × Quantity (D4). Replaces mirror li_expert_hours."),
              ("li_bo", "Back Office Hours / Cohort", "Copied from Catalog Back office H (editable). Replaces mirror li_bo_hours.")]
LI_RATE_MIRRORS = [(f"li_r_{k[5:]}", t) for k, (t, _, _) in RATES.items()]
LI_FORMULAS = {   # new formulas: id -> (title, formula, description)
 "li_pm_c": ("PM Hours / Cohort", f'{B("li_r_pm_cohort")} + {B("li_r_pm_week")} * {B("li_months")}', "Per cohort: PM/cohort + PM/week × Training Weeks."),
 "li_ops_c": ("OPS Hours / Cohort", f'{B("li_r_ops_cohort")} + {B("li_r_ops_week")} * {B("li_months")}', "Per cohort: OPS/cohort + OPS/week × Training Weeks."),
 "li_car_c": ("Career Hours / Cohort", f'IF({B("li_placements")}, {B("li_r_car_cohort")} + {B("li_r_car_week")} * {B("li_pweeks")}, 0)', "Per cohort, only with placement (D11)."),
 "li_part_t": ("Total Participants", f'{B("li_participants")} * {B("li_qty")}', "Participants / Cohort × Quantity."),
 "li_live_t": ("Total Live Hours", f'{B("li_live_hours")} * {B("li_qty")}', "Live hours × Quantity."),
 "li_self_t": ("Total Self Hours", f'{B("li_self_hours")} * {B("li_qty")}', "Self hours × Quantity."),
 "li_trn_t": ("Total Training Hours", f'{B("li_trn_cohort")} * {B("li_qty")}', "Training hours / cohort × Quantity."),
 "li_bo_t": ("Total Back Office Hours", f'{B("li_bo")} * {B("li_qty")}', "Back office / cohort × Quantity."),
 "li_one": ("⚙️Line Item Counter", "1", "Always 1; summed by Opportunity ⚙️Line Items Count."),
}
LI_REPURPOSE = {  # existing placeholder formulas ("0") -> new formula + title
 "formula_mm89hfy4": ("PM Hours Total", f'{B("li_pm_c")} * {B("li_qty")}'),
 "formula_mm89qcd4": ("OPS Hours Total", f'{B("li_ops_c")} * {B("li_qty")}'),
 "formula_mm89b2z4": ("Career Hours Total", f'{B("li_car_c")} * {B("li_qty")}'),
 "formula_mm897s4c": ("Automation Hours Total", f'{B("li_r_auto_cohort")} * {B("li_qty")}'),
 "formula_mm89fxr7": ("Design Hours Total", f'{B("li_r_des_cohort")} * {B("li_qty")}'),
 "formula_mm89sm5r": ("LS Hours (line)", f'{B("li_ls_base")} + {B("li_r_ls_per_cohort")} * {B("li_qty")}'),
}
LI_CHECK = ('IF(AND({li_ls_level}<>"", {li_qty}>0, {li_participants}>0, {li_months}>0, {li_rate}>0, '
            'OR(NOT({li_placements}), AND({li_placement_pct}>0, {li_pweeks}>0))), "Complete", '
            'CONCATENATE("Missing: ", IF({li_ls_level}<>"", "", "Catalog/LS Level "), IF({li_qty}>0, "", "Quantity "), '
            'IF({li_participants}>0, "", "Participants "), IF({li_months}>0, "", "Training Weeks "), IF({li_rate}>0, "", "Rate "), '
            'IF(AND({li_placements}, NOT({li_placement_pct}>0)), "Placement % ", ""), IF(AND({li_placements}, NOT({li_pweeks}>0)), "Placement Weeks ", "")))')
LI_RENAMES = {"li_months": "Training Weeks", "li_cohort_months": "Total Training Weeks", "li_participants": "Participants / Cohort"}
TEST_LINES = {
 "TEST Line A": {"li_catalog_item": {"item_ids": [13200517116]}, "li_parent_opp": {"item_ids": [TEST_ITEM]}, "li_qty": "3", "li_months": "5",
                 "li_placements": {"checked": "true"}, "li_pweeks": "25", "li_placement_pct": "50", "li_participants": "25", "li_rate": "270",
                 "li_ls_base": "28", "li_expert": "9", "li_bo": "8"},
 "TEST Line B": {"li_catalog_item": {"item_ids": [13200527235]}, "li_parent_opp": {"item_ids": [TEST_ITEM]}, "li_qty": "1", "li_months": "3",
                 "li_participants": "20", "li_rate": "300", "li_ls_base": "4", "li_expert": "0", "li_bo": "4"},
}
def line_expected(q, w, placement, pweeks, part, live, self_, trn, ls_base, bo):
    r = EXP_RATES
    pm_c = r["op_r_pm_cohort"] + r["op_r_pm_week"] * w; ops_c = r["op_r_ops_cohort"] + r["op_r_ops_week"] * w
    car_c = (r["op_r_car_cohort"] + r["op_r_car_week"] * pweeks) if placement else 0
    return {"li_pm_c": pm_c, "li_ops_c": ops_c, "li_car_c": car_c, "formula_mm89hfy4": pm_c * q, "formula_mm89qcd4": ops_c * q,
            "formula_mm89b2z4": car_c * q, "formula_mm897s4c": r["op_r_auto_cohort"] * q, "formula_mm89fxr7": r["op_r_des_cohort"] * q,
            "formula_mm89sm5r": ls_base + r["op_r_ls_per_cohort"] * q, "li_part_t": part * q, "li_live_t": live * q, "li_self_t": self_ * q,
            "li_trn_t": trn * q, "li_bo_t": bo * q, "li_cohort_months": w * q, "li_one": 1, "li_trn_cohort": trn}
# Catalog values for the two test products: PM 101 = 40 live / 0 self / 40 total; AI Upgrade (With Self) = 23 / 7 / 30
EXP_LINES = {"TEST Line A": line_expected(3, 5, True, 25, 25, 40, 0, 40, 28, 8),
             "TEST Line B": line_expected(1, 3, False, 0, 20, 23, 7, 30, 4, 4)}

def test_lines():
    d = gql("query($i:[ID!]) { items(ids:$i) { subitems { id name } } }", {"i": [TEST_ITEM]})["items"][0]["subitems"] or []
    have = {s["name"]: s["id"] for s in d}
    return have

if STEP == "p4":
    for cid, t, d in LI_NUMBERS: mk(LI, cid, t, "numbers", d)
    mirror(LI, "li_trn_cohort", "Total Training Hours / Cohort", "Mirror of Catalog 'Total Hours (Live & Self)'.", "li_catalog_item", CAT, "numeric_mm7thk2x")
    for cid, t in LI_RATE_MIRRORS:
        mirror(LI, cid, t, "Mirror of the Opportunity rate (via ⚙️Parent Opportunity).", "li_parent_opp", OPP, "op_r_" + cid[5:])
    for cid, (t, f, d) in LI_FORMULAS.items(): formula(LI, cid, t, d, f)
    for cid, (t, f) in LI_REPURPOSE.items():
        upd_settings(LI, cid, "formula", {"formula": f}); retitle(LI, cid, t)
    upd_settings(LI, "li_check", "formula", {"formula": LI_CHECK})
    for cid, t in LI_RENAMES.items(): retitle(LI, cid, t)
    have = test_lines()
    for name, cv in TEST_LINES.items():
        if name in have: print("test line exists", name, have[name]); continue
        r = gql("mutation($p:ID!,$n:String!,$cv:JSON!) { create_subitem(parent_item_id:$p, item_name:$n, column_values:$cv) { id } }",
                {"p": TEST_ITEM, "n": name, "cv": json.dumps(cv)})["create_subitem"]
        print("created test line", name, r["id"])

if STEP in ("p4", "p4check"):
    have = test_lines()
    cols = sorted({k for e in EXP_LINES.values() for k in e} | {"li_check", "li_ready", "li_r_pm_week"})
    v = read_vals(list(have.values()), cols)
    for name, iid in have.items():
        if name in EXP_LINES:
            check(name, iid, v, EXP_LINES[name])
            print("   li_check:", v[iid].get("li_check"), "| li_ready:", v[iid].get("li_ready"))

# ---- Phase 5: Opportunity totals ----
OPP_SUMS_NEW = [("op_sum_bo", "Σ Back Office (lines)", "li_bo_t"), ("op_sum_live", "Σ Live Hours (lines)", "li_live_t"),
                ("op_sum_self", "Σ Self Hours (lines)", "li_self_t"), ("op_sum_trn", "Σ Training Hours (lines)", "li_trn_t"),
                ("op_li_count", "⚙️Line Items Count", "li_one")]
OPP_SUMS_RENAME = {"lookup_mm89667w": "Σ PM (lines)", "lookup_mm89s51s": "Σ OPS (lines)", "lookup_mm89k0tq": "Σ Career (lines)",
                   "lookup_mm89ydqn": "Σ Automation (lines)", "lookup_mm89qv7b": "Σ Design (lines)", "lookup_mm88cm47": "Σ LS Hours (lines)",
                   "opp_cohort_months": "Total Training Weeks"}
OPP_REPOINT = {"lookup_mm88cm47": "formula_mm89sm5r", "opp_participants": "li_part_t", "opp_expert_hours": "li_expert"}
WEB = f'IF({B("op_website")}="High", {B("opm_des_web_hi")}, IF({B("op_website")}="Low", {B("opm_des_web_lo")}, 0))'
BRAND = f'IF(OR({B("opp_branding_level")}="Low", {B("opp_branding_level")}="High"), {B("opm_des_brand")}, 0)'   # parked: any level = sold, 50 h
OPP_TOTALS = {
 "op_ev_pm": ("⚙️Events PM", f'{B("opp_events")} * {low_default("opp_event_level","opm_ev_lo_pm","opm_ev_hi_pm")}', "Number of Events × event PM rate (Not Sold = 0, empty = Low)."),
 "op_ev_ops": ("⚙️Events OPS", f'{B("opp_events")} * {low_default("opp_event_level","opm_ev_lo_ops","opm_ev_hi_ops")}', "Number of Events × event OPS rate."),
 "op_cm_pm": ("⚙️Cust Mgmt PM", f'{low_default("color_mm88m6bm","opm_cm_lo_pm_m","opm_cm_hi_pm_m")} / {B("opm_wk_per_month")} * {B("op_cm_weeks")}', "Customer Mgmt monthly PM ÷ weeks per month × CM Weeks."),
 "op_cm_ops": ("⚙️Cust Mgmt OPS", f'{low_default("color_mm88m6bm","opm_cm_lo_ops_m","opm_cm_hi_ops_m")} / {B("opm_wk_per_month")} * {B("op_cm_weeks")}', "Customer Mgmt monthly OPS ÷ weeks per month × CM Weeks."),
 "op_tot_pm": ("Total PM Hours", f'{B("lookup_mm89667w")} + {B("op_ev_pm")} + {B("op_cm_pm")}', "Σ line PM + Events PM + Cust Mgmt PM."),
 "op_tot_ops": ("Total OPS Hours", f'{B("lookup_mm89s51s")} + {B("op_ev_ops")} + {B("op_cm_ops")}', "Σ line OPS + Events OPS + Cust Mgmt OPS."),
 "op_tot_learning": ("Total Learning Hours", f'{B("lookup_mm88cm47")} + {B("opp_learning_manual")} + {B("opm_dev_live_ls")} * {B("opp_cd_live_hours")} + {B("opm_dev_self_ls")} * {B("opp_cd_self_hours")}', "Σ LS lines + manual learning + content-dev conversion (Live ×2, Self ×4)."),
 "op_tot_expert": ("Total Expert Hours", f'{B("opp_expert_hours")} + {B("opm_dev_live_exp")} * {B("opp_cd_live_hours")} + {B("opm_dev_self_exp")} * {B("opp_cd_self_hours")}', "Σ line Expert (not × Q) + content-dev conversion (×1)."),
 "op_tot_career": ("Total Career Hours", B("lookup_mm89k0tq"), "Σ line Career totals."),
 "op_tot_auto": ("Total Automation Hours", B("lookup_mm89ydqn"), "Σ line Automation totals."),
 "op_tot_design": ("Total Design Hours", f'{B("lookup_mm89qv7b")} + {BRAND} + {WEB} + IF({ADM_SOLD}, {B("opm_des_adm")}, 0)', "Σ line Design + Branding (parked: any level = 50 h) + Website + Admission support."),
 "op_n_cohorts": ("⚙️# Cohorts", B("opp_cohorts"), "Wrapper so Projects can mirror a formula."),
 "op_n_participants": ("⚙️# Participants", B("opp_participants"), "Wrapper so Projects can mirror a formula."),
}
A_, B_ = EXP_LINES["TEST Line A"], EXP_LINES["TEST Line B"]
S = lambda k: A_[k] + B_[k]
EXP_OPP = {"lookup_mm89667w": S("formula_mm89hfy4"), "op_ev_pm": 10, "op_ev_ops": 30, "op_cm_pm": 8 / WK * 20, "op_cm_ops": 0,
           "op_tot_pm": S("formula_mm89hfy4") + 10 + 8 / WK * 20, "op_tot_ops": S("formula_mm89qcd4") + 30,
           "op_tot_learning": S("formula_mm89sm5r") + 5 + 2 * 10 + 4 * 6, "op_tot_expert": 9 + 0 + 10 + 6,
           "op_tot_career": S("formula_mm89b2z4"), "op_tot_auto": S("formula_mm897s4c"), "op_tot_design": S("formula_mm89fxr7") + 50 + 52 + 24,
           "op_n_cohorts": 4, "op_n_participants": S("li_part_t"), "opp_cohort_months": S("li_cohort_months"), "op_sum_bo": S("li_bo_t"),
           "op_sum_trn": S("li_trn_t"), "op_sum_live": S("li_live_t"), "op_sum_self": S("li_self_t"), "op_li_count": 2, "opp_li_ready": 0}

if STEP == "p5":
    for cid, t, src in OPP_SUMS_NEW:
        mirror(OPP, cid, t, f"Σ of line-item {src}.", "subitems", LI, src, fn="sum")
    for cid, src in OPP_REPOINT.items(): repoint(OPP, cid, "subitems", LI, src, fn="sum")
    for cid, t in OPP_SUMS_RENAME.items(): retitle(OPP, cid, t)
    for cid, (t, f, d) in OPP_TOTALS.items(): formula(OPP, cid, t, d, f)

if STEP in ("p5", "p5check"):
    v = read_vals([TEST_ITEM], list(EXP_OPP))
    print("expected:", {k: round(x, 2) for k, x in EXP_OPP.items() if k.startswith("op_tot")})
    check("Opportunity totals", str(TEST_ITEM), v, EXP_OPP)

if STEP == "repoint_probe":
    c = colstate_b(OPP, "lookup_mm88cm47"); s = dict(c["settings"])
    s["displayed_linked_columns"] = [{"board_id": str(LI), "column_ids": ["formula_mm89sm5r"]}]
    for variant in ("full", "no_function"):
        s2 = dict(s) if variant == "full" else {k: v for k, v in s.items() if k != "function"}
        try:
            gql("mutation($b:ID!,$c:String!,$rev:String!,$s:JSON!) { update_column(board_id:$b, id:$c, revision:$rev, settings:$s, column_type:mirror) { id } }",
                {"b": OPP, "c": "lookup_mm88cm47", "rev": colstate_b(OPP, "lookup_mm88cm47")["revision"], "s": s2}, ver="2025-10")
            print(variant, "OK ->", colstate_b(OPP, "lookup_mm88cm47")["settings"]); break
        except SystemExit as e:
            print(variant, "failed:", str(e)[:200])

if STEP == "p5_learning":
    # lookup_mm88cm47 can't be re-pointed by the API; lookup_mm894g60 already sums formula_mm89sm5r (LS Hours line).
    f = f'{B("lookup_mm894g60")} + {B("opp_learning_manual")} + {B("opm_dev_live_ls")} * {B("opp_cd_live_hours")} + {B("opm_dev_self_ls")} * {B("opp_cd_self_hours")}'
    upd_settings(OPP, "op_tot_learning", "formula", {"formula": f})
    v = read_vals([TEST_ITEM], ["op_tot_learning"])
    check("Total Learning", str(TEST_ITEM), v, {"op_tot_learning": EXP_OPP["op_tot_learning"]})

# ---- Phase 6: Catalog ----
if STEP == "p6":
    upd_settings(CAT, "cat_ls_hours", "formula", {"formula": 'IF({cat_ls_level}="High", 28, IF({cat_ls_level}="Low", 4, 0))'})
    retitle(CAT, "cat_ls_hours", "LS Base Hours")
    describe(CAT, "cat_ls_hours", "LS base hours per product line: High 28, Low 4 (D4). On a line item: LS Hours = base + 2.5 × cohorts.")
    describe(CAT, "cat_ls_level", "Low = 4 LS base hours + 0 expert. High = 28 LS base hours + 9 expert. LS Hours on a line = base + 2.5 × cohorts.")
    mk(CAT, "cat_training_weeks", "Training Weeks", "numbers", "Training weeks per cohort. Copied to the line item (editable) by M2.")
    cs = {c["id"]: c for c in gql("query($b:[ID!]) { boards(ids:$b) { columns { id title type settings_str } } }", {"b": [CAT]})["boards"][0]["columns"]}
    print({k: (cs[k]["title"], cs[k]["type"]) for k in ("cat_ls_hours", "cat_training_weeks")}, json.loads(cs["cat_ls_hours"]["settings_str"]))

# ---- Phase 7: Cohorts + Projects ----
COH_LI = [("co_rate", "Training Hour Rate (planned)", "li_rate"), ("co_weeks", "Training Weeks (planned)", "li_months"),
          ("co_participants", "Participants (planned)", "li_participants"), ("co_placement", "Includes Placement (planned)", "li_placements"),
          ("co_placement_pct", "Placement % (planned)", "li_placement_pct"), ("co_pweeks", "Placement Support Weeks (planned)", "li_pweeks"),
          ("co_bo", "Back Office Hours (planned)", "li_bo"), ("co_expert", "Content Expert Hours (planned)", "li_expert"),
          ("co_pm", "PM Hours (planned)", "li_pm_c"), ("co_ops", "OPS Hours (planned)", "li_ops_c"), ("co_car", "Career Hours (planned)", "li_car_c")]
COH_CAT = [("co_live", "Live Training Hours", "numeric_mm7tv0sp"), ("co_self", "Self Training Hours", "numeric_mm7t38zg"),
           ("co_trn", "Total Training Hours", "numeric_mm7thk2x")]
PRJ_REPOINT = {"prj_pm_hours": "op_tot_pm", "prj_ops_hours": "op_tot_ops", "prj_learning_hours": "op_tot_learning",
               "prj_career_hours": "op_tot_career", "prj_auto_hours": "op_tot_auto", "prj_design_hours": "op_tot_design",
               "lookup_mm8825n1": "op_n_cohorts", "lookup_mm88t3m5": "op_n_participants"}
if STEP == "p7":
    for cid, t, src in COH_LI:
        mirror(COH, cid, t, f"Mirror of line item {src} via Source Line Item (D8).", "board_relation_mm88gj2b", LI, src)
    for cid, t, src in COH_CAT:
        mirror(COH, cid, t, f"Mirror of Catalog {src} via Catalog Item.", "co_catalog_item", CAT, src)
    for cid, src in PRJ_REPOINT.items(): repoint(PRJ, cid, "board_relation_mm7y54c8", OPP, src, fn="sum")
    retitle(PRJ, "lookup_mm88t3m5", "Total Participants")
    retitle(PRJ, "lookup_mm8825n1", "Number of Cohorts")
    retitle(PRJ, "prj_deal_amount", "Total Contract Value")
    mirror(PRJ, "prj_expert", "Total Expert Hours", "Σ Opportunity Total Expert Hours.", "board_relation_mm7y54c8", OPP, "op_tot_expert", fn="sum")

# ---- Views on every board touched (item + subitem level) ----
def board_view_settings(board, item_cols, sub_cols, show_subitems):
    cols = gql("query($b:[ID!]) { boards(ids:$b) { columns { id type settings_str } } }", {"b": [board]})["boards"][0]["columns"]
    ids = [c["id"] for c in cols]
    sub = [c for c in cols if c["type"] == "subtasks"]
    sub_board = json.loads(sub[0]["settings_str"]).get("boardIds", [None])[0] if sub else None
    sub_ids = [c["id"] for c in gql("query($b:[ID!]) { boards(ids:$b) { columns { id } } }", {"b": [sub_board]})["boards"][0]["columns"]] if sub_board else []
    missing = [c for c in item_cols if c not in ids] + [c for c in sub_cols if c not in sub_ids]
    if missing: raise SystemExit(f"view columns not on board {board}: {missing}")
    keep = {"name"} | set(item_cols) | ({sub[0]["id"]} if (sub and show_subitems) else set())
    s = {"columns": {"column_properties": [{"column_id": c, "visible": c in keep} for c in ids],
                     "column_order": json.dumps(["name"] + item_cols + ([sub[0]["id"]] if (sub and show_subitems) else []))}}
    if sub_ids: s["columns"]["subitems_column_properties"] = [{"column_id": c, "visible": c == "name" or c in sub_cols} for c in sub_ids]
    return s

def upsert_board_view(board, name, item_cols, sub_cols=(), show_subitems=False):
    views = gql("query($b:[ID!]) { boards(ids:$b) { views { id name } } }", {"b": [board]}, ver="2025-10")["boards"][0]["views"]
    ex = [v for v in views if v["name"] == name]
    s = board_view_settings(board, list(item_cols), list(sub_cols), show_subitems)
    if ex:
        gql("mutation($v:ID!,$b:ID!,$s:TableViewSettingsInput!) { update_view_table(view_id:$v, board_id:$b, settings:$s) { id } }", {"v": ex[0]["id"], "b": board, "s": s}, ver="2025-10")
        vid = ex[0]["id"]; print("view updated", board, name, vid)
    else:
        vid = gql("mutation($b:ID!,$n:String!,$s:TableViewSettingsInput!) { create_view_table(board_id:$b, name:$n, settings:$s) { id } }", {"b": board, "n": name, "s": s}, ver="2025-10")["create_view_table"]["id"]
        print("view created", board, name, vid)
    # read back: shown = all minus hidden
    st = gql("query($b:[ID!],$v:[ID!]) { boards(ids:$b) { columns { id } views(ids:$v) { settings } } }", {"b": [board], "v": [vid]}, ver="2025-10")["boards"][0]
    hidden = {p["column_id"] for p in st["views"][0]["settings"]["columns"]["column_properties"] if p["visible"] is False}
    shown = [c["id"] for c in st["columns"] if c["id"] not in hidden]
    want = {"name"} | set(item_cols)
    print(f"   shows {len(shown)} columns; missing from view: {sorted(want - set(shown))}; unexpected: {sorted(set(shown) - want - {'subitems', 'subtasks_mm21bg4g'})}")
    return vid

VIEW_SPEC = {
 OPP: {"new": NEW_ITEM + [k for k in RATES if k != "op_r_pm_cohort"] + [c for c, _, _ in OPP_SUMS_NEW] + list(OPP_TOTALS),
       "mod": MOD_ITEM + list(OPP_SUMS_RENAME) + ["opp_participants", "opp_expert_hours"],
       "new_sub": [c for c, _, _ in LI_NUMBERS] + ["li_trn_cohort"] + [c for c, _ in LI_RATE_MIRRORS] + list(LI_FORMULAS),
       "mod_sub": list(LI_REPURPOSE) + ["li_check"] + list(LI_RENAMES), "show_subitems": True},
 CAT: {"new": ["cat_training_weeks"], "mod": ["cat_ls_hours", "cat_ls_level"], "new_sub": [], "mod_sub": [], "show_subitems": False},
 COH: {"new": [c for c, _, _ in COH_LI + COH_CAT], "mod": [], "new_sub": [], "mod_sub": [], "show_subitems": False},
 PRJ: {"new": ["prj_expert"], "mod": ["lookup_mm8825n1", "lookup_mm88t3m5", "prj_deal_amount"], "new_sub": [], "mod_sub": [], "show_subitems": False},
}
if STEP == "views_all":
    out = {}
    for board, sp in VIEW_SPEC.items():
        out[board] = {"new columns": upsert_board_view(board, "new columns", sp["new"], sp["new_sub"], sp["show_subitems"]),
                      "modified columns": upsert_board_view(board, "modified columns", sp["mod"], sp["mod_sub"], sp["show_subitems"])}
    json.dump(out, open("views.json", "w"), indent=1)

# ---- Phase 8: approved deletions, each gated on: no dependents now, backup written, no real data ----
import re as _re
BACKUP_DIR = "/home/user/main/backup"
def dependents_now(board, cid):
    ws = gql("query { boards(workspace_ids:[13463480], limit:200) { id } }")["boards"]
    deps = []
    ids = [b["id"] for b in ws]
    for i in range(0, len(ids), 25):
        for b in gql("query($b:[ID!]) { boards(ids:$b, limit:50) { id columns { id type settings_str } } }", {"b": ids[i:i+25]})["boards"]:
            for c in b["columns"]:
                s = json.loads(c["settings_str"] or "{}")
                if c["type"] == "formula" and str(b["id"]) == str(board) and _re.search(r"\{" + _re.escape(cid) + r"(#\w+)?\}", s.get("formula", "")):
                    deps.append(f'{b["id"]}:{c["id"]} (formula)')
                if c["type"] == "mirror":
                    for tb, cols in (s.get("displayed_linked_columns") or {}).items():
                        if str(tb) == str(board) and cid in cols: deps.append(f'{b["id"]}:{c["id"]} (mirror)')
                    if str(b["id"]) == str(board) and cid in (s.get("relation_column") or {}): deps.append(f'{b["id"]}:{c["id"]} (mirror relation)')
    return deps

def backup_values(board, cid):
    rows, cur = [], None
    F = "cursor items { id name column_values(ids:$c) { text value ... on MirrorValue { display_value } ... on FormulaValue { display_value } } }"
    d = gql("query($b:[ID!],$c:[String!]) { boards(ids:$b) { items_page(limit:200) { %s } } }" % F, {"b": [board], "c": [cid]})["boards"][0]["items_page"]
    while True:
        for it in d["items"]:
            cv = it["column_values"][0] if it["column_values"] else {}
            rows.append({"item_id": it["id"], "name": it["name"], "text": cv.get("text"), "value": cv.get("value"), "display_value": cv.get("display_value")})
        if not d["cursor"]: break
        d = gql("query($k:String!,$c:[String!]) { next_items_page(limit:200, cursor:$k) { %s } }" % F, {"k": d["cursor"], "c": [cid]})["next_items_page"]
    os.makedirs(BACKUP_DIR, exist_ok=True)
    json.dump({"board": board, "column": cid, "settings": colstate_b(board, cid), "rows": rows}, open(f"{BACKUP_DIR}/{board}_{cid}.json", "w"), ensure_ascii=False, indent=1)
    nonempty = [r for r in rows if (r["display_value"] or r["text"] or "").strip() not in ("",) and r["value"] not in ('{"checked":false}',)]
    return len(rows), nonempty

TEST_IDS = {"13349045463", "13349455069", "13349515700", "13334326395"}   # TEST KINDAA, its 2 test lines, old Kindaa test line "1"
def guarded_delete(board, cid):
    if not colstate_b(board, cid): print("already gone", board, cid); return "gone"
    deps = dependents_now(board, cid)
    n, nonempty = backup_values(board, cid)
    real = [r for r in nonempty if r["item_id"] not in TEST_IDS]
    print(f"{board}:{cid} rows={n} nonempty={len(nonempty)} real_nonempty={len(real)} dependents={deps}")
    if deps or real:
        print("   STOP: not deleting", cid); return "stopped"
    gql("mutation($b:ID!,$c:String!) { delete_column(board_id:$b, column_id:$c) { id } }", {"b": board, "c": cid})
    print("   deleted", cid, "(backup:", f"{BACKUP_DIR}/{board}_{cid}.json)"); return "deleted"

if STEP == "p8":
    res = {}
    for board, cid in [(OPP, "color_mm886byb"), (LI, "li_bo_hours"), (LI, "li_expert_hours"), (COH, "co_months")]:
        res[f"{board}:{cid}"] = guarded_delete(board, cid)
    json.dump(res, open("p8_results.json", "w"), indent=1); print(res)

# ---- 22-Oct decisions: LS sum option A, Projects option B, branding dropped ----
PRJ_NEW = [("prj_tot_pm", "Total PM Hours", "op_tot_pm"), ("prj_tot_ops", "Total OPS Hours", "op_tot_ops"),
           ("prj_tot_learning", "Total Learning Hours", "op_tot_learning"), ("prj_tot_career", "Career Hours", "op_tot_career"),
           ("prj_tot_auto", "Automation Hours", "op_tot_auto"), ("prj_tot_design", "Design Hours", "op_tot_design")]
DESIGN_NO_BRAND = f'{B("lookup_mm89qv7b")} + {WEB} + IF({ADM_SOLD}, {B("opm_des_adm")}, 0)'
if STEP == "fix2":
    res = {}
    # Option A: lookup_mm894g60 stays as the LS sum; lookup_mm88cm47 and its source li_total_hours go.
    res["lookup_mm88cm47"] = guarded_delete(OPP, "lookup_mm88cm47")
    if res["lookup_mm88cm47"] in ("deleted", "gone"):
        res["li_total_hours"] = guarded_delete(LI, "li_total_hours")
        retitle(OPP, "lookup_mm894g60", "Σ LS Hours (lines)")
        describe(OPP, "lookup_mm894g60", "Σ of line-item LS Hours (line) (formula_mm89sm5r).")
    # Option B: drop the 6 broken Projects mirrors, then recreate them pointing at the Opportunity totals.
    for old, (cid, t, src) in zip(["prj_pm_hours", "prj_ops_hours", "prj_learning_hours", "prj_career_hours", "prj_auto_hours", "prj_design_hours"], PRJ_NEW):
        res[old] = guarded_delete(PRJ, old)
        if res[old] in ("deleted", "gone"):
            mirror(PRJ, cid, t, f"Σ Opportunity {src} via Opportunity link.", "board_relation_mm7y54c8", OPP, src, fn="sum")
    # Branding dropped from the Design total.
    describe(OPP, "op_tot_design", "Σ line Design + Website + Admission support (branding dropped 22-Oct).")
    upd_settings(OPP, "op_tot_design", "formula", {"formula": DESIGN_NO_BRAND})
    v = read_vals([TEST_ITEM], ["op_tot_design", "op_tot_learning"])
    check("Design without branding / Learning", str(TEST_ITEM), v, {"op_tot_design": EXP_OPP["op_tot_design"] - 50, "op_tot_learning": EXP_OPP["op_tot_learning"]})
    json.dump(res, open("fix2_results.json", "w"), indent=1); print(res)

if STEP in ("fix2", "views_all"):
    VIEW_SPEC[OPP]["mod"] = [c for c in VIEW_SPEC[OPP]["mod"] if c not in ("lookup_mm88cm47",)] + ["lookup_mm894g60", "op_tot_design"][:1]
    VIEW_SPEC[PRJ]["new"] = ["prj_expert"] + [c for c, _, _ in PRJ_NEW]
if STEP == "fix2":
    out = {}
    for board, sp in VIEW_SPEC.items():
        out[board] = {"new columns": upsert_board_view(board, "new columns", sp["new"], sp["new_sub"], sp["show_subitems"]),
                      "modified columns": upsert_board_view(board, "modified columns", sp["mod"], sp["mod_sub"], sp["show_subitems"])}
    json.dump(out, open("views.json", "w"), indent=1)

# ============================== Phase 9: Make scenarios (approved 26-Oct) ==============================
MAKE = "https://eu1.make.com/api/v2"; TEAM = 387027; FOLDER = 381378; CONN = 3107441; M3_ID = 7213714
PRM_ITEM_ID = 13348993282
MLOG = open("make_mutations.log", "a")
def make(method, path, body=None):
    args = ["curl", "-sS", "-X", method, MAKE + path, "-H", "Content-Type: application/json", "-w", "\n%{http_code}"]
    if body is not None: args += ["--data-binary", "@-"]
    r = subprocess.run(args, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    out, code = r.stdout.rsplit("\n", 1)
    d = json.loads(out) if out.strip().startswith(("{", "[")) else {"raw": out}
    if method != "GET":
        MLOG.write(json.dumps({"t": time.strftime("%H:%M:%S"), "m": method, "p": path, "code": code, "resp": d}, ensure_ascii=False)[:20000] + "\n"); MLOG.flush()
    if not code.startswith("2"): raise SystemExit(f"Make {method} {path} -> {code}: {json.dumps(d, ensure_ascii=False)[:800]}")
    return d

def gq_module(mid, query, variables=None, x=0, y=0, flt=None):
    m = {"id": mid, "module": "monday:ExecuteGraphQLQueryV2", "version": 2, "parameters": {"__IMTCONN__": CONN},
         "mapper": {"method": "POST", "queryBody": query, "variablesDataSource": "array"},
         "metadata": {"designer": {"x": x, "y": y}, "restore": {"expect": {"method": {"mode": "chose", "label": "POST (queries and mutations)"},
                      "variables": {"mode": "chose"}, "apiVersion": {"mode": "chose", "label": "Empty"}, "variablesDataSource": {"mode": "chose", "label": "Form"}},
                      "parameters": {"__IMTCONN__": {"data": {"scoped": "true", "connection": "monday"}, "label": "Ariella's Monday connection"}}},
                      "parameters": [{"name": "__IMTCONN__", "type": "account:monday", "label": "Connection", "required": True}]}}
    if variables: m["mapper"]["variables"] = [{"key": k, "value": v} for k, v in variables]; m["metadata"]["restore"]["expect"]["variables"]["items"] = [None] * len(variables)
    if flt: m["filter"] = flt
    return m
def cond(a, o, b=None):
    c = {"a": a, "o": o}
    if b is not None: c["b"] = b
    return c
def router(mid, routes, x=0, y=0, flt=None):
    m = {"id": mid, "module": "builtin:BasicRouter", "version": 1, "mapper": None, "metadata": {"designer": {"x": x, "y": y}}, "routes": [{"flow": r} for r in routes]}
    if flt: m["filter"] = flt
    return m

# ---- M3: extend scenario 7213714 (built on the version edited 25-Oct) ----
Q_LINES = ('query {\n  items(ids: [{{41.id}}]) {\n    id\n'
           '    acct: column_values(ids: ["board_relation_mm1b747v"]) { ... on BoardRelationValue { display_value } }\n'
           '    vt: column_values(ids: ["opp_verticals"]) { ... on MirrorValue { display_value } }\n'
           '    np: column_values(ids: ["op_n_participants"]) { ... on FormulaValue { display_value } }\n'
           '    pm: column_values(ids: ["multiple_person_mm66vf"]) { ... on PeopleValue { persons_and_teams { id kind } } }\n'
           '    subitems {\n      id\n      name\n'
           '      qty: column_values(ids: ["li_qty"]) { text }\n'
           '      cat: column_values(ids: ["li_catalog_item"]) { ... on BoardRelationValue { linked_item_ids display_value } }\n'
           '      chk: column_values(ids: ["li_check"]) { ... on FormulaValue { display_value } }\n    }\n  }\n}')
S = "60.body.data.items[1].subitems"
VARS = {"id": 61, "module": "util:SetVariables", "version": 1, "mapper": {"scope": "roundtrip", "variables": [
            {"name": "readiness_gate", "value": "off"},          # D1 gate: switch to "on" once the Catalog is filled (decision 26-Oct: build it off)
            {"name": "lines_n", "value": "{{length(" + S + ")}}"},
            {"name": "ready_n", "value": "{{length(map(flatten(map(" + S + "; \"chk\")); \"display_value\"; \"display_value\"; \"Complete\"))}}"},
            {"name": "missing", "value": "{{join(map(flatten(map(" + S + "; \"chk\")); \"display_value\"); \" | \")}}"}]},
        "metadata": {"designer": {"x": 450, "y": 0}, "restore": {"expect": {"scope": {"label": "One cycle"}, "variables": {"items": [None, None, None, None]}}}}}
PIPE = "{{41.mappable_column_values.color_mkyd5d32.text}}"
GATE_OK = [[cond(PIPE, "text:notequal", "Matching Needed"), cond("{{61.readiness_gate}}", "text:notequal", "on")],
           [cond(PIPE, "text:notequal", "Matching Needed"), cond("{{61.lines_n}}", "number:greater", "0"), cond("{{61.ready_n}}", "number:equal", "{{61.lines_n}}")]]
GATE_FAIL = [[cond(PIPE, "text:notequal", "Matching Needed"), cond("{{61.readiness_gate}}", "text:equal", "on"), cond("{{61.lines_n}}", "number:equal", "0")],
             [cond(PIPE, "text:notequal", "Matching Needed"), cond("{{61.readiness_gate}}", "text:equal", "on"), cond("{{61.ready_n}}", "number:less", "{{61.lines_n}}")]]
COHORT_Q = 'mutation ($name: String!, $cv: JSON!) { create_item(board_id: 18403700733, group_id: "group_mm2k46ga", item_name: $name, column_values: $cv) { id } }'
COHORT_CV = ('{"board_relation_mm1cag6p": {"item_ids": [{{46.id}}]}, "board_relation_mm1gy9xw": {"item_ids": [{{41.id}}]}, '
             '"board_relation_mm88gj2b": {"item_ids": [{{70.id}}]}, "co_catalog_item": {"item_ids": [{{ifempty(70.cat[1].linked_item_ids[1]; "")}}]}}')
COHORT_CV_NOCAT = '{"board_relation_mm1cag6p": {"item_ids": [{{46.id}}]}, "board_relation_mm1gy9xw": {"item_ids": [{{41.id}}]}, "board_relation_mm88gj2b": {"item_ids": [{{70.id}}]}}'
COHORT_NAME = "{{ifempty(70.cat[1].display_value; 70.name)}} – {{ifempty(60.body.data.items[1].acct[1].display_value; 41.name)}} – {{71.i}}"

def build_m3(bp):
    flow = bp["flow"]
    ids = [m["id"] for m in flow]
    assert ids == [40, 41, 48], f"unexpected top-level flow {ids}; re-read before changing"
    r48 = flow[2]
    r0, r1 = r48["routes"][0]["flow"], r48["routes"][1]["flow"]
    assert [m["id"] for m in r0] == [46, 42, 43, 44] and [m["id"] for m in r1] == [50], "route layout changed since review"
    m46 = r0[0]
    # 1) project field mapping (approved): fall back to today's source when the new one is empty
    cv = m46["mapper"]["columnValues"]
    A = "41.mappable_column_values."
    cv["text_mkydp0n"] = "{{if(parseNumber(60.body.data.items[1].np[1].display_value) > 0; 60.body.data.items[1].np[1].display_value; " + A + "numeric_mm66xkfx)}}"
    cv["dropdown_mm6tvd4w"] = {"labels": "{{deduplicate(split(60.body.data.items[1].vt[1].display_value; \", \"))}}"}
    cv["project_timeline"] = {"from": "{{if(" + A + "date_mm7yfjxw.date; formatDate(" + A + "date_mm7yfjxw.date; \"YYYY-MM-DD\"); " + A + "timerange_mm66c6q6.from)}}",
                              "to": "{{if(" + A + "date_mm7yfjxw.date; formatDate(addMonths(" + A + "date_mm7yfjxw.date; ifempty(" + A + "numeric_mm7xtxtm; 0)); \"YYYY-MM-DD\"); " + A + "timerange_mm66c6q6.to)}}"}
    cv["color_mm6tjy7q"] = {"label": "{{ifempty(" + A + "color_mm6tx1t1.text; " + A + "color_mm6tx1t1.label; " + A + "color_mm6tx1t1)}}"}
    cv["dropdown_mm5yhjtv"] = {"labels": "{{split(" + A + "dropdown_mm6cacm6.text; \",\")}}"}
    cv["multiple_person_mm83qhrn"] = {"personsAndTeams": "{{60.body.data.items[1].pm[1].persons_and_teams}}"}
    for c in ("color_mm6tjy7q", "dropdown_mm5yhjtv", "multiple_person_mm83qhrn"):
        if c not in m46["mapper"]["columnIds"]: m46["mapper"]["columnIds"].append(c)
    m46["mapper"]["create_labels_if_missing"] = True
    # 2) readiness gate (built OFF) on the project route
    m46["filter"] = {"name": "Not Matching Needed + ready (gate off = always)", "conditions": GATE_OK}
    # 3) after the project: router -> [contacts chain unchanged] + [cohorts]
    cohorts = [
        {"id": 70, "module": "builtin:BasicFeeder", "version": 1, "mapper": {"array": "{{" + S + "}}"},
         "filter": {"name": "Has line items", "conditions": [[cond("{{61.lines_n}}", "number:greater", "0")]]},
         "metadata": {"designer": {"x": 1500, "y": 300}, "restore": {"expect": {"array": {"mode": "edit"}}}}},
        {"id": 71, "module": "builtin:BasicRepeater", "version": 1, "mapper": {"start": "1", "repeats": "{{ifempty(parseNumber(70.qty[1].text); 1)}}", "step": "1"},
         "metadata": {"designer": {"x": 1800, "y": 300}}},
        router(74, [[gq_module(72, COHORT_Q, [("name", COHORT_NAME), ("cv", COHORT_CV)], 2400, 200, {"name": "Catalog linked", "conditions": [[cond("{{70.cat[1].linked_item_ids[1]}}", "exist")]]})],
                    [gq_module(73, COHORT_Q, [("name", COHORT_NAME), ("cv", COHORT_CV_NOCAT)], 2400, 400, {"name": "No catalog", "conditions": [[cond("{{70.cat[1].linked_item_ids[1]}}", "notexist")]]})]], 2100, 300)]
    r48["routes"][0]["flow"] = [m46, router(49, [r0[1:], cohorts], 1200, 0)]   # 45/47 are orphan modules on the canvas
    # 4) Matching Needed route: add the missing pipeline filter (it ran for every pipeline)
    r1[0]["filter"] = {"name": "Matching Needed", "conditions": [[cond(PIPE, "text:equal", "Matching Needed")]]}
    # 5) gate-fail route (never taken while readiness_gate = off): revert stage + notify
    revert = json.loads(json.dumps([m for m in r1[0]["routes"][1]["flow"] if m["id"] == 52][0])); revert["id"] = 80; revert.pop("filter", None)
    revert["filter"] = {"name": "Gate ON and not ready", "conditions": GATE_FAIL}
    note = json.loads(json.dumps([m for m in r1[0]["routes"][1]["flow"] if m["id"] == 53][0])); note["id"] = 81; note.pop("filter", None)
    note["mapper"]["text"] = "Closed Won was reverted: line items are not ready ({{61.ready_n}}/{{61.lines_n}} ready). {{61.missing}}"
    r48["routes"].append({"flow": [revert, note]})
    # 6) query + variables before the router
    bp["flow"] = [flow[0], flow[1], gq_module(60, Q_LINES, None, 300, 0), VARS, r48]
    return bp

if STEP in ("m3_build", "m3_apply"):
    live = make("GET", f"/scenarios/{M3_ID}/blueprint")["response"]["blueprint"]
    before = json.load(open("make2/bp_7213714.json"))["response"]["blueprint"]
    if json.dumps(live["flow"], sort_keys=True) != json.dumps(before["flow"], sort_keys=True):
        raise SystemExit("Scenario changed again since it was read for this build; re-read before applying.")
    new = build_m3(json.loads(json.dumps(live)))
    json.dump(new, open("make2/bp_7213714_new.json", "w"), ensure_ascii=False, indent=1)
    print("built blueprint; top flow:", [m["id"] for m in new["flow"]])
    if STEP == "m3_apply":
        r = make("PATCH", f"/scenarios/{M3_ID}", {"blueprint": json.dumps(new, ensure_ascii=False)})
        s = r["scenario"]; print("updated scenario", s["id"], "active:", s["isActive"], "invalid:", s.get("isinvalid"), "lastEdit:", s["lastEdit"])

if STEP == "m3_validate":
    new = json.load(open("make2/bp_7213714_new.json"))
    draft = json.loads(json.dumps(new)); draft["name"] = "ZZ DRAFT validation (Kindaa) – delete me"
    draft["flow"][0]["parameters"] = {}                      # no hook: must not touch the live trigger
    r = make("POST", "/scenarios?confirmed=true", {"blueprint": json.dumps(draft, ensure_ascii=False), "teamId": TEAM, "folderId": FOLDER,
                                                    "scheduling": json.dumps({"type": "indefinitely", "interval": 900})})
    sid = r["scenario"]["id"]; print("draft created", sid, "active:", r["scenario"]["isActive"], "invalid:", r["scenario"].get("isinvalid"))
    back = make("GET", f"/scenarios/{sid}/blueprint")["response"]["blueprint"]
    def ids(flow, out):
        for m in flow:
            out.append((m["id"], m["module"])); [ids(rr["flow"], out) for rr in m.get("routes") or []]
        return out
    print("modules kept by Make:", len(ids(back["flow"], [])), "of", len(ids(new["flow"], [])))
    lost = set(ids(new["flow"], [])) - set(ids(back["flow"], []))
    print("lost/changed modules:", lost)
    rep = [m for _, m in ids(back["flow"], []) if m == "builtin:BasicRepeater"]
    print("repeater present:", bool(rep))
    make("DELETE", f"/scenarios/{sid}?confirmed=true"); print("draft deleted", sid)

def make_logs(sid, n=5):
    return make("GET", f"/scenarios/{sid}/logs?pg%5BsortDir%5D=desc&pg%5Blimit%5D={n}").get("scenarioLogs", [])

def wait_for_run(sid, since_ts, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for l in make_logs(sid, 10):
            if l.get("type") in ("auto", "manual", "instant", None) and l.get("timestamp", "") >= since_ts and l.get("status") in (1, 2, 3):
                return l
        time.sleep(10)
    return None

def find_items_by_name(board, name):
    d = gql('query($b:[ID!],$n:CompareValue!) { boards(ids:$b) { items_page(limit:50, query_params:{rules:[{column_id:"name", compare_value:$n, operator:contains_text}]}) { items { id name created_at state } } } }',
            {"b": [board], "n": name}, ver="2025-10")
    return d["boards"][0]["items_page"]["items"]

if STEP == "m3_test":
    before_prj = {i["id"] for i in find_items_by_name(PRJ, "TEST KINDAA")}
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    setvals(OPP, TEST_ITEM, {"color_mkyd5d32": {"label": "B2B"}})
    setvals(OPP, TEST_ITEM, {"color_mkyzchms": {"label": "Closed Won"}})
    print("TEST KINDAA -> B2B + Closed Won at", since)
    run = wait_for_run(M3_ID, since)
    print("Make run:", json.dumps(run, ensure_ascii=False)[:600] if run else "NONE within timeout")
    time.sleep(15)
    prj = [i for i in find_items_by_name(PRJ, "TEST KINDAA") if i["id"] not in before_prj]
    print("new projects:", prj)
    json.dump({"since": since, "run": run, "projects": prj}, open("m3_test.json", "w"), indent=1)

if STEP == "m3_verify":
    t = json.load(open("m3_test.json")); pid = t["projects"][0]["id"]
    co = [i for i in find_items_by_name(COH, " – test – ") if i["created_at"] >= t["since"][:19]]
    print("new cohorts:", [(c["id"], c["name"]) for c in co])
    cols = ["board_relation_mm1cag6p", "board_relation_mm1gy9xw", "board_relation_mm88gj2b", "co_catalog_item", "co_pm", "co_ops", "co_car",
            "co_participants", "co_weeks", "co_pweeks", "co_rate", "co_bo", "co_expert", "co_trn", "co_live"]
    d = gql("query($i:[ID!],$c:[String!]) { items(ids:$i) { id name group { id } column_values(ids:$c) { id text ... on BoardRelationValue { linked_item_ids } ... on MirrorValue { display_value } } } }",
            {"i": [c["id"] for c in co], "c": cols}, ver="2025-10")["items"]
    for it in d:
        v = {cv["id"]: (cv.get("linked_item_ids") if cv.get("linked_item_ids") is not None else cv.get("display_value")) for cv in it["column_values"]}
        print(it["name"], "| group", it["group"]["id"], "|", json.dumps(v, ensure_ascii=False))
    pcols = ["text_mkydp0n", "dropdown_mm6tvd4w", "project_timeline", "color_mm6tjy7q", "dropdown_mm5yhjtv", "multiple_person_mm83qhrn", "board_relation_mm7y54c8"]
    p = gql("query($i:[ID!],$c:[String!]) { items(ids:$i) { name column_values(ids:$c) { id text } } }", {"i": [pid], "c": pcols}, ver="2025-10")["items"][0]
    print("project:", {cv["id"]: cv["text"] for cv in p["column_values"]})
    json.dump({**t, "cohorts": [c["id"] for c in co]}, open("m3_test.json", "w"), indent=1)

def archive(item_id):
    r = gql("mutation($i:ID!) { archive_item(item_id:$i) { id state } }", {"i": item_id}, ver="2025-10")["archive_item"]
    print("archived", r["id"], r["state"])

if STEP == "m3_cleanup":
    t = json.load(open("m3_test.json"))
    for iid in t["cohorts"] + [p["id"] for p in t["projects"]]: archive(iid)
    setvals(OPP, TEST_ITEM, {"color_mkyzchms": {"label": "Discovery Call & Identification"}})
    setvals(OPP, TEST_ITEM, {"color_mkyd5d32": {"label": "Matching Needed"}})
    print(read_vals([TEST_ITEM], ["color_mkyzchms", "color_mkyd5d32"]))

SCN_META = {"dlq": False, "slots": None, "dataloss": False, "maxErrors": 3, "autoCommit": True, "roundtrips": 1, "sequential": False,
            "confidential": False, "freshVariables": False, "autoCommitTriggerLast": True}
def trigger(hook_id, hook_type, label):
    mod = {"monday4": "monday:watchBoardItemsV2", "monday3": "monday:watchBoardColumnValuesV2"}[hook_type]
    return {"id": 1, "module": mod, "version": 2, "parameters": {"__IMTHOOK__": hook_id}, "mapper": {},
            "metadata": {"designer": {"x": 0, "y": 0}, "restore": {"parameters": {"__IMTHOOK__": {"data": {"editable": "false"}, "label": label}}},
                         "parameters": [{"name": "__IMTHOOK__", "type": f"hook:{hook_type}", "label": "Webhook", "required": True}]}}

L = "2.body.data.items[1].cat[1].linked_items[1]"
Q_LINE = ('query {\n  items(ids: [{{1.pulseId}}]) {\n    id\n    parent_item { id }\n'
          '    qty: column_values(ids: ["li_qty"]) { text }\n'
          '    rate0: column_values(ids: ["li_rate"]) { text }\n    wk0: column_values(ids: ["li_months"]) { text }\n'
          '    ls0: column_values(ids: ["li_ls_base"]) { text }\n    ex0: column_values(ids: ["li_expert"]) { text }\n    bo0: column_values(ids: ["li_bo"]) { text }\n'
          '    cat: column_values(ids: ["li_catalog_item"]) { ... on BoardRelationValue { linked_items { id\n'
          '      rate: column_values(ids: ["numeric_mm7tp9h8"]) { text }\n      wk: column_values(ids: ["cat_training_weeks"]) { text }\n'
          '      ls: column_values(ids: ["cat_ls_hours"]) { ... on FormulaValue { display_value } }\n'
          '      ex: column_values(ids: ["cat_expert_hours"]) { ... on FormulaValue { display_value } }\n'
          '      bo: column_values(ids: ["numeric_mm7t4zmq"]) { text } } } }\n  }\n}')
CHANGE_LI = 'mutation ($cv: JSON!) { change_multiple_column_values(board_id: 18390568739, item_id: {{1.pulseId}}, column_values: $cv) { id } }'
I = "2.body.data.items[1]"
COPY_IF_EMPTY = ('{"li_rate": "{{ifempty(' + I + '.rate0[1].text; ' + L + '.rate[1].text)}}", "li_months": "{{ifempty(' + I + '.wk0[1].text; ' + L + '.wk[1].text)}}", '
                 '"li_ls_base": "{{ifempty(' + I + '.ls0[1].text; ' + L + '.ls[1].display_value)}}", "li_expert": "{{ifempty(' + I + '.ex0[1].text; ' + L + '.ex[1].display_value)}}", '
                 '"li_bo": "{{ifempty(' + I + '.bo0[1].text; ' + L + '.bo[1].text)}}"}')
COPY_OVERWRITE = ('{"li_rate": "{{' + L + '.rate[1].text}}", "li_months": "{{' + L + '.wk[1].text}}", "li_ls_base": "{{' + L + '.ls[1].display_value}}", '
                  '"li_expert": "{{' + L + '.ex[1].display_value}}", "li_bo": "{{' + L + '.bo[1].text}}"}')
HAS_CAT = {"name": "Catalog linked", "conditions": [[cond("{{" + L + ".id}}", "exist")]]}

def m1_flow(hook):
    q = ('query {\n  items(ids: [{{1.pulseId}}]) {\n    id\n    margin: column_values(ids: ["opp_margin"]) { text }\n'
         '    sup: column_values(ids: ["opp_support_level"]) { text }\n    cm: column_values(ids: ["color_mm88m6bm"]) { text }\n'
         '    prm: column_values(ids: ["op_prm_version"]) { ... on BoardRelationValue { linked_item_ids } }\n  }\n'
         '  boards(ids: [18436459887]) { items_page(limit: 5, query_params: {rules: [{column_id: "prm_status", compare_value: [1]}]}) { items { id name } } }\n}')
    cv = ('{"op_prm_version": {"item_ids": [{{ifempty(2.body.data.items[1].prm[1].linked_item_ids[1]; 2.body.data.boards[1].items_page.items[1].id)}}]}, '
          '"opp_margin": "{{ifempty(2.body.data.items[1].margin[1].text; 40)}}", '
          '"opp_support_level": {"label": "{{ifempty(2.body.data.items[1].sup[1].text; \"Low\")}}"}, '
          '"color_mm88m6bm": {"label": "{{ifempty(2.body.data.items[1].cm[1].text; \"Low\")}}"}}')
    mut = 'mutation ($cv: JSON!) { change_multiple_column_values(board_id: 18390568735, item_id: {{1.pulseId}}, column_values: $cv) { id } }'
    return [trigger(hook, "monday4", "M1 Opportunity created"), gq_module(2, q, None, 300, 0),
            gq_module(3, mut, [("cv", cv)], 600, 0, {"name": "Active pricing version found", "conditions": [[cond("{{2.body.data.boards[1].items_page.items[1].id}}", "exist")]]})]

def m2a_flow(hook):
    base = '{"li_parent_opp": {"item_ids": [{{2.body.data.items[1].parent_item.id}}]}, "li_qty": "{{ifempty(2.body.data.items[1].qty[1].text; 1)}}"}'
    return [trigger(hook, "monday4", "M2a Line item created"), gq_module(2, Q_LINE, None, 300, 0),
            gq_module(3, CHANGE_LI, [("cv", base)], 600, 0),
            gq_module(4, CHANGE_LI, [("cv", COPY_IF_EMPTY)], 900, 0, HAS_CAT)]

def m2b_flow(hook):
    q = gq_module(2, Q_LINE, None, 300, 0, {"name": "Catalog Item changed", "conditions": [[cond("{{1.columnId}}", "text:equal", "li_catalog_item")]]})
    return [trigger(hook, "monday3", "M2b Line item catalog changed"), q, gq_module(3, CHANGE_LI, [("cv", COPY_OVERWRITE)], 600, 0, HAS_CAT)]

NEW_SCENARIOS = {
 "m1": ("#02 M1 Opportunity created – pricing defaults (Kindaa)", "monday4", {"boardId": "18390568735", "updateType": "create_item"}, m1_flow),
 "m2a": ("#03 M2a Line item created – copy from Catalog (Kindaa)", "monday4", {"boardId": "18390568735", "updateType": "create_subitem"}, m2a_flow),
 "m2b": ("#04 M2b Line item Catalog changed – copy from Catalog (Kindaa)", "monday3", {"boardId": "18390568735", "updateType": "change_subitem_column_value"}, m2b_flow),
}
STATE = "make_state.json"
def mstate(): return json.load(open(STATE)) if os.path.exists(STATE) else {}
def save_state(s): json.dump(s, open(STATE, "w"), indent=1)

def make_scenario(key):
    name, htype, hdata, builder = NEW_SCENARIOS[key]
    st = mstate(); cur = st.get(key, {})
    if not cur.get("hook"):
        h = make("POST", "/hooks", {"name": name.split(" (")[0][:60], "teamId": TEAM, "typeName": htype, "__IMTCONN__": CONN, **hdata})["hook"]
        cur["hook"] = h["id"]; cur["hook_data"] = h.get("data"); st[key] = cur; save_state(st)
        print("hook created", h["id"], h.get("typeName"), json.dumps(h.get("data")))
    if not cur.get("scenario"):
        bp = {"name": name, "flow": builder(cur["hook"]), "metadata": {"instant": True, "version": 1, "scenario": SCN_META, "designer": {"orphans": []}}}
        s = make("POST", "/scenarios?confirmed=true", {"blueprint": json.dumps(bp, ensure_ascii=False), "teamId": TEAM, "folderId": FOLDER,
                                                       "scheduling": json.dumps({"type": "immediately"})})["scenario"]
        cur["scenario"] = s["id"]; st[key] = cur; save_state(st); print("scenario created", s["id"], "invalid:", s.get("isinvalid"))
    s = make("POST", f"/scenarios/{cur['scenario']}/start")["scenario"]
    print("started", s["id"], "active:", s["isActive"])

LI_COLS = ["li_parent_opp", "li_qty", "li_rate", "li_months", "li_ls_base", "li_expert", "li_bo", "li_catalog_item"]
def li_state(iid):
    d = gql("query($i:[ID!],$c:[String!]) { items(ids:$i) { column_values(ids:$c) { id text ... on BoardRelationValue { linked_item_ids } } } }", {"i": [iid], "c": LI_COLS}, ver="2025-10")["items"][0]
    return {cv["id"]: (cv.get("linked_item_ids") if cv.get("linked_item_ids") is not None else cv.get("text")) for cv in d["column_values"]}

if STEP == "m2a_test":
    st = mstate(); since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    r = gql("mutation($p:ID!,$n:String!,$cv:JSON!) { create_subitem(parent_item_id:$p, item_name:$n, column_values:$cv) { id } }",
            {"p": TEST_ITEM, "n": "TEST Line C", "cv": json.dumps({"li_catalog_item": {"item_ids": [13200517474]}})})["create_subitem"]
    st["test_line_c"] = r["id"]; save_state(st); print("created TEST Line C", r["id"], "at", since)
    run = wait_for_run(st["m2a"]["scenario"], since)
    print("M2a run:", run and {k: run.get(k) for k in ("status", "displayStatus", "operations", "duration")})
    time.sleep(5); print("line C now:", li_state(r["id"]))

if STEP == "m2b_test":
    st = mstate(); lc = st["test_line_c"]; sid = st["m2b"]["scenario"]
    setvals(LI, lc, {"li_rate": "999"}); time.sleep(20)
    print("after rate edit (M2b must ignore):", li_state(lc)["li_rate"])
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    setvals(LI, lc, {"li_catalog_item": {"item_ids": [13200517116]}})
    run = None; t0 = time.time()
    while time.time() - t0 < 240 and not run:      # wait for the run that did real work (the rate edit's run stops at the filter)
        for l in make_logs(sid, 10):
            if l.get("timestamp", "") >= since and l.get("status") in (1, 2, 3) and (l.get("operations") or 0) > 2: run = l; break
        time.sleep(10)
    print("M2b run:", run and {k: run.get(k) for k in ("status", "displayStatus", "operations", "duration")})
    time.sleep(5); print("line C now:", li_state(lc))

if STEP == "m1_test":
    st = mstate(); since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    r = gql('mutation { create_item(board_id: 18390568735, group_id: "topics", item_name: "TEST KINDAA M1") { id group { title } } }', {})["create_item"]
    st["test_m1_item"] = r["id"]; save_state(st); print("created", r["id"], r["group"]["title"], "at", since)
    run = wait_for_run(st["m1"]["scenario"], since)
    print("M1 run:", run and {k: run.get(k) for k in ("status", "displayStatus", "operations", "duration")})
    time.sleep(5)
    v = gql("query($i:[ID!]) { items(ids:$i) { column_values(ids:[\"op_prm_version\",\"opp_margin\",\"opp_support_level\",\"color_mm88m6bm\",\"opm_setup_pm\"]) { id text ... on BoardRelationValue { linked_item_ids } ... on MirrorValue { display_value } } } }", {"i": [r["id"]]}, ver="2025-10")["items"][0]
    print({cv["id"]: cv.get("linked_item_ids") or cv.get("display_value") or cv.get("text") for cv in v["column_values"]})

if STEP == "m_cleanup":
    st = mstate()
    for k in ("test_m1_item", "test_line_c"):
        if st.get(k): archive(st[k])

# ---- One-off backfill (approved 26-Oct): link open Opportunities to the Active pricing version (v1) ----
CLOSED = {"Closed Won", "Closed Lost"}
def opp_rows():
    F = 'cursor items { id name stage: column_values(ids:["color_mkyzchms"]) { text } prm: column_values(ids:["op_prm_version"]) { ... on BoardRelationValue { linked_item_ids } } }'
    d = gql("query { boards(ids:[18390568735]) { items_page(limit:500) { %s } } }" % F, ver="2025-10")["boards"][0]["items_page"]; rows = []
    while True:
        rows += [{"id": i["id"], "name": i["name"], "stage": i["stage"][0]["text"] if i["stage"] else "", "prm": i["prm"][0]["linked_item_ids"] if i["prm"] else []} for i in d["items"]]
        if not d["cursor"]: break
        d = gql("query($c:String!) { next_items_page(limit:500, cursor:$c) { %s } }" % F, {"c": d["cursor"]}, ver="2025-10")["next_items_page"]
    return rows

if STEP in ("backfill_dry", "backfill_run"):
    active = gql('query { boards(ids:[18436459887]) { items_page(limit:5, query_params:{rules:[{column_id:"prm_status", compare_value:[1]}]}) { items { id name } } } }')["boards"][0]["items_page"]["items"]
    assert len(active) == 1, f"expected exactly one Active pricing version, got {active}"
    v1 = active[0]["id"]
    rows = opp_rows()
    todo = [r for r in rows if r["stage"] not in CLOSED and not r["prm"]]
    from collections import Counter
    print("opportunities:", len(rows), "| by stage:", dict(Counter(r["stage"] or "(empty)" for r in rows)))
    print("to link to", active[0]["name"], v1, ":", len(todo), "| already linked:", sum(1 for r in rows if r["prm"]))
    json.dump({"active_version": v1, "todo": todo}, open(f"{BACKUP_DIR}/backfill_op_prm_version_plan.json", "w"), ensure_ascii=False, indent=1)
    if STEP == "backfill_run":
        cv = json.dumps({"op_prm_version": {"item_ids": [int(v1)]}})
        done = []
        for i in range(0, len(todo), 10):
            chunk = todo[i:i + 10]
            body = " ".join(f'u{r["id"]}: change_multiple_column_values(board_id: 18390568735, item_id: {r["id"]}, column_values: {json.dumps(cv)}) {{ id }}' for r in chunk)
            gql("mutation { " + body + " }"); done += [r["id"] for r in chunk]
            print(f"linked {len(done)}/{len(todo)}"); time.sleep(1)
        after = opp_rows()
        left = [r for r in after if r["stage"] not in CLOSED and not r["prm"]]
        print("verify: open opportunities still unlinked:", len(left), "| linked to v1 now:", sum(1 for r in after if v1 in r["prm"]))
        json.dump({"active_version": v1, "linked": done, "unlinked_after": left}, open(f"{BACKUP_DIR}/backfill_op_prm_version_result.json", "w"), ensure_ascii=False, indent=1)

# ---- #05: only one Active pricing version (requested 2-Nov) ----
def m5_flow(hook):
    q = ('query {\n  items(ids: [{{1.pulseId}}]) { id st: column_values(ids: ["prm_status"]) { text } }\n'
         '  boards(ids: [18436459887]) { items_page(limit: 100, query_params: {rules: [{column_id: "prm_status", compare_value: [1]}]}) { items { id name } } }\n}')
    mut = 'mutation { change_multiple_column_values(board_id: 18436459887, item_id: {{3.id}}, column_values: "{\\"prm_status\\": {\\"label\\": \\"Archived\\"}}") { id } }'
    return [trigger(hook, "monday3", "M5 Pricing status changed"),
            gq_module(2, q, None, 300, 0, {"name": "Status column changed", "conditions": [[cond("{{1.columnId}}", "text:equal", "prm_status")]]}),
            {"id": 3, "module": "builtin:BasicFeeder", "version": 1, "mapper": {"array": "{{2.body.data.boards[1].items_page.items}}"},
             "filter": {"name": "Changed item is now Active", "conditions": [[cond("{{2.body.data.items[1].st[1].text}}", "text:equal", "Active")]]},
             "metadata": {"designer": {"x": 600, "y": 0}, "restore": {"expect": {"array": {"mode": "edit"}}}}},
            gq_module(4, mut, None, 900, 0, {"name": "Other Active versions", "conditions": [[cond("{{3.id}}", "text:notequal", "{{1.pulseId}}")]]})]
NEW_SCENARIOS["m5"] = ("#05 Pricing Parameters – keep one Active version (Kindaa)", "monday3",
                       {"boardId": "18436459887", "updateType": "change_specific_column_value", "config": {"columnId": "prm_status"}}, m5_flow)

def prm_status():
    d = gql("query { boards(ids:[18436459887]) { items_page(limit:50) { items { id name state column_values(ids:[\"prm_status\"]) { text } } } } }")
    return {i["id"]: (i["name"], i["column_values"][0]["text"]) for i in d["boards"][0]["items_page"]["items"]}

if STEP == "m5_test":
    st = mstate(); sid = st["m5"]["scenario"]
    print("before:", prm_status())
    dup = gql("mutation { duplicate_item(board_id: 18436459887, item_id: 13348993282, with_updates: false) { id name } }")["duplicate_item"]
    gql("mutation($i:ID!) { change_simple_column_value(board_id: 18436459887, item_id: $i, column_id: \"name\", value: \"TEST copy of v1 (Kindaa)\") { id } }", {"i": dup["id"]})
    setvals(18436459887, dup["id"], {"prm_status": {"label": "Archived"}})
    st["test_prm_copy"] = dup["id"]; save_state(st); time.sleep(15)
    print("copy created (Archived):", prm_status())
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    setvals(18436459887, dup["id"], {"prm_status": {"label": "Active"}})
    run = None; t0 = time.time()
    while time.time() - t0 < 180 and not run:
        for l in make_logs(sid, 10):
            if l.get("timestamp", "") >= since and l.get("status") in (1, 2, 3) and (l.get("operations") or 0) > 3: run = l; break
        time.sleep(8)
    print("run (copy -> Active):", run and {k: run.get(k) for k in ("status", "displayStatus", "operations")})
    time.sleep(5); print("after copy Active:", prm_status())
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    setvals(18436459887, 13348993282, {"prm_status": {"label": "Active"}})
    run = None; t0 = time.time()
    while time.time() - t0 < 180 and not run:
        for l in make_logs(sid, 10):
            if l.get("timestamp", "") >= since and l.get("status") in (1, 2, 3) and (l.get("operations") or 0) > 3: run = l; break
        time.sleep(8)
    print("run (v1 -> Active):", run and {k: run.get(k) for k in ("status", "displayStatus", "operations")})
    time.sleep(5); print("after v1 Active:", prm_status())


if STEP.startswith("mk_"):
    make_scenario(STEP[3:])   # runs last, so scenarios defined further down are known
