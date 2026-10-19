"""Phase 0: read-only discovery. Writes raw JSON to results/phase0/."""
import json
from pathlib import Path

from monday import Monday

OUT = Path(__file__).resolve().parent / "results" / "phase0"
OUT.mkdir(parents=True, exist_ok=True)

ITEM_FIELDS = """id name created_at updated_at state group{id title}
  creator{id name email is_guest}
  column_values{id type text value ... on BoardRelationValue{linked_item_ids display_value}
                ... on MirrorValue{display_value} ... on FormulaValue{display_value}}"""


def dump(name, data):
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    m = Monday(read_only=True)
    boards = m.config["boards"]

    # 1. columns
    meta = {}
    for label, bid in boards.items():
        d = m.query("query($b:[ID!]){boards(ids:$b){id name type state workspace{id name}"
                    " groups{id title} columns{id title type settings_str}}}", {"b": [bid]})
        meta[label] = d["boards"][0] if d["boards"] else None
    dump("boards_columns", meta)

    # 2. webhooks
    hooks = {}
    for label, bid in boards.items():
        entry = {}
        for flag in (True, False):
            try:
                d = m.query("query($b:ID!,$f:Boolean){webhooks(board_id:$b,app_webhooks_only:$f)"
                            "{id event board_id config}}", {"b": bid, "f": flag})
                entry[f"app_only={flag}"] = d["webhooks"]
            except Exception as e:  # record, don't hide
                entry[f"app_only={flag}"] = {"error": str(e)}
        hooks[label] = entry
    dump("webhooks", hooks)

    # 3. recent items
    recent = {}
    for label in ("Transactions", "Stock Updates", "Products"):
        d = m.query("query($b:[ID!]){boards(ids:$b){items_page(limit:50,query_params:{order_by:"
                    "[{column_id:\"__creation_log__\",direction:desc}]}){items{" + ITEM_FIELDS +
                    " subitems{" + ITEM_FIELDS + "}}}}}", {"b": [boards[label]]})
        recent[label] = d["boards"][0]["items_page"]["items"]
    dump("recent_items", recent)

    # 3b. activity logs: Products board (stock changes) and Transactions/Stock Updates boards
    logs = {}
    for label in ("Products", "Transactions", "Stock Updates"):
        d = m.query("query($b:[ID!]){boards(ids:$b){activity_logs(limit:200){id event entity data "
                    "user_id account_id created_at}}}", {"b": [boards[label]]})
        logs[label] = d["boards"][0]["activity_logs"]
    dump("activity_logs", logs)

    # users referenced
    uids = set()
    for items in recent.values():
        for it in items:
            for x in [it] + (it.get("subitems") or []):
                if x.get("creator"): uids.add(x["creator"]["id"])
    for l in logs.values():
        uids |= {str(a["user_id"]) for a in l if a.get("user_id")}
    uids = [u for u in uids if u and u.isdigit()]
    users = m.query("query($i:[ID!]){users(ids:$i){id name email is_guest is_admin}}", {"i": uids})["users"] if uids else []
    dump("users", users)
    print("phase0 done")


if __name__ == "__main__":
    main()
