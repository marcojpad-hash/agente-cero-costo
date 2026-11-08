import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

DB_PATH = os.getenv("ROUTER_DB", "/data/router.sqlite3")
INGEST_TOKEN = os.getenv("ROUTER_INGEST_TOKEN", "")
AGENTS = json.loads(os.getenv("AGENT_WEBHOOKS_JSON", "{}"))
ALLOWED_REPOSITORIES = set(filter(None, os.getenv("ALLOWED_REPOSITORIES", "").split(",")))
app = FastAPI(title="Shared Agent Router", version="1.0.0")


def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("""
      CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        source TEXT NOT NULL,
        repository TEXT,
        payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'RECEIVED'
      )
    """)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS deliveries (
        event_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        updated_at TEXT NOT NULL,
        PRIMARY KEY(event_id, agent_id)
      )
    """)
    conn.commit()
    return conn


def authorized(auth: str | None):
    if not INGEST_TOKEN:
        raise HTTPException(503, "Router ingest token is not configured")
    supplied = (auth or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied, INGEST_TOKEN):
        raise HTTPException(401, "Unauthorized")


def persist_event(payload: dict[str, Any], source: str):
    event_id = str(payload.get("event_id") or uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    repository = payload.get("repository")
    if repository and ALLOWED_REPOSITORIES and repository not in ALLOWED_REPOSITORIES:
        raise HTTPException(403, "Repository is not allowlisted")
    envelope = {
        "schema": "agent-bus.event.v1",
        "event_id": event_id,
        "created_at": now,
        "source": source,
        "repository": repository,
        "payload": payload,
    }
    raw = json.dumps(envelope, ensure_ascii=False)
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO events(event_id,created_at,source,repository,payload) VALUES(?,?,?,?,?)",
            (event_id, now, source, repository, raw),
        )
        for agent_id in AGENTS:
            conn.execute(
                "INSERT OR IGNORE INTO deliveries(event_id,agent_id,updated_at) VALUES(?,?,?)",
                (event_id, agent_id, now),
            )
    return envelope


@app.get("/health")
def health():
    return {"ok": True, "service": "shared-agent-router", "agents_configured": sorted(AGENTS)}


@app.post("/v1/events/github")
async def github_event(request: Request, authorization: str | None = Header(default=None)):
    authorized(authorization)
    payload = await request.json()
    event = persist_event(payload, "github")
    return JSONResponse({"accepted": True, "event_id": event["event_id"]}, status_code=202)


@app.post("/v1/events/conversation")
async def conversation_event(request: Request, authorization: str | None = Header(default=None)):
    authorized(authorization)
    payload = await request.json()
    if not payload.get("content") and not payload.get("artifact_refs"):
        raise HTTPException(400, "content or artifact_refs is required")
    payload.setdefault("event_id", str(uuid.uuid4()))
    payload.setdefault("event_type", "conversation_turn")
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    event = persist_event(payload, "conversation")
    return JSONResponse({"accepted": True, "event_id": event["event_id"]}, status_code=202)


@app.post("/v1/events/whatsapp")
async def whatsapp_event(request: Request, authorization: str | None = Header(default=None)):
    authorized(authorization)
    payload = await request.json()
    if payload.get("from_me") or payload.get("is_status"):
        return {"accepted": False, "ignored": True}
    event = persist_event(payload, "whatsapp")
    return JSONResponse({"accepted": True, "event_id": event["event_id"]}, status_code=202)


@app.get("/v1/events/pending")
def pending_events(agent_id: str, limit: int = 50, authorization: str | None = Header(default=None)):
    authorized(authorization)
    if agent_id not in AGENTS:
        raise HTTPException(404, "Unknown agent")
    limit = max(1, min(limit, 200))
    with db() as conn:
        rows = conn.execute("""
          SELECT e.event_id,e.created_at,e.source,e.repository,e.payload,d.status
          FROM events e JOIN deliveries d ON d.event_id=e.event_id
          WHERE d.agent_id=? AND d.status IN ('PENDING','RETRY')
          ORDER BY e.created_at LIMIT ?
        """, (agent_id, limit)).fetchall()
    return {"agent_id": agent_id, "events": [dict(r) for r in rows]}


@app.post("/v1/events/{event_id}/ack")
async def acknowledge(event_id: str, request: Request, authorization: str | None = Header(default=None)):
    authorized(authorization)
    body = await request.json()
    agent_id = body.get("agent_id")
    status = body.get("status", "RECEIVED")
    if agent_id not in AGENTS or status not in ("RECEIVED", "STARTED", "COMPLETED", "BLOCKED"):
        raise HTTPException(400, "Invalid agent_id or status")
    with db() as conn:
        cur = conn.execute(
            "UPDATE deliveries SET status=?,updated_at=?,last_error=? WHERE event_id=? AND agent_id=?",
            (status, datetime.now(timezone.utc).isoformat(), body.get("detail"), event_id, agent_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Delivery not found")
    return {"ok": True, "event_id": event_id, "agent_id": agent_id, "status": status}


@app.get("/v1/state")
def state(authorization: str | None = Header(default=None)):
    authorized(authorization)
    with db() as conn:
        events = conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
        deliveries = conn.execute(
            "SELECT agent_id,status,COUNT(*) AS n FROM deliveries GROUP BY agent_id,status"
        ).fetchall()
    return {"events": events, "deliveries": [dict(r) for r in deliveries], "agents": sorted(AGENTS)}
