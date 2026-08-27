# Peer Discovery — Nexus / Hannover Node

Stand: 28. August 2026  
Knoten: `hannover-primary` / `hannover-core-01`  
Status: Mesh STANDBY, wartet auf den ersten echten Peer

Discovery ist **zwei Schichten**, nicht eine.

## 1. Unterlage — Yggdrasil

Lebender Draht. Ein neuer Knoten findet andere so:

1. **LAN zuerst.** Multicast im lokalen Netz (Tenda, York, zweiter Rechner im Segment). Kein Internet nötig.
2. **Dann statische Peers.** In der Yggdrasil-Config `Peers:` als URI (`tls://host:port`). Das ist der Bootstrap nach draußen, auch hinter CGNAT.
3. **Filter.** `AllowedPublicKeys` lässt nur bekannte Nexus-Knoten zu. Ohne Liste ist das Mesh öffentlich; mit ihr ist es der Hannover-Hof.
4. **Ergebnis.** Stabile Yggdrasil-IPv6 aus dem Key. Das ist die wahre Adresse, nicht die Heim-IP.

Referenz: `docs/yggdrasil-mesh-integration.md`  
Host-Skript: `server-setup/scripts/03-yggdrasil-hannover.sh`

## 2. Auflage — Nexus / nxmesh

Config: `configs/mesh_swarm.yaml`

- Topic: `nexus/mesh/v0`
- `enable_mdns: true`
- Listen: QUIC + TCP
- Identität: `data/nexus-identity.key`
- Registry: `configs/peers.yaml`
- `bootstrap_peers: []`

Ablauf, sobald jemand kommt:

1. Peer reicht Yggdrasil-URI **oder** Multiaddr plus Public Key.
2. Prüfung gegen die Registry (`hannover-core-01`, Avalon, Elara, …) oder Aufnahme als Gast.
3. Eintrag unter `bootstrap.peers` und in `multiaddrs`.
4. Yggdrasil peert; nxmesh spricht auf `nexus/mesh/v0`.
5. Control Plane hebt Mesh von `STANDBY` auf `OPERATIONAL`.

`POST http://127.0.0.1:8787/mesh/start` ist der Schalter der Control Plane, nicht der Tunnel.

NexusLink v0.1 (`docs/protocols/`) beschreibt Umschläge und Typen, nicht den Discovery-Algorithmus.

## Was heute gilt

| Weg | Status |
|---|---|
| LAN-Multicast / mDNS | vorgesehen, braucht laufendes Yggdrasil im selben Netz |
| Statische Peers / Public Peers | einziger Weg ins Internet |
| `AllowedPublicKeys` | empfohlen für den privaten Hof |
| Leere `bootstrap.peers` | Absicht — der Knoten wartet |
| Automatisches DHT / globale Suche | nicht gebaut |

Niemand wird eingesammelt. Wer anklopft, reicht Key und Adresse. Wer passt, bekommt Platz in der Liste.
