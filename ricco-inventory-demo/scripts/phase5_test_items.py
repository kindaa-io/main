"""ZZ-TEST- items on the demo boards that exercise every mirror and formula (Omer, 2026-10-28:
test items only on the structure boards). Idempotent by item name. No link to Sam's boards."""
import json
import time
import mlib
import columns

PHASE = "5-verify"


def board(k):
    return mlib.id_map()["boards"][k]


def find(bid, name):
    r = mlib.gql("{ boards(ids:[%s]) { items_page(limit:200) { items { id name } } } }" % bid)
    for i in r["data"]["boards"][0]["items_page"]["items"]:
        if i["name"] == name:
            return i["id"]


def record(name, iid, bkey):
    m = mlib.id_map()
    lst = m.setdefault("zz_test_items", [])
    if not any(x["id"] == iid for x in lst):
        lst.append({"name": name, "id": iid, "board": bkey})
        mlib.save_json(mlib.ID_MAP, m)


def item(bkey, name, vals, group_title):
    b = board(bkey)
    iid = find(b["id"], name)
    if iid:
        return iid
    r = mlib.mutate(PHASE, "create_item", b["id"],
                    "mutation ($b:ID!, $n:String!, $v:JSON, $g:String) { create_item(board_id:$b, item_name:$n, "
                    "column_values:$v, group_id:$g) { id } }",
                    {"b": b["id"], "n": name, "v": json.dumps(vals), "g": b["groups"][group_title]}, note=name)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    iid = r["data"]["create_item"]["id"]
    record(name, iid, bkey)
    return iid


def subitem(sub_key, parent_key, parent, name, vals):
    sub = board(sub_key)["id"]
    iid = find(sub, name)
    if iid:
        return iid
    r = mlib.mutate(PHASE, "create_subitem", board(parent_key)["id"],
                    "mutation ($p:ID!, $n:String!, $v:JSON) { create_subitem(parent_item_id:$p, item_name:$n, column_values:$v) { id } }",
                    {"p": parent, "n": name, "v": json.dumps(vals)}, note=name)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    iid = r["data"]["create_subitem"]["id"]
    record(name, iid, sub_key)
    return iid


def link(*ids):
    return {"item_ids": [int(i) for i in ids]}


def read(iid, ids):
    r = mlib.gql("{ items(ids:[%s]) { column_values(ids:%s) { id type text ... on MirrorValue { display_value } "
                 "... on FormulaValue { display_value } } } }" % (iid, json.dumps(ids)))
    return {c["id"]: (c.get("display_value") if c["type"] in ("mirror", "formula") else c["text"])
            for c in r["data"]["items"][0]["column_values"]}


if __name__ == "__main__":
    mlib.check_identity()
    sup = item("Suppliers", "ZZ-TEST-Supplier", {
        "contact_person": "ZZ test contact", "email": {"email": "test@zz-test.example", "text": "test@zz-test.example"},
        "active": {"label": "Active"}}, "Suppliers")
    prod = item("Materials Catalogue", "ZZ-TEST-Product", {
        "category": {"label": "Hinges"}, "stock_type": {"label": "Stocked"}, "uom": {"labels": ["each"]},
        "pack_size": "4", "default_supplier": link(sup), "supplier_part": "ZZ-PART", "minimum_level": "12",
        "last_price": "10"}, "Hinges")
    item("Stock Movements", "ZZ-TEST-Opening in", {
        "product": link(prod), "movement_type": {"label": "Opening"}, "qty": "20", "status": {"label": "Applied"},
        "qty_before": "0", "qty_after": "20", "applied_in": link(prod)}, "Ledger")
    item("Stock Movements", "ZZ-TEST-Manual out", {
        "product": link(prod), "movement_type": {"label": "Manual out"}, "qty": "3", "reason": {"labels": ["Damage/Scrap"]},
        "status": {"label": "Applied"}, "qty_before": "20", "qty_after": "17", "applied_out": link(prod)}, "Ledger")
    po = item("Purchase Orders", "ZZ-TEST-PO", {
        "status": {"label": "Sent"}, "supplier": link(sup), "order_date": {"date": "2026-10-19"},
        "expected_delivery": {"date": "2026-10-26"}, "tax_shipping": "6"}, "Open POs")
    pol = subitem("PO lines", "Purchase Orders", po, "ZZ-TEST-PO line", {
        "product": link(prod), "qty_ordered": "8", "unit_price": "9", "qty_received": "0", "status": {"label": "Open"}})
    req = item("Material Requests", "ZZ-TEST-Request", {
        "status": {"label": "In Review"}, "materials_complete": {"checked": "true"}, "purchase_orders": link(po)},
        "Active requests")
    la = subitem("Request lines", "Material Requests", req, "ZZ-TEST-Line A", {
        "product": link(prod), "qty_requested": "6", "status": {"label": "Partial"}, "qty_reserved": "4",
        "qty_to_order": "2", "po_line": link(pol)})
    lb = subitem("Request lines", "Material Requests", req, "ZZ-TEST-Line B", {
        "product": link(prod), "qty_requested": "2", "status": {"label": "From Stock"}, "qty_reserved": "2",
        "qty_to_order": "0"})
    time.sleep(10)
    checks = [
        ("Materials Catalogue", "ZZ-TEST-Product", prod, {
            "supplier_email": "test@zz-test.example", "in_total": "20", "out_total": "3", "on_hand": "17",
            "reserved": "6", "available": "11", "stock_state": "Low", "stock_value": "170"}),
        ("Request lines", "ZZ-TEST-Line A", la, {
            "uom": "each", "on_hand": "17", "available": "11", "supplier": "ZZ-TEST-Supplier", "qty_outstanding": "2",
            "qty_ordered": "8", "qty_received": "0", "po_unit_price": "9", "est_unit_price": "10", "line_cost": "54"}),
        ("Request lines", "ZZ-TEST-Line B", lb, {"qty_outstanding": "0", "line_cost": "20"}),
        ("Material Requests", "ZZ-TEST-Request", req, {"po_status": "Sent", "material_cost": "74"}),
        ("PO lines", "ZZ-TEST-PO line", pol, {
            "uom": "each", "pack_size": "4", "supplier_part": "ZZ-PART", "packs": "2", "line_total": "72"}),
        ("Purchase Orders", "ZZ-TEST-PO", po, {
            "supplier_email": "test@zz-test.example", "contact": "ZZ test contact", "subtotal": "72", "total": "78",
            "delivery_state": "Overdue"}),
        ("Suppliers", "ZZ-TEST-Supplier", sup, {"total_ordered": "78", "open_pos": "Sent"}),
        ("Stock Movements", "ZZ-TEST-Opening in", find(board("Stock Movements")["id"], "ZZ-TEST-Opening in"), {"uom": "each"}),
    ]
    cm = mlib.load_json(mlib.COLUMN_MAP, {})["boards"]
    rows = []
    for bkey, name, iid, exp in checks:
        got = read(iid, list(exp))
        titles = {v["id"]: t for t, v in cm[bkey]["columns"].items()}
        for cid, want in exp.items():
            g = got.get(cid)
            try:
                ok = float(str(g).replace(",", "")) == float(want)
            except (TypeError, ValueError):
                ok = str(g) == want
            rows.append((bkey, name, titles.get(cid, cid), cid, want, g, ok))
    mlib.save_json(mlib.ROOT + "/data/zz-test-verification.json", {"ts": mlib._now(), "rows": rows})
    for r in rows:
        print("%-19s %-18s %-17s expected %-22s API %-22r %s" % (r[0], r[1], r[2], r[4], r[5], "OK" if r[6] else "--"))
