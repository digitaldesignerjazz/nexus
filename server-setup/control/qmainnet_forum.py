"""XCoin and Qnet Mainnet Forum — threads, VIP area, governance moderation."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/qnet-burn-work/forum")
STATE_PATH = ROOT / "state.json"
BOARDS_PATH = ROOT / "boards.json"
MSG_ROOT = Path("/workspace/qnet-burn-work/vip_messages")
VIP_DRAFT = Path("/workspace/qnet-burn-work/VIP_CANDIDATES_1000_DRAFT.json")
MKT_STATE = Path("/workspace/qnet-burn-work/marketplace/state.json")
GOVERNANCE_ID = "a526ad2c-fdb3-4d2c-830e-0353424101c3"

BLOCKLIST = [
    re.compile(p, re.I)
    for p in [
        r"\b(weapon|waffe|firearm|gun|drug|kokain|heroin|fentanyl|csam|child\s*porn|exploit\s*kit|ransomware|stolen\s*card|human\s*traffick)\b",
        r"\b(bombe|sprengstoff|illegale?\s*droge|darknet\s*drug)\b",
    ]
]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"live": True, "threads": {}, "posts": {}, "users": {}, "moderation_queue": [], "bans": {}, "stats": {}}


def _save(st: dict[str, Any]) -> None:
    st["updated_at"] = _utc()
    STATE_PATH.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n")


def boards() -> dict[str, Any]:
    if BOARDS_PATH.exists():
        return json.loads(BOARDS_PATH.read_text())
    return {"ok": False, "error": "boards_missing"}


def _board_map() -> dict[str, dict[str, Any]]:
    return {b["id"]: b for b in (boards().get("boards") or [])}


def _vip_accounts() -> set[str]:
    out: set[str] = set()
    if not VIP_DRAFT.exists():
        return out
    try:
        draft = json.loads(VIP_DRAFT.read_text())
        for c in draft.get("candidates") or []:
            for k in ("wallet_or_account", "qmainnet_address", "previous_wallet"):
                v = c.get(k)
                if v:
                    out.add(str(v))
            if c.get("name"):
                out.add(f"vip:{(c['name'] or '').lower().replace(' ', '-')}")
    except Exception:
        return out
    return out


def _scan(text: str) -> list[str]:
    hits = []
    for rx in BLOCKLIST:
        m = rx.search(text or "")
        if m:
            hits.append(m.group(0))
    return hits


def _notify(kind: str, to: str, message: str, extra: dict[str, Any] | None = None) -> None:
    MSG_ROOT.mkdir(parents=True, exist_ok=True)
    (MSG_ROOT / "inbox").mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": _utc(),
        "kind": kind,
        "to": to,
        "message": message,
        "channel": "forum_message_system",
        "extra": extra or {},
    }
    with (MSG_ROOT / "outbox.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    safe = re.sub(r"[^a-zA-Z0-9._+-]+", "_", to)[:120]
    with (MSG_ROOT / "inbox" / f"{safe}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with (MSG_ROOT / "FORUM_MESSAGES.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _mentions(text: str) -> list[str]:
    return re.findall(r"@([A-Za-z0-9_.:-]{2,64})", text or "")


def register(body: dict[str, Any]) -> dict[str, Any]:
    st = _load()
    addr = str(body.get("xcoin_address") or body.get("address") or "").strip()
    if not addr:
        return {"ok": False, "error": "xcoin_address_required"}
    if addr in (st.get("bans") or {}):
        return {"ok": False, "error": "account_banned"}
    vip = addr in _vip_accounts() or bool(body.get("vip")) or str(addr).startswith("vip:")
    user = {
        "address": addr,
        "display_name": str(body.get("display_name") or addr)[:80],
        "vip": vip,
        "vip_badge": "VIP" if vip else None,
        "registered_at": _utc(),
        "auth": "xcoin_address" + ("+vip_status" if vip else ""),
    }
    st.setdefault("users", {})[addr] = user
    st.setdefault("stats", {})["users"] = len(st["users"])
    _save(st)
    return {"ok": True, "user": user}


def status() -> dict[str, Any]:
    st = _load()
    b = boards()
    mkt_live = False
    if MKT_STATE.exists():
        try:
            mkt_live = bool(json.loads(MKT_STATE.read_text()).get("live"))
        except Exception:
            mkt_live = True
    return {
        "ok": True,
        "live": bool(st.get("live", True)),
        "name": st.get("name") or "XCoin and Qnet Mainnet Forum",
        "network": "qmainnet",
        "boards": b.get("boards"),
        "stats": st.get("stats"),
        "marketplace_linked": True,
        "marketplace_live": mkt_live,
        "governance_moderator": GOVERNANCE_ID,
        "auth": ["xcoin_address", "vip_status"],
        "message_system": True,
        "moderation_queue_len": len(st.get("moderation_queue") or []),
        "bans": len(st.get("bans") or {}),
    }


def list_threads(board_id: str | None = None) -> dict[str, Any]:
    st = _load()
    items = list((st.get("threads") or {}).values())
    if board_id:
        items = [t for t in items if t.get("board_id") == board_id and t.get("status") != "removed"]
    else:
        items = [t for t in items if t.get("status") != "removed"]
    items.sort(key=lambda t: t.get("updated_at") or t.get("created_at") or "", reverse=True)
    return {"ok": True, "count": len(items), "threads": items}


def create_thread(body: dict[str, Any]) -> dict[str, Any]:
    st = _load()
    author = str(body.get("author") or body.get("address") or "").strip()
    board_id = str(body.get("board_id") or "").strip()
    title = str(body.get("title") or "").strip()
    body_text = str(body.get("body") or body.get("text") or "").strip()
    bmap = _board_map()
    if board_id not in bmap:
        return {"ok": False, "error": "unknown_board", "boards": list(bmap)}
    if not author or not title or not body_text:
        return {"ok": False, "error": "author_title_body_required"}
    if author in (st.get("bans") or {}):
        return {"ok": False, "error": "account_banned"}
    # auto-register
    if author not in st.get("users", {}):
        register({"xcoin_address": author, "display_name": body.get("display_name")})
        st = _load()
    user = st["users"].get(author) or {}
    if bmap[board_id].get("vip_only") and not user.get("vip"):
        return {"ok": False, "error": "vip_only_board"}
    hits = _scan(f"{title}\n{body_text}")
    tid = f"thread_{uuid.uuid4().hex[:12]}"
    pid = f"post_{uuid.uuid4().hex[:12]}"
    listing_id = body.get("listing_id")
    thread = {
        "id": tid,
        "board_id": board_id,
        "title": title,
        "author": author,
        "author_vip": bool(user.get("vip")),
        "status": "removed" if hits else "open",
        "score": 0,
        "votes": {},
        "post_count": 1,
        "created_at": _utc(),
        "updated_at": _utc(),
        "listing_id": listing_id,
        "marketplace_linked": bool(listing_id) or bool(bmap[board_id].get("linked_marketplace")),
    }
    post = {
        "id": pid,
        "thread_id": tid,
        "board_id": board_id,
        "author": author,
        "author_vip": bool(user.get("vip")),
        "body": body_text,
        "score": 0,
        "votes": {},
        "created_at": _utc(),
        "status": "removed" if hits else "visible",
        "is_op": True,
    }
    st.setdefault("threads", {})[tid] = thread
    st.setdefault("posts", {})[pid] = post
    st["stats"]["threads"] = len(st["threads"])
    st["stats"]["posts"] = len(st["posts"])
    if hits:
        st.setdefault("moderation_queue", []).append(
            {"type": "thread", "id": tid, "hits": hits, "queued_at": _utc(), "status": "pending", "reviewer": GOVERNANCE_ID}
        )
        _notify("forum_moderation", "governance", f"Thread {tid} flagged: {hits}", {"thread_id": tid})
    else:
        _notify("forum_thread", author, f"Thread erstellt: {title} in {board_id}", {"thread_id": tid})
    for m in _mentions(body_text):
        _notify("forum_mention", m if m.startswith("vip:") or ":" in m else f"@{m}", f"Erwähnung in Thread {tid}: {title}", {"thread_id": tid})
    _save(st)
    (ROOT / "threads" / f"{tid}.json").write_text(json.dumps(thread, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "posts" / f"{pid}.json").write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n")
    return {"ok": True, "thread": thread, "post": post, "needs_governance": bool(hits)}


def reply(body: dict[str, Any]) -> dict[str, Any]:
    st = _load()
    tid = str(body.get("thread_id") or "")
    author = str(body.get("author") or body.get("address") or "").strip()
    text = str(body.get("body") or body.get("text") or "").strip()
    thread = (st.get("threads") or {}).get(tid)
    if not thread or thread.get("status") == "removed":
        return {"ok": False, "error": "thread_not_found"}
    if not author or not text:
        return {"ok": False, "error": "author_body_required"}
    if author in (st.get("bans") or {}):
        return {"ok": False, "error": "account_banned"}
    if author not in st.get("users", {}):
        register({"xcoin_address": author})
        st = _load()
        thread = st["threads"][tid]
    user = st["users"].get(author) or {}
    bmap = _board_map()
    board = bmap.get(thread["board_id"]) or {}
    if board.get("vip_only") and not user.get("vip"):
        return {"ok": False, "error": "vip_only_board"}
    hits = _scan(text)
    pid = f"post_{uuid.uuid4().hex[:12]}"
    post = {
        "id": pid,
        "thread_id": tid,
        "board_id": thread["board_id"],
        "author": author,
        "author_vip": bool(user.get("vip")),
        "body": text,
        "score": 0,
        "votes": {},
        "created_at": _utc(),
        "status": "removed" if hits else "visible",
        "is_op": False,
        "listing_id": body.get("listing_id") or thread.get("listing_id"),
        "rating": body.get("rating"),
    }
    st["posts"][pid] = post
    if not hits:
        thread["post_count"] = int(thread.get("post_count") or 0) + 1
        thread["updated_at"] = _utc()
    st["stats"]["posts"] = len(st["posts"])
    if hits:
        st.setdefault("moderation_queue", []).append(
            {"type": "post", "id": pid, "hits": hits, "queued_at": _utc(), "status": "pending", "reviewer": GOVERNANCE_ID}
        )
        _notify("forum_moderation", "governance", f"Post {pid} flagged: {hits}", {"post_id": pid})
    else:
        _notify("forum_reply", thread.get("author"), f"Neue Antwort in „{thread.get('title')}“ von {author}", {"thread_id": tid, "post_id": pid})
        for m in _mentions(text):
            _notify("forum_mention", m if (":" in m or m.startswith("vip:")) else f"@{m}", f"Erwähnung in {tid}", {"thread_id": tid, "post_id": pid})
    _save(st)
    (ROOT / "posts" / f"{pid}.json").write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n")
    return {"ok": True, "post": post, "needs_governance": bool(hits)}


def vote(body: dict[str, Any]) -> dict[str, Any]:
    st = _load()
    target = str(body.get("target") or "post")  # post|thread
    oid = str(body.get("id") or "")
    voter = str(body.get("voter") or body.get("address") or "").strip()
    try:
        val = int(body.get("value"))
    except (TypeError, ValueError):
        return {"ok": False, "error": "value_must_be_1_or_-1"}
    if val not in (1, -1) or not voter or not oid:
        return {"ok": False, "error": "invalid_vote"}
    bag = st.get("posts") if target == "post" else st.get("threads")
    item = (bag or {}).get(oid)
    if not item or item.get("status") in ("removed",):
        return {"ok": False, "error": "not_found"}
    votes = item.setdefault("votes", {})
    prev = votes.get(voter)
    if prev == val:
        return {"ok": True, "item": item, "note": "unchanged"}
    if prev in (1, -1):
        item["score"] = int(item.get("score") or 0) - int(prev)
    votes[voter] = val
    item["score"] = int(item.get("score") or 0) + val
    _save(st)
    return {"ok": True, "target": target, "item": {"id": oid, "score": item["score"]}}


def thread_detail(thread_id: str) -> dict[str, Any]:
    st = _load()
    thread = (st.get("threads") or {}).get(thread_id)
    if not thread:
        return {"ok": False, "error": "not_found"}
    posts = [p for p in (st.get("posts") or {}).values() if p.get("thread_id") == thread_id and p.get("status") != "removed"]
    posts.sort(key=lambda p: p.get("created_at") or "")
    return {"ok": True, "thread": thread, "posts": posts}


def governance_moderate(body: dict[str, Any]) -> dict[str, Any]:
    principal = str(body.get("principal") or "")
    if principal not in ("governance", GOVERNANCE_ID):
        return {"ok": False, "error": "acl_governance_only"}
    action = str(body.get("action") or "").lower()
    st = _load()
    if action == "remove_post":
        pid = str(body.get("post_id") or "")
        post = (st.get("posts") or {}).get(pid)
        if not post:
            return {"ok": False, "error": "post_not_found"}
        post["status"] = "removed"
        post["removed_by"] = "governance"
        post["removed_at"] = _utc()
        post["reason"] = str(body.get("reason") or "policy")
        _save(st)
        return {"ok": True, "post": post}
    if action == "remove_thread":
        tid = str(body.get("thread_id") or "")
        thread = (st.get("threads") or {}).get(tid)
        if not thread:
            return {"ok": False, "error": "thread_not_found"}
        thread["status"] = "removed"
        thread["removed_by"] = "governance"
        thread["removed_at"] = _utc()
        thread["reason"] = str(body.get("reason") or "policy")
        for p in (st.get("posts") or {}).values():
            if p.get("thread_id") == tid:
                p["status"] = "removed"
        _save(st)
        return {"ok": True, "thread": thread}
    if action == "ban":
        addr = str(body.get("address") or "")
        if not addr:
            return {"ok": False, "error": "address_required"}
        st.setdefault("bans", {})[addr] = {"banned_at": _utc(), "reason": str(body.get("reason") or "policy"), "by": "governance"}
        _save(st)
        _notify("forum_ban", addr, f"Account gesperrt: {body.get('reason') or 'policy'}", {})
        return {"ok": True, "banned": addr}
    if action == "unban":
        addr = str(body.get("address") or "")
        st.get("bans", {}).pop(addr, None)
        _save(st)
        return {"ok": True, "unbanned": addr}
    return {"ok": False, "error": "unknown_action"}
