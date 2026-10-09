"""Create a private annual report from one explicitly supplied export."""
import argparse
from collections import Counter
import html
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

from analyze_stats import analyze_stats
from build_timeline import build_timeline
from common import write_private
from parse_chat import parse_export


COUNT_LABELS = {
    "assistant_tool_calls": "排除的助手工具调用",
    "duplicate_messages": "已去重的重复来源消息",
    "excluded_conversation_entries": "按用户设置排除的会话条目",
    "excluded_roles": "排除的工具/系统等角色消息",
    "hidden_messages": "排除的隐藏/分析消息",
    "included_messages": "纳入统计的消息",
    "included_without_text": "纳入统计但无可用文本的消息",
    "messages_with_unextracted_content": "含未提取附件内容的消息",
    "outside_year_messages": "年份范围以外的消息",
    "skipped_conversation_entries": "因分支问题跳过的会话条目",
    "structural_nodes": "无消息的结构节点",
    "undated_messages": "无有效日期的消息",
    "unfinished_assistant_messages": "排除的未完成助手回复",
    "unselected_nodes": "未纳入的分支/结构节点",
}
WARNING_LABELS = {
    "ambiguous_current_branch": "缺少当前分支且存在多个叶节点，已跳过",
    "broken_current_branch": "当前分支断裂，已跳过",
    "cyclic_current_branch": "当前分支存在循环，已跳过",
    "inferred_unique_branch": "缺少当前分支，按唯一叶节点选择",
    "missing_or_invalid_timestamp": "无有效消息日期，未纳入年度数据",
    "synthetic_conversation_id": "缺少会话 ID，生成了本地合成 ID",
    "timestamp_out_of_local_range": "日期无法转换到所选时区，已排除",
    "unextracted_nontext_content": "存在附件/非文本内容，未读取其内容",
}


def literal(value):
    # Escape untrusted Markdown links, HTML, remote images and directives.
    value = html.escape(str(value), quote=True)
    for character in ("\\", "`", "*", "_", "[", "]", "{", "}", "(", ")", "#", "+", "-", "!", "|", "~"):
        value = value.replace(character, "\\" + character)
    return value


def render_report(stats, timeline, audit):
    totals = stats["totals"]
    lines = [f"# YearLens · {stats['year']} 年度记录", "",
             "**私密报告 · 月度原文线索尚未确认为人生事件**", "",
             f"统计时区：{literal(stats['timezone'])}。范围：仅限用户提供且符合筛选条件的消息。",
             f"分支口径：{'当前分支' if stats['branches'] == 'current' else '所有分支（含编辑和重生成替代内容）'}。",
             "聊天时间不等于事件时间；用户自述不等于独立核实的现实事实。", "",
             "## 提供的记录中", "",
             f"- 活跃会话：{totals['active_conversations']}（该年有纳入消息的会话）",
             f"- 用户消息：{totals['user_messages']}；助手消息：{totals['assistant_messages']}",
             f"- 用户发言天数：{totals['active_days_user']}；全部消息活跃天数：{totals['active_days_all']}",
             f"- 用户文本字符：{totals['user_text_characters']}（含标点空白，非词数或 token）", "",
             "| 发言月份 | 会话数 | 用户消息 | 助手消息 | 用户发言天数 |", "| --- | ---: | ---: | ---: | ---: |"]
    for month in stats["months"]:
        lines.append(f"| {month['month']} | {month['active_conversations']} | {month['user_messages']} | {month['assistant_messages']} | {month['active_days_user']} |")
    lines += ["", "月度会话数可能重复，不能相加当作年度唯一会话数。", "", "## 数据质量", "",
              f"诊断警告：{len(audit['warnings'])} 条；处理计数见下方，来源详见 audit.json。", ""]
    for code, count in sorted(Counter(item["code"] for item in audit["warnings"]).items()):
        lines.append(f"- {WARNING_LABELS.get(code, literal(code))}：{count}")
    lines += ["", "处理计数：", ""]
    for reason, count in audit["counts"].items():
        lines.append(f"- {COUNT_LABELS.get(reason, literal(reason))}：{count}")
    if audit["unmatched_exclusions"]:
        lines += ["", f"有 {len(audit['unmatched_exclusions'])} 个排除 ID 未匹配输入；请检查 audit.json。"]
    lines += ["", "## 按月重读原文", "", "以下均为聊天原文线索，不进行重要性排名、成长评分或心理诊断。"]
    for month in timeline["months"]:
        lines += ["", f"### {month['month']}", ""]
        if not month["entries"]:
            lines += ["没有可用用户文本线索；不能据此推断该月没有人生事件。"]
        for entry in month["entries"]:
            source = entry["source"]
            lines += [f"#### {entry['evidence_id']} · {entry['mentioned_at'][:10]} · 聊天原文", "",
                      f"会话标题：{literal(entry['title']) or '未提供'}", "",
                      *["> " + literal(line) for line in entry["excerpt"].splitlines()], ""]
            if entry["truncated"]:
                lines += ["摘录已截断，请在 normalized.json 核对全文。", ""]
            lines += [f"来源：conversation={literal(source['conversation_id'])}；node={literal(source['node_id'])}；message={literal(source['message_id'] or '未提供')}。",
                      "事件发生日期：未知；确认状态：待核实。", ""]
    lines += ["## 隐私与下一步", "",
              "本报告及 JSON 包含私人原文、标题和标识。分享前另存副本，删除敏感内容与相关结论，并由用户审阅具体版本。",
              "程序没有联网；把原文提供给 AI 分析仍会让原文进入当前模型会话。", ""]
    return "\n".join(lines)


def run(input_path, output, year, timezone_name="UTC", branches="current", exclude=()):
    output = Path(output)
    if output.exists():
        raise ValueError("Output directory already exists; choose a new private directory")
    normalized, audit = parse_export(input_path, year, timezone_name, branches, exclude)
    stats = analyze_stats(normalized)
    timeline = build_timeline(normalized)
    report = render_report(stats, timeline, audit)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, value in (("normalized.json", normalized), ("audit.json", audit), ("stats.json", stats),
                        ("timeline.json", timeline), ("report.md", report)):
        write_private(output / name, value)
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--timezone", default="UTC", help="IANA timezone; defaults to UTC")
    parser.add_argument("--branches", choices=("current", "all"), default="current")
    parser.add_argument("--exclude-conversation", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        stats = run(args.input, args.output, args.year, args.timezone, args.branches, args.exclude_conversation)
    except (OSError, ValueError, ZoneInfoNotFoundError) as error:
        parser.exit(2, f"YearLens: {error}\n")
    print(f"YearLens {args.year}: {stats['totals']['messages']} included messages. Private report created.")


if __name__ == "__main__":
    main()
