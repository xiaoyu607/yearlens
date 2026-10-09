# YearLens — AI 年度回忆录

版本 v0.1.1，2026 年 10 月 9 日。此版本包含导出解析、年度统计、月度原文线索，以及非法内容类型的错误处理修复。数据 schema 仍为 yearlens/0.1。完整变更见 [CHANGELOG](CHANGELOG.md)。

**这一年，你成为了怎样的人？**

YearLens 把你主动提供的聊天导出记录整理成可核验的年度统计和月度原文线索，让你重新阅读这一年。它不会自动获取账号历史，也不会把聊天频次当成人生重要性。

这是可运行的 v0.1.1 原型：本地 Python 工具 + 可复用 SKILL.md。三个原则：**有证据、不虚构、保护隐私**。深度人生分析、交互 Wrapped 页面和可安装 Plugin 是后续阶段。

## 快速运行

需要 Python 3.10+，不用 API key，不用安装 Python 包。在解压后的项目根目录运行：

```bash
python3 yearlens/scripts/yearlens.py examples/conversations.synthetic.json \
  --year 2025 --timezone Asia/Bangkok --output /tmp/yearlens-synthetic-2025
```

输出目录必须不存在。真实使用时把输入换成自己导出的 conversations.json，年份和 IANA 时区换成你的选择；输出存入源码目录以外的私密位置。默认时区是 UTC，不从所在地猜测。

```bash
python3 yearlens/scripts/yearlens.py /path/to/conversations.json \
  --year 2025 --timezone Asia/Shanghai --output /path/to/private-yearlens-2025
```

会得到五个文件：`report.md`、`stats.json`、`timeline.json`、`normalized.json`、`audit.json`。优先阅读数据质量说明；诊断中可能有无日期消息、未解析附件和被跳过的分支。

如需删除整段会话，重复添加 `--exclude-conversation CONVERSATION_ID`，并生成到另一个新目录。此操作不修改输入，也不会自动删除以前生成的报告。来源 ID 可在本地 normalized.json 找到；审阅其他内容与标题仍需人工完成。

## 作为 Skill 使用

`yearlens/` 就是完整 Skill 文件夹，包含 SKILL.md、scripts、references、agents/openai.yaml。复制到你使用的支持 Agent Skills 的环境的技能目录；具体安装入口由该环境决定。本项目不自动安装或修改用户配置。

示例请求：

> 使用 $yearlens 分析我提供的 conversations.json，回顾 2025 年，时区 Asia/Shanghai。先说明缺失数据，再整理带证据编号的月度线索。

官方文档说明了 [Skills 的工作流结构](https://developers.openai.com/plugins/concepts/skills)。本版本验证的是 Python CLI；不同 ChatGPT/Codex 环境能否安装技能、读取本地文件或运行脚本取决于产品及配置，不承诺所有普通 ChatGPT 会话都能直接执行它。只有上传你主动选择的记录，模型才有这些材料。把摘录交给模型分析时，摘录进入当前 AI 会话；“本地处理”指本项目的 Python 处理流程。

## 第一版的边界

- 统计依据每条消息的时间，不用会话创建日期代替；默认当前分支，重复来源去重但重复文字保留。
- 月度索引只含用户原文，不把助手回答当作用户人生；索引不是自动识别的人生事件。
- “聊天原文”“AI 推断”“用户确认”分开，事件日期与发言日期分开。
- 图像/附件不读取。没有可用文本的消息仍可计数；无日期消息不进入年度数据。
- 只支持已知 conversations.json 节点图及 conversations 包装，不支持 zip、整理后的纯文本或流式读取。大文件内存需求为文件大小数倍。
- 无自动脱敏、云服务、API 调用或发布功能。原始数据与报告默认私密，分享要先制作独立副本并审阅。

详细口径见 [数据约定](yearlens/references/data_contract.md) 和 [分析规则](yearlens/references/analysis_rules.md)。

## 验证

```bash
python3 -m unittest discover -s tests -v
```

测试与 examples 下的记录均为纯虚构材料，无真实用户数据。测试覆盖跨年/时区、分支、去重冲突、缺失日期、附件、隐藏消息、证据偏移、排除、输入不变、输出权限与 Markdown 转义。真实导出兼容性仍需用用户授权提供的文件验证。

## 开发顺序

1. v0.1：导出解析、真实统计、按月证据线索（已实现）。
2. v0.2：分批事件核验和个人变化分析，每个结论可追溯，保留不确定性。
3. v0.3：逐屏年度回顾网页、可编辑分享副本；之后再评估 Plugin 包装。

## 开源与贡献

MIT License。[项目仓库](https://github.com/xiaoyu607/yearlens)提供源码和版本记录。贡献流程见 [CONTRIBUTING](CONTRIBUTING.md)。提交问题时仅提供最小纯虚构复现，不上传 conversations.json 或个人报告。请不要把真实聊天“改几个名字”当作测试样例。
