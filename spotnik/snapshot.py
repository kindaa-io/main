"""Capture full state of the test products and all ZZ-TEST- transactions / stock updates."""
import json
import time

from monday import Monday, PREFIX

FIELDS = """id name state created_at updated_at group{id title} creator{id name}
  column_values{id type text value ... on BoardRelationValue{linked_item_ids}
                ... on MirrorValue{display_value} ... on FormulaValue{display_value}}"""


def _prefixed(m, board_id, with_subitems=False):
    sub = (" subitems{" + FIELDS + "}") if with_subitems else ""
    q = ("query($b:ID!,$c:String){boards(ids:[$b]){items_page(limit:500,query_params:{rules:[{column_id:\"name\","
         "compare_value:[$c],operator:starts_with}]}){items{" + FIELDS + sub + "}}}}")
    return m.query(q, {"b": str(board_id), "c": PREFIX})["boards"][0]["items_page"]["items"]


def snapshot(m: Monday):
    b = m.config["boards"]
    return {
        "taken_at": time.time(),
        "products": _prefixed(m, b["Products"]),
        "transactions": _prefixed(m, b["Transactions"]),
        "stock_updates": _prefixed(m, b["Stock Updates"], with_subitems=True),
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(Monday(read_only=True)), indent=2, ensure_ascii=False))
