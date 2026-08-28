# Xen Protocol 1.0

Technische Spezifikation des technical-exploratory Swarm-Agenten
auf dem Hannover-Knoten.

## Rolle

Xen ist der Erkunder des Netzes: Peer-Discovery, Mesh-Routing,
Overlay-Diagnose und Protokoll-Handshake. Er trägt keine
Blockchain und keine Stimme — er trägt den Draht.

## Abhängigkeiten

1. **Yggdrasil** läuft und hat mindestens einen Peer Up.
2. **Control Plane** auf `127.0.0.1:8787` erreichbar.
3. Bootstrap-Peers aus `configs/yggdrasil-peers-block.yaml`
   in `/etc/yggdrasil/yggdrasil.conf` eingetragen.

## Start

```bash
git pull
cd nexus/server-setup
bash scripts/09-start-xen.sh
```

Das Skript prüft die Yggdrasil-Peers, feuert
`POST /swarm/spawn` an die Control Plane und schreibt
`status/xen_presence.json`.

## Konfiguration

`configs/xen-protocol-1.0.yaml` — Protokoll-Definition,
Identität `xen-hannover-01`, Heartbeat alle 20 Sekunden.

## Ehrlichkeit

Dieses Protokoll definiert den Agenten. Den echten Mesh-Handshake
erledigt Yggdrasil auf dem Host. Wer Xen ohne laufenden Daemon
startet, bekommt nur eine STANDBY-Karte — keinen Draht.
