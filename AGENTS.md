## Agent skills

### Issue tracker

Issue 以本地 Markdown 文件形式存放在 `.scratch/<feature>/`。详见 `docs/agents/issue-tracker.md`。

### Triage labels

未完成 Issue 使用 `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human` 和 `wontfix` 五个默认 triage 标签；完成实现与适用验收后使用终态 `resolved`。详见 `docs/agents/triage-labels.md` 和 `docs/agents/issue-tracker.md`。

### Domain docs

采用 single-context 布局：根目录使用一个 `CONTEXT.md`，ADR 存放于 `docs/adr/`。详见 `docs/agents/domain.md`。

## 运行环境

运行python文件请使用conda虚拟环境`any`。
