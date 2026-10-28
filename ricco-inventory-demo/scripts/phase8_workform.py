"""Phase 8: WorkForm "Manual stock update" on Stock Movements (form view 288954194), per spec §7."""
import json
import mlib

PHASE = "8"
BOARD = "18437453030"
TOKEN = "40a69954f3e3be3ace6dc747077e3018"
DESC = ("Manual stock changes only. To take material for a job, use a material request. A manual out or a count "
        "that would cut into stock reserved for projects will be rejected.")
MANUAL_IN, MANUAL_OUT, COUNT = "15", "0", "4"


def show_if(values):
    return {"operator": "OR", "rules": [{"operator": "OR", "conditions": [
        {"building_block_id": "movement_type", "operator": "OR", "values": values}]}]}


def form():
    r = mlib.gql('{ form(formToken:"%s") { title description questions { id type title visible required '
                 'options { label value visible } show_if_rules } } }' % TOKEN)
    return r["data"]["form"]


def upd(qid, q, note):
    r = mlib.mutate(PHASE, "update_form_question", BOARD,
                    "mutation ($t:String!, $id:String!, $q:UpdateQuestionInput!) { update_form_question(formToken:$t, "
                    "questionId:$id, question:$q) { id title visible required } }",
                    {"t": TOKEN, "id": qid, "q": q}, note=note)
    if r.get("errors"):
        print("  FAILED", qid, json.dumps(r["errors"])[:400])
    return r


if __name__ == "__main__":
    mlib.check_identity()
    f = form()
    types = {q["id"]: q["type"] for q in f["questions"]}
    r = mlib.mutate(PHASE, "update_form", BOARD,
                    "mutation ($t:String!, $i:UpdateFormInput!) { update_form(formToken:$t, input:$i) { title description } }",
                    {"t": TOKEN, "i": {"title": "Manual stock update", "description": DESC}}, note="WorkForm title + description")
    print(r.get("errors") or r["data"])
    wanted = {
        "product": dict(title="Product", visible=True, required=True),
        "movement_type": dict(title="Movement type", visible=True, required=True),
        "qty": dict(title="Quantity", visible=True, required=True, show_if_rules=show_if([MANUAL_IN, MANUAL_OUT])),
        "counted_qty": dict(title="Counted quantity", visible=True, required=True, show_if_rules=show_if([COUNT])),
        "reason": dict(title="Reason", visible=True, required=True, show_if_rules=show_if([MANUAL_IN, MANUAL_OUT])),
        "note": dict(title="Note", visible=True, required=False),
    }
    for qid in types:
        if qid == "page_block__classic_default":
            continue
        q = dict(wanted.get(qid, dict(visible=False, required=False)), type=types[qid])
        upd(qid, q, "form question %s" % qid)
    # Movement type: offer only Manual in / Manual out / Stock count
    mt = next(q for q in form()["questions"] if q["id"] == "movement_type")
    opts = [{"label": o["label"], "visible": o["value"] in (MANUAL_IN, MANUAL_OUT, COUNT)} for o in mt["options"]]
    upd("movement_type", {"type": "SingleSelect", "options": opts}, "Movement type: only Manual in/out, Stock count")
    # Status hidden, default Pending
    upd("status", {"type": "SingleSelect", "visible": False, "settings": {"default_answer": "0"}},
        "Status hidden, default Pending")
    out = form()
    print(out["title"], "|", out["description"])
    for q in out["questions"]:
        if q["visible"]:
            print("  ", q["id"], repr(q["title"]), "req", q["required"], q["show_if_rules"]["rules"],
                  [(o["label"], o["visible"]) for o in (q["options"] or [])])
    print("hidden:", [q["id"] for q in out["questions"] if not q["visible"]])
