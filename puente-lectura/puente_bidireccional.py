#!/usr/bin/env python3
"""Puente bidireccional mínimo entre agentes.

Un único relay recibe anuncios y permite que cualquier agente los recoja.
Solo usa la biblioteca estándar. No ejecuta instrucciones recibidas.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DB_PATH = os.environ.get("PUENTE_DB", "puente_agentes.sqlite3")
TOKEN = os.environ.get("PUENTE_TOKEN", "")
MAX_BODY = 256_000
MAX_EVENTS = 200


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_db():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        sender TEXT NOT NULL,
        kind TEXT NOT NULL,
        created_at TEXT NOT NULL,
        payload TEXT NOT NULL
    )""")
    db.commit()
    return db


class RelayHandler(BaseHTTPRequestHandler):
    server_version = "AgentRelay/1.0"

    def log_message(self, fmt, *args):
        # No registrar tokens ni cuerpos potencialmente sensibles.
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

    def send_json(self, status, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN
        return bool(TOKEN) and secrets.compare_digest(supplied, expected)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            return self.send_json(200, {"ok": True, "service": "agent-relay"})
        if parsed.path != "/v1/events":
            return self.send_json(404, {"error": "not_found"})
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})

        q = urllib.parse.parse_qs(parsed.query)
        try:
            after = max(0, int(q.get("after", ["0"])[0]))
            wait = min(25, max(0, int(q.get("wait", ["0"])[0])))
            limit = min(MAX_EVENTS, max(1, int(q.get("limit", ["50"])[0])))
        except ValueError:
            return self.send_json(400, {"error": "invalid_query"})
        agent = self.headers.get("X-Agent-ID", "unknown")[:100]
        deadline = time.monotonic() + wait

        while True:
            with connect_db() as db:
                latest = db.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
                rows = db.execute(
                    "SELECT seq,event_id,sender,kind,created_at,payload "
                    "FROM events WHERE seq>? AND sender<>? ORDER BY seq LIMIT ?",
                    (after, agent, limit),
                ).fetchall()
            if rows or time.monotonic() >= deadline:
                events = []
                for row in rows:
                    events.append({
                        "seq": row["seq"], "event_id": row["event_id"],
                        "sender": row["sender"], "kind": row["kind"],
                        "created_at": row["created_at"],
                        "payload": json.loads(row["payload"]),
                    })
                return self.send_json(200, {
                    "events": events,
                    "next_cursor": max(latest, after),
                    "server_time": utc_now(),
                })
            time.sleep(1)

    def do_POST(self):
        if self.path != "/v1/events":
            return self.send_json(404, {"error": "not_found"})
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > MAX_BODY:
                return self.send_json(413, {"error": "body_size_invalid"})
            body = json.loads(self.rfile.read(length))
            sender = str(body["sender"]).strip()[:100]
            kind = str(body["kind"]).strip()[:100]
            payload = body.get("payload", {})
            event_id = str(body.get("event_id") or uuid.uuid4())
            if not sender or not kind or not isinstance(payload, (dict, list, str, int, float, bool, type(None))):
                return self.send_json(400, {"error": "invalid_event"})
            payload_text = json.dumps(payload, ensure_ascii=False)
            with connect_db() as db:
                db.execute(
                    "INSERT OR IGNORE INTO events(event_id,sender,kind,created_at,payload) VALUES(?,?,?,?,?)",
                    (event_id, sender, kind, utc_now(), payload_text),
                )
                row = db.execute("SELECT seq FROM events WHERE event_id=?", (event_id,)).fetchone()
            return self.send_json(201, {"accepted": True, "event_id": event_id, "seq": row["seq"]})
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return self.send_json(400, {"error": "invalid_json_or_fields"})
        except Exception:
            return self.send_json(500, {"error": "relay_error"})


def request_json(url, token, agent, data=None, timeout=35):
    raw = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {"Authorization": "Bearer " + token, "X-Agent-ID": agent}
    if raw is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def client_config(args):
    base = (args.url or os.environ.get("PUENTE_URL", "")).rstrip("/")
    token = args.token or os.environ.get("PUENTE_TOKEN", "")
    if not base or not token:
        raise SystemExit("Configura PUENTE_URL y PUENTE_TOKEN, o usa --url y --token.")
    return base, token


def cmd_serve(args):
    if not TOKEN:
        raise SystemExit("Falta PUENTE_TOKEN. No inicies el relay sin autenticación.")
    print(f"Relay escuchando en {args.host}:{args.port}; DB={DB_PATH}")
    ThreadingHTTPServer((args.host, args.port), RelayHandler).serve_forever()


def cmd_announce(args):
    base, token = client_config(args)
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--payload no es JSON válido: {exc}")
    event = {
        "event_id": str(uuid.uuid4()),
        "sender": args.agent,
        "kind": args.kind,
        "payload": payload,
    }
    result = request_json(base + "/v1/events", token, args.agent, event)
    print(json.dumps(result, ensure_ascii=False))


def cmd_listen(args):
    base, token = client_config(args)
    state = Path(args.state)
    try:
        cursor = int(state.read_text(encoding="utf-8").strip()) if state.exists() else 0
    except ValueError:
        cursor = 0
    while True:
        query = urllib.parse.urlencode({"after": cursor, "wait": args.wait, "limit": args.limit})
        result = request_json(base + "/v1/events?" + query, token, args.agent, timeout=args.wait + 10)
        for event in result["events"]:
            print(json.dumps(event, ensure_ascii=False), flush=True)
        cursor = max(cursor, int(result["next_cursor"]))
        state.write_text(str(cursor), encoding="utf-8")
        if args.once:
            break


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=cmd_serve)
    for name, func in (("announce", cmd_announce), ("listen", cmd_listen)):
        p = sub.add_parser(name)
        p.add_argument("--url")
        p.add_argument("--token")
        p.add_argument("--agent", required=True)
        if name == "announce":
            p.add_argument("--kind", required=True)
            p.add_argument("--payload", default="{}")
        else:
            p.add_argument("--state", default=".agent-relay-cursor")
            p.add_argument("--wait", type=int, default=20)
            p.add_argument("--limit", type=int, default=50)
            p.add_argument("--once", action="store_true")
        p.set_defaults(func=func)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
