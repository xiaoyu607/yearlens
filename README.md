# YearLens — AI 年度回忆录 / Annual chat review

v0.2.0 · 2026-10-27 · 公开预览版 / Public preview. [变更记录 / Changelog](CHANGELOG.md)

将用户主动提供的 ChatGPT `conversations.json` 整理为年度统计和月度原文线索。作者：姚明宇（[xiaoyu607](https://github.com/xiaoyu607)），与 YearLens contributors。代码及文档由 AI 辅助完成，验证使用纯虚构数据；没有真实用户效果或完整历史读取的保证。

YearLens turns an explicitly supplied ChatGPT export into annual statistics and monthly source excerpts. Created by 姚明宇 ([xiaoyu607](https://github.com/xiaoyu607)) and YearLens contributors, with AI assistance. Validation uses synthetic records; real-export compatibility remains unverified.

## 环境 / Requirements

使用仍受官方安全维护的 Python 3.11 或更新版本，仅标准库，无需 API key、pip 安装或网络访问。Python 3.10 已停止官方安全维护，不建议新安装使用；见 [Python 版本状态](https://devguide.python.org/versions/)。CLI 及报告核对工具的实际验证范围见[验证记录](docs/validation.md)，不推定所有版本或系统兼容。

Use a currently security-maintained Python 3.11 or newer. Both commands use only the standard library and require no API key, pip packages or network. Python 3.10 is end-of-life. See [validation](docs/validation.md) for the versions and systems actually tested. An IANA timezone database must be available to Python; a missing database is not silently replaced with a guessed timezone.

## 快速运行 / Quick start

在项目根目录运行。输出目录必须不存在，选择源码目录之外的新私密目录。下面的 `/tmp` 仅用于虚构演示。

Run from the project root, selecting a new private output directory outside this repository. It must not already exist. `/tmp` below is for the synthetic demonstration only.

```bash
python3 yearlens/scripts/yearlens.py examples/conversations.synthetic.json \
  --year 2025 --timezone Asia/Bangkok --output /tmp/yearlens-v020-synthetic
python3 yearlens/scripts/check_report.py \
  --report-dir /tmp/yearlens-v020-synthetic \
  --expect-year 2025 --expect-timezone Asia/Bangkok --expect-branches current
```

生成 `report.md`、`normalized.json`、`stats.json`、`timeline.json` 和 `audit.json`，样例为15条消息（8条用户、7条助手）和7条原文线索。先阅读数据质量说明，再核对日期与摘录。

The generator writes five files with statistics, normalized messages, excerpts and diagnostics. The example has 15 messages (8 user, 7 assistant) and 7 source leads. Review data quality, dates and excerpts before interpreting them.

真实使用只把生成命令的输入换成自己选择的文件，并明确年份、IANA时区和私密输出路径。默认时区 UTC，默认当前分支；`--branches all` 包括替代分支。可重复使用 `--exclude-conversation ID` 排除整段会话，再生成到新目录；不修改输入或删除历史报告。

For real use, explicitly select your export, year, IANA timezone and private output location. The defaults are UTC and the current branch; `--branches all` includes alternatives. Repeat `--exclude-conversation ID` to exclude whole conversations and generate into a new directory. Inputs and older reports are unchanged.

## 新增：只读报告核对 / New: read-only report checks

核对工具只读取显式目录中的五个固定文件，检查UTF-8、JSON顶层设置及消息/角色总数；拒绝重复键、非有限数、符号链接与超预算文件。成功退出0、失败退出2，stdout为简短JSON诊断，不回显摘录、标题、来源ID、路径或解析原文。

The checker reads only the five fixed files in the selected report directory. It checks readable UTF-8, JSON metadata and message/role totals, rejecting duplicate keys, nonfinite numbers, symlinks and oversized files. It exits 0 on success or 2 on failure, with a small JSON summary that omits excerpts, titles, source IDs, paths and parser input.

单文件16 MiB、五文件合计48 MiB是读取预算，不是峰值内存限制。运行时目录应已写入完成且不被并发修改。通过只表示上述内部一致性，不证明原始导出完整、事件真实或月度/时间线细节正确。详见[核对范围与人工验收 / checker scope and manual review](yearlens/references/report_check.md)。

The read budgets are 16 MiB per file and 48 MiB total, not a memory cap. Use a completed report with no concurrent writers. Passing means only these internal checks passed; it does not establish export completeness, real-world events or monthly/timeline correctness. See the linked scope and review checklist.

## Skill 使用 / Skill use

`yearlens/` 是可独立复制的 Skill 文件夹，包含 `SKILL.md`、脚本、引用文档、UI元数据、许可证和双语说明。将该文件夹放入所用环境支持的技能目录；安装入口和执行能力由环境决定，本项目不修改配置。

The `yearlens/` directory is a self-contained Skill. Copy it into the skill location supported by your environment. Installation and execution capabilities depend on that environment; this project does not install itself or change settings.

> 使用 $yearlens 分析我主动提供的 conversations.json，回顾2025年，时区 Asia/Shanghai。先检查数据质量与报告内部一致性，再整理带证据编号的月度线索。
>
> Use $yearlens with the export I explicitly provide for 2025 in Asia/Shanghai. Check data quality and report consistency before presenting monthly source leads.

## 边界与隐私 / Limits and privacy

- 只支持已知节点图JSON数组及 conversations 包装；不支持ZIP、纯文本、流式读取或附件内容。整个输入载入内存。 / Supports known node-graph JSON arrays and the conversations wrapper, not ZIPs, plain text, streaming or attachment contents. The input is loaded into memory.
- 以消息日期筛年，默认当前分支；按来源去重，不按文字去重。 / Filters by message date and current branch; deduplicates sources, not repeated text.
- 用户原文仅为线索，聊天日期不等于事件日期，助手建议不等于用户行动。 / User excerpts are leads; chat dates are not event dates, and assistant advice is not user action.
- 不自动获取账号历史，不做自动脱敏、心理诊断、深度人生分析或交互网页。 / No automatic account-history access, redaction, psychological diagnosis, deep life analysis or interactive website.
- 原始输入和所有报告默认私密；分享须另存独立副本并审阅。Python流程不联网，把摘录交给AI仍会让其进入模型会话。 / Inputs and reports are private. Review a separate copy before sharing. Python processing is local; excerpts given to an AI enter that model conversation.

详见[数据约定](yearlens/references/data_contract.md)和[分析规则](yearlens/references/analysis_rules.md)。See the data contract and analysis rules for exact semantics. Future analysis and web features remain unimplemented; v0.2.0 adds validation tooling rather than those features.

## 验证与贡献 / Tests and contributions

```bash
python3 -m unittest discover -s tests -v
```

测试和示例从空白编写，均为虚构材料。覆盖解析、日期/分支/去重、附件/隐藏消息、权限、转义及报告核对的正确和失败路径。真实导出仍需具体授权文件与人工核对；历史规模观测不当作容量保证。

Tests and examples are synthetic. They cover parsing, date/branch/deduplication rules, attachment/hidden-message handling, permissions, escaping and checker success/failure paths. Real exports still need explicit selection and manual validation. Historical scale observations are not capacity guarantees.

[MIT License](LICENSE) · [贡献指南 / Contributing](CONTRIBUTING.md) · [发布页 / Releases](https://github.com/xiaoyu607/yearlens/releases)

请只提交最小虚构复现，不上传真实聊天、报告或把真实内容改几个名字后的样例。Submit minimal synthetic reproductions, never real chats, reports or lightly renamed private data.
