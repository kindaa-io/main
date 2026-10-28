"""Phase 4: connect columns (two-way inside the demo; one-way to Sam's boards). Idempotent."""
import json
import sys
import mlib
import columns
import spec_columns as S

PHASE = "4"
PROJECTS, UNITS, PCAL = 18412939430, 18412939439, 18433554480

# (board, column id, target boards (keys or ids), multi, two_way, reflection title on target)
CONNECTS = [
    ("Materials Catalogue", "default_supplier", ["Suppliers"], False, True, "Products"),
    ("Purchase Orders", "supplier", ["Suppliers"], False, True, "Purchase Orders"),
    ("Material Requests", "purchase_orders", ["Purchase Orders"], True, True, "Material Requests"),
    ("Request lines", "product", ["Materials Catalogue"], False, True, "⚙️ Request lines"),
    ("Request lines", "po_line", ["PO lines"], False, True, "Request line"),
    ("Stock Movements", "applied_in", ["Materials Catalogue"], False, True, "⚙️ Applied in"),
    ("Stock Movements", "applied_out", ["Materials Catalogue"], False, True, "⚙️ Applied out"),
    ("PO lines", "product", ["Materials Catalogue"], False, False, None),
    ("Stock Movements", "product", ["Materials Catalogue"], False, False, None),
    ("Stock Movements", "request_line", ["Request lines"], False, False, None),
    ("Stock Movements", "po_line", ["PO lines"], False, False, None),
    ("Material Requests", "pc_job", [PCAL], False, False, None),
    ("PO lines", "project", [PROJECTS], False, False, None),
    ("Stock Movements", "unit_project", [PROJECTS, UNITS], False, False, None),
]


def bid_of(x):
    return int(x) if isinstance(x, int) else int(columns.board_id(x))


def ensure_connect(board, cid, targets, multi, two_way, refl_title):
    tids = [bid_of(t) for t in targets]
    src = int(columns.board_id(board))
    before = {}
    if two_way:
        assert len(tids) == 1 and tids[0] not in (PROJECTS, UNITS, PCAL)
        before = {c["id"] for c in columns.read_columns(tids[0])}
    d = {"boardIds": tids, "allowMultipleItems": multi, "allowCreateReflectionColumn": two_way}
    if len(tids) == 1:
        d["boardId"] = tids[0]
    existed = any(c["id"] == cid for c in columns.read_columns(src))
    columns.ensure(board, cid, PHASE, defaults=d)
    col = next(c for c in columns.read_columns(src) if c["id"] == cid)
    st = json.loads(col["settings_str"])
    print("   settings:", st)
    if sorted(st.get("boardIds", [])) != sorted(tids) or bool(st.get("allowMultipleItems")) != multi:
        raise mlib.StopBuild("%s.%s settings mismatch %s" % (board, cid, st))
    if not two_way:
        if st.get("allowCreateReflectionColumn"):
            raise mlib.StopBuild("%s.%s is two-way but should be one-way" % (board, cid))
        return
    tcols = columns.read_columns(tids[0])
    refl = [c for c in tcols if c["type"] == "board_relation"
            and src in json.loads(c["settings_str"]).get("boardIds", [])]
    titled = [c for c in refl if c["title"] == refl_title]
    if titled:
        print("   reflection:", titled[0]["id"], refl_title)
        return titled[0]["id"]
    new = [c for c in refl if c["id"] not in before] if not existed else refl
    if len(new) != 1:
        raise mlib.StopBuild("%s.%s: expected 1 reflection on target, found %s (two-way may not have been created)"
                             % (board, cid, [(c["id"], c["title"]) for c in refl]))
    r = mlib.mutate(PHASE, "change_column_title", str(tids[0]),
                    "mutation ($b:ID!, $c:String!, $t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id title } }",
                    {"b": str(tids[0]), "c": new[0]["id"], "t": refl_title},
                    note="rename reflection of %s.%s (was %r)" % (board, cid, new[0]["title"]))
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    print("   reflection:", new[0]["id"], new[0]["title"], "->", refl_title)
    return new[0]["id"]


def sam_diff():
    snap = mlib.load_json(mlib.ROOT + "/snapshots/pre-build.json", None)
    diffs = []
    for b in snap["boards"]:
        now = {c["id"]: c for c in columns.read_columns(b["id"])}
        then = {c["id"]: c for c in b["columns"]}
        for k in now.keys() - then.keys():
            diffs.append(("NEW", b["name"], k, now[k]["title"]))
        for k in then.keys() - now.keys():
            diffs.append(("GONE", b["name"], k, then[k]["title"]))
        for k in now.keys() & then.keys():
            if now[k]["title"] != then[k]["title"] or now[k]["settings_str"] != then[k]["settings_str"]:
                diffs.append(("CHANGED", b["name"], k, now[k]["title"]))
    return diffs


if __name__ == "__main__":
    mlib.check_identity()
    only = sys.argv[1:]
    for c in CONNECTS:
        if only and "%s.%s" % (c[0], c[1]) not in only:
            continue
        print(c[0], c[1])
        ensure_connect(*c)
        d = sam_diff()
        if d:
            raise mlib.StopBuild("Sam's boards changed: %s" % d)
    print("Sam's boards vs snapshot:", sam_diff() or "no change")
