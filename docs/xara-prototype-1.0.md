# Xara Prototype 1.0

Experimental overlay agent for the Hannover swarm.

## Role

Xara is the **experimental prototype** of the Nexus mesh. It inherits the
Xen Protocol 1.0 substrate but adds **no routing authority**. All real mesh
work stays with Yggdrasil and Xen.

## Files

| Path | Purpose |
|---|---|
| `configs/xara-prototype-1.0.yaml` | Prototype definition |
| `server-setup/scripts/10-start-xara.sh` | Start script (host) |
| `status/xara_presence.json` | Runtime presence (written on start) |

## Start (on Hannover host)

```bash
git pull
cd nexus/server-setup
bash scripts/09-start-xen.sh      # substrate first
bash scripts/10-start-xara.sh    # then Xara
```

## Guardrails

- No production traffic
- No key generation
- Read-only against the mesh
- Aborts probes when peers are down

## Honesty

This is a **prototype definition**, not a runtime. The daemon and the real
mesh handshake run on the host. Without a live Yggdrasil daemon and at least
one peer Up, Xara stays in STANDBY — a card, not a tunnel.
