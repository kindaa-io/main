"""Phase 1: folder, 5 boards, groups. Idempotent: re-running reuses recorded IDs.

Usage: python3 scripts/phase1_folder_boards.py [folder|boards|groups]
"""
import sys
import mlib

PHASE = "1"
FOLDER_NAME = "Inventory & Procurement (Demo)"
BOARDS = ["Suppliers", "Materials Catalogue", "Material Requests", "Purchase Orders", "Stock Movements"]
GROUPS = {
    "Suppliers": ["Suppliers"],
    "Materials Catalogue": ["🆕 New – needs review", "Sheet Goods", "Edgeband", "Hinges",
                            "Slides & Hardware", "Accessories", "Finish / Paint"],
    "Material Requests": ["Active requests", "Closed & cancelled"],
    "Purchase Orders": ["Open POs", "Closed & cancelled"],
    "Stock Movements": ["Ledger"],
}


def ensure_folder():
    m = mlib.id_map()
    folders = mlib.gql("{ folders(workspace_ids:[%s], limit:100) { id name } }" % mlib.WORKSPACE_ID)
    same = [f for f in folders["data"]["folders"] if f["name"] == FOLDER_NAME]
    if m.get("folder"):
        assert any(f["id"] == m["folder"]["id"] for f in same), "recorded folder not found"
        print("folder exists:", m["folder"])
        return m["folder"]["id"]
    if same:
        raise mlib.StopBuild("folder %r already exists but is not recorded: %s" % (FOLDER_NAME, same))
    r = mlib.mutate(PHASE, "create_folder", mlib.WORKSPACE_ID,
                    "mutation ($n:String!, $w:ID!) { create_folder(name:$n, workspace_id:$w) { id name } }",
                    {"n": FOLDER_NAME, "w": mlib.WORKSPACE_ID}, note=FOLDER_NAME, allow_new_folder=True)
    f = r["data"]["create_folder"]
    m["folder"] = {"id": f["id"], "name": f["name"]}
    mlib.save_json(mlib.ID_MAP, m)
    print("created folder", f)
    return f["id"]


def ensure_boards(only=None):
    m = mlib.id_map()
    fid = m["folder"]["id"]
    existing = mlib.gql("{ boards(workspace_ids:[%s], limit:500, state:active) { id name board_folder_id type } }"
                        % mlib.WORKSPACE_ID)["data"]["boards"]
    for name in BOARDS:
        if only and name not in only:
            continue
        if name in m["boards"]:
            print("board exists:", name, m["boards"][name]["id"])
            continue
        clash = [b for b in existing if b["name"] == name and str(b["board_folder_id"]) == str(fid)]
        if clash:
            raise mlib.StopBuild("board %r already in folder but not recorded: %s" % (name, clash))
        r = mlib.mutate(PHASE, "create_board", fid,
                        "mutation ($n:String!, $f:ID!, $w:ID!) { create_board(board_name:$n, board_kind:public, "
                        "folder_id:$f, workspace_id:$w, empty:true) { id name } }",
                        {"n": name, "f": fid, "w": mlib.WORKSPACE_ID}, note=name)
        b = r["data"]["create_board"]
        m["boards"][name] = {"id": b["id"]}
        mlib.save_json(mlib.ID_MAP, m)
        print("created board", name, b["id"])


def board_groups(bid):
    r = mlib.gql("{ boards(ids:[%s]) { groups { id title position } } }" % bid)
    return sorted(r["data"]["boards"][0]["groups"], key=lambda g: float(g["position"]))


def ensure_groups():
    m = mlib.id_map()
    for name, wanted in GROUPS.items():
        bid = m["boards"][name]["id"]
        groups = board_groups(bid)
        titles = [g["title"] for g in groups]
        # Repurpose the default group (rename) instead of leaving an unused one.
        if wanted[0] not in titles and len(groups) == 1 and groups[0]["title"] not in wanted:
            g = groups[0]
            mlib.mutate(PHASE, "update_group(title)", bid,
                        "mutation ($b:ID!, $g:String!, $v:String!) { update_group(board_id:$b, group_id:$g, "
                        "group_attribute:title, new_value:$v) { id title } }",
                        {"b": bid, "g": g["id"], "v": wanted[0]}, note="%s: rename default %r" % (name, g["title"]))
            groups = board_groups(bid)
            titles = [g["title"] for g in groups]
        prev = next(g for g in groups if g["title"] == wanted[0])["id"]
        for title in wanted[1:]:
            if title in titles:
                prev = next(g for g in groups if g["title"] == title)["id"]
                continue
            r = mlib.mutate(PHASE, "create_group", bid,
                            "mutation ($b:ID!, $n:String!, $rel:String) { create_group(board_id:$b, group_name:$n, "
                            "relative_to:$rel, position_relative_method:after_at) { id title } }",
                            {"b": bid, "n": title, "rel": prev}, note="%s: %s" % (name, title))
            prev = r["data"]["create_group"]["id"]
        final = board_groups(bid)
        m["boards"][name]["groups"] = {g["title"]: g["id"] for g in final}
        mlib.save_json(mlib.ID_MAP, m)
        print(name, [g["title"] for g in final])
        if [g["title"] for g in final] != wanted:
            raise mlib.StopBuild("%s group order %s != spec %s" % (name, [g["title"] for g in final], wanted))


if __name__ == "__main__":
    mlib.check_identity()
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("folder", "all"):
        ensure_folder()
    if step in ("boards", "all"):
        ensure_boards(sys.argv[2:] or None)
    if step in ("groups", "all"):
        ensure_groups()
