"""monday.com GraphQL client with retry/backoff, read-only mode and ZZ-TEST- prefix guard."""
import json
import os
import re
import time
from pathlib import Path

import requests

API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-10"
HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
LEDGER_PATH = HERE / "results" / "created_items.json"  # every item we create, persisted across runs

PREFIX = "ZZ-TEST-"
ALLOWED_PRODUCTS = {"ZZ-TEST-A", "ZZ-TEST-B"}
MAX_PRODUCT_CREATES = 2
MUTATION_RE = re.compile(r"^\s*mutation\b", re.I)


class GuardError(RuntimeError):
    """Raised when a mutation would touch non-test data. Never catch this."""


def load_config():
    return json.loads(CONFIG_PATH.read_text())


class Monday:
    def __init__(self, token=None, read_only=True, max_retries=6):
        self.token = token or os.environ.get("MONDAY_API_TOKEN")
        if not self.token:
            raise SystemExit("MONDAY_API_TOKEN is not set")
        self.read_only = read_only
        self.max_retries = max_retries
        self.config = load_config()
        self.s = requests.Session()
        self.s.headers.update({"Authorization": self.token, "Content-Type": "application/json",
                               "API-Version": API_VERSION})

    # ---------------- transport ----------------
    def _post(self, query, variables=None):
        delay = 2
        for attempt in range(self.max_retries):
            r = self.s.post(API_URL, json={"query": query, "variables": variables or {}}, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                wait = int(r.headers.get("Retry-After", delay))
                time.sleep(wait); delay = min(delay * 2, 60); continue
            body = r.json()
            errs = body.get("errors") or []
            codes = {(e.get("extensions") or {}).get("code") for e in errs} | {body.get("error_code")}
            if codes & {"ComplexityException", "COMPLEXITY_BUDGET_EXHAUSTED", "RATE_LIMIT_EXCEEDED",
                        "maxConcurrencyExceeded", "IP_RATE_LIMIT_EXCEEDED"}:
                retry = max([(e.get("extensions") or {}).get("retry_in_seconds", 0) for e in errs] + [delay])
                time.sleep(retry); delay = min(delay * 2, 60); continue
            if errs or body.get("error_message"):
                raise RuntimeError(f"monday API error: {json.dumps(errs or body)[:2000]}")
            return body["data"]
        raise RuntimeError("monday API: retries exhausted")

    def query(self, q, variables=None):
        if MUTATION_RE.match(q):
            raise GuardError("query() refuses mutations; use a guarded mutation helper")
        return self._post(q, variables)

    # ---------------- guard ----------------
    def _check_writable(self):
        if self.read_only:
            raise GuardError("Client is in READ-ONLY mode (Phase 0). Mutation refused.")
        if not self.config.get("confirmed_by_user"):
            raise GuardError("config.json not confirmed_by_user. Mutation refused.")

    def _ledger(self):
        return json.loads(LEDGER_PATH.read_text()) if LEDGER_PATH.exists() else []

    def _record(self, entry):
        led = self._ledger(); led.append(entry)
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        LEDGER_PATH.write_text(json.dumps(led, indent=2))

    def guard_existing_item(self, item_id):
        """Refuse to touch any existing item whose name lacks the prefix."""
        d = self.query("query($id:[ID!]){items(ids:$id){id name}}", {"id": [str(item_id)]})
        items = d["items"]
        if not items:
            raise GuardError(f"item {item_id} not found / not readable; refusing")
        name = items[0]["name"]
        if not name.startswith(PREFIX):
            raise GuardError(f"GUARD TRIPPED: item {item_id} '{name}' has no {PREFIX} prefix")
        return name

    def guard_new_item(self, board_id, name):
        if not name.startswith(PREFIX):
            raise GuardError(f"GUARD TRIPPED: new item name '{name}' has no {PREFIX} prefix")
        if str(board_id) == str(self.config["boards"]["Products"]):
            if name not in ALLOWED_PRODUCTS:
                raise GuardError(f"GUARD TRIPPED: product '{name}' not in {ALLOWED_PRODUCTS}")
            made = [e for e in self._ledger() if e.get("board") == "Products"]
            if len(made) >= MAX_PRODUCT_CREATES or any(e["name"] == name for e in made):
                raise GuardError(f"GUARD TRIPPED: Products creation cap reached / duplicate ({made})")

    # ---------------- guarded mutations ----------------
    def create_item(self, board_id, name, column_values=None, group_id=None, create_labels=False):
        self._check_writable(); self.guard_new_item(board_id, name)
        q = ("mutation($b:ID!,$n:String!,$cv:JSON,$g:String,$cl:Boolean){create_item(board_id:$b,"
             "item_name:$n,column_values:$cv,group_id:$g,create_labels_if_missing:$cl){id name}}")
        d = self._post(q, {"b": str(board_id), "n": name, "g": group_id, "cl": create_labels,
                           "cv": json.dumps(column_values or {})})
        board_label = next((k for k, v in self.config["boards"].items() if v == str(board_id)), str(board_id))
        self._record({"board": board_label, "board_id": str(board_id), "id": d["create_item"]["id"],
                      "name": name, "at": time.time()})
        return d["create_item"]

    def create_subitem(self, parent_id, name, column_values=None):
        self._check_writable(); self.guard_existing_item(parent_id)
        if not name.startswith(PREFIX):
            raise GuardError(f"GUARD TRIPPED: subitem name '{name}' has no {PREFIX} prefix")
        q = ("mutation($p:ID!,$n:String!,$cv:JSON){create_subitem(parent_item_id:$p,item_name:$n,"
             "column_values:$cv){id name board{id}}}")
        d = self._post(q, {"p": str(parent_id), "n": name, "cv": json.dumps(column_values or {})})
        self._record({"board": "subitem", "parent": str(parent_id), "id": d["create_subitem"]["id"],
                      "name": name, "at": time.time()})
        return d["create_subitem"]

    def change_columns(self, board_id, item_id, column_values):
        self._check_writable(); self.guard_existing_item(item_id)
        q = ("mutation($b:ID!,$i:ID!,$cv:JSON!){change_multiple_column_values(board_id:$b,item_id:$i,"
             "column_values:$cv){id}}")
        return self._post(q, {"b": str(board_id), "i": str(item_id), "cv": json.dumps(column_values)})

    def archive_item(self, item_id):
        self._check_writable(); self.guard_existing_item(item_id)
        return self._post("mutation($i:ID!){archive_item(item_id:$i){id}}", {"i": str(item_id)})

    # No delete helper by design.

    # ---------------- helpers ----------------
    def columns(self, board_id):
        d = self.query("query($b:[ID!]){boards(ids:$b){id name columns{id title type settings_str}}}",
                       {"b": [str(board_id)]})
        return d["boards"][0]["columns"]

    def col_map(self, board_id):
        """title -> {id, type}. Never hardcode column IDs."""
        return {c["title"]: {"id": c["id"], "type": c["type"]} for c in self.columns(board_id)}
