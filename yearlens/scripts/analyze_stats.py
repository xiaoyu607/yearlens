"""Count included records; character counts are not token/word estimates."""
import argparse
from pathlib import Path
from common import load_json, write_private


def aggregate(messages):
    users = [row for row in messages if row["role"] == "user"]
    return {
        "active_conversations": len({row["conversation_id"] for row in messages}),
        "messages": len(messages), "user_messages": len(users),
        "assistant_messages": len(messages) - len(users),
        "active_days_all": len({row["date"] for row in messages}),
        "active_days_user": len({row["date"] for row in users}),
        "user_text_characters": sum(len(row["text"]) for row in users),
        "assistant_text_characters": sum(len(row["text"]) for row in messages if row["role"] == "assistant"),
        "user_messages_with_text": sum(bool(row["text"].strip()) for row in users),
    }


def analyze_stats(normalized):
    messages = normalized["messages"]
    return {
        "schema_version": "yearlens/0.1", "year": normalized["year"],
        "timezone": normalized["timezone"], "branches": normalized["branches"],
        "totals": aggregate(messages),
        "first_message_at": messages[0]["timestamp_local"] if messages else None,
        "last_message_at": messages[-1]["timestamp_local"] if messages else None,
        "months": [{"month": f"{normalized['year']:04d}-{month:02d}",
                    **aggregate([row for row in messages if row["month"] == f"{normalized['year']:04d}-{month:02d}"])}
                   for month in range(1, 13)],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_private(args.output, analyze_stats(load_json(args.input)))
