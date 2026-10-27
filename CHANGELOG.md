# 变更记录 / Changelog

## v0.2.0 — 2026-10-27

公开预览版 / Public preview.

- 新增独立只读 `yearlens/scripts/check_report.py`：五输出可读、四JSON设置及消息/角色总数一致性；固定简短诊断，拒绝重复键、非有限数及超预算输入。Added a standard-library read-only report checker with fixed diagnostics and explicit read budgets.
- 修复核对工具开发首版中指数溢出绕过非有限数检查的问题。Rejects positive/negative exponent overflow as well as NaN/Infinity constants.
- 同步仍受安全维护的Python 3.11+建议，公开实际测试范围和历史有限规模观测；不把历史数据当容量保证。Updated runtime guidance, actual validation scope and historical scale limitations.
- 增加可重跑的虚构报告核对测试、人工验收说明、自包含Skill打包清单和双语使用说明。Added reusable synthetic checker tests, manual acceptance documentation, Skill packaging and bilingual instructions.
- 数据schema保持 `yearlens/0.1`；原解析/统计/时间线五个脚本未改，未实现深度人生分析或交互网页。Data schema and the five original processing scripts are unchanged; deep life analysis and a web interface remain unimplemented.
- 真实导出兼容性仍未验证。Real-export compatibility remains unverified. See [validation](docs/validation.md).

## v0.1.1 — 2026 年 10 月 9 日

首个公开版本，包含 v0.1 的本地解析工具、年度统计、按月原文线索、Skill 文件、MIT 许可证和纯虚构示例。

- 修复 content.content_type 为列表、字典或数字时的输入处理。非法类型返回清楚的格式错误，主 CLI 退出码为 2，不生成报告、不修改输入。
- 增加一个 CLI 回归测试，覆盖 6 个有文本和无文本的非法输入场景。
- 完整 20 项测试通过。样例和测试全部使用纯虚构材料；真实导出兼容性仍需另行验证。
- 数据 schema 保持 yearlens/0.1。

## v0.1 — 2026 年 10 月 8 日

本地原型，未单独公开发布。提供导出解析、时区和分支筛选、统计、证据索引与 19 项测试。
