# Domain 文档

本文说明 engineering skills 在探索代码库时如何读取本仓库的 domain 文档。

## 当前布局

本仓库采用 single-context 布局：

- 根目录的 `CONTEXT.md` 记录 domain 术语和上下文
- `docs/adr/` 存放 Architecture Decision Record（ADR）

这些内容按需创建，不要求在尚无有效信息时预先生成空文件。

## 探索代码前应读取

- 根目录的 `CONTEXT.md`
- 如果根目录存在 `CONTEXT-MAP.md`，则按照其中的指引读取与当前主题相关的各个 `CONTEXT.md`
- `docs/adr/` 中与即将处理区域相关的 ADR
- 在 multi-context 仓库中，还应检查 `src/<context>/docs/adr/` 中特定上下文的决策

如果上述文件不存在，应直接继续，不报告缺失，也不预先建议创建。`/domain-modeling` skill 会在术语或决策真正明确后按需创建这些文件。

## 文件结构

当前 single-context 布局：

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

如果仓库以后演变为 multi-context，可使用：

```text
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← 系统级决策
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← 特定上下文的决策
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## 使用 glossary 中的词汇

当输出中需要命名 domain 概念时，例如 issue 标题、重构建议、假设或测试名称，应使用 `CONTEXT.md` 定义的术语，不要改用 glossary 明确避免的同义词。

如果 glossary 尚未包含所需概念，应重新判断是否引入了项目未使用的语言；如果确属知识缺口，则记录下来供 `/domain-modeling` 处理。

## 标明 ADR 冲突

如果输出与现有 ADR 冲突，应明确指出，不得静默覆盖。例如：

> 与 ADR-0007（event-sourced orders）冲突，但值得重新讨论，因为……
