"""VIP payment messaging for qmainnet XCoin airdrops.

On each VIP payout (default: 50 XCoin TRANSFER), attach an on-chain memo and
append a recipient notification (inbox + outbox JSONL). Congrats use the
running VIP list number (VIP #N), never "first owner".
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/qnet-burn-work/vip_messages")
INBOX = ROOT / "inbox"
OUTBOX = ROOT / "outbox.jsonl"
LEDGER = ROOT / "VIP_PAYMENT_MESSAGES.jsonl"
MAP_PATH = ROOT / "recipient_map.json"
STATUS_PATH = ROOT / "SYSTEM_STATUS.json"
DRAFT_PATH = Path("/workspace/qnet-burn-work/VIP_CANDIDATES_1000_DRAFT.json")
DEFAULT_AMOUNT = 50.0

ROOT.mkdir(parents=True, exist_ok=True)
INBOX.mkdir(parents=True, exist_ok=True)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._+-]+", "_", s)[:120]


def load_recipient_map() -> dict[str, Any]:
    if MAP_PATH.exists():
        try:
            return json.loads(MAP_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_status(extra: dict[str, Any] | None = None) -> None:
    st = {
        "live": True,
        "updated_at": _utc(),
        "congrats_style": "sequential_vip_number",
        "congrats_rule": "Use VIP #N from list order; never call anyone first XCoin owner.",
        "paths": {
            "inbox": str(INBOX),
            "outbox": str(OUTBOX),
            "ledger": str(LEDGER),
            "map": str(MAP_PATH),
        },
        "channels": ["on_chain_memo", "local_inbox", "outbox", "agent_chat_when_mapped"],
        "rule": "Every VIP 50 XCoin payout auto-notifies with amount, tx_id, VIP #N thanks.",
    }
    if extra:
        st.update(extra)
    STATUS_PATH.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n")


def resolve_vip_number(to: str, explicit: int | None = None) -> int | None:
    if explicit is not None:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            pass
    rmap = load_recipient_map()
    meta = rmap.get(to) or rmap.get(to.lower()) or {}
    if meta.get("vip_number") is not None:
        try:
            return int(meta["vip_number"])
        except (TypeError, ValueError):
            pass
    # fall back to draft list order (1-based)
    try:
        draft = json.loads(DRAFT_PATH.read_text())
        cands = draft.get("candidates", draft if isinstance(draft, list) else [])
        for i, c in enumerate(cands, 1):
            acct = str(c.get("wallet_or_account") or "")
            prev = str(c.get("previous_wallet") or "")
            qaddr = str(c.get("qmainnet_address") or "")
            if to in (acct, prev, qaddr) or to.lower() in (acct.lower(), prev.lower(), qaddr.lower()):
                return i
            if c.get("name") and to.lower() in str(c.get("name")).lower():
                return i
    except Exception:
        return None
    return None


def build_thanks(
    amount: float,
    asset: str,
    tx_id: str,
    network: str,
    lang: str = "en",
    vip_number: int | None = None,
) -> str:
    num = f"VIP #{vip_number}" if vip_number is not None else "VIP"
    if lang == "de":
        return (
            f"Glückwunsch — du bist {num}. "
            f"Du hast {amount:g} {asset} auf {network} erhalten. Tx: {tx_id}."
        )
    return (
        f"Congrats — you are {num}. "
        f"You received {amount:g} {asset} on {network}. Tx: {tx_id}."
    )


def is_vip_payout(tx: dict[str, Any]) -> bool:
    if str(tx.get("type", "")).upper() != "TRANSFER":
        return False
    if str(tx.get("asset", "XCoin")) != "XCoin":
        return False
    try:
        amount = float(tx.get("amount", 0))
    except (TypeError, ValueError):
        return False
    to = str(tx.get("to") or "")
    if to.startswith("vip:") or to.startswith("github:") or tx.get("vip") is True:
        return abs(amount - DEFAULT_AMOUNT) < 1e-9 or bool(tx.get("vip"))
    return bool(tx.get("vip")) and abs(amount - DEFAULT_AMOUNT) < 1e-9


def notify_vip_payment(
    *,
    to: str,
    amount: float,
    asset: str,
    tx_id: str,
    height: int | None,
    network: str,
    memo: str | None = None,
    lang: str | None = None,
    vip_number: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rmap = load_recipient_map()
    meta = rmap.get(to) or rmap.get(to.lower()) or {}
    use_lang = lang or meta.get("lang") or ("de" if meta.get("prefer_de") else "en")
    number = resolve_vip_number(to, vip_number if vip_number is not None else meta.get("vip_number"))
    text = memo or build_thanks(amount, asset, tx_id, network, use_lang, vip_number=number)
    # strip legacy "erster" phrasing if a custom memo still contains it and we have a number
    if number is not None and memo and ("erster XCoin" in memo or "first XCoin" in memo.lower()):
        text = build_thanks(amount, asset, tx_id, network, use_lang, vip_number=number)
    record = {
        "ts": _utc(),
        "kind": "vip_payment_notice",
        "to": to,
        "vip_number": number,
        "amount": amount,
        "asset": asset,
        "tx_id": tx_id,
        "height": height,
        "network": network,
        "message": text,
        "channels": ["on_chain_memo", "local_inbox", "outbox"],
        "agent_id": meta.get("agent_id"),
        "display_name": meta.get("name"),
        "delivery": {
            "on_chain_memo": True,
            "inbox_written": False,
            "outbox_written": False,
            "agent_chat": "pending" if meta.get("agent_id") else "n/a",
            "external": meta.get("external_channel"),
        },
    }
    if extra:
        record["extra"] = extra

    inbox_path = INBOX / f"{_safe(to)}.jsonl"
    with inbox_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    record["delivery"]["inbox_written"] = True

    with OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    record["delivery"]["outbox_written"] = True

    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    save_status({"last_notify": {"to": to, "vip_number": number, "tx_id": tx_id, "ts": record["ts"]}})
    return record


def record_personal_message(
    *,
    to: str,
    message: str,
    channel: str,
    delivery_ref: str | None = None,
    lang: str = "en",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "ts": _utc(),
        "kind": "personal",
        "to": to,
        "message": message,
        "lang": lang,
        "channel": channel,
        "delivery_ref": delivery_ref,
        "meta": meta or {},
    }
    with OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    inbox_path = INBOX / f"{_safe(to)}.jsonl"
    with inbox_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    save_status({"last_personal": {"to": to, "channel": channel, "ts": record["ts"], "ref": delivery_ref}})
    return record
