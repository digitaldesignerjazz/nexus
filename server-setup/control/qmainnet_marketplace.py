"""qmainnet XCoin marketplace — legal digital & physical goods with escrow."""
from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/qnet-burn-work/marketplace")
STATE_PATH = ROOT / "state.json"
CATS_PATH = ROOT / "categories.json"
MSG_ROOT = Path("/workspace/qnet-burn-work/vip_messages")
VAULT_REF = Path("/workspace/qnet-burn-work/QMAINNET_VAULT_REF.json")

BLOCKLIST = [
    re.compile(p, re.I)
    for p in [
        r"\b(weapon|waffe|firearm|gun|drug|kokain|heroin|fentanyl|csam|child\s*porn|exploit\s*kit|ransomware|stolen\s*card|credit\s*card\s*dump|human\s*traffick)\b",
        r"\b(bombe|sprengstoff|illegale?\s*droge|darknet\s*drug)\b",
    ]
]

LEGAL_KINDS = {"digital", "physical"}
GOVERNANCE_ID = "a526ad2c-fdb3-4d2c-830e-0353424101c3"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "live": True,
        "network": "qmainnet",
        "asset": "XCoin",
        "escrow_account": "marketplace:escrow",
        "listings": {},
        "orders": {},
        "moderation_queue": [],
        "stats": {"listings": 0, "orders": 0, "escrow_held": 0.0, "released": 0.0},
        "vip_list_separate": True,
    }


def _save_state(st: dict[str, Any]) -> None:
    st["updated_at"] = _utc()
    STATE_PATH.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n")


def categories() -> dict[str, Any]:
    if CATS_PATH.exists():
        return json.loads(CATS_PATH.read_text())
    return {"ok": False, "error": "categories_missing"}


def _cat_index() -> dict[str, dict[str, Any]]:
    cats = categories().get("categories") or {}
    idx: dict[str, dict[str, Any]] = {}
    for kind, items in cats.items():
        for c in items:
            idx[c["id"]] = {**c, "kind": c.get("kind") or kind}
    return idx


def _scan_illegal(text: str) -> list[str]:
    hits = []
    for rx in BLOCKLIST:
        m = rx.search(text or "")
        if m:
            hits.append(m.group(0))
    return hits


def _notify(kind: str, to: str, message: str, extra: dict[str, Any] | None = None) -> None:
    MSG_ROOT.mkdir(parents=True, exist_ok=True)
    inbox = MSG_ROOT / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": _utc(),
        "kind": kind,
        "to": to,
        "message": message,
        "channel": "marketplace_message_system",
        "extra": extra or {},
        "vault_ref": str(VAULT_REF) if VAULT_REF.exists() else None,
    }
    with (MSG_ROOT / "outbox.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    safe = re.sub(r"[^a-zA-Z0-9._+-]+", "_", to)[:120]
    with (inbox / f"{safe}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (MSG_ROOT / "MARKETPLACE_MESSAGES.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def status() -> dict[str, Any]:
    st = _load_state()
    cats = categories()
    return {
        "ok": True,
        "live": bool(st.get("live", True)),
        "network": st.get("network", "qmainnet"),
        "asset": "XCoin",
        "escrow_account": st.get("escrow_account", "marketplace:escrow"),
        "vip_list_separate": True,
        "open_to": "all_xcoin_holders",
        "stats": st.get("stats"),
        "categories": cats.get("categories"),
        "moderation_queue_len": len(st.get("moderation_queue") or []),
        "governance_reviewer": GOVERNANCE_ID,
        "vault_integration": VAULT_REF.exists(),
        "message_system": True,
        "listing_example_path": str(ROOT / "samples" / "listing_example.json"),
    }


def list_listings(active_only: bool = True) -> dict[str, Any]:
    st = _load_state()
    items = list(st.get("listings", {}).values())
    if active_only:
        items = [x for x in items if x.get("status") == "active"]
    return {"ok": True, "count": len(items), "listings": items}


def create_listing(body: dict[str, Any]) -> dict[str, Any]:
    st = _load_state()
    idx = _cat_index()
    cat_id = str(body.get("category_id") or "")
    if cat_id not in idx:
        return {"ok": False, "error": "unknown_category", "categories": list(idx)}
    title = str(body.get("title") or "").strip()
    desc = str(body.get("description") or "").strip()
    seller = str(body.get("seller") or "").strip()
    try:
        price = float(body.get("price_xcoin") or body.get("price") or 0)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_price"}
    if not title or not seller or price <= 0:
        return {"ok": False, "error": "title_seller_price_required"}
    kind = idx[cat_id]["kind"]
    blob = f"{title}\n{desc}\n{body.get('tags') or ''}"
    hits = _scan_illegal(blob)
    lid = f"listing_{uuid.uuid4().hex[:12]}"
    listing = {
        "id": lid,
        "title": title,
        "description": desc,
        "category_id": cat_id,
        "kind": kind,
        "price_xcoin": price,
        "seller": seller,
        "status": "pending_review" if hits else "active",
        "moderation": "flagged_illegal_heuristic" if hits else "auto_pass",
        "moderation_hits": hits,
        "created_at": _utc(),
        "legal_only": True,
    }
    st.setdefault("listings", {})[lid] = listing
    st.setdefault("stats", {}).setdefault("listings", 0)
    st["stats"]["listings"] = len(st["listings"])
    if hits:
        st.setdefault("moderation_queue", []).append(
            {
                "listing_id": lid,
                "reason": "blocklist_hit",
                "hits": hits,
                "queued_at": _utc(),
                "reviewer": GOVERNANCE_ID,
                "status": "pending",
            }
        )
        _notify(
            "marketplace_moderation",
            "governance",
            f"Listing {lid} flagged for review: {hits}",
            {"listing_id": lid, "governance": GOVERNANCE_ID},
        )
    else:
        _notify(
            "marketplace_listing",
            seller,
            f"Listing live: {title} ({price:g} XCoin) in {cat_id}.",
            {"listing_id": lid},
        )
    _save_state(st)
    # persist listing file
    (ROOT / "listings" / f"{lid}.json").write_text(json.dumps(listing, indent=2, ensure_ascii=False) + "\n")
    return {"ok": True, "listing": listing, "needs_governance": bool(hits)}


def governance_review(body: dict[str, Any]) -> dict[str, Any]:
    """Approve or reject a flagged listing. principal must be governance."""
    principal = str(body.get("principal") or "")
    if principal not in ("governance", GOVERNANCE_ID):
        return {"ok": False, "error": "acl_governance_only"}
    lid = str(body.get("listing_id") or "")
    verdict = str(body.get("verdict") or "").upper()
    st = _load_state()
    listing = st.get("listings", {}).get(lid)
    if not listing:
        return {"ok": False, "error": "listing_not_found"}
    if verdict == "APPROVE":
        listing["status"] = "active"
        listing["moderation"] = "governance_approve"
    elif verdict == "REJECT":
        listing["status"] = "rejected"
        listing["moderation"] = "governance_reject"
    else:
        return {"ok": False, "error": "verdict_APPROVE_or_REJECT"}
    listing["governance_reason"] = str(body.get("reason") or "")
    listing["reviewed_at"] = _utc()
    for q in st.get("moderation_queue") or []:
        if q.get("listing_id") == lid and q.get("status") == "pending":
            q["status"] = verdict.lower()
            q["reviewed_at"] = _utc()
    _save_state(st)
    (ROOT / "listings" / f"{lid}.json").write_text(json.dumps(listing, indent=2, ensure_ascii=False) + "\n")
    return {"ok": True, "listing": listing}


def _tx(blockchain_tx, body: dict[str, Any]) -> dict[str, Any]:
    return blockchain_tx(body, network="qmainnet")


def place_order(body: dict[str, Any], blockchain_tx) -> dict[str, Any]:
    """Buyer pays into escrow; funds released only after delivery confirm."""
    st = _load_state()
    lid = str(body.get("listing_id") or "")
    buyer = str(body.get("buyer") or "").strip()
    listing = st.get("listings", {}).get(lid)
    if not listing or listing.get("status") != "active":
        return {"ok": False, "error": "listing_not_active"}
    if not buyer:
        return {"ok": False, "error": "buyer_required"}
    if buyer == listing.get("seller"):
        return {"ok": False, "error": "buyer_equals_seller"}
    price = float(listing["price_xcoin"])
    escrow = st.get("escrow_account", "marketplace:escrow")
    pay = _tx(
        blockchain_tx,
        {
            "from": buyer,
            "to": escrow,
            "amount": price,
            "asset": "XCoin",
            "type": "TRANSFER",
            "memo": f"marketplace escrow order for {lid}",
        },
    )
    if not pay.get("ok"):
        return {"ok": False, "error": "escrow_funding_failed", "tx": pay}
    oid = f"order_{uuid.uuid4().hex[:12]}"
    order = {
        "id": oid,
        "listing_id": lid,
        "title": listing.get("title"),
        "seller": listing.get("seller"),
        "buyer": buyer,
        "price_xcoin": price,
        "status": "escrow_held",
        "escrow_account": escrow,
        "escrow_tx": pay.get("tx_id"),
        "escrow_height": pay.get("height"),
        "created_at": _utc(),
        "vault_ref": str(VAULT_REF) if VAULT_REF.exists() else None,
    }
    st.setdefault("orders", {})[oid] = order
    st["stats"]["orders"] = len(st["orders"])
    st["stats"]["escrow_held"] = float(st["stats"].get("escrow_held") or 0) + price
    _save_state(st)
    (ROOT / "orders" / f"{oid}.json").write_text(json.dumps(order, indent=2, ensure_ascii=False) + "\n")
    msg = (
        f"Bestellung {oid} bestätigt: {listing.get('title')} für {price:g} XCoin. "
        f"Escrow-Tx {pay.get('tx_id')}. Freigabe nach Lieferbestätigung."
    )
    _notify("marketplace_order", buyer, msg, {"order_id": oid, "tx_id": pay.get("tx_id")})
    _notify("marketplace_order", listing.get("seller"), msg, {"order_id": oid, "tx_id": pay.get("tx_id")})
    return {"ok": True, "order": order, "escrow_tx": pay}


def confirm_delivery(body: dict[str, Any], blockchain_tx) -> dict[str, Any]:
    """Buyer (or governance override) confirms delivery → release escrow to seller."""
    st = _load_state()
    oid = str(body.get("order_id") or "")
    actor = str(body.get("actor") or "")
    order = st.get("orders", {}).get(oid)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if order.get("status") != "escrow_held":
        return {"ok": False, "error": "order_not_in_escrow", "status": order.get("status")}
    if actor not in (order.get("buyer"), "governance", GOVERNANCE_ID):
        return {"ok": False, "error": "only_buyer_or_governance_can_confirm"}
    escrow = order["escrow_account"]
    release = _tx(
        blockchain_tx,
        {
            "from": escrow,
            "to": order["seller"],
            "amount": float(order["price_xcoin"]),
            "asset": "XCoin",
            "type": "TRANSFER",
            "memo": f"marketplace escrow release {oid}",
        },
    )
    if not release.get("ok"):
        return {"ok": False, "error": "escrow_release_failed", "tx": release}
    order["status"] = "completed"
    order["release_tx"] = release.get("tx_id")
    order["release_height"] = release.get("height")
    order["completed_at"] = _utc()
    order["confirmed_by"] = actor
    st["stats"]["escrow_held"] = max(0.0, float(st["stats"].get("escrow_held") or 0) - float(order["price_xcoin"]))
    st["stats"]["released"] = float(st["stats"].get("released") or 0) + float(order["price_xcoin"])
    _save_state(st)
    (ROOT / "orders" / f"{oid}.json").write_text(json.dumps(order, indent=2, ensure_ascii=False) + "\n")
    msg = f"Escrow freigegeben für {oid}: {order['price_xcoin']:g} XCoin an {order['seller']} (Tx {release.get('tx_id')})."
    _notify("marketplace_release", order["seller"], msg, {"order_id": oid})
    _notify("marketplace_release", order["buyer"], msg, {"order_id": oid})
    return {"ok": True, "order": order, "release_tx": release}
