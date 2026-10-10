# 06: 使用 Codex 订阅额度执行领域分类

**What to build:** 默认通过本机 `codex exec` 和当前 ChatGPT 登录态分类完整面经原文，以现有 Codex 订阅额度替代 DeepSeek API 按量费用；默认模型固定为 `gpt-5.6-luna`，reasoning effort 使用该模型支持的最高档 `max`；DeepSeek 保留为显式可选后端。

**Status:** resolved

- [x] 新增 Codex CLI 分类器，并使用严格 JSON Schema 约束文章标识、问题和领域。
- [x] Codex 在临时空目录、临时会话和只读沙箱中运行，不修改仓库。
- [x] 默认分类器切换为 Codex，DeepSeek 仍可通过 `classifier.provider` 选择。
- [x] 命令行、一键运行和 MCP 共用同一分类器选择与失败语义。
- [x] Codex 未安装、未登录、额度不可用和模型不可用时返回明确中文错误。
- [x] 示例配置和文档说明 Codex 登录、订阅额度消耗和 DeepSeek 切换方式。
- [x] 自动化测试覆盖 Codex 命令、完整正文、JSON Schema、登录失败和后端选择。
- [x] 使用真实 ChatGPT 登录态完成一篇最小面经的 Codex 分类烟测。
