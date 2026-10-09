# 数据与统计口径 v0.1

## 支持范围

接受 conversations.json 的顶层会话数组或 `{"conversations": [...]}`。会话使用 `mapping` 节点图、`current_node`、可选 `id` / `conversation_id` 和 `title`。这是对提供的数据形状的支持，不保证未来导出格式不变。未知顶层格式或损坏节点会报错，不生成伪成功的零值报告。

仅 `message.author.role` 为 user/assistant 的可见消息进入统计，系统/工具/其他角色计入诊断后排除。仅抽取 `content.parts` 的字符串，不将附件字典或图片标识转成用户文本。无文本的消息计入消息数，但没有月度原文线索。附件内容不读取，语音有字符串转录时按文本处理。

隐藏消息（metadata.is_visually_hidden_from_conversation=true）、助手 analysis 通道、助手发给工具的调用（recipient 既不是 all 也不是空）、未完成的助手消息（存在非 finished_successfully 的 status）排除。字符数为提取文本的 Python len，包括空白和标点；不是中文词数、字数或 token 估计。

## 分支与去重

- 默认 current：沿 current_node 的 parent 追到根。缺失 current_node 而图有唯一叶节点时使用唯一分支并标注警告；多叶节点时跳过，不猜分支。
- 当前分支有循环/断裂时跳过整段会话。all 模式纳入各节点，明确标为包含替代分支，不能把不同分支拼成人生叙事。
- 去重键为 (conversation_id, node_id)，相同原始消息只计一次；相同键内容冲突时失败，不静默覆盖。
- 不按文本去重。不同时间的相同发言可能是真实重复；message_id 作为追溯字段，不用于跨会话合并。
- 缺失会话 ID 时对规范化会话 JSON 生成 SHA-256 ID 并标注合成 ID，不能当作官方聊天链接。

## 时间与覆盖范围

支持 Unix 秒时间戳（含数字字符串）和含时区的 ISO 8601。零时间戳有效。NaN、无限值、超出 datetime 范围的时间戳、无时区 ISO 文本均不猜测。缺失或无效 message.create_time 单独记为 undated，不借用会话日期，不进入年度统计。

按所选 IANA 时区转换后的**消息年份**筛选，不按会话创建年份。活跃会话指该年有至少一条纳入消息的会话。活跃天数分别给出用户与全部消息两种口径。月度会话数不可相加当作年度唯一会话数。

audit 保存输入 sha256（不保存绝对输入路径）、年份、时区及分支模式。始终列出 12 个月，包括零数据月份。覆盖范围仅描述提供的数据，不能据首末消息推断完整性。

## 输出

| 文件 | 内容 |
| --- | --- |
| normalized.json | 年内消息、时间、提取原文和来源 ID |
| audit.json | 文件指纹、设置、排除计数、带节点 ID 的警告 |
| stats.json | 年/月消息数、会话数、活跃天数、文本字符数 |
| timeline.json | 全部有文本的用户消息，按月排列的原文摘录 |
| report.md | 统计、诊断摘要、月度摘录与证据编号 |

所有输出默认私密。timeline 条目包含 evidence_id、label、status、mentioned_at、event_date=null、source、excerpt、字符偏移和截断标记。默认最多 280 字符，从提取文本开头取精确子串，不自动总结事件。证据编号只在当次报告内稳定，更换筛选条件后需重新核对。

输出目录必须尚不存在。验证完成才创建目录；POSIX 下目录 0700、文件 0600。一次载入 JSON，内存消耗可能为文件大小数倍。暂不支持流式读取、zip 输入、纯文本、附件内容、跨账号合并、自动脱敏。
