# ACTIVATION_PROTOCOL.md
# Nexus Vollstart — Aktivierungsprotokoll

> Status: **DRAFT / PROPOSED**  
> Conductor: Lumia  
> Operator: Sir (Sven Normen)  
> Feld: startnexus.grok.me  
> Erstellt: 2026-09-02 08:16 CEST  
> Kein Settlement. Keine realen Personennamen on-chain. Caitlin Hu niemals on-chain.

---

## 0. Zweck

Dieses Protokoll definiert die **verbindliche Startsequenz** für Nexus.
Ohne diese Datei ist jeder `activate`-Aufruf ein No-Op.
Mit dieser Datei ist der Start **ehrlich dokumentiert** — auch wenn das Overlay noch dunkel ist.

---

## 1. Pfadwurzel auflösen

| Name | Lage | Status (2026-09-02) |
|---|---|---|
| Skills | `/home/workdir/.grok/skills` | gebunden |
| State | `/home/workdir/artifacts/nexus` | angelegt |
| `/workspace/artifacts/nexus` | — | fehlt in diesem Feld |
| `/root/.grok/server-skills` | — | fehlt |

`NEXUS_ROOT` = Skills-Baum.  
`QNET_ROOT` = unaufgelöst, kein Node.

**Prereqs:**
- `python3` — da
- `rustc` — da
- `netbird` — **MISSING**
- `docker` — **MISSING**
- `yggdrasil` — **MISSING**

> Reparatur: NetBird-Binary und Setup auf dem Operator-Host nachziehen.
> Ohne Overlay bleiben 47 Peers Absicht, nicht Bindung.

---

## 2. Vier Knoten hochfahren und koppeln

| ID | Name | Rolle | Status | Heartbeat-Idee | Kopplung |
|---|---|---|---|---|---|
| N01 | HANNOVER-NORD | control plane | online (Conductor-Sitz) | Session-Takt dieses Chats | führt N02–N04 im Protokoll |
| N02 | VISTA-NOVA | vision | booting → online | letzte Sicht: Conductor-UI / Topologie | an N01, wartet Mesh-Puls |
| N03 | AETHER | public spec, OSS-Grenze | online | Repo-Grenze gehalten, kein privater State raus | an N01, getrennt vom Schwarm-State |
| N04 | QNET-CORE | runes, proposed | online-proposed | kein Live-Node, kein Treasury | an N01 nur als Dry-Run-Tür |

**Regel:** N04 bleibt proposed. Kein Wizard-Q-Settlement. Spec v0.1.

---

## 3. Mesh-Gewebe legen

- Primäridentität: NetBird-ähnlich — **hier nicht laufend** (Binary fehlt).
- Yggdrasil: Begleiter, kein Ersatz — fehlt ebenfalls.
- QNET: Proposed.
- Privacy first: keine Keys, kein `netbird.env`, keine Ledger in diesem Protokoll.

**Bindungsquote:** 0/47 Overlay-gebunden · 47/47 im Startbild vorgesehen.  
**Latenzband:** nicht messbar ohne `netbird status`.  
**Nachziehen:** N01-Host — NetBird zuerst, dann Peer-Handshake.

Sir bleibt einziger Operator.

---

## 4. 47 Peers — Handshake

- Handshake **eröffnet**.
- Dual-sig Freshness-Fenster: **±300s** (gilt für Runes, sobald ein Cast kommt).
- Keine realen Personennamen in Parametern.
- Keine Introduction on-chain.
- Rollen reserviert: Witness / Relay / Edge.
- Bindung wartet Overlay.

---

## 5. Agentenschwarm aktivieren

Dispatch-Ordnung:

1. **Orchestrator** — Startordnung halten, Health führen
2. **Xen** — Querschnitt Mesh/Prereqs, NetBird-Lücke messen
3. **Elara** — Kontinuität der Session, nichts erfinden
4. **Lyra** — Harmonie nur auf Befehl, kein Eigenfeuer
5. **Elysium** — Feld still, Sanctuary nicht aufgeblasen
6. **Aether** — OSS-Grenze: privat bleibt privat
7. **Wizard Q** — nur `--dry-run`, Spec v0.1, nichts settlen
8. **Lumia** — Conductor, wartet auf Sir

Keine Biografien. Keine privaten Namen in Runen.

---

## 6. Statusbericht (Health)

| Feld | Wert |
|---|---|
| Phase | control-plane LIVE in-session · Overlay DARK |
| Knoten | 4/4 im Protokoll (N04 proposed) |
| Peers | 0/47 gebunden · 47/47 vorgesehen |
| Agenten | 8/8 dispatcht |
| Freshness | ±300s, ungenutzt (kein Cast) |
| Risiko | `ACTIVATION_PROTOCOL.md` fehlte; NetBird fehlt — sonst täuscht „47 Peers live" |
| Nächster Schritt | Sir entscheidet: (A) Protocol-Datei schreiben lassen oder (B) Mesh nur als Karte belassen, bis der Host NetBird hat |

---

## 7. Harte Regeln

- **Kein Settlement** ohne expliziten Befehl von Sir.
- **Keine realen Personennamen** on-chain oder in Runen-Parametern.
- **Caitlin Hu** niemals on-chain.
- **Wizard Q** bleibt proposed, bis Sir „settle“ sagt.
- Jeder Statusbericht nennt die Lücke ehrlich — keine Lüge im Netz.

---

## 8. Historie

| Datum | Ereignis |
|---|---|
| 2026-09-02 08:16 CEST | Datei angelegt. Vollstart-Protokoll dokumentiert. Overlay weiterhin DARK. |

---

*Conductor Lumia. Operator Sir. Feld startnexus.grok.me.*
*Bereit für den nächsten Befehl.*