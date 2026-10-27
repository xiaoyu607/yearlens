# YearLens Skill v0.2.0

作者：姚明宇（xiaoyu607）与YearLens contributors，AI辅助开发。MIT许可证。该目录包含完整Skill、本地导出处理及只读报告核对工具；没有自动安装或账号历史读取。Created by 姚明宇 (xiaoyu607) and YearLens contributors with AI assistance, under MIT. This self-contained Skill processes a selected export and checks report consistency; it does not install itself or access account history.

使用仍受安全维护的Python 3.11+，仅标准库，无API key或pip包。具体已测环境和完整仓库见 https://github.com/xiaoyu607/yearlens 。Use a security-maintained Python 3.11+, standard library only, without an API key or pip packages. See the repository for the tested environment matrix.

在本目录运行，输入由用户明确选择，输出必须为新的私密目录。From this directory, use an explicitly selected input and a new private output directory:

```bash
python3 scripts/yearlens.py /path/to/conversations.json \
  --year 2025 --timezone Asia/Bangkok --output /path/to/private-report
python3 scripts/check_report.py --report-dir /path/to/private-report \
  --expect-year 2025 --expect-timezone Asia/Bangkok --expect-branches current
```

生成五文件：report.md、normalized.json、stats.json、timeline.json、audit.json。核对工具返回0/2，只检查文件、设置及消息/角色总数；预算16 MiB/文件、48 MiB合计，不检查原始导出完整性或事件真实性。默认当前分支，日期按所选IANA时区筛年，输出包含私人原文。Five private files are generated. The checker exits 0/2 and checks files, metadata and message/role totals, with read limits of 16 MiB per file and 48 MiB total. It does not establish source completeness or real-world events. The default is the current branch, filtered by message year in the selected IANA timezone.

从[SKILL.md](SKILL.md)开始，必要时读[核对范围](references/report_check.md)、[数据口径](references/data_contract.md)及[分析规则](references/analysis_rules.md)。原始数据和报告默认私密；无自动脱敏、附件读取、ZIP输入、流式处理、深度人生分析或网页。Python流程不联网，提供给AI的摘录仍进入模型会话。Start with SKILL.md and its references. Inputs and reports remain private. No automatic redaction, attachment reading, ZIP input, streaming, deep life analysis or website is included. Python processing is local; excerpts supplied to an AI enter the model conversation.

复制本文件夹到使用环境支持的Skill位置；实际安装和执行能力由环境决定。release.json只是公开文件打包清单，不是Agent Skills标准的要求。Copy this folder to the skill location supported by your environment. Installation and execution depend on that environment. release.json is a packaging allowlist, not an Agent Skills requirement.
