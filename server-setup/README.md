# Nexus Server Setup

Ein-Kommando auf dem Operator-Host (Onyx / Hannover):

```bash
# niemals ~/nexus überschreiben, wenn dort kein server-setup liegt
git clone https://github.com/digitaldesignerjazz/nexus.git ~/nexus-hub
cd ~/nexus-hub/server-setup
bash scripts/earth-node-bootstrap.sh
curl -sS http://127.0.0.1:8787/health
```

Schrittweise:

```bash
cd ~/nexus-hub/server-setup
bash scripts/00-doctor.sh
bash scripts/01-bootstrap.sh
bash scripts/02-start-control-plane.sh --background
```

`02` ohne Flag bleibt im Vordergrund (`exec`). `--background` schreibt PID und Log nach `logs/`.

Doctor-Exitcodes: `0` ok · `2` Pflichtbefehl fehlt · `3` falscher Baum.

Morgen-Routine (Backup + Restart):

```bash
bash scripts/07-restart-backup.sh
```

Details: SETUP.md
