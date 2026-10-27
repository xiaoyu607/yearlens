# 验证记录 / Validation record

v0.2.0 · 2026-10-27。由AI助手执行，全部功能输入为从空白编写的虚构数据。Run by an AI assistant using synthetic inputs only. This record does not represent user learning, real users or accepted community contributions.

## 本版本 / This version

| 本机环境 / Local environment | 结果 / Result |
| --- | --- |
| macOS 27.0.1 / arm64 / Python 3.11.17 | 59 tests passed, no skips |
| macOS 27.0.1 / arm64 / Python 3.14.8 | 59 tests passed, no skips |

在仓库根目录运行 / Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

20项原产品测试加39项独立报告核对测试。新增场景覆盖15/1000/0消息报告、缺文件、总数/角色/设置冲突、期望不符、JSON损坏/重复键/错误类型、非有限数与指数溢出、非法编码、符号链接、FIFO、无关文件不读取、16 MiB单文件和48 MiB合计边界。每次核对检查报告文件不变及诊断不回显虚构标记/目录。

The suite includes the original 20 product tests and 39 checker tests. It covers valid 15/1000/0-message reports, missing files, count/metadata mismatches, malformed and duplicate-key JSON, invalid structures, nonfinite and overflowing numbers, encoding errors, symlinks, FIFOs, ignored extra files, and the 16 MiB/file and 48 MiB/total byte boundaries. Checker calls assert report files are unchanged and diagnostics omit the synthetic marker and selected directory.

FIFO/symlink tests may skip where those features are unavailable; the local results above had no skips. The suite generates its own temporary inputs/reports and does not access private exports. Passing in these two local interpreters does not imply Windows, Linux or every Python version has been tested. Both commands need a usable IANA timezone database.

原有五个处理脚本与v0.1.1相同，数据schema仍为yearlens/0.1。新工具核对内部关系，不证明真实导出兼容或原始数据完整。The five original processing scripts are unchanged from v0.1.1. The data schema remains yearlens/0.1. The new tool checks internal consistency, not real-export compatibility or source completeness.

## 历史规模观测 / Historical scale observation

以下是2026-10-21对v0.1.1原CLI的本机单次结果，未在本版本重测。The following are single local observations of the original v0.1.1 CLI on 2026-10-21, not rerun or presented as measurements of the new checker.

| 消息 / Messages | 输入字节 / Input bytes | CLI墙钟秒 / Wall seconds | CLI峰值RSS / Peak RSS |
| ---: | ---: | ---: | ---: |
| 1,000 | 296,431 | 0.085658 | 28.0625 MiB |
| 10,000 | 2,964,301 | 0.309678 | 63.0625 MiB |

Python 3.14.8，macOS 27.0.1/arm64；每会话100节点单链，用户/助手交替，每消息128字符（134 UTF-8字节），无附件、隐藏消息或复杂分支。墙钟从启动CLI子进程到退出，峰值RSS来自macOS RUSAGE_CHILDREN、单位字节，包含解释器，不含生成/验证进程。每规模一轮，无缓存控制、预热或统计分布；不能推出真实容量、百分位延迟或跨平台性能保证。

Python 3.14.8 on macOS 27.0.1/arm64; 100-node linear conversations, alternating user/assistant roles, 128 characters (134 UTF-8 bytes) per message, without attachments, hidden messages or complex branches. Wall time spans child CLI startup to exit; peak RSS is macOS RUSAGE_CHILDREN in bytes, including the interpreter and excluding the generator/validator. One trial per size, without cache controls, warm-up or distribution estimates. These results are not a capacity, latency-percentile or cross-platform guarantee.

## 发布包与未验证项 / Packages and unverified scope

发布包含完整源码ZIP、独立Skill ZIP及SHA256SUMS.txt。完整包含测试和示例，独立Skill包只含其运行资源；Skill包的RELEASE-MANIFEST.json列出所选文件摘要，release.json为打包约定。哈希用于完整性核对，不是数字签名。Release assets include the repository ZIP, standalone Skill ZIP and SHA256SUMS.txt. The full package includes tests/examples; the Skill package includes only its runtime resources and hash manifest. Hashes support integrity checks, not signatures.

真实导出、用户安装和理解、所有操作系统、并发路径替换攻击、完整月度/时间线契约及全面安全审计未验证。原始数据、私人维护日志、个人资料、解释器、依赖缓存和未提交的社区草稿不在公开包中。Real exports, actual user installation/understanding, all platforms, concurrent path replacement, the complete monthly/timeline schema and a comprehensive security audit remain unverified. Private exports, maintenance logs, personal records, runtimes, caches and unsubmitted community drafts are excluded.
