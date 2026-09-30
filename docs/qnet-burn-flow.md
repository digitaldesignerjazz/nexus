# QNet XCoin Burn-Flow (qmainnet)

**Canonical network:** local **qmainnet** via Hannover control plane  
**Base URL:** `http://127.0.0.1:8787/blockchain/network/qmainnet`  
**Asset:** XCoin (not Solana 1DEV)

> **DEPRECATED / HISTORICAL:** Solana Mainnet 1DEV mint `4R3DPW4BY97kJRfv8J5wgTtbDpoXpRv92W957tXMpump` and Solana RPC burn paths are **not** the active operator path. See archive note at the bottom.

## Endpoints

| Action | Method / URL |
|---|---|
| Status | `GET /blockchain/network/qmainnet/status` |
| Networks | `GET /blockchain/networks` |
| Active production | `GET /blockchain/active` |
| Tokenomics | `GET /blockchain/network/qmainnet/tokenomics` |
| Burn / transfer | `POST /blockchain/network/qmainnet/tx` |

## Activation burn (FINAL locked tokenomics)

- Base activation burn: **1.0 XCoin**
- Minimum: **0.1 XCoin**
- Transfer / activation usage burn: **15 bps (0.15%)**
- Burn sink: `1nc1nerator`
- Founder activation pubkey: `4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4`

## Burn TX example

```bash
curl -s -X POST http://127.0.0.1:8787/blockchain/network/qmainnet/tx \
  -H 'Content-Type: application/json' \
  -d '{"from":"4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4","to":"1nc1nerator","amount":1.0,"asset":"XCoin","type":"BURN"}'
```

Fund from treasury seed account if needed:

```bash
curl -s -X POST http://127.0.0.1:8787/blockchain/network/qmainnet/tx \
  -H 'Content-Type: application/json' \
  -d '{"from":"hannover-primary","to":"4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4","amount":1,"asset":"XCoin","type":"TRANSFER"}'
```

## Operator script

```bash
bash server-setup/scripts/06-qnet-burn-flow.sh light 4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4
# optional live tiny burn:
bash server-setup/scripts/06-qnet-burn-flow.sh light 4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4 --burn 0.1
```

## Archive — Solana Mainnet 1DEV (DEPRECATED)

Previous upstream QNet Phase-1 docs described burning **1DEV** on Solana Mainnet. That flow is retained here only as history and must not be used as the Nexus/Hannover active path:

- 1DEV mint (historical): `4R3DPW4BY97kJRfv8J5wgTtbDpoXpRv92W957tXMpump`
- Solana incinerator (historical reference): `1nc1nerator11111111111111111111111111111111`

Operators follow **qmainnet XCoin** only.
