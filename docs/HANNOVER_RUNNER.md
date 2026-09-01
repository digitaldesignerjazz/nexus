# Hannover Runner — Update-Anleitung

## Aktueller Stand
- Runner-Version auf dem Knoten: **2.321.0** (installiert)
- Neueste stabile: **2.337.0** (26. August 2026)
- Mindestversion für Jobs: **2.329.0** (Registrierung), höher für Runtime
- Vollständige Durchsetzung ab: **25. September 2026**

## Update (auf dem Hannover-Knoten)
```bash
cd ~/actions-runner   # oder /opt/actions-runner
sudo ./svc.sh stop
curl -fsSL -o runner.tar.gz https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-linux-x64-2.337.0.tar.gz
tar xzf runner.tar.gz
sudo ./svc.sh start
./run.sh --version   # sollte 2.337.0 zeigen
```

## Labels (unverändert)
`self-hosted`, `linux`, `x64`, `lumina`, `hannover`

## Nach dem Update
Die wartenden Jobs (Nexus Overlay Apply, Lumina Runner) greifen automatisch.
