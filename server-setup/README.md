# Nexus Server Setup

Ein-Kommando auf Deinem Host:

```bash
cd server-setup
bash scripts/00-doctor.sh
bash scripts/01-bootstrap.sh
bash scripts/02-start-control-plane.sh
```

Danach: http://127.0.0.1:8787/health

Details: SETUP.md
