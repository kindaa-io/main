"""Phase 3: bring the subitem boards into existence (API can't create a subtasks column),
then park the ZZ-TEST- bootstrap parent on a test board (DEVIATIONS D-03/D-04), then plain
subitem columns. Idempotent."""
import mlib
import testlib
import columns
import spec_columns as S

PHASE = "3"
PARKING = "ZZ-TEST- bootstrap parking"


def subtasks_col(bid):
    for c in columns.read_columns(bid):
        if c["type"] == "subtasks":
            import json
            return c["id"], str(json.loads(c["settings_str"])["boardIds"][0])
    return None, None


def bootstrap(sub_key, parent_key):
    m = mlib.id_map()
    if sub_key in m["boards"]:
        print(sub_key, "exists", m["boards"][sub_key])
        return
    pbid = m["boards"][parent_key]["id"]
    col, sub_bid = subtasks_col(pbid)
    if not col:
        group = list(m["boards"][parent_key]["groups"].values())[0]
        r = mlib.mutate(PHASE, "create_item", pbid,
                        "mutation ($b:ID!, $n:String!, $g:String) { create_item(board_id:$b, item_name:$n, group_id:$g) { id } }",
                        {"b": pbid, "n": "ZZ-TEST-bootstrap", "g": group}, note=parent_key + ": bootstrap parent")
        parent = r["data"]["create_item"]["id"]
        r = mlib.mutate(PHASE, "create_subitem", pbid,
                        "mutation ($p:ID!, $n:String!) { create_subitem(parent_item_id:$p, item_name:$n) { id board { id name } } }",
                        {"p": parent, "n": "ZZ-TEST-bootstrap line"}, note=parent_key + ": bootstrap subitem")
        col, sub_bid = subtasks_col(pbid)
        park = testlib.ensure_test_board(PHASE, PARKING)
        pg = mlib.gql("{ boards(ids:[%s]) { groups { id } } }" % park)["data"]["boards"][0]["groups"][0]["id"]
        r = mlib.mutate(PHASE, "move_item_to_board", pbid,
                        "mutation ($b:ID!, $i:ID!, $g:ID!) { move_item_to_board(board_id:$b, item_id:$i, group_id:$g) { id board { id } } }",
                        {"b": park, "i": parent, "g": pg}, note=parent_key + ": park ZZ-TEST-bootstrap (+subitem) in test folder")
        if r.get("errors"):
            raise mlib.StopBuild("move failed: %s" % r["errors"])
        m = mlib.id_map()
        m.setdefault("zz_test_items", []).append({"name": "ZZ-TEST-bootstrap", "id": parent, "created_on": parent_key,
                                                 "now_on": PARKING})
    m["boards"][parent_key]["subitems_column"] = col
    m["boards"][sub_key] = {"id": sub_bid, "parent": parent_key}
    mlib.save_json(mlib.ID_MAP, m)
    print(sub_key, "->", sub_bid, "via", col)


if __name__ == "__main__":
    mlib.check_identity()
    for sub_key, parent_key in S.SUBITEM_BOARDS.items():
        bootstrap(sub_key, parent_key)
    m = mlib.id_map()
    for sub_key in S.SUBITEM_BOARDS:
        cols = columns.read_columns(m["boards"][sub_key]["id"])
        print(sub_key, "default columns:", [(c["id"], c["type"], c["title"]) for c in cols])
        items = mlib.gql("{ boards(ids:[%s]) { items_count } }" % m["boards"][sub_key]["id"])
        print("   items on board:", items["data"]["boards"][0]["items_count"])


def repurpose_defaults():
    import json
    m = mlib.id_map()
    # PO lines: Status -> Line status (labels), Date -> Received date. Request lines Decision done above.
    for sub_key in S.SUBITEM_BOARDS:
        bid = m["boards"][sub_key]["id"]
        for cid, title, ctype, ph, extra in S.BOARDS[sub_key]:
            if cid not in ("status", "date0"):
                continue
            col = next(c for c in columns.read_columns(bid) if c["id"] == cid)
            if col["title"] == title:
                print("  already repurposed:", sub_key, cid, title)
                continue
            if ctype == "status":
                labels = [dict(l, id=i) if i < 3 else dict(l) for i, l in enumerate(extra["labels"])]
                r = mlib.mutate(PHASE, "update_status_column", bid,
                                "mutation ($b:ID!, $r:String!, $t:String, $s:UpdateStatusColumnSettingsInput) "
                                "{ update_status_column(board_id:$b, id:\"status\", title:$t, revision:$r, settings:$s) { id title } }",
                                {"b": bid, "r": col["revision"], "t": title, "s": {"labels": labels}},
                                note="%s: repurpose default Status -> %s" % (sub_key, title))
            else:
                r = mlib.mutate(PHASE, "change_column_title", bid,
                                "mutation ($b:ID!, $c:String!, $t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id title } }",
                                {"b": bid, "c": cid, "t": title}, note="%s: repurpose default Date -> %s" % (sub_key, title))
            if r.get("errors"):
                raise mlib.StopBuild(str(r["errors"]))
        for cid, orig in S.UNUSED_DEFAULTS.get(sub_key, {}).items():
            new = "zz-unused – " + orig
            col = next(c for c in columns.read_columns(bid) if c["id"] == cid)
            if col["title"] == new:
                continue
            r = mlib.mutate(PHASE, "change_column_title", bid,
                            "mutation ($b:ID!, $c:String!, $t:String!) { change_column_title(board_id:$b, column_id:$c, title:$t) { id title } }",
                            {"b": bid, "c": cid, "t": new}, note="%s: unused default %s" % (sub_key, orig))
            if r.get("errors"):
                raise mlib.StopBuild(str(r["errors"]))


def plain_columns():
    import phase2_plain_columns as p2
    p2.run(phase=PHASE, boards=list(S.SUBITEM_BOARDS), spec_phase=3)


if __name__ == "__main__":
    repurpose_defaults()
    plain_columns()
