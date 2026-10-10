# Issue tracker：本地 Markdown

本仓库的 issue 和 spec 以 Markdown 文件形式存放在 `.scratch/`。

## 约定

- 每个功能使用一个目录：`.scratch/<feature-slug>/`
- Spec 文件为 `.scratch/<feature-slug>/spec.md`
- 每个实现任务使用单独的 issue 文件，路径为 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`
- Issue 从 `01` 开始编号，不使用单个合并的 tickets 文件
- 未完成 issue 的 triage 状态记录在顶部附近的 `Status:` 行中，角色字符串见 `triage-labels.md`
- 实现与适用验收全部完成后，将 `Status:` 改为 `resolved`；`resolved` 是终态，不属于 triage 标签
- 评论和讨论历史追加到文件末尾的 `## Comments` 标题下

## 当 skill 要求“发布到 issue tracker”时

在 `.scratch/<feature-slug>/` 下创建新文件；目录不存在时一并创建。

## 当 skill 要求“获取相关 ticket”时

读取所引用路径中的文件。用户通常会直接提供文件路径或 issue 编号。

## Wayfinding 操作

供 `/wayfinder` 使用。Map 文件对应多个 ticket 子文件。

- **Map**：`.scratch/<effort>/map.md`，用于记录 Notes、Decisions-so-far 和 Fog
- **Ticket 子文件**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 开始编号，并在正文中记录问题
- `Type:` 行记录 ticket 类型：`research`、`prototype`、`grilling` 或 `task`
- `Status:` 行记录 `claimed` 或 `resolved`
- **阻塞关系**：在文件顶部附近使用 `Blocked by: NN, NN`；列出的所有 ticket 均为 `resolved` 后，该 ticket 才解除阻塞
- **Frontier**：扫描 `.scratch/<effort>/issues/`，找到状态为 open、未阻塞且未认领的文件；编号最小者优先
- **认领**：开始工作前，将 `Status:` 设置为 `claimed` 并保存
- **解决**：将答案追加到 `## Answer` 标题下，将 `Status:` 设置为 `resolved`，再把上下文指针（摘要与链接）追加到 `map.md` 的 Decisions-so-far 中
