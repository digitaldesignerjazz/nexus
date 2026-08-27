#!/usr/bin/env python3
"""Nexus Control Plane — lightweight HTTP orchestrator for the Hannover node."""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

STARTED = time.time()
NODE_NAME = os.environ.get("NEXUS_NODE_NAME", "hannover-primary")
BIND = os.environ.get("NEXUS_BIND", "127.0.0.1")
PORT = int(os.environ.get("NEXUS_PORT", "8787"))
OWNER = os.environ.get("NEXUS_OWNER", "Sir Sven Normen Eßlinger")
SITE = os.environ.get("NEXUS_SITE", "Hannover")
ENV = os.environ.get("NEXUS_ENV", "development")
HERE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NEXUS_DATA_DIR", HERE / "data")).resolve()
LOG_DIR = Path(os.environ.get("NEXUS_LOG_DIR", HERE / "logs")).resolve()
SWARM_SIZE = int(os.environ.get("NEXUS_SWARM_SIZE", "5"))
MESH_PEERS = int(os.environ.get("NEXUS_MESH_PEERS", "12"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "nexus-control.log"
STATE_FILE = DATA_DIR / "state.json"
LOCK = threading.Lock()

STATE: dict[str, Any] = {
    "node": NODE_NAME,
    "owner": OWNER,
    "site": SITE,
    "env": ENV,
    "status": "INITIALIZING",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "layers": {
        "control": {"status": "INITIALIZING"},
        "mesh": {"status": "STANDBY", "peers": 0},
        "blockchain": {"status": "STANDBY", "height": 0},
        "swarm": {"status": "STANDBY", "agents": 0},
        "prototypes": {"status": "STANDBY"},
    },
    "events": [],
    "metrics": {"events": 0, "requests": 0},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(level: str, message: str) -> None:
    line = f"{utc_now()} [{level}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def persist() -> None:
    payload = dict(STATE)
    payload["events"] = STATE["events"][-50:]
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE_FILE)
    except OSError as exc:
        log("WARN", f"state persist skipped: {exc}")


def emit(event_type: str, payload: dict[str, Any] | None = None) -> None:
    event = {"ts": utc_now(), "type": event_type, "payload": payload or {}}
    STATE["events"].append(event)
    STATE["events"] = STATE["events"][-200:]
    STATE["metrics"]["events"] += 1
    log("EVENT", f"{event_type} {payload or {}}")
    if event_type in {"NEXUS_ONLINE", "MESH_EXPAND", "SWARM_EXPAND", "NEXUS_STOP"}:
        persist()


def boot() -> None:
    log("INFO", f"Boot {NODE_NAME} · {SITE} · {OWNER}")
    sequence = [
        ("control", "OPERATIONAL", {}),
        ("mesh", "STANDBY", {"peers": 0, "note": "Yggdrasil host-side"}),
        ("blockchain", "STANDBY", {"height": 0, "note": "QCoin/XCoin placeholder"}),
        ("swarm", "STANDBY", {"agents": 0}),
        ("prototypes", "STANDBY", {"note": "Soilnova / Vista Nova / Lumia"}),
    ]
    for layer, status, extra in sequence:
        STATE["layers"][layer]["status"] = status
        STATE["layers"][layer].update(extra)
        emit("LAYER_READY", {"layer": layer, "status": status})
    STATE["status"] = "OPERATIONAL"
    emit("NEXUS_ONLINE", {"bind": f"{BIND}:{PORT}"})


def snapshot() -> dict[str, Any]:
    return {
        **STATE,
        "uptime_s": int(time.time() - STARTED),
        "listen": f"{BIND}:{PORT}",
        "events": STATE["events"][-20:],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "NexusControl/0.1"

    def _json(self, code: int, body: Any) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt: str, *args: Any) -> None:
        log("HTTP", fmt % args)

    def do_GET(self) -> None:  # noqa: N802
        with LOCK:
            STATE["metrics"]["requests"] += 1
            path = urlparse(self.path).path
            if path in ("/", "/health"):
                self._json(200, {"status": "ok", "node": NODE_NAME, "plane": STATE["status"]})
            elif path == "/status":
                self._json(200, snapshot())
            elif path == "/layers":
                self._json(200, STATE["layers"])
            else:
                self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        with LOCK:
            STATE["metrics"]["requests"] += 1
            path = urlparse(self.path).path
            if path == "/mesh/start":
                STATE["layers"]["mesh"].update({"status": "OPERATIONAL", "peers": MESH_PEERS})
                emit("MESH_EXPAND", {"peers": MESH_PEERS})
                self._json(200, STATE["layers"]["mesh"])
            elif path == "/swarm/spawn":
                STATE["layers"]["swarm"].update({"status": "OPERATIONAL", "agents": SWARM_SIZE})
                emit("SWARM_EXPAND", {"agents": SWARM_SIZE})
                self._json(200, STATE["layers"]["swarm"])
            elif path == "/stop":
                STATE["status"] = "STOPPING"
                emit("NEXUS_STOP", {})
                self._json(200, {"status": "stopping"})
                threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
            else:
                self._json(404, {"error": "not_found", "path": path})


def main() -> None:
    boot()
    httpd = ThreadingHTTPServer((BIND, PORT), Handler)
    log("INFO", f"Control Plane listening on http://{BIND}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        emit("NEXUS_STOP", {"reason": "keyboard"})
        httpd.server_close()


if __name__ == "__main__":
    main()
