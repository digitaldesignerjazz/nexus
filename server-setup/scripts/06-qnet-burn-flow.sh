#!/usr/bin/env bash
# 06-qnet-burn-flow.sh — QNet Phase-1 Burn-Flow (Dokumentation + Checkliste)
# Nexus / Esslinger Consulting — Sir Sven Normen
set -euo pipefail

# ---------------------------------------------------------------------------
# QNET 1DEV BURN-FLOW
# Aktivierung eines QNet-Knotens durch Verbrennen von 1DEV auf Solana.
# Quelle der Wahrheit: AIQnetLab/QNet-Blockchain (Tokenomics.md, API_REFERENCE.md)
# Dieses Skript BRENNT NICHTS. Es dokumentiert den Ablauf und prueft die
# Voraussetzungen. Der echte Burn laeuft ausschliesslich in der QNet-Wallet.
# ---------------------------------------------------------------------------

MINT="4R3DPW4BY97kJRfv8J5wgTtbDpoXpRv92W957tXMpump"          # 1DEV SPL Mint (Mainnet)
BURN_CONTRACT="CCZSessk1TbWie6Ye2JX2cNEWHTEWxCwe5sLz8JaFriw" # Burn-Programm (Devnet v14.5)
INCINERATOR="1nc1nerator11111111111111111111111111111111"     # Solana-Incinerator
BASE_COST=1500                                                  # 1DEV, Phase 1, alle Knotentypen
MIN_COST=300
API_BASE="https://api.qnet.network"                            # Platzhalter — offizielle Wallet nutzt eigene Endpunkte

node_type="${1:-light}"   # light | full | super
wallet="${2:-}"           # Solana-Adresse des Aktivierers

echo "=== QNet 1DEV Burn-Flow ==="
echo "Knoten-Typ : $node_type"
echo "Mint       : $MINT"
echo "Burn-Prog  : $BURN_CONTRACT"
echo "Incinerator: $INCINERATOR"
echo "Basispreis : ${BASE_COST} 1DEV (sinkt dynamisch mit verbrannter Supply)"
echo

# 1) Voraussetzungen
echo "[1/5] Voraussetzungen"
command -v solana >/dev/null 2>&1 || echo "  ! 'solana' CLI fehlt — nur fuer manuelle Burn-TX noetig"
command -v curl  >/dev/null 2>&1 || { echo "  x curl fehlt"; exit 1; }
echo "  + curl vorhanden"

# 2) Aktuellen Preis abfragen (oeffentliche API, falls erreichbar)
echo "[2/5] Preisabfrage"
price_json=$(curl -fsS "${API_BASE}/api/v1/activation/price?type=${node_type}" 2>/dev/null || true)
if [[ -n "$price_json" ]]; then
  echo "  + $price_json"
else
  echo "  ~ API nicht erreichbar — Fallback auf Basispreis ${BASE_COST} 1DEV"
  echo "  Formel: price = max(1500 - floor(burn% / 10) * 150, 300)"
fi

# 3) Burn-Checkliste (manuell in der QNet-Wallet)
echo "[3/5] Burn-Checkliste (QNet-Wallet Extension / Mobile App)"
cat <<'EOF'
  a) Wallet oeffnen -> Node Activation -> 1DEV Burn waehlen
  b) Betrag >= aktueller Preis (mind. 300 1DEV, aktuell 1500)
  c) Ziel: Incinerator 1nc1nerator...1111  ODER Burn-Programm
  d) TX bestaetigen, Signatur notieren  ->  BURN_TX=<signature>
  e) Code wird LOKAL in der Wallet erzeugt, nur der Hash geht on-chain
EOF

# 4) Aktivierungscode anfordern (POST /api/v1/generate-activation-code)
echo "[4/5] Code-Generierung"
if [[ -z "$wallet" ]]; then
  echo "  ~ Keine Wallet-Adresse uebergeben."
  echo "    Aufruf: $0 <light|full|super> <SOLANA_WALLET>"
  echo "    Danach: curl -X POST ${API_BASE}/api/v1/generate-activation-code \\"
  echo "      -H 'Content-Type: application/json' \\"
  echo "      -d '{\"wallet_address\":\"$wallet\",\"burn_tx_hash\":\"$BURN_TX\",\"node_type\":\"$node_type\",\"burn_amount\":$BASE_COST,\"phase\":1}'"
else
  echo "  + Wallet: $wallet"
  echo "  + Sende generate-activation-code Request ..."
  curl -fsS -X POST "${API_BASE}/api/v1/generate-activation-code" \
    -H "Content-Type: application/json" \
    -d "{\"wallet_address\":\"${wallet}\",\"burn_tx_hash\":\"${BURN_TX:-}\",\"node_type\":\"${node_type}\",\"burn_amount\":${BASE_COST},\"phase\":1}" \
    || echo "  ! Request fehlgeschlagen — API-Endpunkt ist Platzhalter, echte Wallet nutzt interne Endpunkte."
fi

# 5) Code-Format und Bindung
echo "[5/5] Code-Format"
cat <<'EOF'
  Format : QNET-XXXXXX-XXXXXX-XXXXXX  (25 Zeichen)
           |------|------|------|
           Typ+Zeit  Wallet1 Wallet2+Entropie
  - Permanent, laeuft nie ab
  - Kryptografisch an burn_tx_hash + Wallet gebunden
  - Ein Wallet = ein Knoten
EOF

echo
echo "Fertig. Echter Burn nur ueber die offizielle QNet-Wallet."
echo "Quelle: https://github.com/AIQnetLab/QNet-Blockchain"
