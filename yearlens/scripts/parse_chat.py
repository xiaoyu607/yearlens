"""Parse a supplied ChatGPT export without networking or attachment access."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from common import write_private


def timestamp(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        try:
            date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return date.astimezone(timezone.utc) if date.tzinfo else None
        except (ValueError, OverflowError):
            return None
    if not math.isfinite(number):
        return None
    try:
        return datetime.fromtimestamp(number, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def select_nodes(conversation, mapping, mode, warn):
    if mode == "all":
        return list(mapping)
    current = conversation.get("current_node")
    if current is None:
        parents = {node.get("parent") for node in mapping.values() if node.get("parent") is not None}
        leaves = set(mapping) - parents
        if len(leaves) != 1:
            warn("ambiguous_current_branch")
            return []
        current = next(iter(leaves))
        warn("inferred_unique_branch", current)
    selected, seen = [], set()
    while current is not None:
        if not isinstance(current, str) or current not in mapping:
            warn("broken_current_branch", str(current))
            return []
        if current in seen:
            warn("cyclic_current_branch", current)
            return []
        seen.add(current)
        selected.append(current)
        current = mapping[current].get("parent")
    return list(reversed(selected))


def parse_export(path, year, timezone_name="UTC", branches="current", exclude=()):
    if not 1 <= year <= 9999:
        raise ValueError("year must be between 1 and 9999")
    if branches not in {"current", "all"}:
        raise ValueError("branches must be current or all")
    zone = ZoneInfo(timezone_name)
    raw = Path(path).read_bytes()
    data = json.loads(raw.decode("utf-8-sig"))
    conversations = data.get("conversations") if isinstance(data, dict) else data
    if not isinstance(conversations, list):
        raise ValueError("Expected a conversation array or {'conversations': [...]} export")
    counts, warnings, messages, seen, undated, excluded_ids = Counter(), [], [], {}, set(), set()
    exclude = set(exclude)
    for index, conversation in enumerate(conversations):
        if not isinstance(conversation, dict) or not isinstance(conversation.get("mapping"), dict):
            raise ValueError(f"Conversation {index}: missing or invalid mapping")
        mapping = conversation["mapping"]
        if any(not isinstance(node, dict) or (node.get("parent") is not None and not isinstance(node["parent"], str))
               for node in mapping.values()):
            raise ValueError(f"Conversation {index}: invalid node or parent")
        cid = conversation.get("id") or conversation.get("conversation_id")
        synthesized = not isinstance(cid, str) or not cid
        if synthesized:
            canonical = json.dumps(conversation, ensure_ascii=False, sort_keys=True)
            cid = "synthetic-" + hashlib.sha256(canonical.encode()).hexdigest()

        def warn(code, node_id=None):
            item = {"code": code, "conversation_id": cid}
            if node_id is not None:
                item["node_id"] = node_id
            warnings.append(item)

        if cid in exclude:
            excluded_ids.add(cid)
            counts["excluded_conversation_entries"] += 1
            continue
        if synthesized:
            warn("synthetic_conversation_id")
        selected = select_nodes(conversation, mapping, branches, warn)
        counts["unselected_nodes"] += len(mapping) - len(selected)
        if mapping and not selected:
            counts["skipped_conversation_entries"] += 1
        for node_id in selected:
            message = mapping[node_id].get("message")
            if message is None:
                counts["structural_nodes"] += 1
                continue
            if not isinstance(message, dict):
                raise ValueError(f"Conversation {index}: invalid message at node {node_id}")
            key = (cid, node_id)
            fingerprint = json.dumps(message, sort_keys=True, ensure_ascii=False)
            if key in seen:
                if seen[key] != fingerprint:
                    raise ValueError(f"Conflicting duplicate source at conversation {index}, node {node_id}")
                counts["duplicate_messages"] += 1
                continue
            seen[key] = fingerprint
            author = message.get("author") or {}
            if not isinstance(author, dict):
                raise ValueError(f"Conversation {index}: invalid author at node {node_id}")
            role = author.get("role")
            if not isinstance(role, str) or role not in {"user", "assistant"}:
                counts["excluded_roles"] += 1
                continue
            metadata = message.get("metadata") or {}
            if not isinstance(metadata, dict):
                raise ValueError(f"Conversation {index}: invalid metadata at node {node_id}")
            if metadata.get("is_visually_hidden_from_conversation") is True or message.get("channel") == "analysis":
                counts["hidden_messages"] += 1
                continue
            if role == "assistant" and message.get("recipient") not in (None, "all"):
                counts["assistant_tool_calls"] += 1
                continue
            if role == "assistant" and message.get("status") not in (None, "finished_successfully"):
                counts["unfinished_assistant_messages"] += 1
                continue
            date = timestamp(message.get("create_time"))
            if date is None:
                counts["undated_messages"] += 1
                undated.add(cid)
                warn("missing_or_invalid_timestamp", node_id)
                continue
            try:
                local = date.astimezone(zone)
            except (ValueError, OverflowError):
                counts["undated_messages"] += 1
                undated.add(cid)
                warn("timestamp_out_of_local_range", node_id)
                continue
            if local.year != year:
                counts["outside_year_messages"] += 1
                continue
            content = message.get("content") or {}
            if not isinstance(content, dict):
                raise ValueError(f"Conversation {index}: invalid content at node {node_id}")
            content_type = content.get("content_type")
            if content_type is not None and not isinstance(content_type, str):
                raise ValueError(f"Conversation {index}: invalid content.content_type at node {node_id}")
            parts = content.get("parts", [])
            if not isinstance(parts, list):
                raise ValueError(f"Conversation {index}: invalid content.parts at node {node_id}")
            strings = [part for part in parts if isinstance(part, str)]
            text = "\n".join(strings)
            if len(strings) < len(parts) or (not strings and content_type not in {None, "text"}):
                counts["messages_with_unextracted_content"] += 1
                warn("unextracted_nontext_content", node_id)
            counts["included_messages"] += 1
            if not text.strip():
                counts["included_without_text"] += 1
            messages.append({
                "conversation_id": cid, "node_id": node_id,
                "message_id": message.get("id") if isinstance(message.get("id"), str) else None,
                "title": conversation.get("title") if isinstance(conversation.get("title"), str) else "",
                "role": role, "timestamp_utc": date.isoformat(),
                "timestamp_local": local.isoformat(), "date": local.date().isoformat(),
                "month": f"{local.year:04d}-{local.month:02d}", "text": text,
            })
    messages.sort(key=lambda row: (row["timestamp_utc"], row["conversation_id"], row["node_id"]))
    audit = {
        "schema_version": "yearlens/0.1", "input_sha256": hashlib.sha256(raw).hexdigest(),
        "year": year, "timezone": timezone_name, "branches": branches,
        "conversation_entries": len(conversations), "counts": dict(sorted(counts.items())),
        "excluded_conversation_ids": sorted(excluded_ids),
        "unmatched_exclusions": sorted(exclude - excluded_ids),
        "undated_conversations": len(undated), "warnings": warnings,
        "coverage": "Only supplied records; export completeness and real-world events are not verified.",
    }
    return {"schema_version": "yearlens/0.1", "year": year, "timezone": timezone_name,
            "branches": branches, "messages": messages}, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--branches", choices=("current", "all"), default="current")
    parser.add_argument("--exclude-conversation", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    args = parser.parse_args()
    normalized, audit = parse_export(args.input, args.year, args.timezone, args.branches, args.exclude_conversation)
    if args.output.resolve() == args.audit.resolve() or args.output.exists() or args.audit.exists():
        parser.error("Output and audit must be distinct, new files")
    write_private(args.output, normalized)
    write_private(args.audit, audit)


if __name__ == "__main__":
    main()
