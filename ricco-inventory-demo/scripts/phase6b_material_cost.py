"""Phase 6b (Omer approved 2026-10-28): stored request Material cost + single-hop mirrors on Units/Projects
+ Projects total formula. Idempotent by title."""
import json
import mlib
import columns
import phase6_sam_boards as p6

PHASE = "6b"
REQ, LINES = "18437453027", "18437453414"
UNITS, PROJECTS = p6.UNITS, p6.PROJECTS
LINE_COST = "formula_mm8jjeek"
STORED = "mat_cost"
VALUES = {"MR-1": 2573.00, "MR-2": 2700.00, "MR-3": 3880.00, "MR-4": 1769.00, "MR-5": 5148.00}  # §9.7
ZZ = {"ZZ-TEST-Request": 74.00}  # sum of its two lines (54 + 20)


def col(bid, cid):
    return next((c for c in columns.read_columns(bid) if c["id"] == cid), None)


def ok(r, what):
    if r.get("errors"):
        raise mlib.StopBuild("%s: %s" % (what, json.dumps(r["errors"])[:400]))
    return r


def fix_calc_mirror():
    c = col(REQ, "material_cost")
    st = json.loads(c["settings_str"])
    want = {"relation_column": {"subtasks_mm8jad4w": True},
            "displayed_linked_columns": [{"board_id": LINES, "column_ids": [LINE_COST]}], "function": "sum"}
    if c["title"] == "⚙️ Material cost (calc)" and st["displayed_linked_columns"].get(LINES) == [LINE_COST]:
        print("  calc mirror already fixed")
        return
    ok(mlib.mutate(PHASE, "update_column(mirror)", REQ,
                   "mutation ($b:ID!, $id:String!, $r:String!, $t:String, $s:JSON) { update_column(board_id:$b, id:$id, "
                   "revision:$r, title:$t, column_type:mirror, settings:$s) { id title } }",
                   {"b": REQ, "id": "material_cost", "r": c["revision"], "t": "⚙️ Material cost (calc)", "s": want},
                   note="Requests: rename mirror → ⚙️ Material cost (calc), re-point to Line cost formula_mm8jjeek"), "calc mirror")
    print("  calc mirror renamed + re-pointed")


def stored_column():
    if col(REQ, STORED):
        print("  stored column exists")
        return
    ok(mlib.mutate(PHASE, "create_column(numbers)", REQ,
                   "mutation ($b:ID!, $d:JSON) { create_column(board_id:$b, id:\"mat_cost\", title:\"Material cost\", "
                   "column_type:numbers, after_column_id:\"po_status\", defaults:$d) { id title } }",
                   {"b": REQ, "d": json.dumps({"unit": {"symbol": "$", "direction": "left"}})},
                   note="Requests: stored Material cost (numbers, $). Full build: written by the process"), "stored col")
    print("  created Material cost (numbers)")


def fill():
    items = mlib.id_map()["items"]
    targets = {items[k]["id"]: v for k, v in VALUES.items()}
    for z in mlib.id_map()["zz_test_items"]:
        if z["name"] in ZZ:
            targets[z["id"]] = ZZ[z["name"]]
    cur = mlib.gql("{ items(ids:[%s]) { id name column_values(ids:[\"mat_cost\"]) { text } } }" % ",".join(targets))
    for it in cur["data"]["items"]:
        want = targets[it["id"]]
        if (it["column_values"][0]["text"] or "") and float(it["column_values"][0]["text"]) == want:
            continue
        ok(mlib.mutate(PHASE, "change_simple_column_value", REQ,
                       "mutation ($b:ID!, $i:ID!, $v:String!) { change_simple_column_value(board_id:$b, item_id:$i, "
                       "column_id:\"mat_cost\", value:$v) { id } }",
                       {"b": REQ, "i": it["id"], "v": "%.2f" % want}, note="%s Material cost = %.2f" % (it["name"], want)), "fill")


def mirror(bid, title, rel, src_board, src_col, note):
    ex = [c for c in columns.read_columns(bid) if c["title"] == title]
    if ex:
        print("  exists:", title, ex[0]["id"])
        return ex[0]["id"]
    d = {"relation_column": {rel: True}, "displayed_linked_columns": [{"board_id": str(src_board), "column_ids": [src_col]}],
         "function": "sum"}
    r = ok(mlib.mutate(PHASE, "create_column(mirror)", bid,
                       "mutation ($b:ID!, $t:String!, $d:JSON) { create_column(board_id:$b, title:$t, column_type:mirror, defaults:$d) { id title } }",
                       {"b": bid, "t": title, "d": json.dumps(d)}, note=note, allow_sam_board=True), title)
    cid = r["data"]["create_column"]["id"]
    print("  created:", bid, title, cid)
    return cid


def formula(bid, title, expr, note):
    ex = [c for c in columns.read_columns(bid) if c["title"] == title]
    if ex:
        print("  exists:", title, ex[0]["id"])
        return ex[0]["id"]
    r = ok(mlib.mutate(PHASE, "create_column(formula)", bid,
                       "mutation ($b:ID!, $t:String!, $d:JSON) { create_column(board_id:$b, title:$t, column_type:formula, defaults:$d) { id title } }",
                       {"b": bid, "t": title, "d": json.dumps({"formula": expr})}, note=note, allow_sam_board=True), title)
    cid = r["data"]["create_column"]["id"]
    print("  created:", bid, title, cid)
    return cid


if __name__ == "__main__":
    mlib.check_identity()
    fix_calc_mirror()
    stored_column()
    fill()
    u = mirror(UNITS, "Material cost", "board_relation_mm8j9wgg", REQ, STORED,
               "Units: Material cost <- Material Requests.Material cost (stored), sum")
    p = mirror(PROJECTS, "Material cost", "board_relation_mm8jqhv4", REQ, STORED,
               "Projects: Material cost (project-level requests) <- Material Requests.Material cost (stored), sum")
    pu = mirror(PROJECTS, "Units material cost", "subtasks_mm3aqxk2", UNITS, u,
                "Projects: Units material cost <- Units.Material cost, sum")
    t = formula(PROJECTS, "Total material cost", "{%s} + {%s}" % (p, pu),
                "Projects: Total material cost = Material cost + Units material cost")
    m = mlib.id_map()
    m["material_cost_v2"] = {"requests_stored": STORED, "units_mirror": u, "projects_mirror": p,
                             "projects_units_mirror": pu, "projects_total_formula": t}
    mlib.save_json(mlib.ID_MAP, m)
    print(m["material_cost_v2"])
