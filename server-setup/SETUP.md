# Nexus Server Setup — Esslinger & Co.

Vorbereitet für Sir Sven Normen Eßlinger · Hannover / Onyx Earth Node  
Stand: 23. September 2026  
Quelle: `digitaldesignerjazz/nexus` (Python-Referenz) + `go-nexus` (Orchestrator-CLI)

## Was hier aufgesetzt wird

Nexus ist kein einzelnes Binary. Der lebende Stand ist:

| Schicht | Repo | Realität heute |
|---|---|---|
| Referenz-Orchestrator | `digitaldesignerjazz/nexus` → `python/` | Lauffähig: `start_nexus.py`, `nexus_orchestrator.py` |
| Start-CLI | `digitaldesignerjazz/go-nexus` | `doctor` / `start` (Default: Dry-Run) |
| Control Plane | `server-setup/control/nexus_control.py` | HTTP `127.0.0.1:8787` |
| Mesh | Yggdrasil nativ auf dem Host | Nicht in Docker, außer als Sidecar |
| Blockchain / Swarm / Prototypen | Platzhalter + Prototypen | QCoin-Miner existiert in `nexus-project` |

## Empfohlene Reihenfolge auf dem Host

Wenn `~/nexus` schon existiert und **kein** `server-setup` enthält: nicht überschreiben. Hub nach `~/nexus-hub` klonen.

1. `bash scripts/00-doctor.sh` — Pflicht: python3, git. Optional: go, docker, yggdrasil, cargo.
2. `bash scripts/01-bootstrap.sh` — `.env`, `data/`, `logs/`, Python-Vendor.
3. `bash scripts/02-start-control-plane.sh --background`
4. Optional Mesh: `bash scripts/03-yggdrasil-hannover.sh`
5. Optional Dauerbetrieb: `sudo cp systemd/nexus-control.service /etc/systemd/system/`

Oder gebündelt: `bash scripts/earth-node-bootstrap.sh`

Kontrolle:

```bash
curl -sS http://127.0.0.1:8787/health
curl -sS http://127.0.0.1:8787/status | python3 -m json.tool
```

## Exitcodes (00 / 01 / 02)

| Code | Bedeutung |
|---|---|
| 0 | ok |
| 2 | Pflichtbefehl oder Argument fehlt |
| 3 | falscher Verzeichnisbaum / Datei fehlt |
| 5 | git clone / fetch / pull fehlgeschlagen |
| 6 | Port belegt |
| 7 | Health-Check nach Start timeout |

Fehler laufen nach `stderr` mit Präfix `[ERR]`. Keine Auth-Keys in Logs.

## Ports

| Dienst | Port | Bind |
|---|---|---|
| Nexus Control Plane | 8787 | 127.0.0.1 (Default) / 0.0.0.0 mit `NEXUS_BIND` |
| Yggdrasil | 9001 (typisch) | Host |
| go-nexus Compose | intern | `nexus-net` |

Keine öffentlichen Ports ohne Reverse-Proxy und Auth.

## Sicherheit (Hannover-Node)

- Yggdrasil-Private Keys niemals committen.
- Control Plane zuerst nur localhost.
- Secrets nur in `.env` (chmod 600).
- Root nur für systemd/Yggdrasil-TUN, sonst User `nexus`.
