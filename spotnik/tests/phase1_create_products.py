"""Phase 1 step 1: create ZZ-TEST-A and ZZ-TEST-B on Products via API, then poll what the engine does."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monday import Monday  # noqa: E402
from poll import flatten, poll, save  # noqa: E402
from snapshot import snapshot  # noqa: E402


def main():
    m = Monday(read_only=False)
    pb = m.config["boards"]["Products"]
    cols = m.col_map(pb)
    existing = snapshot(m)["products"]
    if existing:
        raise SystemExit(f"ZZ-TEST- products already exist, refusing to create: {[e['name'] for e in existing]}")
    cv = {cols["Current Quantity"]["id"]: "0", cols["Minimum Level"]["id"]: "10",
          cols["Out of stock level"]["id"]: "0", cols["Price per unit"]["id"]: "5"}
    before = snapshot(m)
    actions, t0 = [], time.time()
    for name in ("ZZ-TEST-A", "ZZ-TEST-B"):
        r = m.create_item(pb, name, cv)
        actions.append({"t": round(time.time() - t0, 1), "create_item": name, "column_values": cv, "result": r})
    timeline, _ = poll(lambda: flatten(snapshot(m)["products"]), start=t0)
    after = snapshot(m)
    p = save("1.1_create_products", {"before": before, "actions": actions, "timeline": timeline, "after": after,
                                     "column_map": cols})
    print("saved", p)
    for it in after["products"]:
        print(it["id"], it["name"], it["creator"], {c["id"]: c.get("text") for c in it["column_values"] if c.get("text")})


if __name__ == "__main__":
    main()
