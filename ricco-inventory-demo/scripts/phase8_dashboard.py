"""Phase 8: dashboard "Procurement Overview (Demo)" in the demo folder + API-buildable widgets (§8)."""
import json
import mlib

PHASE = "8"
NAME = "Procurement Overview (Demo)"
PROJECTS = "18412939430"


def B(k):
    return mlib.id_map()["boards"][k]["id"]


def ensure_dashboard():
    m = mlib.id_map()
    if NAME in m.get("dashboards", {}):
        return m["dashboards"][NAME]["id"]
    boards = [B(k) for k in ("Suppliers", "Materials Catalogue", "Material Requests", "Purchase Orders", "Stock Movements")]
    boards.append(PROJECTS)  # read-only source for widget 5 (spec §8)
    r = mlib.mutate(PHASE, "create_dashboard", m["folder"]["id"],
                    "mutation ($n:String!, $w:ID!, $b:[ID!]!, $f:ID) { create_dashboard(name:$n, workspace_id:$w, "
                    "board_ids:$b, kind:PUBLIC, board_folder_id:$f) { id name } }",
                    {"n": NAME, "w": mlib.WORKSPACE_ID, "b": boards, "f": m["folder"]["id"]}, note=NAME)
    if r.get("errors"):
        raise mlib.StopBuild(str(r["errors"]))
    did = r["data"]["create_dashboard"]["id"]
    m = mlib.id_map()
    m.setdefault("dashboards", {})[NAME] = {"id": did, "widgets": {}}
    mlib.save_json(mlib.ID_MAP, m)
    return did


def widget(did, key, kind, name, settings):
    m = mlib.id_map()
    if key in m["dashboards"][NAME]["widgets"]:
        print("  exists:", name)
        return
    r = mlib.mutate(PHASE, "create_widget", did,
                    "mutation ($p:WidgetParentInput!, $k:ExternalWidget!, $n:String!, $s:JSON!) { create_widget(parent:$p, "
                    "kind:$k, name:$n, settings:$s) { id name kind } }",
                    {"p": {"kind": "DASHBOARD", "id": did}, "k": kind, "n": name, "s": settings}, note=name)
    if r.get("errors"):
        print("  FAILED:", name, json.dumps(r["errors"])[:500])
        return
    w = r["data"]["create_widget"]
    m = mlib.id_map()
    m["dashboards"][NAME]["widgets"][key] = {"id": w["id"], "name": name}
    mlib.save_json(mlib.ID_MAP, m)
    print("  created:", name, w["id"])


if __name__ == "__main__":
    mlib.check_identity()
    did = ensure_dashboard()
    print("dashboard", did)
    REQ, PO, CAT = B("Material Requests"), B("Purchase Orders"), B("Materials Catalogue")
    widget(did, "w1", "CHART", "Requests by status", {
        "graph_type": "bar", "x_axis_columns": {REQ: ["status"]}, "y_axis_columns": {REQ: ["default-label-count"]},
        "x_axis_group_by": "color", "y_axis_group_by": "default-label-count"})
    widget(did, "w2", "CHART", "Open POs by supplier", {
        "graph_type": "bar", "x_axis_columns": {PO: ["supplier"]}, "y_axis_columns": {PO: ["default-label-count"]},
        "y_axis_group_by": "default-label-count"})
    widget(did, "w4", "CHART", "Spend by supplier", {
        "graph_type": "bar", "x_axis_columns": {PO: ["supplier"]}, "y_axis_columns": {PO: ["total"]},
        "y_axis_group_by": "formula", "calc_function_type": "sum"})
    widget(did, "w5", "CHART", "Material cost per project", {
        "graph_type": "bar", "x_axis_columns": {PROJECTS: ["name"]},
        "y_axis_columns": {PROJECTS: ["lookup_mm8jr37y", "lookup_mm8jvw8q"]},
        "x_axis_group_by": "name", "y_axis_group_by": "numeric", "calc_function_type": "sum"})
    widget(did, "w7", "NUMBER", "Stock value", {
        "counter_data": {"calculation_type": "columns", "column_ids_per_board": {CAT: ["stock_value"]},
                         "counter_type": "sum", "counter_unit": {"symbol": "$", "direction": "left"}}})
