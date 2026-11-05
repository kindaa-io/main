# Phase 10 (approved 5-Nov): editable 🔒 line-item fields copied from the Catalog, Customer Mgmt without "Not Sold",
# OLD manual fields, Projects re-points + Project Duration (Weeks), M2a/M2b/M3 mapping changes.
# Usage: python3 phase10_build.py <step>. Helpers + log come from rates_build.py.
import json, os, re, sys, time
STEP = sys.argv[1] if len(sys.argv) > 1 else ""
sys.argv = [sys.argv[0], "__import__"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rates_build import gql, col, mk, upd, formula, mirror, make, blueprint, state, save, LOGDIR, OPP, PRJ, LI
CAT, COH = 18433874513, 18403700733
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backup")

def retitle(board, cid, title):
    if col(board, cid)["title"] == title: print("title ok", cid); return
    gql("mutation($b:ID!,$c:String!,$t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id } }", {"b": board, "c": cid, "t": title})
    print("renamed", board, cid, "->", title)

def describe(board, cid, text):
    gql("mutation($b:ID!,$c:String!,$v:String!) { change_column_metadata(board_id:$b, column_id:$c, column_property:description, value:$v) { id } }",
        {"b": board, "c": cid, "v": text}); print("description", board, cid)

def items(board, cols):
    F = "cursor items { id name column_values(ids:$c) { id text value ... on MirrorValue { display_value } ... on FormulaValue { display_value } ... on BoardRelationValue { linked_item_ids } } }"
    d = gql("query($b:[ID!],$c:[String!]) { boards(ids:$b) { items_page(limit:500) { %s } } }" % F, {"b": [board], "c": cols})["boards"][0]["items_page"]; out = []
    while True:
        out += d["items"]
        if not d["cursor"]: return out
        d = gql("query($k:String!,$c:[String!]) { next_items_page(limit:500, cursor:$k) { %s } }" % F, {"k": d["cursor"], "c": cols})["next_items_page"]

def backup_column(board, cid):
    os.makedirs(BACKUP, exist_ok=True)
    rows = [{"item_id": i["id"], "name": i["name"], **{k: i["column_values"][0].get(k) for k in ("text", "value", "display_value", "linked_item_ids")}} for i in items(board, [cid])]
    json.dump({"board": board, "column": cid, "settings": col(board, cid), "rows": rows}, open(f"{BACKUP}/{board}_{cid}.json", "w"), ensure_ascii=False, indent=1)
    return rows

def dependents(board, cid):
    deps = []
    ws = [b["id"] for b in gql("query { boards(workspace_ids:[13463480], limit:200) { id } }")["boards"]]
    for i in range(0, len(ws), 25):
        for b in gql("query($b:[ID!]) { boards(ids:$b, limit:50) { id columns { id type settings_str } } }", {"b": ws[i:i + 25]})["boards"]:
            for c in b["columns"]:
                s = json.loads(c["settings_str"] or "{}")
                if c["type"] == "formula" and str(b["id"]) == str(board) and re.search(r"\{" + re.escape(cid) + r"\}", s.get("formula", "")): deps.append(f"{b['id']}:{c['id']} formula")
                if c["type"] == "mirror":
                    dl = s.get("displayed_linked_columns") or {}
                    if isinstance(dl, dict) and cid in dl.get(str(board), []): deps.append(f"{b['id']}:{c['id']} mirror")
                    if str(b["id"]) == str(board) and cid in (s.get("relation_column") or {}): deps.append(f"{b['id']}:{c['id']} relation")
    return deps

def delete_col(board, cid):
    if not col(board, cid): print("already gone", cid); return
    d = dependents(board, cid)
    if d: raise SystemExit(f"STOP: {cid} still has dependents {d}")
    backup_column(board, cid)
    gql("mutation($b:ID!,$c:String!) { delete_column(board_id:$b, column_id:$c) { id } }", {"b": board, "c": cid}); print("deleted", board, cid)

# monday colour id -> API enum (ids 0..19 follow the enum order; newer palette ids matched by hex)
COLORS = ["working_orange", "done_green", "stuck_red", "dark_blue", "purple", "explosive", "grass_green", "bright_blue", "saladish", "egg_yolk",
          "blackish", "dark_red", "sofia_pink", "lipstick", "dark_purple", "bright_green", "chili_blue", "american_gray", "brown", "dark_orange"]
EXTRA = {101: "sunset", 110: "dark_indigo", 152: "lavender", 160: "teal"}
def labels_from(board, cid):
    out = []
    for l in col(board, cid)["settings"]["labels"]:
        if l.get("is_deactivated"): continue
        c = l["color"]; out.append({"label": l["label"], "index": l["index"], "color": COLORS[c] if c < len(COLORS) else EXTRA[c]})
    return out

# ---------------- 1. Line items: 🔒 editable copies of the Catalog mirrors ----------------
# (new id, title, type, old mirror, Catalog source column, M2 alias)
LOCKED = [("li_lsl", "🔒 Learning Services Level", "status", "li_ls_level", "cat_ls_level", "lsl"),
          ("li_live_h", "🔒 Live Training Hours", "numbers", "li_live_hours", "numeric_mm7tv0sp", "liv"),
          ("li_self_h", "🔒 Self Training Hours", "numbers", "li_self_hours", "numeric_mm7t38zg", "slf"),
          ("li_trn_c", "🔒 Total Training Hours / Cohort", "numbers", "li_trn_cohort", "numeric_mm7thk2x", "trc"),
          ("li_cstatus", "🔒 Content Status", "status", "li_content_status", "color_mm7tdr8h", "cst"),
          ("li_vert", "🔒 Vertical", "status", "li_vertical", "color_mm7tmzwg", "vrt")]
LI_FORMULAS = {"li_check": None, "li_live_t": "{li_live_h} * {li_qty}", "li_self_t": "{li_self_h} * {li_qty}", "li_trn_t": "{li_trn_c} * {li_qty}"}

if STEP == "li_create":
    for cid, title, typ, old, src, _ in LOCKED:
        desc = f"Copied from Catalog {src} by #03 M2a (when empty) / #04 M2b (Catalog changed). Editable. Replaces mirror {old}."
        mk(LI, cid, title, typ, desc, {"labels": labels_from(CAT, src)} if typ == "status" else None)
        if typ == "status":
            got = {(l["label"], l["hex"]) for l in col(LI, cid)["settings"]["labels"]}
            want = {(l["label"], l["hex"]) for l in col(CAT, src)["settings"]["labels"] if not l.get("is_deactivated")}
            print("   labels match Catalog:", got == want, "" if got == want else sorted(want - got))

if STEP == "li_formulas":
    f = col(LI, "li_check")["settings"]["formula"]; LI_FORMULAS["li_check"] = f.replace("{li_ls_level}", "{li_lsl}")
    for cid, f in LI_FORMULAS.items():
        before = col(LI, cid)["settings"]["formula"]
        if before != f: upd(LI, cid, "formula", {"formula": f}); print("  ", cid, ":", before, "->", f)
    # Opportunity 'Verticals' (read by #01 M3 for the Project Vertical) now shows the editable 🔒 Vertical
    upd(OPP, "opp_verticals", "mirror", {"relation_column": {"subitems": True}, "displayed_linked_columns": [{"board_id": str(LI), "column_ids": ["li_vert"]}]})

if STEP == "li_copy":   # one-off: fill the new columns on existing line items from their Catalog product
    rows = items(LI, ["li_catalog_item"] + [c for c, *_ in LOCKED])
    for r in rows:
        cv = {c["id"]: c for c in r["column_values"]}
        cat = (cv["li_catalog_item"].get("linked_item_ids") or [None])[0]
        if not cat: print("no catalog:", r["id"], r["name"]); continue
        src = {c["id"]: c for c in gql("query($i:[ID!],$c:[String!]) { items(ids:$i) { column_values(ids:$c) { id text } } }",
                                        {"i": [cat], "c": [s for *_, s, _ in LOCKED]})["items"][0]["column_values"]}
        new = {cid: src[s]["text"] for cid, _, _, _, s, _ in LOCKED if not (cv[cid].get("text") or "").strip() and (src[s]["text"] or "").strip()}
        if new: gql("mutation($i:ID!,$cv:JSON!) { change_multiple_column_values(board_id:%d, item_id:$i, column_values:$cv) { id } }" % LI, {"i": r["id"], "cv": json.dumps(new)})
        print("line", r["id"], r["name"], "<-", new)

if STEP == "li_delete_old":
    for cid, _, _, old, _, _ in LOCKED: delete_col(LI, old)

# ---------------- 2. M2a / M2b copy the six fields ----------------
CAT_Q = "".join(f'       {a}: column_values(ids: ["{s}"]) {{ text }}\n' for *_, s, a in LOCKED)
CUR_Q = "".join(f'    {a}0: column_values(ids: ["{c}"]) {{ text }}\n' for c, *_, a in LOCKED)
def m2_patch(sid, only_when_empty):
    os.makedirs(f"{BACKUP}/make", exist_ok=True)
    bp = blueprint(sid); json.dump(bp, open(f"{BACKUP}/make/{sid}_blueprint_before_p10.json", "w"), ensure_ascii=False, indent=1)
    q = bp["flow"][1]["mapper"]["queryBody"]
    if "li_lsl" not in q:
        q = q.replace('    bo0: column_values(ids: ["li_bo"]) { text }\n', '    bo0: column_values(ids: ["li_bo"]) { text }\n' + CUR_Q)
        q = q.replace('bo: column_values(ids: ["numeric_mm7t4zmq"]) { text }', 'bo: column_values(ids: ["numeric_mm7t4zmq"]) { text }\n' + CAT_Q.rstrip("\n"), 1)
        assert q.count("li_lsl") == 1 and q.count("cat_ls_level") == 1, q
        bp["flow"][1]["mapper"]["queryBody"] = q
    mod = [m for m in bp["flow"] if m.get("filter", {}) and m["filter"].get("name") == "Catalog linked"][0]
    val = mod["mapper"]["variables"][0]["value"]
    if "li_lsl" not in val:
        add = []
        for cid, *_, a in LOCKED:
            catv = f"2.body.data.items[1].cat[1].linked_items[1].{a}[1].text"
            add.append(f'"{cid}": "{{{{ifempty(2.body.data.items[1].{a}0[1].text; {catv})}}}}"' if only_when_empty else f'"{cid}": "{{{{{catv}}}}}"')
        val = val.rstrip()[:-1] + ", " + ", ".join(add) + "}"
        mod["mapper"]["variables"][0]["value"] = val
    make("PATCH", f"/scenarios/{sid}?confirmed=true", {"blueprint": json.dumps(bp, ensure_ascii=False)})
    a = blueprint(sid); m = [x for x in a["flow"] if x.get("filter", {}) and x["filter"].get("name") == "Catalog linked"][0]
    print(sid, "patched\n  Q:", a["flow"][1]["mapper"]["queryBody"].count("li_lsl"), "\n  CV:", m["mapper"]["variables"][0]["value"])
if STEP == "m2":
    m2_patch(8189111, True)    # #03 M2a: only fill empty fields
    m2_patch(8189131, False)   # #04 M2b: Catalog product changed -> overwrite

# ---------------- 3. Opportunity ----------------
CM_F = lambda lo, hi: '%s / {opm_wk_per_month} * {op_cm_weeks}' % ('IF({color_mm88m6bm}="High", {%s}, {%s})' % (hi, lo))
OLD_OPP = {"numeric_mm66xkfx": "OLD Approx. overall number of participants", "numeric_mm6kk1kf": "OLD Expected number of cohorts",
           "numeric_mm66zj7": "OLD Expected number of training hours (overall)", "numeric_mm7xtxtm": "OLD Project duration (Months)"}
OLD_PRJ = {"text_mkydp0n": "OLD # of Participants (Planned)", "text_mm1cs1k0": "OLD # of participants"}
if STEP == "opp":
    c = col(OPP, "color_mm88m6bm")
    labels = [{"id": l["id"], "label": l["label"], "index": l["index"], "color": COLORS[l["color"]]} for l in c["settings"]["labels"] if l["label"] != "Not Sold"]
    if len(labels) != len(c["settings"]["labels"]):
        gql("mutation($b:ID!,$c:String!,$rev:String!,$s:UpdateStatusColumnSettingsInput!) { update_status_column(board_id:$b, id:$c, revision:$rev, settings:$s) { id } }",
            {"b": OPP, "c": "color_mm88m6bm", "rev": c["revision"], "s": {"labels": labels}})
    print("Customer Mgmt labels:", [(l["label"], l.get("is_deactivated")) for l in col(OPP, "color_mm88m6bm")["settings"]["labels"]])
    for cid, lo, hi in [("op_cm_pm", "opm_cm_lo_pm_m", "opm_cm_hi_pm_m"), ("op_cm_ops", "opm_cm_lo_ops_m", "opm_cm_hi_ops_m")]:
        upd(OPP, cid, "formula", {"formula": CM_F(lo, hi)})
    describe(OPP, "op_cm_weeks", "Total project duration in weeks. Drives Customer Mgmt hours and the Project timeline / Project Duration (Weeks) (#01 M3).")
    describe(OPP, "op_cm_pm", "Customer Mgmt PM: monthly rate (Low/High, empty = Low) ÷ Weeks per Month × Total Project Weeks.")
    describe(OPP, "op_cm_ops", "Customer Mgmt OPS: monthly rate (Low/High, empty = Low) ÷ Weeks per Month × Total Project Weeks.")
    retitle(OPP, "opp_expert_hours", "Σ Expert Hours (lines)")
    for cid, t in OLD_OPP.items(): retitle(OPP, cid, t)
    # the automatic replacements (sums of line items)
    retitle(OPP, "opp_cohorts", "Expected number of cohorts"); describe(OPP, "opp_cohorts", "Σ line-item Quantity. Replaces the manual OLD Expected number of cohorts.")
    retitle(OPP, "opp_participants", "Overall number of participants"); describe(OPP, "opp_participants", "Σ line-item Total Participants. Replaces the manual OLD Approx. overall number of participants.")
    retitle(OPP, "op_sum_trn", "Expected number of training hours (overall)"); describe(OPP, "op_sum_trn", "Σ line-item Total Training Hours. Replaces the manual OLD Expected number of training hours.")
    formula(OPP, "op_n_trn", "⚙️# Training Hours", "Wrapper so Projects can mirror the training-hours sum.", "{op_sum_trn}")

# ---------------- 4. Projects ----------------
if STEP == "prj":
    for cid, t in OLD_PRJ.items(): retitle(PRJ, cid, t)
    mk(PRJ, "prj_weeks", "Project Duration (Weeks)", "numbers", "Copied from Opportunity Total Project Weeks by #01 M3 on Closed Won.")
    mirror(PRJ, "prj_trn", "Expected Training Hours", "Σ Opportunity Expected number of training hours (via ⚙️# Training Hours).", "board_relation_mm7y54c8", OPP, "op_n_trn", fn="sum")
    for cid, src, title in [("prj_cogs", "op_cogs", "COGS (₪)"), ("prj_pricelist", "op_price_list", "Price List (₪)")]:
        s = {"relation_column": {"board_relation_mm7y54c8": True}, "displayed_linked_columns": [{"board_id": str(OPP), "column_ids": [src]}], "function": "sum"}
        try:
            upd(PRJ, cid, "mirror", s); describe(PRJ, cid, f"Σ Opportunity {src}.")
        except SystemExit as e:
            print("re-point refused for", cid, "->", str(e)[:200])
            st = state(); st.setdefault("prj_repoint_failed", []).append(cid); save(st)

# ---------------- 5. #01 M3 project mapping ----------------
M3 = 7213714
def find(flow, mid):
    for m in flow:
        if m["id"] == mid: return m
        for r in m.get("routes", []):
            x = find(r["flow"], mid)
            if x: return x
WEEKS = "41.mappable_column_values.op_cm_weeks"
START = "41.mappable_column_values.date_mm7yfjxw.date"
if STEP == "m3":
    bp = blueprint(M3); os.makedirs(f"{BACKUP}/make", exist_ok=True)
    json.dump(bp, open(f"{BACKUP}/make/{M3}_blueprint_before_p10.json", "w"), ensure_ascii=False, indent=1)
    m = find(bp["flow"], 46); mp = m["mapper"]
    for gone in ("text_mkydp0n", "color_mm6tjy7q"):          # OLD planned participants (Projects mirrors the sum) / placements are per cohort
        if gone in mp["columnIds"]: mp["columnIds"].remove(gone)
        mp["columnValues"].pop(gone, None)
    if "prj_weeks" not in mp["columnIds"]: mp["columnIds"].append("prj_weeks")
    mp["columnValues"]["prj_weeks"] = "{{%s}}" % WEEKS
    tl = mp["columnValues"]["project_timeline"]
    tl["to"] = ('{{if(%s; formatDate(addDays(%s; parseNumber(ifempty(%s; 0)) * 7); "YYYY-MM-DD"); 41.mappable_column_values.timerange_mm66c6q6.to)}}' % (START, START, WEEKS))
    make("PATCH", f"/scenarios/{M3}?confirmed=true", {"blueprint": json.dumps(bp, ensure_ascii=False)})
    a = find(blueprint(M3)["flow"], 46)["mapper"]
    print("columns:", a["columnIds"]); print("prj_weeks:", a["columnValues"].get("prj_weeks")); print("timeline:", a["columnValues"]["project_timeline"])
    print("removed ok:", all(x not in a["columnIds"] for x in ("text_mkydp0n", "color_mm6tjy7q")))
