# Nexus → LuminaCyberspace (`server-setup/lumina`)

**Version:** siehe `VERSION` (aktuell **0.3.0-alpha.2**)  
**Zweck:** Downloadbares, lauffähiges Paket, mit dem Nexus den öffentlichen LuminaCyberspace-Snapshot holen und einen **verifizierbaren** Cyberspace-Kern starten kann.

> Ehrlich: Bis alpha.2 gab es **keinen** funktionierenden Nexus→LuminaCyberspace-Launcher. Die Control Plane auf `:8787` spawnt keine Prozesse. Das GHCR-Image `lumina-cyberspace:alpha` ist nur Info. Dieses Paket schließt die Lücke **skriptbasiert**.

---

## Was wirklich startet

| Komponente | Startet? | Hinweis |
|---|---|---|
| `nexus_orchestrator.py` | **Ja** | Aus Snapshot oder Repo-`python/` |
| Overlay-Prototyp (`run-overlay-relocatable.py`) | **Ja, wenn PyNaCl** | Relocatable, ohne hartcodiertes `/workspace` |
| Yggdrasil | Optional (`ENABLE_YGGDRASIL=1`) | Braucht lokale Keys aus `02-gen-keys.sh` + oft Root/TUN |
| Control Plane `:8787` | Nicht durch dieses Paket | Wenn schon laufend: Smoke via `curl /health` |
| `onyx-listen` / Actions-Runner / `dockerd` | **Nein** | Nur mit `ENABLE_HANNOVER_EXTRAS=1` und selbst dann bewusst **nicht** aus dem öffentlichen Paket (Credentials fehlen) |

Hannover-only-Extras gehören in den **lebenden** `/workspace/lumina-state/start-stack.sh` auf dem Hannover-Host — nicht in dieses Public-Paket.

---

## Voraussetzungen

- Linux, `python3` ≥ 3.9, `curl`, `tar`, `sha256sum`
- Optional: `yggdrasil` / `yggdrasilctl`, `pip install pynacl` (für Overlay)
- Keine Secrets im Paket: Snapshot ist secret-scrubbed (`PrivateKey` / Multicast-Passwort = `<REDACTED>`)

---

## Schnellstart (Deutsch)

```bash
# Paket aus dem Release (oder aus dem Repo)
curl -LO https://github.com/digitaldesignerjazz/nexus/releases/download/v0.3.0-alpha.2/nexus-lumina-0.3.0-alpha.2.tar.gz
curl -LO https://github.com/digitaldesignerjazz/nexus/releases/download/v0.3.0-alpha.2/SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS
tar xzf nexus-lumina-0.3.0-alpha.2.tar.gz
cd nexus-lumina-0.3.0-alpha.2

cp .env.example .env
bash scripts/00-doctor-lumina.sh
bash scripts/01-fetch-snapshot.sh
bash scripts/02-gen-keys.sh
bash scripts/03-start-cyberspace.sh
bash scripts/04-status.sh
```

Aus dem geklonten Nexus-Repo:

```bash
cd server-setup/lumina
cp .env.example .env
bash scripts/00-doctor-lumina.sh
bash scripts/03-start-cyberspace.sh   # holt Snapshot bei Bedarf selbst
bash scripts/04-status.sh
```

Runtime landet unter `runtime/` (gitignored): Snapshot, Keys, PIDs, Logs, Status.

---

## English quick start

```bash
tar xzf nexus-lumina-0.3.0-alpha.2.tar.gz && cd nexus-lumina-0.3.0-alpha.2
cp .env.example .env
bash scripts/00-doctor-lumina.sh
bash scripts/03-start-cyberspace.sh
bash scripts/04-status.sh
```

What actually comes up: `nexus_orchestrator.py` (required smoke), optional relocatable overlay if PyNaCl is installed, optional yggdrasil if `ENABLE_YGGDRASIL=1` and local keys exist. Hannover extras (`onyx-listen`, actions-runner, dockerd) stay **off**.

Pinned public snapshot: `pins/SNAPSHOT_URL.txt` → LuminaCyberspace release asset  
`lumina-stack-public-20260924-2240.tar.gz` (sha256 in `pins/SNAPSHOT.sha256`).

---

## Layout

```
server-setup/lumina/
  README.md                 # diese Datei
  VERSION                   # 0.3.0-alpha.2
  .env.example
  pins/SNAPSHOT_URL.txt     # Release-Asset-URL
  pins/SNAPSHOT.sha256
  scripts/
    00-doctor-lumina.sh
    01-fetch-snapshot.sh
    02-gen-keys.sh          # lokale Keys → runtime/keys/ (nie committen)
    03-start-cyberspace.sh  # echter Start + Smoke
    04-status.sh
    lib-lumina.sh
  layouts/
    start-stack-min.sh      # relocatable via LUMINA_ROOT; keine Hannover-Extras
    run-overlay-relocatable.py
  runtime/                  # erzeugt zur Laufzeit (gitignored)
```

---

## Sicherheit

- Keine Overlay-Private-Keys, keine Yggdrasil-`PrivateKey`s, keine Runner-PATs im Paket.
- `02-gen-keys.sh` erzeugt **lokale** Keys unter `runtime/keys/` (chmod 600 / 700).
- Scrubbed Snapshot-Configs mit `<REDACTED>` werden **nicht** als lauffähige Mesh-Configs gestartet.
- Control-Plane-Hook (falls vorhanden) startet höchstens dieses Skript — kein Secret-Handling.

---

## Bekannte Grenzen (alpha.2)

1. Control Plane `:8787` bleibt zustandsbasiert; Prozess-Spawn ist Skript-Sache (dünner optionaler Hook möglich).
2. Snapshot-`overlay_daemon.py` enthält `/workspace`-Pfade — deshalb eigener relocatable Launcher.
3. Agent-Skripte (`elara.sh` …) aus dem Snapshot brauchen oft Ollama/Host-Pfade → best-effort, nicht Teil des Smokes.
4. Yggdrasil auf Nicht-Hannover-Hosts braucht eigene Keys + ggf. Root für TUN.
5. `ENABLE_HANNOVER_EXTRAS=1` schaltet **keine** Secret-Dienste aus diesem Public-Paket frei.

---

## Verwandtes

- Parent: `server-setup/` (Control Plane, Earth-Node-Bootstrap) — siehe `../README.md`, `../SETUP.md`
- Snapshot-Quelle: [LuminaCyberspace `v1.0.0-alpha.1` Assets](https://github.com/digitaldesignerjazz/LuminaCyberspace/releases/tag/v1.0.0-alpha.1)
