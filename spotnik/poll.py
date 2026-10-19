"""Poll helpers: record elapsed time at which each field changes."""
import json
import time
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def flatten(items):
    """items -> {"<name>#<id>.<col_id>": text-ish value} plus updated_at / group / state."""
    out = {}
    for it in items:
        k = f"{it['name']}#{it['id']}"
        out[f"{k}.updated_at"] = it.get("updated_at")
        out[f"{k}.state"] = it.get("state")
        out[f"{k}.group"] = (it.get("group") or {}).get("title")
        for cv in it.get("column_values", []):
            v = cv.get("display_value") if cv.get("display_value") is not None else cv.get("text")
            if "linked_item_ids" in cv:
                v = ",".join(cv["linked_item_ids"])
            out[f"{k}.{cv['id']}"] = v
        for s in it.get("subitems") or []:
            for kk, vv in flatten([s]).items():
                out[f"{k}/sub:{kk}"] = vv
    return out


def poll(read_state, interval=5, timeout=180, start=None):
    """read_state() -> flat dict. Returns (timeline, final_state)."""
    start = start or time.time()
    prev = read_state()
    timeline = [{"t": round(time.time() - start, 1), "event": "initial", "state": prev}]
    while time.time() - start < timeout:
        time.sleep(interval)
        cur = read_state()
        t = round(time.time() - start, 1)
        changes = {k: {"from": prev.get(k), "to": v} for k, v in cur.items() if prev.get(k) != v}
        changes.update({k: {"from": v, "to": None} for k, v in prev.items() if k not in cur})
        if changes:
            timeline.append({"t": t, "changes": changes})
        prev = cur
    timeline.append({"t": round(time.time() - start, 1), "event": "end"})
    return timeline, prev


def save(test_id, data):
    RESULTS.mkdir(exist_ok=True)
    p = RESULTS / f"{test_id}.json"
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    return p
