# QNet 1DEV Burn-Flow

Dokumentation des Phase-1-Aktivierungsflusses fuer QNet-Knoten,
integriert in das Nexus-Server-Setup.

## Adressen (Stand August 2026)

| Zweck | Adresse |
|---|---|
| 1DEV Mint (Mainnet) | `4R3DPW4BY97kJRfv8J5wgTtbDpoXpRv92W957tXMpump` |
| Burn-Programm (Devnet v14.5) | `CCZSessk1TbWie6Ye2JX2cNEWHTEWxCwe5sLz8JaFriw` |
| Solana-Incinerator | `1nc1nerator11111111111111111111111111111111` |

Quelle: [AIQnetLab/QNet-Blockchain](https://github.com/AIQnetLab/QNet-Blockchain) — `Tokenomics.md`, `docs/API_REFERENCE.md`.

## Preis (Phase 1)

- Basis: **1.500 1DEV** fuer alle Knotentypen (light / full / super).
- Dynamisch: sinkt um 150 1DEV pro 10 % verbrannter Supply, Minimum 300.
- Formel: `price = max(1500 - floor(burn% / 10) * 150, 300)`.
- Phase 2 (QNC) startet bei 90 % verbrannter Supply oder nach 5 Jahren.

## Ablauf

1. **Wallet** — QNet-Wallet-Extension (Chrome) oder Mobile-App oeffnen.
2. **Burn** — 1DEV an Incinerator oder Burn-Programm senden. Betrag >= aktueller Preis.
3. **Signatur notieren** — `BURN_TX = <solana_tx_signature>`.
4. **Code erzeugen** — die Wallet erzeugt den Code *lokal*. Nur der Hash geht on-chain.
5. **Registrieren** — Code an QNet-Node binden. Ein Wallet = ein Knoten. Code ist permanent.

## Code-Format

```
QNET-XXXXXX-XXXXXX-XXXXXX   (25 Zeichen)
|------|------|------|
Typ+Zeit Wallet1 Wallet2+Entropie
```

Kryptografisch an `burn_tx_hash` und Wallet-Adresse gebunden.

## API (Referenz)

`POST /api/v1/generate-activation-code`

```json
{
  "wallet_address": "Solana_oder_EON_Adresse",
  "burn_tx_hash": "solana_burn_tx_signature",
  "node_type": "light|full|super",
  "burn_amount": 1350,
  "phase": 1
}
```

Antwort:

```json
{
  "success": true,
  "activation_code": "QNET-XXXXXX-XXXXXX-XXXXXX",
  "node_type": "light",
  "permanent": true
}
```

> Der Endpunkt `api.qnet.network` im Skript `06-qnet-burn-flow.sh` ist ein
> Platzhalter. Die echte Wallet nutzt ihre eigenen, signierten Endpunkte.
> Niemand kann einen Aktivierungscode ohne echte Burn-TX erzeugen.

## Skript

`server-setup/scripts/06-qnet-burn-flow.sh` — ausfuehrbare Checkliste:

```bash
bash scripts/06-qnet-burn-flow.sh light <SOLANA_WALLET>
```

Brennt nichts. Prueft Voraussetzungen, fragt Preis ab, gibt die manuelle
Burn-Checkliste aus und versucht den Code-Request.
