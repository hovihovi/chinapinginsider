#!/usr/bin/env python3
"""Pipeline queue manager for China Pinginsider."""

import json
import os
from datetime import datetime

QUEUE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "queue", "queue.json")
DRAFTS_DIR = os.path.join(os.path.dirname(QUEUE_PATH), "drafts")
ARTICLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "articles")

os.makedirs(DRAFTS_DIR, exist_ok=True)
os.makedirs(ARTICLES_DIR, exist_ok=True)


def _load():
    with open(QUEUE_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(QUEUE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_draft(title_en, title_fr, slug, sources, tag="News"):
    """Register a new draft in the queue."""
    data = _load()
    article_id = f"{datetime.now().strftime('%Y%m%d')}-{len(data['drafts']) + len(data['published']) + 1:03d}"
    entry = {
        "id": article_id,
        "status": "pending_review",
        "title_en": title_en,
        "title_fr": title_fr,
        "slug": slug,
        "tag": tag,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sources": sources,
        "discord_message_id": None,
        "created_at": datetime.now().isoformat()
    }
    data["drafts"].append(entry)
    _save(data)
    return article_id


def approve(article_id):
    """Mark a draft as approved."""
    data = _load()
    for d in data["drafts"]:
        if d["id"] == article_id:
            d["status"] = "approved"
            d["approved_at"] = datetime.now().isoformat()
            _save(data)
            return True
    return False


def reject(article_id, reason=None):
    """Mark a draft as rejected."""
    data = _load()
    for d in data["drafts"]:
        if d["id"] == article_id:
            d["status"] = "rejected"
            d["rejected_at"] = datetime.now().isoformat()
            d["reject_reason"] = reason
            _save(data)
            return True
    return False


def publish(article_id):
    """Move an approved draft to published."""
    data = _load()
    for i, d in enumerate(data["drafts"]):
        if d["id"] == article_id and d["status"] == "approved":
            d["status"] = "published"
            d["published_at"] = datetime.now().isoformat()
            data["published"].append(d)
            data["drafts"].pop(i)
            _save(data)
            return True
    return False


def pending():
    """List all pending drafts."""
    data = _load()
    return [d for d in data["drafts"] if d["status"] == "pending_review"]


def approved():
    """List all approved but not yet published."""
    data = _load()
    return [d for d in data["drafts"] if d["status"] == "approved"]


def status():
    """Print current queue status."""
    data = _load()
    pending_count = len([d for d in data["drafts"] if d["status"] == "pending_review"])
    approved_count = len([d for d in data["drafts"] if d["status"] == "approved"])
    rejected_count = len([d for d in data["drafts"] if d["status"] == "rejected"])
    published_count = len(data["published"])
    return {
        "pending": pending_count,
        "approved": approved_count,
        "rejected": rejected_count,
        "published": published_count
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: pipeline.py <status|add|approve|reject|publish> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        s = status()
        print(f"Pending: {s['pending']} | Approved: {s['approved']} | Rejected: {s['rejected']} | Published: {s['published']}")
    elif cmd == "pending":
        for d in pending():
            print(f"  [{d['id']}] {d['title_en']} ({d['slug']})")
    elif cmd == "approve" and len(sys.argv) >= 3:
        approve(sys.argv[2])
        print(f"Approved: {sys.argv[2]}")
    elif cmd == "reject" and len(sys.argv) >= 3:
        reason = sys.argv[3] if len(sys.argv) > 3 else None
        reject(sys.argv[2], reason)
        print(f"Rejected: {sys.argv[2]}")
    elif cmd == "publish" and len(sys.argv) >= 3:
        publish(sys.argv[2])
        print(f"Published: {sys.argv[2]}")
    else:
        print("Unknown command")
