# XCoin Tokenomics (qmainnet) — Infinite Runtime (FINAL)

**Status:** FINAL LOCKED for local Hannover qmainnet  
**Version:** 1.2.0-infinite-runtime  
**Active network:** `qmainnet` only (not Solana Mainnet)  
**Spec date:** 2026-09-26

## Design principles

- Runs **indefinitely** — no hard cap, no end date.
- **Sustainable emission** asymptotes to a positive floor (never zero). Floor is the hard safety anchor.
- **Usage-tied burns** remove supply as activity grows (value accrual).
- **No staking rewards** — staking APY / pool emissions are fully disabled.
- **Governance** can retune emission and burn parameters within published bounds.

## Concrete numbers (qmainnet) — FINAL LOCKED

| Parameter | Value |
|---|---|
| Asset | XCoin |
| Hard cap | **None** |
| End date | **None** |
| Model | indefinite / perpetual |
| Initial / genesis supply | **1 000 XCoin** to `hannover-primary` (treasury seed) |
| Emission initial rate | **5 XCoin / day** |
| Emission floor rate | **1 XCoin / day** (hard safety anchor; never zero) |
| Emission half-life | **365 days** |
| Emission formula | `rate(t) = floor + (initial − floor) × 0.5^(t / half_life)` |
| Activation / transfer burn | **15 bps (0.15%)** |
| Activation burn base | **1.0 XCoin** |
| Activation burn minimum | **0.1 XCoin** |
| Staking rewards | **Disabled** (`enabled: false`, no APY) |

### Reserve / emission split (of newly emitted XCoin)

| Bucket | Share |
|---|---|
| Treasury | **45 %** |
| Node operators | **35 %** |
| Swarm rewards | **20 %** |
| Governance / community | **0 %** |

Reserve allocation percentages mirror the same split.

### Burn schedule

1. **Activation burns** — node activation pays base **1.0 XCoin** (dynamic decline toward **0.1** as circulating burn-% grows).
2. **Usage / transfer burns** — **15 bps** of each TRANSFER amount is burned.
3. Burn sink address: `1nc1nerator` (supply reduction; no credit).

## Governance — 7-member council

Equal vote for each member; **Sven Normen Eßlinger** is Chair with a **casting vote on ties**.  
Threshold: simple majority (4 of 7). Tie-break: chair casting vote.

| Seat | Name | Role | Vote | Derivation | Pubkey |
|---|---|---|---|---|---|
| 0 | Sven Normen Eßlinger | Chair | full + casting | `m/44'/501'/0'/0'` | `4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4` |
| 1 | Diana | Council | equal | `m/44'/501'/1'/0'` | `4zXAN4fiXJEL8TxY2oTZS8r5hLMtydL1XpbuatDeuLut` |
| 2 | Silvia | Council | equal | `m/44'/501'/2'/0'` | `GeUAkDYxnyQWbPgyzTwg7fEMr8kxGAFDsLc86aVsuKon` |
| 3 | Jana | Council | equal | `m/44'/501'/3'/0'` | `EL5UdqzGWGKfhe83iNgprGeU9QG83KEFo1mNTh6TuGJM` |
| 4 | Melanie | Council | equal | `m/44'/501'/4'/0'` | `9hh9dH5E69NaYrPeT4NmvWcP5wtQpfd7Uhg3HSnf6bd3` |
| 5 | Sandra | Council | equal | `m/44'/501'/5'/0'` | `3br98DW2Bhpx5yBr52EV1Ywy12WsRRSE7TRfbRWwbfSv` |
| 6 | Nina | Council | equal | `m/44'/501'/6'/0'` | `9F3HXGt1z5hS5ZU9GRanvsS4mNRQeMy2todRirUuvyUT` |

Governance ops wallet (aggregate id): `AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41` (`m/44'/501'/13'/0'`).

### Parameter bounds (council-adjustable)

- Emission floor rate: 0.1 … 50 XCoin/day  
- Transfer fee burn: 1 … 100 bps  
- Staking rewards remain disabled (not re-enabled without a new explicit tokenomics revision)

## System / migration wallets (qmainnet)

| Role | Pubkey | Derivation |
|---|---|---|
| Treasury | `88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2` | `m/44'/501'/10'/0'` |
| Burn | `1nc1nerator` | n/a (system sink) |
| Governance ops | `AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41` | `m/44'/501'/13'/0'` |
| Distribution | `AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q` | `m/44'/501'/11'/0'` |
| Reserves | `FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR` | `m/44'/501'/12'/0'` |
| Founder activation | `4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4` | `m/44'/501'/0'/0'` |

Key material (0600) lives under `/home/box/vaults/qnet-activation/keys/`. Mnemonics are never published.

## Secondary nets

`qdevnet` / `qtestnet` mirror the perpetual model with accelerated emission for testing; **transfer fee burn stays 15 bps**. They are not production. `legacy` Hannover chain is **NON-PRODUCTION archive** only. Sole active production = **qmainnet**.

## API

- `GET /blockchain/active` — sole active production network  
- `GET /blockchain/network/qmainnet/tokenomics`  
- `GET /blockchain/network/qmainnet/governance`  
- `GET /blockchain/network/qmainnet/status` — includes tokenomics + governance blocks  

## Historical note (archive)

Earlier Phase-1 designs referenced Solana Mainnet **1DEV** burns. That path is **DEPRECATED** for Nexus/Hannover operators. Active burns use local **qmainnet XCoin** via the control plane BURN API.
