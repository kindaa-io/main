"""Idempotent column creation in spec order (shared by Phases 2-5)."""
import json
import mlib
import spec_columns as S


def board_id(board_key):
    return mlib.id_map()["boards"][board_key]["id"]


def read_columns(bid):
    r = mlib.gql("{ boards(ids:[%s]) { columns { id title type settings_str revision } } }" % bid)
    return r["data"]["boards"][0]["columns"]


def record_column_map(board_key, cols):
    cm = mlib.load_json(mlib.COLUMN_MAP, {"boards": {}})
    cm.setdefault("boards", {})[board_key] = {
        "board_id": board_id(board_key),
        "columns": {c["title"]: {"id": c["id"], "type": c["type"]} for c in cols}}
    mlib.save_json(mlib.COLUMN_MAP, cm)


def _after(board_key, idx, existing_ids, existing_titles):
    """Id of the closest earlier spec column that exists; else 'name'."""
    for cid, title, ctype, _ph, _x in reversed(S.BOARDS[board_key][:idx]):
        if cid and cid in existing_ids:
            return cid
        if ctype == "reflection" and title in existing_titles:
            return existing_titles[title]
    return "name"


def ensure(board_key, cid, phase, defaults=None, note=None):
    """Create spec column `cid` on `board_key` if missing. `defaults` overrides the spec extra."""
    bid = board_id(board_key)
    spec = S.BOARDS[board_key]
    idx = next(i for i, c in enumerate(spec) if c[0] == cid)
    _cid, title, ctype, _ph, extra = spec[idx]
    cols = read_columns(bid)
    ids = {c["id"]: c for c in cols}
    titles = {c["title"]: c["id"] for c in cols}
    if cid in ids:
        if ids[cid]["title"] != title or ids[cid]["type"] != ctype:
            raise mlib.StopBuild("%s.%s exists as %r/%s, spec %r/%s" % (
                board_key, cid, ids[cid]["title"], ids[cid]["type"], title, ctype))
        print("  exists:", board_key, cid)
        return ids[cid]
    if title in titles:
        raise mlib.StopBuild("%s already has a column titled %r (id %s)" % (board_key, title, titles[title]))
    after = _after(board_key, idx, ids, titles)
    d = defaults if defaults is not None else extra
    v = {"b": bid, "id": cid, "t": title, "a": after}
    if ctype == "status":
        q = ("mutation ($b:ID!, $id:String!, $t:String!, $a:ID, $d:CreateStatusColumnSettingsInput) "
             "{ create_status_column(board_id:$b, id:$id, title:$t, after_column_id:$a, defaults:$d) { id title type } }")
        v["d"] = d
        op = "create_status_column"
    elif ctype == "dropdown":
        q = ("mutation ($b:ID!, $id:String!, $t:String!, $a:ID, $d:CreateDropdownColumnSettingsInput) "
             "{ create_dropdown_column(board_id:$b, id:$id, title:$t, after_column_id:$a, defaults:$d) { id title type } }")
        v["d"] = d
        op = "create_dropdown_column"
    else:
        q = ("mutation ($b:ID!, $id:String!, $t:String!, $a:ID, $ty:ColumnType!, $d:JSON) "
             "{ create_column(board_id:$b, id:$id, title:$t, after_column_id:$a, column_type:$ty, defaults:$d) "
             "{ id title type } }")
        v["ty"] = ctype
        v["d"] = json.dumps(d) if d is not None else None
        op = "create_column(%s)" % ctype
    r = mlib.mutate(phase, op, bid, q, v, note=note or "%s: %s" % (board_key, title),
                    allow_sam_board=False)
    if r.get("errors"):
        raise mlib.StopBuild("create %s.%s failed: %s" % (board_key, cid, r["errors"]))
    key = op.split("(")[0]
    print("  created:", board_key, r["data"][key])
    return r["data"][key]
