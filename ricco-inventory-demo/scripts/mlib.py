"""Shared helpers for the build scripts.

- gql(): read-only queries.
- mutate(): writes. Refuses any target outside the write scope recorded in
  data/id-map.json (demo folder + approved test folder) and refuses Sam's boards.
  Every write is appended to BUILD-LOG.md and logs/write-log.jsonl.
- Stops after 3 consecutive API errors (CLAUDE.md STOP rule).

Auth: MONDAY_API_TOKEN if set, otherwise the environment's egress proxy injects
the credential for api.monday.com. The token is never printed or logged.
"""
import datetime
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = "https://api.monday.com/v2"
API_VERSION = os.environ.get("MONDAY_API_VERSION", "2026-10")
ID_MAP = os.path.join(ROOT, "data", "id-map.json")
COLUMN_MAP = os.path.join(ROOT, "data", "column-map.json")
BUILD_LOG = os.path.join(ROOT, "BUILD-LOG.md")
WRITE_LOG = os.path.join(ROOT, "logs", "write-log.jsonl")

WORKSPACE_ID = "15462830"
EXPECTED_USER = "103186497"
EXPECTED_ACCOUNT = "34799434"

# Sam's boards: never a mutation target. Indirect writes (two-way connects,
# mirrors) are only allowed through mutate(..., allow_sam_board=True) after Gate 2.
SAM_BOARDS = {
    "18412939430", "18412939439", "18433554480", "18433554544",
    "18412939838", "18412939852", "18412939318", "18414401596",
    "18427258253", "18427258255", "18427258261", "18427258257",
    "18427258254", "18427258252", "18427258269", "18427258274", "18427258278",
}

_consecutive_errors = 0


class StopBuild(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _post(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}})
    cmd = ["curl", "-sS", API_URL, "-H", "Content-Type: application/json",
           "-H", "API-Version: " + API_VERSION, "--data-binary", "@-"]
    token = os.environ.get("MONDAY_API_TOKEN")
    if token:
        cmd[4:4] = ["-H", "Authorization: " + token]
    out = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        msg = out.stderr
        if token:
            msg = msg.replace(token, "***")
        return {"errors": [{"message": "curl failed: " + msg.strip()}]}
    try:
        return json.loads(out.stdout)
    except ValueError:
        return {"errors": [{"message": "non-JSON response: " + out.stdout[:300]}]}


def _track(resp):
    global _consecutive_errors
    if resp.get("errors") or resp.get("error_message") or resp.get("error_code"):
        _consecutive_errors += 1
        if _consecutive_errors > 3:
            raise StopBuild("more than 3 consecutive API errors; stopping")
    else:
        _consecutive_errors = 0


def gql(query, variables=None):
    if query.lstrip().startswith("mutation"):
        raise StopBuild("gql() is read-only; use mutate()")
    resp = _post(query, variables)
    _track(resp)
    return resp


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def id_map():
    return load_json(ID_MAP, {})


def allowed_targets():
    m = id_map()
    ids = set()
    for scope in ("folder", "test_folder"):
        if m.get(scope):
            ids.add(str(m[scope]["id"]))
    for scope in ("boards", "test_boards", "dashboards"):
        for v in (m.get(scope) or {}).values():
            ids.add(str(v["id"]))
    return ids


def check_identity():
    r = gql("{ me { id account { id } } }")
    me = r["data"]["me"]
    if me["id"] != EXPECTED_USER or me["account"]["id"] != EXPECTED_ACCOUNT:
        raise StopBuild("identity mismatch: user %s account %s" % (me["id"], me["account"]["id"]))
    return me


def _log(phase, op, target, query, variables, resp, note):
    os.makedirs(os.path.dirname(WRITE_LOG), exist_ok=True)
    ok = not resp.get("errors")
    entry = {"ts": _now(), "phase": phase, "op": op, "target": target, "note": note,
             "query": " ".join(query.split()), "variables": variables,
             "result": resp.get("data") if ok else {"errors": resp.get("errors")}}
    with open(WRITE_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if ok:
        res = json.dumps(resp.get("data"), ensure_ascii=False)
        res = res if len(res) <= 160 else res[:157] + "..."
    else:
        res = "ERROR: " + "; ".join(e.get("message", "")[:150] for e in resp["errors"])
    line = "| %s | %s | `%s` | %s | %s | %s |\n" % (
        entry["ts"], phase, op, target, (note or "").replace("|", "/"), res.replace("|", "/"))
    with open(BUILD_LOG, "a") as f:
        f.write(line)


def mutate(phase, op, target, query, variables=None, note="", allow_new_folder=False,
           allow_sam_board=False):
    """Run one mutation against `target` (board/folder/workspace id)."""
    target = str(target)
    if target in SAM_BOARDS and not allow_sam_board:
        raise StopBuild("refused: %s targets Sam's board %s" % (op, target))
    if target == WORKSPACE_ID:
        if not allow_new_folder:
            raise StopBuild("refused: %s directly on the workspace" % op)
    elif target not in allowed_targets() and not allow_sam_board:
        raise StopBuild("refused: %s target %s is outside the write scope" % (op, target))
    if not query.lstrip().startswith("mutation"):
        raise StopBuild("mutate() needs a mutation")
    resp = _post(query, variables)
    _log(phase, op, target, query, variables, resp, note)
    _track(resp)
    return resp
