# Team & Rates board (approved 5-Nov): private board with one item per rate version, hourly rate per function,
# linked from every Opportunity (+ mirrors), COGS (ILS) and Price List (ILS) formulas on the Opportunity.
# Usage: python3 rates_build.py <step>.  Every mutation is logged to rates_mutations.log next to the log dir.
import json, os, subprocess, sys, time
LOGDIR = os.environ.get("ELEV_LOGDIR", os.path.dirname(os.path.abspath(__file__)))
LOG = open(os.path.join(LOGDIR, "rates_mutations.log"), "a")
STATE_F = os.path.join(LOGDIR, "rates_state.json")
STEP = sys.argv[1] if len(sys.argv) > 1 else ""
WS, OPP, PRJ, LI = 13463480, 18390568735, 18390568732, 18390568739
KINDAA, NOFAR = 111441380, 27155026

def gql(q, v=None, ver="2025-10"):
    r = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.monday.com/v2", "-H", "Content-Type: application/json",
                        "-H", f"API-Version: {ver}", "--data-binary", "@-"], input=json.dumps({"query": q, "variables": v or {}}),
                       capture_output=True, text=True)
    d = json.loads(r.stdout)
    if q.lstrip().startswith("mutation"):
        LOG.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "q": q, "v": v, "resp": d}, ensure_ascii=False) + "\n"); LOG.flush()
    if d.get("errors") or d.get("error_code"):
        raise SystemExit("API error: " + json.dumps(d, ensure_ascii=False)[:1500])
    return d["data"]

def state(): return json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}
def save(s): json.dump(s, open(STATE_F, "w"), indent=1)

def col(board, cid):
    c = gql("query($b:[ID!],$c:[String!]) { boards(ids:$b) { columns(ids:$c) { id title type revision settings description } } }",
            {"b": [board], "c": [cid]})["boards"][0]["columns"]
    return c[0] if c else None

def mk(board, cid, title, ctype, desc, defaults=None):
    if col(board, cid): print("exists", board, cid); return
    v = {"b": board, "id": cid, "t": title, "d": desc}
    if defaults is not None: v["def"] = defaults
    q = "mutation($b:ID!,$id:String!,$t:String!,$d:String%s) { create_column(board_id:$b, id:$id, title:$t, column_type:%s, description:$d%s) { id } }" % (
        ",$def:JSON" if defaults is not None else "", ctype, ", defaults:$def" if defaults is not None else "")
    gql(q, v); print("created", board, cid, title)

def upd(board, cid, ctype, settings):
    c = col(board, cid)
    gql("mutation($b:ID!,$c:String!,$rev:String!,$s:JSON!) { update_column(board_id:$b, id:$c, revision:$rev, settings:$s, column_type:%s) { id } }" % ctype,
        {"b": board, "c": cid, "rev": c["revision"], "s": settings})
    after = col(board, cid)["settings"]
    for k, val in settings.items():
        if after.get(k) != val: raise SystemExit(f"settings did not stick on {cid}: {k}={after.get(k)!r}")
    print("settings set", board, cid)

def formula(board, cid, title, desc, f):
    mk(board, cid, title, "formula", desc)
    if (col(board, cid)["settings"] or {}).get("formula") != f: upd(board, cid, "formula", {"formula": f})

def mirror(board, cid, title, desc, rel, tboard, tcol, fn=None):
    s = {"relation_column": {rel: True}, "displayed_linked_columns": [{"board_id": str(tboard), "column_ids": [tcol]}]}
    if fn: s["function"] = fn
    mk(board, cid, title, "mirror", desc, s)
    if col(board, cid)["settings"].get("displayed_linked_columns") != s["displayed_linked_columns"]: upd(board, cid, "mirror", s)

ILS = {"unit": {"symbol": "custom", "custom_unit": "₪", "direction": "left"}}
# (column id on rates board, title, Opportunity mirror id, Opportunity hours total it prices)
RATES = [("rts_pm", "PM Rate / Hour", "opr_pm", "op_tot_pm"),
         ("rts_ops", "OPS Rate / Hour", "opr_ops", "op_tot_ops"),
         ("rts_learning", "Learning Rate / Hour", "opr_learning", "op_tot_learning"),
         ("rts_expert", "Expert (Instructor) Rate / Hour", "opr_expert", "op_tot_expert"),
         ("rts_career", "Career Rate / Hour", "opr_career", "op_tot_career"),
         ("rts_auto", "Automation Rate / Hour", "opr_auto", "op_tot_auto"),
         ("rts_design", "Design Rate / Hour", "opr_design", "op_tot_design")]

if STEP == "board":
    s = state()
    if not s.get("board"):
        b = gql("mutation($o:[ID!]) { create_board(board_name:\"🔒 Team & Rates\", board_kind:private, workspace_id:%d, board_owner_ids:$o, empty:true, "
                "description:\"Hourly cost rate per function, one item per version. Exactly one version is Active; new Opportunities link to it. Private: Kindaa + Nofar.\") { id } }" % WS,
                {"o": [KINDAA, NOFAR]})["create_board"]
        s["board"] = b["id"]; save(s); print("board created", b["id"])
    B = int(s["board"])
    mk(B, "rts_status", "Status", "status", "Active / Archived. Only one version may be Active (scenario #06).",
       {"labels": [{"label": "Archived", "color": "working_orange", "index": 0}, {"label": "Active", "color": "done_green", "index": 1}]})
    mk(B, "rts_effective", "Effective Date", "date", "Date this rate version takes effect.")
    for cid, title, _, _ in RATES:
        mk(B, cid, title, "numbers", f"{title} in ILS (cost to Elevation).", ILS)
    g = gql("query($b:[ID!]) { boards(ids:$b) { groups { id title } items_page(limit:20) { items { id name } } } }", {"b": [B]})["boards"][0]
    if g["groups"] and g["groups"][0]["title"] != "Versions":
        gql("mutation($b:ID!,$g:String!) { update_group(board_id:$b, group_id:$g, group_attribute:title, new_value:\"Versions\") { id } }", {"b": B, "g": g["groups"][0]["id"]})
    if not g["groups"]:
        gql("mutation($b:ID!) { create_group(board_id:$b, group_name:\"Versions\") { id } }", {"b": B})
    if not s.get("v1"):
        it = gql("mutation($b:ID!,$cv:JSON!) { create_item(board_id:$b, item_name:\"v1 – Nov 2026\", column_values:$cv) { id } }",
                 {"b": B, "cv": json.dumps({"rts_status": {"label": "Active"}, "rts_effective": {"date": "2026-11-05"}})})["create_item"]
        s["v1"] = it["id"]; save(s); print("v1 created", it["id"])
    print(json.dumps(gql("query($b:[ID!]) { boards(ids:$b) { id name board_kind owners { id name } subscribers { id name } groups { id title } "
                         "columns { id title type } items_page { items { id name column_values { id text } } } } }", {"b": [B]})["boards"][0], ensure_ascii=False, indent=1))

if STEP == "opp":
    s = state(); B = int(s["board"])
    # Link column on the Opportunity, then one mirror per rate.
    mk(OPP, "op_rts_version", "⚙️Rates Version", "board_relation", "Link to the Active Team & Rates version (set by #02 M1 on creation).",
       {"boardIds": [B], "allowMultipleItems": False})
    for cid, title, mid, _ in RATES:
        mirror(OPP, mid, "⚙️" + title, f"Mirror of Team & Rates {cid}.", "op_rts_version", B, cid)

COGS_F = " + ".join("{%s} * {%s}" % (tot, mid) for _, _, mid, tot in RATES) + " + {opp_mkt_budget}"
PRICE_F = "{op_cogs} * (1 + {opp_margin})"   # a % number column reads as a fraction in formulas (40% -> 0.4)
FINAL_F = "{op_price_list} - {op_discount}"
if STEP == "formulas":
    formula(OPP, "op_cogs", "COGS (ILS)", "Σ (Total hours per function × its hourly rate from Team & Rates) + Marketing Budget. Content dev sits inside Learning/Expert totals.", COGS_F)
    formula(OPP, "op_price_list", "Price List (ILS)", "COGS × (1 + Margin %). Margin defaults to 40%.", PRICE_F)
    mk(OPP, "op_discount", "Discount (ILS)", "numbers", "Fixed discount amount in ILS (not a percent).", ILS)
    formula(OPP, "op_final_price", "Final Price (ILS)", "Price List − Discount.", FINAL_F)

# ---------------- Make: #06 (one Active rates version) and #02 M1 extension ----------------
MAKE = "https://eu1.make.com/api/v2"; TEAM, FOLDER, CONN, M1_ID, M5_ID = 387027, 381378, 3107441, 8189159, 8326233
def make(method, path, body=None):
    a = ["curl", "-sS", "-X", method, MAKE + path, "-H", "Content-Type: application/json", "-w", "\n%{http_code}"]
    if body is not None: a += ["--data-binary", "@-"]
    r = subprocess.run(a, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    out, code = r.stdout.rsplit("\n", 1)
    d = json.loads(out) if out.strip().startswith(("{", "[")) else {"raw": out}
    if method != "GET": LOG.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "make": method, "p": path, "code": code, "resp": d}, ensure_ascii=False)[:20000] + "\n"); LOG.flush()
    if not code.startswith("2"): raise SystemExit(f"Make {method} {path} -> {code}: {json.dumps(d, ensure_ascii=False)[:800]}")
    return d
def blueprint(sid): return make("GET", f"/scenarios/{sid}/blueprint")["response"]["blueprint"]

if STEP == "m6":
    s = state(); B = str(s["board"])
    if not s.get("m6_hook"):
        h = make("POST", "/hooks", {"name": "#06 Team & Rates – keep one Active version", "teamId": TEAM, "typeName": "monday3", "__IMTCONN__": CONN,
                                    "boardId": B, "updateType": "change_specific_column_value", "config": {"columnId": "rts_status"}})["hook"]
        s["m6_hook"] = h["id"]; save(s); print("hook", h["id"], h.get("data"))
    if not s.get("m6"):
        bp = blueprint(M5_ID)
        txt = json.dumps(bp["flow"], ensure_ascii=False).replace("18436459887", B).replace("prm_status", "rts_status").replace("M5 Pricing status changed", "M6 Rates status changed")
        flow = json.loads(txt); flow[0]["parameters"]["__IMTHOOK__"] = s["m6_hook"]
        new = {"name": "#06 Team & Rates – keep one Active version (Kindaa)", "flow": flow, "metadata": bp["metadata"]}
        sc = make("POST", "/scenarios?confirmed=true", {"blueprint": json.dumps(new, ensure_ascii=False), "teamId": TEAM, "folderId": FOLDER,
                                                         "scheduling": json.dumps({"type": "immediately"})})["scenario"]
        s["m6"] = sc["id"]; save(s); print("scenario", sc["id"], "invalid:", sc.get("isinvalid"))
    print("started", make("POST", f"/scenarios/{s['m6']}/start")["scenario"]["isActive"])

if STEP == "m1":
    s = state(); B = s["board"]
    bp = blueprint(M1_ID); q2 = bp["flow"][1]["mapper"]["queryBody"]
    if "op_rts_version" not in q2:
        q2 = q2.replace('    prm: column_values(ids: ["op_prm_version"]) { ... on BoardRelationValue { linked_item_ids } }\n',
                        '    prm: column_values(ids: ["op_prm_version"]) { ... on BoardRelationValue { linked_item_ids } }\n'
                        '    rts: column_values(ids: ["op_rts_version"]) { ... on BoardRelationValue { linked_item_ids } }\n')
        q2 = q2.rstrip()[:-1] + ('  rates: boards(ids: [%s]) { items_page(limit: 5, query_params: {rules: [{column_id: "rts_status", compare_value: [1]}]}) { items { id name } } }\n}' % B)
        assert "rts:" in q2 and "rates:" in q2
        bp["flow"][1]["mapper"]["queryBody"] = q2
        m3 = bp["flow"][2]
        m3["filter"] = {"name": "Active pricing or rates version found", "conditions": [
            [{"a": "{{2.body.data.boards[1].items_page.items[1].id}}", "o": "exist"}],
            [{"a": "{{2.body.data.rates[1].items_page.items[1].id}}", "o": "exist"}]]}
        cv = m3["mapper"]["variables"][0]["value"]
        cv = cv.replace('"op_prm_version": {"item_ids": [{{ifempty(2.body.data.items[1].prm[1].linked_item_ids[1]; 2.body.data.boards[1].items_page.items[1].id)}}]}, ',
                        '"op_prm_version": {"item_ids": [{{ifempty(2.body.data.items[1].prm[1].linked_item_ids[1]; 2.body.data.boards[1].items_page.items[1].id)}}]}, '
                        '"op_rts_version": {"item_ids": [{{ifempty(2.body.data.items[1].rts[1].linked_item_ids[1]; 2.body.data.rates[1].items_page.items[1].id)}}]}, ')
        assert "op_rts_version" in cv
        m3["mapper"]["variables"][0]["value"] = cv
        make("PATCH", f"/scenarios/{M1_ID}?confirmed=true", {"blueprint": json.dumps(bp, ensure_ascii=False)})
        print("M1 patched")
    after = blueprint(M1_ID)
    print(after["flow"][1]["mapper"]["queryBody"]); print(after["flow"][2]["filter"]); print(after["flow"][2]["mapper"]["variables"][0]["value"])
