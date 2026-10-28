"""Phase 7 verification (read-only): compare §9.7 (adjusted for MR-6, D-08) with values read back.
Where the API can't expose a mirror of a formula, the value is derived from readable formulas and
marked 'derived'; those still need a UI glance."""
import json
import mlib

D = mlib.load_json(mlib.ROOT + "/data/sample-data.json", None)
E = D["expected"]


def num(s):
    try:
        return float(str(s).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def vals(item_ids, cols):
    out = {}
    for i in range(0, len(item_ids), 50):
        chunk = item_ids[i:i + 50]
        r = mlib.gql("{ items(ids:[%s]) { id column_values(ids:%s) { id type text ... on MirrorValue { display_value } "
                     "... on FormulaValue { display_value } } } }" % (",".join(chunk), json.dumps(cols)))
        for it in r["data"]["items"]:
            out[it["id"]] = {c["id"]: (c.get("display_value") if c["type"] in ("mirror", "formula") else c["text"])
                             for c in it["column_values"]}
    return out


def main():
    items = mlib.id_map()["items"]
    rows = []

    def row(area, ref, what, exp, got, how="API"):
        ok = (num(exp) == num(got)) if num(exp) is not None else (str(exp) == str(got or ""))
        rows.append([area, ref, what, exp, got, how, "OK" if ok else "MISMATCH"])

    cat = vals([items[p]["id"] for p in E["catalogue"]], ["on_hand", "available", "stock_state", "reserved"])
    for p, (oh, res, av, st) in E["catalogue"].items():
        v = cat[items[p]["id"]]
        row("Catalogue", p, "On hand", oh, v["on_hand"])
        row("Catalogue", p, "Reserved", res, (num(v["on_hand"]) or 0) - (num(v["available"]) or 0), "derived: On hand − Available")
        row("Catalogue", p, "Available", av, v["available"])
        row("Catalogue", p, "Stock state", st, v["stock_state"])
    for mr, cost in E["material_cost"].items():
        lines = [k for k in items if k.startswith(mr + "/")]
        lv = vals([items[k]["id"] for k in lines], ["formula_mm8jjeek"])
        row("Requests", mr, "Material cost", cost, round(sum(num(x.get("formula_mm8jjeek")) or 0 for x in lv.values()), 2),
            "derived: sum of line Line cost")
    po_totals = {}
    pv = vals([items[p]["id"] for p in E["po"]], ["total", "tax_shipping", "delivery_state"])
    for p, (sub, tot, dstate) in E["po"].items():
        v = pv[items[p]["id"]]
        po_totals[p] = num(v["total"])
        row("POs", p, "Subtotal", sub, (num(v["total"]) or 0) - (num(v["tax_shipping"]) or 0), "derived: Total − Tax")
        row("POs", p, "Total", tot, v["total"])
        row("POs", p, "Delivery state", dstate, v["delivery_state"])
    for s, tot in E["supplier_total"].items():
        mine = [p for p, v in D["pos"].items() if v[2] == s]
        row("Suppliers", s, "Total ordered", tot, sum(po_totals[p] or 0 for p in mine), "derived: sum of its PO Totals")
    mlib.save_json(mlib.ROOT + "/data/verification-phase7.json", {"ts": mlib._now(), "rows": rows})
    bad = [r for r in rows if r[-1] != "OK"]
    for r in rows:
        print("%-10s %-8s %-15s expected %-10s got %-10s %-32s %s" % tuple(str(x) for x in r))
    print("mismatches:", len(bad))
    return rows


if __name__ == "__main__":
    main()
