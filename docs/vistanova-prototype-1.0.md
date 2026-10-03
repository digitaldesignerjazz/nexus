# VistaNova Prototype 1.0

Read-only vision and topology observer for the Hannover swarm ("the eye").

Status: **DRAFT** · Maturity: experimental · Node: `vistanova-hannover-01`

## Role

VistaNova is the **eye** of the Nexus mesh. Every 30 seconds it reads the
mesh state of `hannover-primary` and the status of the other prototypes and
builds one topology map. It adds **no routing authority** and changes
nothing. All real mesh work stays with Yggdrasil and Xen.

## Files

| Path | Purpose |
|---|---|
| `configs/vistanova-prototype-1.0.yaml` | Prototype definition |
| `server-setup/vistanova/topology_collector.py` | Stage 1 collector (draft, read-only) |
| `status/topology.json` | Runtime topology map (written every 30 s, git-ignored) |
| `/workspace/lumina-state/prototype_bot.py` | Shared prototype bot framework (runtime) |
| `/workspace/lumina-state/run-vista-nova-bot.sh` | Launcher (slug `vista-nova`, port 4252) |

## Sources (read-only, every 30 s)

| Source | What VistaNova takes from it |
|---|---|
| `yggdrasilctl -json getSelf` | Own node: IPv6, public key, routing table size |
| `yggdrasilctl -json getPeers` | Links: URI, direction, state, latency, uptime, RX/TX, cost |
| `prototypes/soilnova.status.json` | SoilNova node status and last heartbeat |
| `status/xara_presence.json` | Xara node status |
| `http://127.0.0.1:8787/status` | Control plane and layer status of hannover-primary |

A source that fails is marked `unavailable`; one whose heartbeat is older
than 90 s is marked `stale`. For a prototype bot with a longer
`--heartbeat-interval` (SoilNova runs with 3600 s) the limit is
3 × its interval, read from the bot's command line. Xara has no heartbeat,
so its presence snapshot is judged by `started_at`. VistaNova keeps running.

## Output: `status/topology.json`

```json
{
  "generated_at": "2026-10-03T13:15:00Z",
  "observer": "vistanova-hannover-01",
  "self": { "id": "hannover-primary", "ygg_ipv6": "200:47dd:...", "public_key": "dc11..." },
  "nodes": [
    { "id": "hannover-primary", "kind": "host", "status": "OPERATIONAL" },
    { "id": "220:f022:...", "kind": "ygg-peer", "status": "up" },
    { "id": "soilnova", "kind": "prototype", "status": "running", "last_seen": "..." },
    { "id": "xara-hannover-01", "kind": "prototype", "status": "STANDBY" }
  ],
  "links": [
    { "from": "hannover-primary", "to": "220:f022:...", "uri": "tls://ygg1.mk16.de:1338",
      "direction": "out", "state": "up", "latency_ms": 98.7, "uptime_s": 11445 }
  ],
  "sources": { "yggdrasil": "ok", "soilnova": "ok", "xara": "ok", "control_plane": "ok" }
}
```

The file is written atomically (temporary file, then rename).

## Runtime

One process through the shared `prototype_bot.py` framework, same as
SoilNova. This keeps it visible to `prototypes/prototype_supervisor.py`
(name `Vista Nova`, slug `vista-nova`) and to the prototype watchdog.
The stage 1 collector exists as a draft in
`server-setup/vistanova/topology_collector.py`. It is **not wired** into
`prototype_bot.py`, `start-stack.sh` or the watchdog yet. Today the
`vista-nova` bot is still only a soft presence with a heartbeat.

```bash
# one-shot (manual check)
python3 server-setup/vistanova/topology_collector.py --once
# runtime mode (later, driven by the prototype bot)
python3 server-setup/vistanova/topology_collector.py --loop 30
```

Overrides (environment): `VISTANOVA_CTRL_URL`, `VISTANOVA_SOILNOVA_JSON`,
`VISTANOVA_XARA_JSON`, `VISTANOVA_YGG_ENDPOINT`, `VISTANOVA_STALE_AFTER_SECS`.

## Stage 2 (planned, not in scope)

- **Web view:** read-only graph view of `status/topology.json`, bound to
  `127.0.0.1` only.
- **Peer health:** detects dead and slow peers and writes replacement
  suggestions to `status/vistanova_peer_suggestions.json`. Nothing is applied
  automatically. A human approves every change.

Stage 2 needs separate approval.

## Guardrails

- Read-only against the mesh
- No routing
- No peer changes (no add, remove or replace)
- No key generation
- No production traffic
- No chain account

## Honesty

This is a **prototype definition** in DRAFT, not a runtime. Until the
collector is wired into `prototype_bot.py`, VistaNova only draws a map when
someone runs it by hand. Without a live Yggdrasil daemon it stays blind: an eye, not a hand.
