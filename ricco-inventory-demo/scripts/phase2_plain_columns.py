"""Phase 2: plain columns on the 5 main boards (idempotent), then read back and verify."""
import mlib
import columns
import spec_columns as S

MAIN = ["Suppliers", "Materials Catalogue", "Material Requests", "Purchase Orders", "Stock Movements"]


def run(phase="2", boards=MAIN, spec_phase=2):
    mlib.check_identity()
    for b in boards:
        for cid, title, ctype, ph, extra in S.BOARDS[b]:
            if ph == spec_phase and cid:
                columns.ensure(b, cid, phase)
        cols = columns.read_columns(columns.board_id(b))
        columns.record_column_map(b, cols)
        verify(b, cols, spec_phase)


def verify(b, cols, spec_phase):
    import json
    by_id = {c["id"]: c for c in cols}
    problems = []
    for cid, title, ctype, ph, extra in S.BOARDS[b]:
        if ph != spec_phase or not cid:
            continue
        c = by_id.get(cid)
        if not c or c["title"] != title or c["type"] != ctype:
            problems.append("missing/mismatch %s" % cid)
            continue
        st = json.loads(c["settings_str"] or "{}")
        if ctype == "status":
            want = [(l["label"], l["is_done"]) for l in extra["labels"]]
            labels = st["labels"]
            pos = st.get("labels_positions_v2", {})
            got = sorted(labels.items(), key=lambda kv: pos.get(kv[0], 0))
            got_names = [v for k, v in got]
            if got_names != [w[0] for w in want]:
                problems.append("%s labels %s" % (cid, got_names))
            done_ids = set(str(x) for x in st.get("done_colors", []))
            got_done = [v for k, v in got if k in done_ids]
            if got_done != [w[0] for w in want if w[1]]:
                problems.append("%s done %s" % (cid, got_done))
        if ctype == "dropdown":
            got = [l["name"] for l in st["labels"]]
            if got != [l["label"] for l in extra["labels"]]:
                problems.append("%s labels %s" % (cid, got))
    order = [c["title"] for c in cols]
    print(b, "->", order)
    if problems:
        raise mlib.StopBuild("%s verify failed: %s" % (b, problems))


if __name__ == "__main__":
    run()
