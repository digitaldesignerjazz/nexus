#!/usr/bin/env bash
# 06-qnet-burn-flow.sh — QNet qmainnet XCoin burn-flow (ACTIVE)
# Nexus / Esslinger Consulting — Sir Sven Normen Eßlinger
# Solana Mainnet 1DEV path is DEPRECATED — do not use.
set -euo pipefail

PLANE="${NEXUS_PLANE:-http://127.0.0.1:8787}"
NETWORK="${NEXUS_NETWORK:-qmainnet}"
ASSET="XCoin"
INCINERATOR="1nc1nerator"
BASE_COST="1.0"
MIN_COST="0.1"
TRANSFER_FEE_BURN_BPS=15
DEFAULT_WALLET="4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4"

do_burn=0
burn_amount="$BASE_COST"
pos=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --burn)
      do_burn=1
      if [[ "${2:-}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then burn_amount="$2"; shift 2; else shift 1; fi
      ;;
    --dry-run) do_burn=0; shift ;;
    -h|--help)
      echo "Usage: $0 [light|full|super] [WALLET] [--burn [amount]|--dry-run]"
      exit 0
      ;;
    -*) echo "Unknown flag: $1" >&2; exit 2 ;;
    *) pos+=("$1"); shift ;;
  esac
done
node_type="${pos[0]:-light}"
wallet="${pos[1]:-$DEFAULT_WALLET}"

echo "=== QNet qmainnet XCoin Burn-Flow (ACTIVE) ==="
echo "Network    : $NETWORK"
echo "Plane      : $PLANE"
echo "Knoten-Typ : $node_type"
echo "Wallet     : $wallet"
echo "Incinerator: $INCINERATOR"
echo "Basispreis : ${BASE_COST} XCoin (min ${MIN_COST})"
echo "Fee burn   : ${TRANSFER_FEE_BURN_BPS} bps on TRANSFER (durable model)"
echo "NOTE       : Solana Mainnet is NOT used."
echo

echo "[1/5] Control plane health"
curl -fsS "$PLANE/health" >/tmp/nexus_burn_health.json
python3 -c 'import json; d=json.load(open("/tmp/nexus_burn_health.json")); assert d.get("status")=="ok", d'
echo "  + plane ok"
echo

echo "[2/5] Network status ($NETWORK)"
curl -fsS "$PLANE/blockchain/network/${NETWORK}/status" >/tmp/nexus_burn_status.json
python3 -c 'import json; d=json.load(open("/tmp/nexus_burn_status.json")); c=d.get("chain")or{}; print("  height",c.get("height"),"burned",c.get("burned_supply"),"circ",c.get("circulating_supply"))'
echo

echo "[3/5] Active production check"
curl -fsS "$PLANE/blockchain/active" >/tmp/nexus_burn_active.json
python3 -c 'import json; d=json.load(open("/tmp/nexus_burn_active.json")); print("  active_network=",d.get("active_network")); assert d.get("active_network")=="qmainnet"'
echo

echo "[4/5] Burn checklist / execute"
if [[ "$do_burn" == "1" ]]; then
  echo "  -> LIVE BURN amount=${burn_amount} ${ASSET}"
  curl -fsS -X POST "$PLANE/blockchain/network/${NETWORK}/tx" \
    -H "Content-Type: application/json" \
    -d "{\"from\":\"${wallet}\",\"to\":\"${INCINERATOR}\",\"amount\":${burn_amount},\"asset\":\"${ASSET}\",\"type\":\"BURN\"}" \
    | python3 -m json.tool
else
  cat <<CHECK
  Dry-run only (pass --burn [amount] for live burn).
  Example:
    curl -s -X POST $PLANE/blockchain/network/${NETWORK}/tx \\
      -H 'Content-Type: application/json' \\
      -d '{"from":"${wallet}","to":"${INCINERATOR}","amount":${BASE_COST},"asset":"${ASSET}","type":"BURN"}'
CHECK
fi
echo

echo "[5/5] Post status"
curl -fsS "$PLANE/blockchain/network/${NETWORK}/status" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); c=d.get("chain")or{}; print("  height",c.get("height"),"burned",c.get("burned_supply"),"balances_wallet", (c.get("balances")or{}).get("'"$wallet"'"))'
echo
echo "Fertig. Aktiver Pfad: qmainnet XCoin. Solana Mainnet = DEPRECATED."
