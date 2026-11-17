# 分支选择与歧义 / Branch selection and ambiguity

这些输入完全虚构。运行于仓库根目录；每个输出目录必须不存在。替换下列目录为新的私密路径。
These inputs are synthetic. Run from the repository root and choose new private output directories that do not exist.

```sh
python3 yearlens/scripts/yearlens.py examples/branches.synthetic.json --year 2025 --timezone Asia/Bangkok --branches current --output /tmp/yearlens-example-current
python3 yearlens/scripts/yearlens.py examples/branches.synthetic.json --year 2025 --timezone Asia/Bangkok --branches all --output /tmp/yearlens-example-all
python3 yearlens/scripts/yearlens.py examples/ambiguous.synthetic.json --year 2025 --timezone Asia/Bangkok --branches current --output /tmp/yearlens-example-ambiguous
python3 yearlens/scripts/check_report.py --report-dir /tmp/yearlens-example-ambiguous --expect-year 2025 --expect-timezone Asia/Bangkok --expect-branches current
```

在 `normalized.json` 中检查节点：明确分支的 `current` 包含 u、b，`all` 包含 u、a、b。替代答案不能视为同一条实际对话。歧义样例缺少 `current_node`，生成器和核对工具都退出 0，但 `audit.json` 报告 `ambiguous_current_branch` 并跳过会话；这不能证明原始对话为空。应由文件持有人检查原始分支，不能单凭通过核对或切换到 `all` 就认定完整。

In `normalized.json`, the explicit branch includes u and b with `current`, and u, a and b with `all`. Alternative answers do not form one actual conversation. The ambiguous example lacks `current_node`: both commands exit 0, but `audit.json` reports `ambiguous_current_branch` and skips the conversation. This does not show that the source had no conversations. The file owner must review the source; neither a successful check nor switching to `all` establishes completeness.

仅覆盖这两个简单构造，不证明真实导出兼容。 / These simple synthetic cases do not establish compatibility with real exports.
