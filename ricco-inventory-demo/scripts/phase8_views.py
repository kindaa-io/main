"""Phase 8: table views from spec §6 (kanban views → MANUAL-STEPS). Idempotent by view name."""
import json
import sys
import mlib
import columns

PHASE = "8"


def bid(k):
    return columns.board_id(k)


def cols(k):
    return columns.read_columns(bid(k))


def label_ids(k, cid, names):
    c = next(c for c in cols(k) if c["id"] == cid)
    labels = json.loads(c["settings_str"])["labels"]
    return [int(i) for i, n in labels.items() if n in names]


def visibility(k, only=None):
    """Hide ⚙️ columns; if `only` is given, show just those column ids."""
    props = []
    for c in cols(k):
        if c["id"] == "name":
            continue
        vis = (c["id"] in only) if only else not c["title"].startswith("⚙️")
        props.append({"column_id": c["id"], "visible": vis})
    return props


def existing(k):
    r = mlib.gql("{ boards(ids:[%s]) { views { id name type } } }" % bid(k))
    return {v["name"]: v for v in r["data"]["boards"][0]["views"]}


def view(k, name, filt=None, sort=None, settings=None):
    if name in existing(k):
        print("  exists:", k, name)
        return existing(k)[name]["id"], None
    v = {"b": bid(k), "n": name, "f": filt, "s": sort, "st": settings}
    r = mlib.mutate(PHASE, "create_view_table", bid(k),
                    "mutation ($b:ID!, $n:String, $f:ItemsQueryGroup, $s:[ItemsQueryOrderBy!], $st:TableViewSettingsInput) "
                    "{ create_view_table(board_id:$b, name:$n, filter:$f, sort:$s, settings:$st) { id name } }",
                    v, note="%s: view %s" % (k, name))
    if r.get("errors"):
        print("  FAILED:", k, name, r["errors"][0].get("message"), r["errors"][0].get("extensions", {}).get("errors"))
        return None, r["errors"]
    print("  created:", k, name, r["data"]["create_view_table"]["id"])
    return r["data"]["create_view_table"]["id"], None


def run(only=None):
    mlib.check_identity()
    results = {}
    specs = [
        ("Stock Movements", "Rejected & pending",
         lambda: dict(filt={"rules": [{"column_id": "status", "compare_value": label_ids("Stock Movements", "status", ["Rejected", "Pending"]), "operator": "any_of"}]},
                      settings={"columns": {"column_properties": visibility("Stock Movements")}})),
        ("Stock Movements", "Ledger",
         lambda: dict(sort=[{"column_id": "movement_no", "direction": "asc"}],
                      settings={"columns": {"column_properties": visibility("Stock Movements")}})),
        ("Stock Movements", "By product",
         lambda: dict(settings={"columns": {"column_properties": visibility("Stock Movements")},
                                "group_by": {"conditions": [{"columnId": "product"}]}})),
        ("Materials Catalogue", "Low & out",
         lambda: dict(filt={"rules": [{"column_id": "stock_state", "compare_value": ["Low", "Out"], "operator": "any_of"}]},
                      settings={"columns": {"column_properties": visibility("Materials Catalogue")}})),
        ("Materials Catalogue", "Reserved vs available",
         lambda: dict(sort=[{"column_id": "reserved", "direction": "desc"}],
                      settings={"columns": {"column_properties": visibility(
                          "Materials Catalogue", {"uom", "on_hand", "reserved", "available", "stock_state"})}})),
        ("Purchase Orders", "By supplier",
         lambda: dict(settings={"group_by": {"conditions": [{"columnId": "supplier"}]}})),
        ("Purchase Orders", "Overdue deliveries",
         lambda: dict(filt={"rules": [{"column_id": "delivery_state", "compare_value": ["Overdue"], "operator": "any_of"}]})),
    ]
    for k, name, mk in specs:
        if only and name not in only:
            continue
        a = mk()
        results[(k, name)] = view(k, name, a.get("filt"), a.get("sort"), a.get("settings"))
    return results


if __name__ == "__main__":
    run(sys.argv[1:] or None)
