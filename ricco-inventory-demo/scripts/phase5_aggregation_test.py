"""Phase 5.1 aggregation test on ZZ-TEST- boards (D-03). Idempotent-ish: reuses recorded test boards/items.

Chain under test (expected values):
  CAT item price 10
  REQ subitems: line1 qty 3, line2 qty 2, each Product -> CAT item
    line.est   = mirror(product -> price)            -> 10
    line.lc    = formula {qty} * {est}                -> 30, 20     (formula over mirror)
  REQ.cost     = mirror(subitems -> lc, sum)          -> 50         (mirror SUM of formula, via subitems)
  REQ.total    = formula {cost} + {tax=5}             -> 55         (formula over mirror)
  SUP.ordered  = mirror(conn -> REQ.total, sum)       -> 55         (mirror SUM of formula-over-mirror)
  CAT2.on_hand = formula {in_total} - {out_total} with in/out mirrors of movements (7, 2) -> 5
  PRJ subitem (unit) -> REQ (connect), unit.cost = mirror(REQ.cost, sum) -> 50  (mirror of mirror)
  PRJ.units_cost = mirror(subitems -> unit.cost, sum)  -> 50        (mirror of mirror of mirror; §5 #8)
"""
import json
import time
import mlib
import testlib

P = "5-test"


def col(bid, cid, title, ctype, defaults=None):
    cols = mlib.gql("{ boards(ids:[%s]) { columns { id } } }" % bid)["data"]["boards"][0]["columns"]
    if any(c["id"] == cid for c in cols):
        return
    r = mlib.mutate(P, "create_column(%s)" % ctype, bid,
                    "mutation ($b:ID!, $id:String!, $t:String!, $ty:ColumnType!, $d:JSON) { create_column(board_id:$b, "
                    "id:$id, title:$t, column_type:$ty, defaults:$d) { id } }",
                    {"b": bid, "id": cid, "t": title, "ty": ctype, "d": json.dumps(defaults) if defaults else None},
                    note="test col %s" % cid)
    if r.get("errors"):
        raise mlib.StopBuild("test column %s failed: %s" % (cid, r["errors"]))


def item(bid, name, vals=None):
    items = mlib.gql("{ boards(ids:[%s]) { items_page(limit:100) { items { id name } } } }" % bid)
    for i in items["data"]["boards"][0]["items_page"]["items"]:
        if i["name"] == name:
            return i["id"]
    return testlib.create_item(P, bid, name, vals)


def subitem(parent_bid, parent, name, vals=None):
    r = mlib.gql("{ items(ids:[%s]) { subitems { id name board { id } } } }" % parent)["data"]["items"][0]["subitems"] or []
    for s in r:
        if s["name"] == name:
            return s["id"], s["board"]["id"]
    r = mlib.mutate(P, "create_subitem", parent_bid,
                    "mutation ($p:ID!, $n:String!, $v:JSON) { create_subitem(parent_item_id:$p, item_name:$n, column_values:$v) { id board { id } } }",
                    {"p": parent, "n": name, "v": json.dumps(vals or {})}, note=name)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    return r["data"]["create_subitem"]["id"], r["data"]["create_subitem"]["board"]["id"]


def register_subboard(name, bid):
    m = mlib.id_map()
    m["test_boards"].setdefault(name, {"id": str(bid)})
    mlib.save_json(mlib.ID_MAP, m)


def setval(bid, item_id, vals):
    r = mlib.mutate(P, "change_multiple_column_values", bid,
                    "mutation ($b:ID!, $i:ID!, $v:JSON!) { change_multiple_column_values(board_id:$b, item_id:$i, column_values:$v) { id } }",
                    {"b": bid, "i": item_id, "v": json.dumps(vals)}, note="test values")
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))


def subtasks_id(bid):
    for c in mlib.gql("{ boards(ids:[%s]) { columns { id type } } }" % bid)["data"]["boards"][0]["columns"]:
        if c["type"] == "subtasks":
            return c["id"]


def mirror(bid, cid, title, rel, src_board, src_col, fn=None):
    d = {"relation_column": {rel: True},
         "displayed_linked_columns": [{"board_id": str(src_board), "column_ids": [src_col]}]}
    if fn:
        d["function"] = fn
    col(bid, cid, title, "mirror", d)


def values(item_id):
    r = mlib.gql("{ items(ids:[%s]) { name column_values { id type text ... on MirrorValue { display_value } "
                 "... on FormulaValue { display_value } } } }" % item_id)
    it = r["data"]["items"][0]
    return {c["id"]: (c.get("display_value") if c["type"] in ("mirror", "formula") else c["text"])
            for c in it["column_values"]}


if __name__ == "__main__":
    mlib.check_identity()
    CAT = testlib.ensure_test_board(P, "ZZ-TEST- agg catalogue")
    REQ = testlib.ensure_test_board(P, "ZZ-TEST- agg requests")
    SUP = testlib.ensure_test_board(P, "ZZ-TEST- agg supplier")
    MOV = testlib.ensure_test_board(P, "ZZ-TEST- agg movements")
    PRJ = testlib.ensure_test_board(P, "ZZ-TEST- agg projects")

    # catalogue
    col(CAT, "price", "Price", "numbers")
    cat1 = item(CAT, "ZZ-TEST-product", {"price": "10"})
    # movements -> catalogue (two-way, like Applied in/out) for the On hand formula test
    col(MOV, "qty", "Qty", "numbers")
    col(MOV, "applied_in", "Applied in", "board_relation", {"boardIds": [int(CAT)], "boardId": int(CAT),
                                                            "allowMultipleItems": False, "allowCreateReflectionColumn": True})
    col(MOV, "applied_out", "Applied out", "board_relation", {"boardIds": [int(CAT)], "boardId": int(CAT),
                                                              "allowMultipleItems": False, "allowCreateReflectionColumn": True})
    item(MOV, "ZZ-TEST-in", {"qty": "7", "applied_in": {"item_ids": [int(cat1)]}})
    item(MOV, "ZZ-TEST-out", {"qty": "2", "applied_out": {"item_ids": [int(cat1)]}})
    refl = {}
    for c in mlib.gql("{ boards(ids:[%s]) { columns { id title type settings_str } } }" % CAT)["data"]["boards"][0]["columns"]:
        if c["type"] == "board_relation":
            refl[c["title"]] = c["id"]
    rin = [v for k, v in refl.items() if "Movements" in k or "movements" in k]
    print("CAT reflections:", refl)
    cat_cols = mlib.gql("{ boards(ids:[%s]) { columns { id title type settings_str } } }" % CAT)["data"]["boards"][0]["columns"]
    in_ref = [c["id"] for c in cat_cols if c["type"] == "board_relation" and "applied_in" in c["settings_str"]]
    # Identify reflections by the order they were created (in first, then out)
    rels = [c["id"] for c in cat_cols if c["type"] == "board_relation"]
    mirror(CAT, "in_total", "In total", rels[0], MOV, "qty", "sum")
    mirror(CAT, "out_total", "Out total", rels[1], MOV, "qty", "sum")
    col(CAT, "on_hand", "On hand", "formula", {"formula": "{in_total} - {out_total}"})

    # requests with subitems
    req1 = item(REQ, "ZZ-TEST-request", {})
    s1, LINES = subitem(REQ, req1, "ZZ-TEST-line1")
    register_subboard("ZZ-TEST- agg request lines (subitems)", LINES)
    col(LINES, "qty", "Qty", "numbers")
    col(LINES, "product", "Product", "board_relation", {"boardIds": [int(CAT)], "boardId": int(CAT),
                                                        "allowMultipleItems": False, "allowCreateReflectionColumn": False})
    mirror(LINES, "est", "Est price", "product", CAT, "price", "sum")
    col(LINES, "lc", "Line cost", "formula", {"formula": "{qty} * IF({est}>0,{est},0)"})
    s2, _ = subitem(REQ, req1, "ZZ-TEST-line2")
    setval(LINES, s1, {"qty": "3", "product": {"item_ids": [int(cat1)]}})
    setval(LINES, s2, {"qty": "2", "product": {"item_ids": [int(cat1)]}})
    mirror(REQ, "cost", "Material cost", subtasks_id(REQ), LINES, "lc", "sum")
    col(REQ, "tax", "Tax", "numbers")
    setval(REQ, req1, {"tax": "5"})
    col(REQ, "total", "Total", "formula", {"formula": "{cost} + {tax}"})

    # supplier -> requests total (sum of formula over mirror)
    col(SUP, "conn", "Requests", "board_relation", {"boardIds": [int(REQ)], "boardId": int(REQ),
                                                    "allowMultipleItems": True, "allowCreateReflectionColumn": False})
    sup1 = item(SUP, "ZZ-TEST-supplier", {"conn": {"item_ids": [int(req1)]}})
    mirror(SUP, "ordered", "Total ordered", "conn", REQ, "total", "sum")

    # project/unit chain (§5 #2 and #8 pattern)
    prj1 = item(PRJ, "ZZ-TEST-project", {})
    u1, UNITS = subitem(PRJ, prj1, "ZZ-TEST-unit")
    register_subboard("ZZ-TEST- agg units (subitems)", UNITS)
    col(UNITS, "mr", "Material Requests", "board_relation", {"boardIds": [int(REQ)], "boardId": int(REQ),
                                                             "allowMultipleItems": True, "allowCreateReflectionColumn": False})
    setval(UNITS, u1, {"mr": {"item_ids": [int(req1)]}})
    mirror(UNITS, "ucost", "Material cost", "mr", REQ, "cost", "sum")
    mirror(PRJ, "units_cost", "Units material cost", subtasks_id(PRJ), UNITS, "ucost", "sum")

    time.sleep(8)
    for _ in range(6):
        out = {"line1": values(s1), "line2": values(s2), "request": values(req1), "supplier": values(sup1),
               "catalogue": values(cat1), "unit": values(u1), "project": values(prj1)}
        got = {"line1.est": out["line1"].get("est"), "line1.lc": out["line1"].get("lc"),
               "line2.lc": out["line2"].get("lc"), "request.cost": out["request"].get("cost"),
               "request.total": out["request"].get("total"), "supplier.ordered": out["supplier"].get("ordered"),
               "catalogue.on_hand": out["catalogue"].get("on_hand"), "unit.ucost": out["unit"].get("ucost"),
               "project.units_cost": out["project"].get("units_cost")}
        print(json.dumps(got))
        if all(v not in (None, "") for v in got.values()):
            break
        time.sleep(10)
    mlib.save_json(mlib.ROOT + "/data/aggregation-test-result.json", {"ts": mlib._now(), "got": got, "raw": out})
