"""Build monthly source leads, not inferred or confirmed life events."""
import argparse
from pathlib import Path
from common import load_json, write_private


def build_timeline(normalized, excerpt_limit=280):
    if excerpt_limit < 1:
        raise ValueError("excerpt_limit must be positive")
    entries = []
    for row in normalized["messages"]:
        if row["role"] != "user" or not row["text"].strip():
            continue
        excerpt = row["text"][:excerpt_limit]
        entries.append({
            "evidence_id": f"E{len(entries) + 1:06d}", "label": "聊天原文",
            "status": "unreviewed_source_lead", "mentioned_at": row["timestamp_local"],
            "event_date": None, "month": row["month"], "title": row["title"],
            "source": {key: row[key] for key in ("conversation_id", "node_id", "message_id")},
            "excerpt": excerpt, "excerpt_start": 0, "excerpt_end": len(excerpt),
            "truncated": len(row["text"]) > len(excerpt),
        })
    return {"schema_version": "yearlens/0.1", "year": normalized["year"],
            "timezone": normalized["timezone"], "branches": normalized["branches"],
            "notice": "用户原文线索，未确认为人生事件；月份为发言月份。",
            "months": [{"month": f"{normalized['year']:04d}-{month:02d}",
                        "entries": [entry for entry in entries if entry["month"] == f"{normalized['year']:04d}-{month:02d}"]}
                       for month in range(1, 13)]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_private(args.output, build_timeline(load_json(args.input)))
