"""Test folder + ZZ-TEST- boards (DEVIATIONS D-03). Idempotent."""
import mlib

TEST_FOLDER = "ZZ-TEST- Inventory Demo Tests"


def ensure_test_folder(phase):
    m = mlib.id_map()
    if m.get("test_folder"):
        return m["test_folder"]["id"]
    folders = mlib.gql("{ folders(workspace_ids:[%s], limit:100) { id name } }" % mlib.WORKSPACE_ID)["data"]["folders"]
    if any(f["name"] == TEST_FOLDER for f in folders):
        raise mlib.StopBuild("test folder exists but not recorded")
    r = mlib.mutate(phase, "create_folder", mlib.WORKSPACE_ID,
                    "mutation ($n:String!, $w:ID!) { create_folder(name:$n, workspace_id:$w) { id name } }",
                    {"n": TEST_FOLDER, "w": mlib.WORKSPACE_ID}, note=TEST_FOLDER, allow_new_folder=True)
    f = r["data"]["create_folder"]
    m["test_folder"] = {"id": f["id"], "name": f["name"]}
    mlib.save_json(mlib.ID_MAP, m)
    return f["id"]


def ensure_test_board(phase, name):
    assert name.startswith("ZZ-TEST-")
    m = mlib.id_map()
    if name in m["test_boards"]:
        return m["test_boards"][name]["id"]
    fid = ensure_test_folder(phase)
    r = mlib.mutate(phase, "create_board", fid,
                    "mutation ($n:String!, $f:ID!, $w:ID!) { create_board(board_name:$n, board_kind:public, "
                    "folder_id:$f, workspace_id:$w, empty:true) { id name } }",
                    {"n": name, "f": fid, "w": mlib.WORKSPACE_ID}, note=name)
    b = r["data"]["create_board"]
    m = mlib.id_map()
    m["test_boards"][name] = {"id": b["id"]}
    mlib.save_json(mlib.ID_MAP, m)
    return b["id"]


def create_item(phase, bid, name, values=None, group=None):
    assert name.startswith("ZZ-TEST-")
    import json
    r = mlib.mutate(phase, "create_item", bid,
                    "mutation ($b:ID!, $n:String!, $v:JSON, $g:String) { create_item(board_id:$b, item_name:$n, "
                    "column_values:$v, group_id:$g) { id name } }",
                    {"b": bid, "n": name, "v": json.dumps(values or {}), "g": group}, note=name)
    if r.get("errors"):
        raise mlib.StopBuild("create_item failed: %s" % r["errors"])
    return r["data"]["create_item"]["id"]
