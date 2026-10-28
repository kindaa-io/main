"""Phase 6 (Gate 2 approved by Omer 2026-10-28): rename the 4 reflections Omer's connects created
on Projects/Units and add the 6 approved mirrors. Idempotent (by title). Then diff vs snapshot."""
import json
import mlib
import columns
import phase4_connects as p4

PHASE = "6"
PROJECTS, UNITS = "18412939430", "18412939439"
REQ = "18437453027"
PO_LINES = "18437453449"

RENAMES = [  # (board, column id, new title) — Omer approved renaming
    (PROJECTS, "board_relation_mm8jqhv4", "Material Requests"),
    (UNITS, "board_relation_mm8j9wgg", "Material Requests"),
    (PROJECTS, "board_relation_mm8jbv88", "PO lines"),
    (UNITS, "board_relation_mm8jxknn", "PO lines"),
]
# Columns allowed to differ from snapshots/pre-build.json after this phase.
ALLOWED_NEW = {
    PROJECTS: {"board_relation_mm8jqhv4", "board_relation_mm8jbv88"},
    UNITS: {"board_relation_mm8j9wgg", "board_relation_mm8jxknn",
            "board_relation_mm8j89fg"},  # 'link to Stock Updates': not ours; Omer said ignore
}
# Deleted in the UI by the Kindaa Support account on 2026-10-28 11:03 UTC (activity log), not by this
# build; Omer: "ignore" the Stock Updates link.
KNOWN_GONE = {PROJECTS: {"board_relation_mm6vdxt9"}}
ALLOWED_TITLES = {PROJECTS: {"Material cost", "Request status", "Units material cost", "PO status"},
                  UNITS: {"Material cost", "Request status"}}


def cols(bid):
    return {c["id"]: c for c in columns.read_columns(bid)}


def by_title(bid, title):
    return [c for c in columns.read_columns(bid) if c["title"] == title]


def rename(bid, cid, title):
    c = cols(bid)[cid]
    if c["title"] == title:
        print("  already:", bid, cid, title)
        return
    r = mlib.mutate(PHASE, "change_column_title", bid,
                    "mutation ($b:ID!, $c:String!, $t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id title } }",
                    {"b": bid, "c": cid, "t": title}, note="rename %r -> %r" % (c["title"], title), allow_sam_board=True)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    print("  renamed:", bid, cid, c["title"], "->", title)


def mirror(bid, title, rel, src_board, src_col, kind, note):
    existing = by_title(bid, title)
    if existing:
        if len(existing) > 1 or existing[0]["type"] != "mirror":
            raise mlib.StopBuild("unexpected existing %r on %s: %s" % (title, bid, existing))
        print("  exists:", bid, title, existing[0]["id"])
        return existing[0]["id"]
    d = {"relation_column": {rel: True},
         "displayed_linked_columns": [{"board_id": str(src_board), "column_ids": [src_col]}]}
    d.update({"function": "sum"} if kind == "sum" else {"sumType": "allStatuses"})
    r = mlib.mutate(PHASE, "create_column(mirror)", bid,
                    "mutation ($b:ID!, $t:String!, $d:JSON) { create_column(board_id:$b, title:$t, column_type:mirror, defaults:$d) { id title } }",
                    {"b": bid, "t": title, "d": json.dumps(d)}, note=note, allow_sam_board=True)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    cid = r["data"]["create_column"]["id"]
    print("  created:", bid, title, cid)
    return cid


def check():
    snap = mlib.load_json(mlib.ROOT + "/snapshots/pre-build.json", None)
    bad = []
    for b in snap["boards"]:
        then = {c["id"]: c for c in b["columns"]}
        now = cols(b["id"])
        for k in then:
            if k in KNOWN_GONE.get(b["id"], set()) and k not in now:
                continue
            if k not in now or now[k]["title"] != then[k]["title"] or now[k]["settings_str"] != then[k]["settings_str"]:
                bad.append(("CHANGED/GONE", b["name"], k))
        for k in now.keys() - then.keys():
            ok = k in ALLOWED_NEW.get(b["id"], set()) or (
                now[k]["type"] == "mirror" and now[k]["title"] in ALLOWED_TITLES.get(b["id"], set()))
            if not ok:
                bad.append(("UNEXPECTED NEW", b["name"], k, now[k]["title"]))
    return bad


if __name__ == "__main__":
    mlib.check_identity()
    pre = check()
    if pre:
        raise mlib.StopBuild("Sam's boards differ before Phase 6: %s" % pre)
    for bid, cid, title in RENAMES:
        rename(bid, cid, title)
    u_cost = mirror(UNITS, "Material cost", "board_relation_mm8j9wgg", REQ, "material_cost", "sum",
                    "#2 Units Material cost <- Material Requests.Material cost (sum)")
    mirror(UNITS, "Request status", "board_relation_mm8j9wgg", REQ, "status", "status",
           "#3 Units Request status <- Material Requests.Status (all statuses)")
    mirror(PROJECTS, "Material cost", "board_relation_mm8jqhv4", REQ, "material_cost", "sum",
           "#6 Projects Material cost <- Material Requests.Material cost (sum)")
    mirror(PROJECTS, "Request status", "board_relation_mm8jqhv4", REQ, "status", "status",
           "#7 Projects Request status <- Material Requests.Status (all statuses)")
    mirror(PROJECTS, "Units material cost", "subtasks_mm3aqxk2", UNITS, u_cost, "sum",
           "#8 Projects Units material cost <- Units.Material cost (sum)")
    mirror(PROJECTS, "PO status", "board_relation_mm8jbv88", PO_LINES, "status", "status",
           "#9 Projects PO status <- PO lines.Line status (all statuses)")
    post = check()
    print("check vs snapshot:", post or "only approved columns added")
    if post:
        raise mlib.StopBuild("unexpected change on Sam's boards: %s" % post)
    snap = mlib.load_json(mlib.ROOT + "/snapshots/pre-build.json", None)
    for b in snap["boards"]:
        b["columns"] = mlib.gql("{ boards(ids:[%s]) { columns { id title type description archived settings settings_str } } }"
                                % b["id"])["data"]["boards"][0]["columns"]
    snap["captured_at"] = mlib._now()
    snap["purpose"] = "Columns of Sam's boards after Phase 6 (approved additions only)."
    mlib.save_json(mlib.ROOT + "/snapshots/post-phase-6.json", snap)
    for bid in (UNITS, PROJECTS):
        for c in columns.read_columns(bid):
            if c["id"] in ALLOWED_NEW.get(bid, set()) or c["type"] == "mirror" and c["title"] in ALLOWED_TITLES[bid]:
                print("   ", bid, c["id"], c["type"], c["title"], c["settings_str"][:160])
