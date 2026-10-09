"""Behavioral checks against fully synthetic records; no private data."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "yearlens" / "scripts"))
from parse_chat import parse_export, timestamp
from analyze_stats import analyze_stats
from build_timeline import build_timeline
from yearlens import run, render_report


def message(node, text, date="2025-06-03T08:00:00Z", role="user", parent=None, **fields):
    return {"parent": parent, "message": {"id": node, "author": {"role": role},
            "create_time": date, "content": {"content_type": "text", "parts": [text]}, **fields}}


def conversation(nodes, current, cid="synthetic-test"):
    return {"id": cid, "title": "纯虚构测试", "mapping": nodes, "current_node": current}


class YearLensTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.folder = Path(self.workspace.name)
        self.input = self.folder / "input.json"

    def tearDown(self):
        self.workspace.cleanup()

    def parse(self, records, year=2025, zone="UTC", mode="current", exclude=()):
        self.input.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        return parse_export(self.input, year, zone, mode, exclude)

    def test_cli_rejects_invalid_content_type_without_traceback(self):
        for index, content_type in enumerate(([], {}, 123)):
            for parts in ([], ["纯虚构内容"]):
                with self.subTest(content_type=content_type, parts=parts):
                    item = conversation({"x": message("x", "")}, "x")
                    item["mapping"]["x"]["message"]["content"] = {
                        "content_type": content_type, "parts": parts}
                    self.input.write_text(json.dumps([item], ensure_ascii=False), encoding="utf-8")
                    before = self.input.read_bytes()
                    output = self.folder / f"invalid-{index}-{len(parts)}"
                    result = subprocess.run([
                        sys.executable, str(ROOT / "yearlens/scripts/yearlens.py"),
                        str(self.input), "--year", "2025", "--output", str(output)
                    ], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("invalid content.content_type", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())
                    self.assertEqual(self.input.read_bytes(), before)

    def test_year_is_per_message_in_selected_timezone(self):
        data = [conversation({
            "old": message("old", "旧年", "2024-12-31T17:30:00Z"),
            "new": message("new", "新年", "2025-12-31T17:30:00Z", parent="old"),
        }, "new")]
        utc, _ = self.parse(data)
        local, _ = self.parse(data, zone="Asia/Bangkok")
        self.assertEqual([row["node_id"] for row in utc["messages"]], ["new"])
        self.assertEqual([row["node_id"] for row in local["messages"]], ["old"])
        self.assertEqual(local["messages"][0]["date"], "2025-01-01")

    def test_current_and_all_branch_semantics(self):
        data = [conversation({"u": message("u", "开始"),
                              "a1": message("a1", "替代回复", role="assistant", parent="u"),
                              "a2": message("a2", "当前回复", role="assistant", parent="u")}, "a2")]
        normalized, audit = self.parse(data)
        all_nodes, _ = self.parse(data, mode="all")
        self.assertEqual({row["node_id"] for row in normalized["messages"]}, {"u", "a2"})
        self.assertEqual(len(all_nodes["messages"]), 3)
        self.assertEqual(audit["counts"]["unselected_nodes"], 1)

    def test_missing_ambiguous_branch_not_guessed(self):
        data = [conversation({"x": message("x", "甲"), "y": message("y", "乙")}, None)]
        normalized, audit = self.parse(data)
        self.assertEqual(normalized["messages"], [])
        self.assertEqual(audit["warnings"][0]["code"], "ambiguous_current_branch")

    def test_unique_branch_inferred_with_warning(self):
        normalized, audit = self.parse([conversation({"x": message("x", "甲")}, None)])
        self.assertEqual(len(normalized["messages"]), 1)
        self.assertEqual(audit["warnings"][0]["code"], "inferred_unique_branch")

    def test_cycle_and_missing_parent_exclude_entire_branch(self):
        for parent, code in (("x", "cyclic_current_branch"), ("missing", "broken_current_branch")):
            normalized, audit = self.parse([conversation({"x": message("x", "甲", parent=parent)}, "x")])
            self.assertEqual(normalized["messages"], [])
            self.assertEqual(audit["warnings"][0]["code"], code)

    def test_duplicate_source_dedup_but_repeated_text_kept(self):
        item = conversation({"x": message("x", "相同文字"),
                             "y": message("y", "相同文字", parent="x")}, "y")
        normalized, audit = self.parse([item, copy.deepcopy(item)])
        self.assertEqual(len(normalized["messages"]), 2)
        self.assertEqual(audit["counts"]["duplicate_messages"], 2)
        other = copy.deepcopy(item)
        other["id"] = "different-conversation"
        normalized, _ = self.parse([item, other])
        self.assertEqual(len(normalized["messages"]), 4)

    def test_conflicting_duplicate_fails(self):
        item = conversation({"x": message("x", "甲")}, "x")
        changed = copy.deepcopy(item)
        changed["mapping"]["x"]["message"]["content"]["parts"] = ["乙"]
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            self.parse([item, changed])

    def test_undated_never_inherits_conversation_timestamp(self):
        item = conversation({"x": message("x", "无日期", date=None)}, "x")
        item["create_time"] = 1748937600
        normalized, audit = self.parse([item])
        self.assertEqual(normalized["messages"], [])
        self.assertEqual(audit["counts"]["undated_messages"], 1)
        self.assertIsNotNone(timestamp(0))
        for value in (None, True, "2025-06-03", "nan", "inf", -1e100, "invalid"):
            self.assertIsNone(timestamp(value))

    def test_nontext_counted_without_fabricated_text(self):
        item = conversation({"x": message("x", "")}, "x")
        item["mapping"]["x"]["message"]["content"] = {
            "content_type": "multimodal_text", "parts": [{"asset_pointer": "synthetic-private-image"}]}
        normalized, audit = self.parse([item])
        self.assertEqual(analyze_stats(normalized)["totals"]["user_messages"], 1)
        self.assertEqual(normalized["messages"][0]["text"], "")
        self.assertEqual(build_timeline(normalized)["months"][5]["entries"], [])
        self.assertEqual(audit["counts"]["messages_with_unextracted_content"], 1)

    def test_hidden_unfinished_and_tools_not_user_evidence(self):
        data = [conversation({
            "u": message("u", "用户自述"),
            "a": message("a", "建议你搬家", role="assistant", parent="u"),
            "tool": message("tool", "工具输出", role="tool", parent="a"),
            "hidden": message("hidden", "隐藏", parent="tool", metadata={"is_visually_hidden_from_conversation": True}),
            "thinking": message("thinking", "思考", role="assistant", parent="hidden", channel="analysis"),
            "partial": message("partial", "未完成", role="assistant", parent="thinking", status="in_progress"),
        }, "partial")]
        normalized, audit = self.parse(data)
        stats = analyze_stats(normalized)
        self.assertEqual(stats["totals"]["messages"], 2)
        self.assertEqual(audit["counts"]["hidden_messages"], 2)
        self.assertEqual(audit["counts"]["unfinished_assistant_messages"], 1)
        leads = build_timeline(normalized)["months"][5]["entries"]
        self.assertEqual([entry["excerpt"] for entry in leads], ["用户自述"])

    def test_evidence_exact_and_dates_not_assumed(self):
        text = "明年想换工作；这只是计划。" * 50
        normalized, _ = self.parse([conversation({"x": message("x", text)}, "x")])
        entry = build_timeline(normalized)["months"][5]["entries"][0]
        self.assertEqual(entry["excerpt"], text[entry["excerpt_start"]:entry["excerpt_end"]])
        self.assertTrue(entry["truncated"])
        self.assertIsNone(entry["event_date"])
        self.assertEqual(entry["status"], "unreviewed_source_lead")
        self.assertEqual(entry["source"]["node_id"], "x")

    def test_empty_export_has_twelve_zero_months(self):
        normalized, _ = self.parse([])
        stats = analyze_stats(normalized)
        self.assertEqual(len(stats["months"]), 12)
        self.assertEqual(stats["totals"]["messages"], 0)
        self.assertIsNone(stats["first_message_at"])

    def test_exclusion_removes_content_from_all_deliverables(self):
        data = [conversation({"x": message("x", "SECRET_SAMPLE_ONLY")}, "x", "private"),
                conversation({"y": message("y", "可见")}, "y", "public")]
        normalized, audit = self.parse(data, exclude=("private", "not-found"))
        output = self.folder / "private-report"
        run(self.input, output, 2025, exclude=("private", "not-found"))
        self.assertEqual(len(normalized["messages"]), 1)
        self.assertEqual(audit["unmatched_exclusions"], ["not-found"])
        for path in output.iterdir():
            self.assertNotIn("SECRET_SAMPLE_ONLY", path.read_text())

    def test_cli_no_overwrite_input_immutable_and_permissions(self):
        self.parse([conversation({"x": message("x", "甲")}, "x")])
        before = hashlib.sha256(self.input.read_bytes()).hexdigest()
        output = self.folder / "report"
        cli = [sys.executable, str(ROOT / "yearlens/scripts/yearlens.py"), str(self.input),
               "--year", "2025", "--output", str(output)]
        first = subprocess.run(cli, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(hashlib.sha256(self.input.read_bytes()).hexdigest(), before)
        second = subprocess.run(cli, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual({p.name for p in output.iterdir()},
                         {"normalized.json", "audit.json", "stats.json", "timeline.json", "report.md"})
        if os.name == "posix":
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            self.assertTrue(all((p.stat().st_mode & 0o777) == 0o600 for p in output.iterdir()))

    def test_bad_format_does_not_create_output(self):
        self.input.write_text('{"unknown": []}')
        output = self.folder / "report"
        with self.assertRaises(ValueError):
            run(self.input, output, 2025)
        self.assertFalse(output.exists())

    def test_markdown_payload_is_literal(self):
        payload = '![x](https://example.invalid/pixel)\n<script>alert(1)</script>\n::directive{test="yes"}'
        item = conversation({"x": message("x", payload)}, "x")
        item["title"] = payload
        normalized, audit = self.parse([item])
        report = render_report(analyze_stats(normalized), build_timeline(normalized), audit)
        self.assertNotIn("![x]", report)
        self.assertNotIn("<script>", report)
        self.assertNotIn('::directive{', report)

    def test_tool_call_not_counted_as_visible_assistant_reply(self):
        data = [conversation({
            "u": message("u", "需要统计"),
            "call": message("call", "print(1)", role="assistant", parent="u", recipient="python"),
            "a": message("a", "结果是 1", role="assistant", parent="call", recipient="all"),
        }, "a")]
        normalized, audit = self.parse(data)
        self.assertEqual(analyze_stats(normalized)["totals"]["assistant_messages"], 1)
        self.assertEqual(audit["counts"]["assistant_tool_calls"], 1)

    def test_full_synthetic_fixture_counts_and_traceability(self):
        path = ROOT / "examples/conversations.synthetic.json"
        normalized, audit = parse_export(path, 2025, "Asia/Bangkok")
        stats = analyze_stats(normalized)
        self.assertEqual(stats["totals"]["messages"], 15)
        self.assertEqual(stats["totals"]["active_conversations"], 6)
        self.assertEqual(stats["totals"]["user_messages"], 8)
        self.assertEqual(stats["totals"]["assistant_messages"], 7)
        self.assertEqual(stats["totals"]["user_text_characters"], 175)
        self.assertEqual(sum(month["messages"] for month in stats["months"]), 15)
        self.assertEqual(audit["counts"]["undated_messages"], 1)
        source_rows = {(r["conversation_id"], r["node_id"]): r for r in normalized["messages"]}
        entries = [e for month in build_timeline(normalized)["months"] for e in month["entries"]]
        self.assertEqual(len(entries), 7)
        for entry in entries:
            key = (entry["source"]["conversation_id"], entry["source"]["node_id"])
            row = source_rows[key]
            self.assertEqual(row["role"], "user")
            self.assertEqual(entry["excerpt"], row["text"][entry["excerpt_start"]:entry["excerpt_end"]])

    def test_wrapper_and_missing_conversation_id(self):
        item = conversation({"x": message("x", "甲")}, "x")
        del item["id"]
        normalized, audit = self.parse({"conversations": [item, item]})
        self.assertEqual(len(normalized["messages"]), 1)
        self.assertTrue(normalized["messages"][0]["conversation_id"].startswith("synthetic-"))
        self.assertIn("synthetic_conversation_id", {w["code"] for w in audit["warnings"]})


if __name__ == "__main__":
    unittest.main()
