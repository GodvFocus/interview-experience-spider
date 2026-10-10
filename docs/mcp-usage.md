# MCP 使用指南

本工具支持作为 MCP（Model Context Protocol）服务运行，让 Cursor、Claude Desktop 等 AI 工具直接调用。

报告工具与命令行、一键运行共用 `config.json`。调用 `generate_report` 或 `collect_all` 前，请先配置 `deepseek`：

```json
{
  "deepseek": {
    "api_key": "你的 DeepSeek API key",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-flash",
    "batch_max_articles": 5,
    "batch_max_chars": 12000
  }
}
```

API key 只允许保存在被 Git 忽略的 `config.json`，不要放入 MCP 配置、日志或报告。key 缺失、鉴权失败或 DeepSeek 无法完成某篇面经的分类时，整次报告会失败，不会输出不完整结果。每次生成都会重新分类，不使用历史缓存；动态分批会影响请求次数、耗时和费用。

---

## 安装到 Cursor

### 第一步：找到 MCP 配置文件

文件路径：`~/.cursor/mcp.json`（没有就新建）

### 第二步：添加配置

```json
{
  "mcpServers": {
    "interview-spider": {
      "command": "python3",
      "args": ["/Users/你的用户名/Desktop/interview-experience-spider/mcp_server.py"]
    }
  }
}
```

> ⚠️ 把路径改为你的实际路径！

### 第三步：重启 Cursor

保存配置后，重启 Cursor，在 MCP 面板中确认 `interview-spider` 已加载。

---

## 在 Cursor 中使用

配置好后，直接在聊天框说：

```
帮我搜索字节飞书后端实习的面经，生成备考手册
```

```
搜索腾讯微信 Golang 面试经验，只保留后端相关的
```

```
查看我已经收集了多少面经
```

---

## 可用工具一览

### `search_nowcoder` — 搜索牛客网

```
search_nowcoder(query="字节飞书后端", pages=5)
```

### `search_xiaohongshu` — 搜索小红书

```
search_xiaohongshu(query="字节飞书面试", pages=3)
```

需要先配置 Cookie，见 [get-xhs-cookies.md](get-xhs-cookies.md)。

### `generate_report` — 生成报告

```
generate_report(title="字节飞书备考", filter_mode="backend")
```

生成结果包含按固定顺序排列的 Java语法、JUC、JVM、消息队列、MySQL、Redis、Spring全家桶、计算机网络、Agent、场景题、其他。所有参与分类的面经原文都会完整保存在 Markdown 末尾和 HTML 折叠附录中；HTML 页面支持软删除、撤销和浏览器本地导出清理版，不会修改抓取 JSON 或原始报告。

### `collect_all` — 一键全流程

```
collect_all(company="字节飞书", position="后端实习")
collect_all(company="腾讯", position="C++客户端", filter_mode="all")
```

### `list_collected` — 查看已有数据

```
list_collected(source="all")
```

---

## 安装到 Claude Desktop

配置文件路径：
- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

配置内容与 Cursor 相同。
