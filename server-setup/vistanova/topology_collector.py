#!/usr/bin/env python3
"""VistaNova Prototype 1.0 — topology collector (stage 1, DRAFT).

Read-only "eye" of the Hannover swarm. One collection pass:
  - yggdrasilctl -json getSelf / getPeers   (own node + links)
  - SoilNova status json                     (prototype status)
  - status/xara_presence.json                (prototype presence)
  - control plane GET /status                (host + layer status)
and writes status/topology.json atomically (tmp file + rename).

Guardrails: it only reads. No routing, no peer changes, no key generation,
no production traffic, no chain account. It never starts or stops anything.

Usage:
  topology_collector.py --once            # single pass (default)
  topology_collector.py --loop 30         # repeat every 30 s (runtime mode,
                                          # meant to be driven by prototype_bot.py later)
See docs/vistanova-prototype-1.0.md and configs/vistanova-prototype-1.0.yaml.
"""
from __future__ import annotations
import argparse, json, os, signal, subprocess, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OBSERVER = "vistanova-hannover-01"
HOST_ID = os.environ.get("VISTANOVA_HOST_ID", "hannover-primary")
STALE_AFTER = int(os.environ.get("VISTANOVA_STALE_AFTER_SECS", "90"))
TIMEOUT = 3.0
SOILNOVA_JSON = Path(os.environ.get("VISTANOVA_SOILNOVA_JSON",
                                    "/workspace/lumina-state/prototypes/soilnova.status.json"))
XARA_JSON = Path(os.environ.get("VISTANOVA_XARA_JSON", str(REPO / "status" / "xara_presence.json")))
CTRL_URL = os.environ.get("VISTANOVA_CTRL_URL", "http://127.0.0.1:8787/status")
YGG_ENDPOINT = os.environ.get("VISTANOVA_YGG_ENDPOINT", "")  # empty = yggdrasilctl default socket
running = True


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z") if dt else None


def parse_ts(s) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except ValueError:
        return None


def ygg(cmd: str) -> dict:
    args = ["yggdrasilctl", "-json"]
    if YGG_ENDPOINT:
        args += ["-endpoint", YGG_ENDPOINT]
    out = subprocess.run(args + [cmd], capture_output=True, text=True, timeout=TIMEOUT, check=True)
    try:
        return json.loads(out.stdout)
    except ValueError:
        raise ValueError(f"yggdrasilctl {cmd}: {(out.stdout or out.stderr).strip()[:160]!r}") from None


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:  # GET only
        return json.loads(r.read().decode("utf-8"))


def proc_interval(pid) -> int | None:
    """--heartbeat-interval of a live prototype_bot.py process (read from /proc), if any."""
    try:
        args = Path(f"/proc/{int(pid)}/cmdline").read_bytes().split(b"\0")
    except (OSError, ValueError, TypeError):
        return None
    for i, a in enumerate(args):
        if a == b"--heartbeat-interval" and i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                return None
    return 30 if any(b"prototype_bot.py" in a for a in args) else None


def source_state(t: datetime, ts: datetime | None, limit: int) -> tuple[str, float | None]:
    if ts is None:
        return "stale", None
    age = round((t - ts).total_seconds(), 1)
    return ("ok" if age <= limit else "stale"), age


def collect() -> dict:
    t = now()
    sources: dict[str, dict] = {}
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    # --- yggdrasil: self + peers -------------------------------------------------
    self_info = {"id": HOST_ID}
    try:
        s = ygg("getSelf")
        self_info.update(ygg_ipv6=s.get("address"), public_key=s.get("key"), subnet=s.get("subnet"),
                         routing_entries=s.get("routing_entries"), build_version=s.get("build_version"))
        p = ygg("getPeers").get("peers", [])
        sources["yggdrasil"] = {"state": "ok", "fetched_at": iso(t), "peers": len(p),
                                "peers_up": sum(1 for x in p if x.get("up"))}
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        p = []
        sources["yggdrasil"] = {"state": "unavailable", "fetched_at": iso(t), "error": str(e)[:200]}
    nodes[HOST_ID] = {"id": HOST_ID, "kind": "host", "ygg_ipv6": self_info.get("ygg_ipv6"),
                      "public_key": self_info.get("public_key"), "source": "yggdrasil",
                      "status": "unknown", "last_seen": iso(t)}
    for peer in p:
        addr = peer.get("address")
        remote = peer.get("remote") or ""
        local = "[fe80:" in remote or remote.startswith("unix:")
        if addr and addr not in nodes:
            nodes[addr] = {"id": addr, "kind": "local-ygg-peer" if local else "ygg-peer",
                           "ygg_ipv6": addr, "public_key": peer.get("key"), "source": "yggdrasil",
                           "status": "up" if peer.get("up") else "down", "last_seen": iso(t)}
        elif addr and peer.get("up"):
            nodes[addr]["status"] = "up"
        lat = peer.get("latency")
        links.append({
            "from": HOST_ID, "to": addr, "uri": remote,
            "direction": "in" if peer.get("inbound") else "out",
            "state": "up" if peer.get("up") else "down",
            "latency_ms": round(lat / 1e6, 2) if isinstance(lat, (int, float)) else None,
            "uptime_s": round(float(peer.get("uptime") or 0), 1),
            "rx_bytes": peer.get("bytes_recvd"), "tx_bytes": peer.get("bytes_sent"),
            "cost": peer.get("cost"), "kind": "ygg-peering",
        })

    # --- control plane -----------------------------------------------------------
    try:
        c = http_json(CTRL_URL)
        layers = {k: (v or {}).get("status") for k, v in (c.get("layers") or {}).items()}
        sources["control_plane"] = {"state": "ok", "fetched_at": iso(t), "node": c.get("node"),
                                    "status": c.get("status"), "layers": layers}
        if c.get("node") in (None, HOST_ID):
            nodes[HOST_ID]["status"] = c.get("status") or "unknown"
    except (OSError, urllib.error.URLError, ValueError) as e:
        sources["control_plane"] = {"state": "unavailable", "fetched_at": iso(t), "error": str(e)[:200]}

    # --- SoilNova ----------------------------------------------------------------
    try:
        d = read_json(SOILNOVA_JSON)
        interval = proc_interval(d.get("pid"))
        limit = max(STALE_AFTER, 3 * interval) if interval else STALE_AFTER
        hb = parse_ts(d.get("last_heartbeat"))
        state, age = source_state(t, hb, limit)
        sources["soilnova"] = {"state": state, "path": str(SOILNOVA_JSON), "age_s": age,
                               "stale_after_s": limit}
        nodes["soilnova"] = {"id": "soilnova", "kind": "prototype", "source": "soilnova",
                             "status": d.get("status") if state == "ok" else f"{d.get('status')} (stale)",
                             "pid": d.get("pid"), "bind": d.get("bind"), "last_seen": iso(hb)}
        links.append({"from": "soilnova", "to": HOST_ID, "kind": "hosted-on", "state": state})
    except (OSError, ValueError) as e:
        sources["soilnova"] = {"state": "unavailable", "path": str(SOILNOVA_JSON), "error": str(e)[:200]}

    # --- Xara --------------------------------------------------------------------
    try:
        d = read_json(XARA_JSON)
        started = parse_ts(d.get("started_at"))
        state, age = source_state(t, started, STALE_AFTER)
        sources["xara"] = {"state": state, "path": str(XARA_JSON), "age_s": age,
                           "stale_after_s": STALE_AFTER,
                           "note": "presence is a snapshot written by 10-start-xara.sh"}
        nid = d.get("node_id") or "xara"
        nodes[nid] = {"id": nid, "kind": "prototype", "source": "xara",
                      "status": d.get("status") if state == "ok" else f"{d.get('status')} (stale)",
                      "last_seen": iso(started)}
        links.append({"from": nid, "to": HOST_ID, "kind": "hosted-on", "state": state})
    except (OSError, ValueError) as e:
        sources["xara"] = {"state": "unavailable", "path": str(XARA_JSON), "error": str(e)[:200]}

    nodes[OBSERVER] = {"id": OBSERVER, "kind": "observer", "source": "self", "status": "observing",
                       "last_seen": iso(t)}
    return {
        "generated_at": iso(t),
        "observer": OBSERVER,
        "draft": True,
        "self": self_info,
        "summary": {
            "nodes": len(nodes),
            "links": len(links),
            "ygg_links_up": sum(1 for l in links if l.get("kind") == "ygg-peering" and l["state"] == "up"),
            "sources_ok": sorted(k for k, v in sources.items() if v["state"] == "ok"),
            "sources_not_ok": sorted(k for k, v in sources.items() if v["state"] != "ok"),
        },
        "nodes": list(nodes.values()),
        "links": links,
        "sources": sources,
    }


def write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def stop(*_):
    global running
    running = False


def main() -> None:
    ap = argparse.ArgumentParser(description="VistaNova topology collector (read-only, stage 1)")
    ap.add_argument("--output", default=str(REPO / "status" / "topology.json"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="single pass (default)")
    g.add_argument("--loop", type=int, default=0, metavar="SECS", help="repeat every SECS seconds")
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    out = Path(a.output)
    while True:
        topo = collect()
        write_atomic(out, topo)
        s = topo["summary"]
        print(f"{topo['generated_at']} nodes={s['nodes']} links={s['links']} "
              f"ygg_up={s['ygg_links_up']} not_ok={s['sources_not_ok']} -> {out}", flush=True)
        if a.loop <= 0:
            break
        deadline = time.monotonic() + a.loop
        while running and time.monotonic() < deadline:
            time.sleep(1)
        if not running:
            break


if __name__ == "__main__":
    main()
