# 报告核对与人工验收 / Report checks and manual review

v0.2.0。工具：`scripts/check_report.py`，只读，无网络或第三方Python依赖。Tool: read-only, standard-library Python, no network access.

## 运行 / Invocation

在仓库根目录：From the repository root:

```bash
python3 yearlens/scripts/check_report.py --report-dir /path/to/private-report \
  --expect-year 2025 --expect-timezone Asia/Bangkok --expect-branches current
```

复制Skill后使用其 `scripts/check_report.py` 路径。`--report-dir` 必填；三个 `--expect-*` 可选。不提供时仅比较报告之间是否一致，不证明用户原本选择了什么。After copying the Skill, use its script path. The report directory is required; expected settings are optional. Omitting them checks mutual agreement, not the user's intended selection.

## 自动检查 / Automated scope

| 检查 / Check | 内容 / Behavior |
| --- | --- |
| 五文件 / Five files | report.md、normalized.json、stats.json、timeline.json、audit.json 非空普通文件、可读UTF-8 / Nonempty regular readable UTF-8 files |
| JSON | 四个顶层对象，schema_version=yearlens/0.1；拒绝重复键、NaN/Infinity及浮点指数溢出 / Four objects, supported schema, no duplicate keys or nonfinite numeric results |
| 设置 / Settings | 合法年份、IANA时区、current/all分支，四JSON一致，并匹配明确提供的期望 / Valid mutually consistent metadata, matching supplied expectations |
| 总数 / Totals | normalized消息数、stats消息/角色数和audit纳入数相符，计数为非负整数且不接受布尔值 / Matching message and user/assistant counts with nonnegative integer values, excluding booleans |

空消息列表可以通过；空报告的audit可能省略included_messages，此时按0核对。零消息不证明输入原本完整或真的没有记录。Empty message lists may pass. An omitted included_messages audit count is interpreted as zero, as emitted for a valid empty export. This does not establish input completeness.

成功退出0，status=internal_checks_passed，含必要计数和明确的未检查范围；失败退出2，status=internal_checks_failed、error为固定码。摘要不输出标题、摘录、来源ID或目录路径，仍应作为所选材料的派生信息私密保存。Success exits 0 with counts and explicit exclusions; failure exits 2 with a fixed error code. The summary omits titles, excerpts, source IDs and directory paths, but is still private derived information.

常见错误 / Common errors: missing_or_nonregular_report_file、report_json_invalid、duplicate_json_key、nonfinite_json_number、report_settings_disagree、report_settings_differ_from_expected、message_totals_disagree、message_role_counts_disagree、report_directory_over_budget。参数错误仅返回invalid_arguments；`--help`显示固定用法。Invalid arguments produce only invalid_arguments; --help shows static usage.

## 预算与目录前提 / Budgets and directory assumptions

- 单文件16 MiB，五文件合计48 MiB，恰好上限允许。Only the five fixed names are read, up to 16 MiB each and 48 MiB total, inclusive.
- 拒绝符号链接文件和符号链接报告目录；不递归、不打开原始导出。Rejects symlink files and a symlink report directory; no recursion or raw-export reads.
- 选已经完成写入且没有并发修改的本地目录；类型检查和读取不是原子操作，不提供并发路径替换隔离。Use a completed local report without concurrent writers; file checks and reads are not atomic or secure against concurrent path replacement.
- 字节预算不是内存上限；JSON解析仍会分配内存。Read-byte limits are not peak-memory limits.

## 仍需人工完成 / Manual acceptance

1. 确认原始文件、处理授权与原文件完整性；核对年份、时区、分支、排除选择。Confirm the selected input, authorization, completeness and intended filters.
2. 检查audit警告及排除原因；五文件齐全和计数相同不能证明没有遗漏。Review warnings and exclusions; file presence and equal totals do not rule out omissions.
3. 核对12个月统计、时间线来源和原文摘录，抽查跨年/时区/分支等实际边界。Check all twelve months, timeline sources and original excerpts, including relevant date/branch boundaries.
4. 区分聊天原文、AI推断、用户确认和计划；未确认线索不能当成已发生事件。Separate source statements, AI inference, confirmation and plans.
5. 检查私密输出位置和权限；分享前另存副本、删除敏感信息并审阅。Check output location and permissions, and review a separate sanitized copy before sharing.

本工具不执行月度/时间线字段完整契约、Markdown含义、权限、原始输入对照或现实意义核验；不宣称全面安全审计、真实兼容性或用户已经掌握。It does not validate the complete monthly/timeline schema, Markdown meaning, permissions, raw-export equivalence or real-world meaning. It is not a full security audit, compatibility proof or evidence of user learning.
