# Nexus Server Setup — Esslinger & Co.

Vorbereitet für Sir Sven Normen Eßlinger · Hannover Node  
Stand: 28. August 2026  
Quelle: `digitaldesignerjazz/nexus` (Python-Referenz) + `go-nexus` (Orchestrator-CLI)

## Was hier aufgesetzt wird

Nexus ist kein einzelnes Binary. Der lebende Stand ist:

| Schicht | Repo | Realität heute |
|---|---|---|
| Referenz-Orchestrator | `digitaldesignerjazz/nexus` → `python/` | Lauffähig: `start_nexus.py`, `nexus_orchestrator.py` |
| Start-CLI | `digitaldesignerjazz/go-nexus` | `doctor` / `start` (Default: Dry-Run) |
| Mesh | Yggdrasil nativ auf dem Host | Nicht in Docker, außer als Sidecar |
| Blockchain / Swarm / Prototypen | Platzhalter + Prototypen | QCoin-Miner existiert in `nexus-project` |

Dieses Paket startet eine **steuerbare Nexus Control Plane** auf Port **8787**, bindet die Python-Referenz ein und gibt Dir Host-Skripte für Mesh und systemd.

## Empfohlene Reihenfolge auf Deinem Host

1. `bash scripts/00-doctor.sh`
2. `bash scripts/01-bootstrap.sh`
3. `bash scripts/02-start-control-plane.sh`
4. Optional Mesh: `bash scripts/03-yggdrasil-hannover.sh`
5. Optional Dauerbetrieb: `sudo cp systemd/nexus-control.service /etc/systemd/system/`

Kontrolle:

```bash
curl -s http://127.0.0.1:8787/health
curl -s http://127.0.0.1:8787/status | python3 -m json.tool
```

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
