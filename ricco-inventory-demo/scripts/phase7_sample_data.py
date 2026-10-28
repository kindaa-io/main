"""Phase 7: load §9 sample data (MR-6 excluded, D-08) in spec order; link by item ID only.
Idempotent: every created item is recorded in id-map.json → items[ref] and reused on re-run."""
import datetime
import json
import sys
import mlib

PHASE = "7"
T = datetime.date(2026, 10, 28)  # build day
PEOPLE = {"personsAndTeams": [{"id": 103186497, "kind": "person"}]}
D = mlib.load_json(mlib.ROOT + "/data/sample-data.json", None)
REQ_LINK = "board_relation_mm8j4n2b"  # Material Requests → Project \ Unit (Omer)
POL_LINK = "board_relation_mm8jy91z"  # PO lines → Project \ Unit (Omer)


def day(off):
    return None if off is None else {"date": (T + datetime.timedelta(days=off)).isoformat()}


def B(k):
    return mlib.id_map()["boards"][k]


def ids():
    return mlib.id_map().setdefault("items", {})


def real(ph):
    return mlib.id_map()["real_items"][ph]


def save_item(ref, iid, board):
    m = mlib.id_map()
    m.setdefault("items", {})[ref] = {"id": iid, "board": board}
    mlib.save_json(mlib.ID_MAP, m)


def link(*item_ids):
    return {"item_ids": [int(i) for i in item_ids if i]}


def clean(vals):
    return {k: v for k, v in vals.items() if v not in (None, "", [])}


def create(ref, bkey, name, vals, group):
    if ref in ids():
        return ids()[ref]["id"]
    b = B(bkey)
    r = mlib.mutate(PHASE, "create_item", b["id"],
                    "mutation ($b:ID!, $n:String!, $v:JSON, $g:String) { create_item(board_id:$b, item_name:$n, "
                    "column_values:$v, group_id:$g) { id } }",
                    {"b": b["id"], "n": name, "v": json.dumps(clean(vals)), "g": b["groups"][group]}, note=ref + " " + name)
    if r.get("errors"):
        raise mlib.StopBuild("%s: %s" % (ref, r["errors"]))
    iid = r["data"]["create_item"]["id"]
    save_item(ref, iid, bkey)
    return iid


def create_sub(ref, parent_board, parent_id, sub_board, name, vals):
    if ref in ids():
        return ids()[ref]["id"]
    r = mlib.mutate(PHASE, "create_subitem", B(parent_board)["id"],
                    "mutation ($p:ID!, $n:String!, $v:JSON) { create_subitem(parent_item_id:$p, item_name:$n, column_values:$v) { id } }",
                    {"p": parent_id, "n": name, "v": json.dumps(clean(vals))}, note=ref + " " + name)
    if r.get("errors"):
        raise mlib.StopBuild("%s: %s" % (ref, r["errors"]))
    iid = r["data"]["create_subitem"]["id"]
    save_item(ref, iid, sub_board)
    return iid


def update(ref, vals, note):
    it = ids()[ref]
    bid = B(it["board"])["id"]
    r = mlib.mutate(PHASE, "change_multiple_column_values", bid,
                    "mutation ($b:ID!, $i:ID!, $v:JSON!) { change_multiple_column_values(board_id:$b, item_id:$i, column_values:$v) { id } }",
                    {"b": bid, "i": it["id"], "v": json.dumps(vals)}, note="%s %s" % (ref, note))
    if r.get("errors"):
        raise mlib.StopBuild("%s: %s" % (ref, r["errors"]))


def done(step):
    m = mlib.id_map()
    return step in m.setdefault("phase7_steps_done", [])


def mark(step):
    m = mlib.id_map()
    m.setdefault("phase7_steps_done", []).append(step)
    mlib.save_json(mlib.ID_MAP, m)


def pid(ref):
    return ids()[ref]["id"]


def run():
    mlib.check_identity()
    # 1 Suppliers
    for ref, (name, contact, email, phone, terms, cats) in D["suppliers"].items():
        create(ref, "Suppliers", name, {"contact_person": contact, "email": {"email": email, "text": email},
                                        "phone": {"phone": phone, "countryShortName": "US"},
                                        "payment_terms": terms, "categories": {"labels": cats},
                                        "active": {"label": "Active"}}, "Suppliers")
    # 2 Catalogue
    for ref, (name, cat, uom, st, pack, sup, part, mn, price) in D["products"].items():
        group = cat or "🆕 New – needs review"
        create(ref, "Materials Catalogue", name, {
            "category": {"label": cat} if cat else None, "stock_type": {"label": st},
            "uom": {"labels": [uom]} if uom else None, "pack_size": str(pack) if pack is not None else None,
            "default_supplier": link(pid(sup)) if sup else None, "supplier_part": part,
            "minimum_level": str(mn) if mn is not None else None,
            "last_price": str(price) if price is not None else None}, group)
    pname = {ref: v[0] for ref, v in D["products"].items()}
    # 3 Movements, without links (statuses in step 11)
    for (ref, mtype, p, qty, counted, reason, before, after, _l, _u, _rl, _pl, off, _st, note, rej) in D["movements"]:
        dt = day(off)
        create(ref, "Stock Movements", "%s – %s" % (mtype, pname[p]), {
            "movement_type": {"label": mtype}, "qty": str(qty), "counted_qty": str(counted) if counted else None,
            "reason": {"labels": [reason]} if reason else None, "note": {"text": note} if note else None,
            "qty_before": str(before) if before is not None else None,
            "qty_after": str(after) if after is not None else None,
            "applied_at": dict(dt, time="09:00:00") if _st == "Applied" else None,
            "rejection_reason": rej}, "Ledger")
    # 4 Requests (Unit / Project link)
    for ref, (ph, _st, group, sub, need, _pos, note, _lines) in D["requests"].items():
        n = ref.split("-")[1]
        create(ref, "Material Requests", "DEMO – %s – MR #%s" % (real(ph)["name"], n), {
            REQ_LINK: link(real(ph)["id"]), "materials_complete": {"checked": "true"},
            "programmer": PEOPLE, "purchaser": PEOPLE, "inventory_owner": PEOPLE,
            "needed_by": day(need), "submitted_on": day(sub), "notes": {"text": note} if note else None}, group)
    # 5 Request lines
    for ref, (_ph, _st, _g, _s, _n, _pos, _note, lines) in D["requests"].items():
        for i, (p, req, _dec, res, to_order, issued, _pol) in enumerate(lines, start=1):
            create_sub("%s/L%d" % (ref, i), "Material Requests", pid(ref), "Request lines", pname[p], {
                "product": link(pid(p)), "qty_requested": str(req), "qty_reserved": str(res),
                "qty_to_order": str(to_order), "qty_issued": str(issued) if issued is not None else None})
    # 6 POs (Supplier; no PO header Projects connect, D-07)
    sname = {ref: v[0] for ref, v in D["suppliers"].items()}
    for ref, (_st, group, sup, _prj, order, exp, sent, tax, note) in D["pos"].items():
        draft = _st == "Draft"
        create(ref, "Purchase Orders", "DEMO – %s – %s" % (ref, sname[sup]), {
            "supplier": link(pid(sup)), "purchaser": PEOPLE, "approved_by": None if draft else PEOPLE,
            "order_date": day(order), "expected_delivery": day(exp), "sent_date": day(sent),
            "tax_shipping": str(tax), "notes_to_supplier": {"text": note} if note else None}, group)
    # 7 PO lines (Project \ Unit = project; blank = replenishment)
    for ref, (p, qty, price, rec, rdate, prj, _ls, _rl) in D["po_lines"].items():
        po = ref.split("/")[0]
        create_sub(ref, "Purchase Orders", pid(po), "PO lines", pname[p], {
            "product": link(pid(p)), "qty_ordered": str(qty), "unit_price": str(price), "qty_received": str(rec),
            "date0": day(rdate), POL_LINK: link(real(prj)["id"]) if prj else None})
    # 8 Request line ↔ PO line
    if not done("8"):
        for ref, v in D["po_lines"].items():
            if v[7]:
                update(v[7].replace("/", "/"), {"po_line": link(pid(ref))}, "PO line → " + ref)
        mark("8")
    # 9 Request ↔ PO
    if not done("9"):
        for ref, v in D["requests"].items():
            if v[5]:
                update(ref, {"purchase_orders": link(*[pid(p) for p in v[5]])}, "Purchase Orders → " + ",".join(v[5]))
        mark("9")
    # 10 Movement links
    if not done("10"):
        for (ref, _t, p, _q, _c, _r, _b, _a, direction, up, rl, pl, *_rest) in D["movements"]:
            vals = {"product": link(pid(p))}
            if direction == "in":
                vals["applied_in"] = link(pid(p))
            elif direction == "out":
                vals["applied_out"] = link(pid(p))
            if up:
                vals["unit_project"] = link(real(up)["id"])
            if rl:
                vals["request_line"] = link(pid(rl))
            if pl:
                vals["po_line"] = link(pid(pl))
            update(ref, vals, "links")
        mark("10")
    # 11 Statuses
    if not done("11"):
        for ref, v in D["requests"].items():
            update(ref, {"status": {"label": v[1]}}, "Status " + v[1])
            for i, line in enumerate(v[7], start=1):
                update("%s/L%d" % (ref, i), {"status": {"label": line[2]}}, "Decision " + line[2])
        for ref, v in D["pos"].items():
            update(ref, {"status": {"label": v[0]}}, "Status " + v[0])
        for ref, v in D["po_lines"].items():
            update(ref, {"status": {"label": v[6]}}, "Line status " + v[6])
        for mv in D["movements"]:
            update(mv[0], {"status": {"label": mv[13]}}, "Status " + mv[13])
        mark("11")
    print("loaded", len(ids()), "items")


if __name__ == "__main__":
    run()
