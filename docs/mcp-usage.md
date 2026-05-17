# MCP 使用指南

本工具支持作为 MCP（Model Context Protocol）服务运行，让 Cursor、Claude Desktop 等 AI 工具直接调用。

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
