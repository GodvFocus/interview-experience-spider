# 🕷️ 面经猎手 Interview Experience Spider

> 一键批量爬取**牛客网** + **小红书**的面试经验帖，自动生成带导航的 HTML 备考手册。

**完全开源 · 小白友好 · 支持 MCP（可在 Cursor/Claude 中直接调用）**

---

## 📸 效果预览

- 搜索关键词 → 自动抓取数十/数百篇面经原文
- 生成带领域导航、来源直链和固定浅色主题的本地 HTML 手册
- 支持作为 MCP 工具，让 AI 帮你自动收集和整理

---

## 🚀 快速开始（5分钟上手）

### 第一步：确认环境

```bash
python3 --version   # 需要 Python 3.10+
node --version      # 需要 Node.js 20+（小红书签名需要）
```

如果没有安装：
- Python：https://www.python.org/downloads/
- Node.js：https://nodejs.org/

### 第二步：克隆项目

```bash
git clone https://github.com/bcefghj/interview-experience-spider.git
cd interview-experience-spider
```

### 第三步：安装依赖

```bash
pip3 install -r requirements.txt
cd Spider_XHS_signing && npm install && cd ..
```

### 第四步：配置搜索关键词

复制配置模板，填写你的搜索关键词：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "nowcoder": {
    "queries": ["字节飞书后端实习", "字节飞书 golang 面经"],
    "max_pages": 3
  },
  "xiaohongshu": {
    "enabled": true,
    "cookies": {
      "a1": "你的a1 cookie",
      "web_session": "你的web_session cookie"
    },
    "queries": ["字节飞书面试", "字节飞书后端面经"]
  },
  "output": {
    "dir": "./output",
    "title": "字节飞书面试备考手册"
  }
}
```

> **如何获取小红书 Cookie？** 见 [docs/get-xhs-cookies.md](docs/get-xhs-cookies.md)

### 分类器配置

默认分类器是本机 Codex CLI。它复用 `codex login` 保存的 ChatGPT 登录态，消耗现有 Codex/ChatGPT 订阅额度，不需要 DeepSeek API key。先确认：

```bash
codex --version
codex login status
```

Windows 通过 npm 安装时，`PATH` 中的入口可能是 `codex.cmd`。报告生成器会使用查找到的完整绝对路径启动 CLI，避免裸命令在 Python 子进程中触发 `WinError 2`；`codex.command` 也可填写 CLI 的完整路径。

首次使用若尚未登录，请执行 `codex login`。`config.json` 中的默认配置如下：

```json
{
  "classifier": {
    "provider": "codex",
    "batch_max_articles": 5,
    "batch_max_chars": 12000,
    "max_workers": 4
  },
  "codex": {
    "command": "codex",
    "model": "gpt-5.6-luna",
    "reasoning_effort": "max",
    "timeout_seconds": 300
  }
}
```

默认固定使用 `gpt-5.6-luna`，并将 `reasoning_effort` 设为该模型支持的最高档 `max`。分类以非交互、临时会话、只读沙箱运行，并通过 JSON Schema 返回结构化结果。`max_workers` 控制同时处理的批次数；设为 1 可关闭并行，较大的值会缩短等待时间，但会增加同时消耗的订阅额度和触发限流的可能性。订阅方式不会产生 DeepSeek API 费用，但仍会占用 ChatGPT/Codex 方案额度；`max` 相比低档位通常耗时更长、消耗更多额度，额度耗尽时整次报告会失败。

如需切回 DeepSeek，可改为：

```json
{
  "classifier": {
    "provider": "deepseek",
    "batch_max_articles": 5,
    "batch_max_chars": 12000,
    "max_workers": 4
  },
  "deepseek": {
    "api_key": "你的 DeepSeek API key",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-flash"
  }
}
```

DeepSeek API key 只允许写入被 Git 忽略的 `config.json`，不得提交，也不会写入报告、请求日志或错误信息。两种后端都会在每次生成时重新分类，不使用历史缓存；文章总长度、模型结果和请求次数会影响耗时和额度或费用。

### 第五步：一键运行

```bash
python3 run_all.py
```

运行完成后，在 `output/` 目录找到：
- `面经备考手册.md` — Markdown 格式
- `面经备考手册.html` — 可直接用浏览器打开的固定浅色 HTML 手册

报告按以下固定顺序组织：Java语法、JUC、JVM、消息队列、MySQL、Redis、Spring全家桶、计算机网络、Agent、场景题、其他。题目只在主领域展示一次，其他领域标签仍保留在分类数据中；方案设计、故障排查、容量规划、一致性处理和工程权衡优先归入“场景题”。Markdown 保留所有参与分类的完整面经原文及页内来源锚点；HTML 不嵌入原文，题目旁的来源标题直接链接到来源平台原文。

---

## 📋 目录结构

```
interview-experience-spider/
├── README.md               # 本文件
├── config.example.json     # 配置模板（不含真实 Cookie）
├── requirements.txt        # Python 依赖
├── run_all.py              # 一键运行入口
├── scrape_nowcoder.py      # 牛客网爬虫
├── scrape_xhs.py           # 小红书爬虫（需要 Cookie）
├── generate_report.py      # MD/HTML 报告生成器
├── mcp_server.py           # MCP 服务（供 Cursor/Claude 调用）
├── Spider_XHS_signing/     # 小红书签名算法（来自 cv-cat/Spider_XHS）
│   ├── static/             # JS 签名文件
│   ├── xhs_utils/          # Python 工具函数
│   └── package.json        # Node.js 依赖
├── docs/                   # 详细文档
│   ├── get-xhs-cookies.md  # 如何获取小红书 Cookie
│   └── mcp-usage.md        # MCP 使用指南
└── output/                 # 输出目录（自动生成）
```

---

## 🍪 小红书 Cookie 获取方法

详细图文说明见 [docs/get-xhs-cookies.md](docs/get-xhs-cookies.md)，简要步骤：

1. 用 Chrome 打开 [www.xiaohongshu.com](https://www.xiaohongshu.com) 并登录
2. 按 `F12` 打开开发者工具 → 点击 `Application`（应用程序）标签
3. 左侧找到 `Cookies` → 点击 `https://www.xiaohongshu.com`
4. 找到并复制以下字段的值，填入 `config.json`：
   - `a1`
   - `web_session`
   - `webId`
   - `gid`

> ⚠️ Cookie 有效期约1天，过期后需要重新获取。请勿将含有 Cookie 的 config.json 上传到公开仓库！

---

## 🤖 MCP 使用方式（在 Cursor / Claude 中调用）

MCP（Model Context Protocol）让 AI 可以直接调用本工具，无需手动运行脚本。

### 安装到 Cursor

在 `~/.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "interview-spider": {
      "command": "python3",
      "args": ["/path/to/interview-experience-spider/mcp_server.py"],
      "env": {}
    }
  }
}
```

然后在 Cursor 聊天框中输入：
> "帮我搜索字节飞书后端实习的面经，生成备考手册"

### 可用 MCP 工具

| 工具名 | 功能 |
|--------|------|
| `search_nowcoder` | 搜索牛客网面经 |
| `search_xiaohongshu` | 搜索小红书面经 |
| `generate_report` | 生成 MD/HTML 报告 |
| `collect_all` | 一键全流程（搜索+抓取+生成报告）|

---

## ⚙️ 命令行使用

只爬牛客（不需要 Cookie）：

```bash
python3 scrape_nowcoder.py --query "字节飞书后端" --pages 5 --output output/nc.json
```

只爬小红书：

```bash
python3 scrape_xhs.py --query "字节飞书面试" --config config.json --output output/xhs.json
```

只生成报告（用已有数据）：

```bash
python3 generate_report.py --nc output/nc.json --xhs output/xhs.json --title "字节飞书备考"
```

---

## 🔧 常见问题

**Q: 牛客爬取失败？**
A: 检查网络，牛客 API 无需登录，偶发超时重试即可。

**Q: 小红书返回 `code=300011`？**
A: 缺少 `x-s/x-t` 签名。确认已在项目目录执行过 `cd Spider_XHS_signing && npm install`。

**Q: 小红书返回 `code=461` 需要验证？**
A: Cookie 已过期，需要重新获取。见 [docs/get-xhs-cookies.md](docs/get-xhs-cookies.md)。

**Q: 生成的 HTML 乱码？**
A: 用 Chrome 或 Safari 打开，确保浏览器编码为 UTF-8。

**Q: 为什么报告生成直接失败？**
A: 默认 Codex 后端请运行 `codex login status`，并检查 Codex CLI 是否在 `PATH`、订阅额度是否可用，以及 `codex.model` 是否为当前账号可用模型。使用 DeepSeek 时，再检查 `deepseek.api_key`、服务地址和模型名。任一分类后端失败时，系统都会停止整次生成，避免输出不完整报告。

**Q: 如何清理报告？**
A: 在 HTML 页面点击题目旁的“删除”，页面会软删除题目并实时更新统计；“撤销删除”只恢复最近一次操作。“下载清理版 HTML”会在浏览器本地生成独立文件，不会修改 JSON、原始 HTML、Markdown 或抓取数据。导出的清理版仍可继续编辑和再次导出，刷新原始报告会恢复未导出的删除状态。

**Q: 如何收藏题目？**
A: 点击题目后的 ☆ 加入“收藏夹”，星标变为 ★；再次点击即可取消收藏，原题和收藏夹中的星标同步更新。收藏夹保留问题和面经原文直链，同一来源的相同问题只显示一次，不重复计入报告统计。删除原题会暂时隐藏对应收藏，撤销删除后恢复。收藏通过 localStorage 保存在当前浏览器；清除浏览器数据、换设备或移动本地 HTML 文件后不保证保留。下载清理版 HTML 会把当前星标写入文件，导出的报告仍可继续收藏和取消收藏。浏览器限制存储时会显示提示，收藏操作仍在当前页面生效。

**Q: 报告是否截断文章或限制每个平台 30 篇？**
A: 不会。分类使用过滤后的所有文章和完整正文；动态分批只控制请求边界，单篇超过字符上限时仍会完整独占一个请求。

---

## 📄 免责声明

本项目仅供**个人学习和研究**使用，请遵守各平台用户协议，不得用于商业目的。爬取频率请控制合理，避免对服务器造成压力。

---

## 🙏 致谢

- 签名算法来自 [cv-cat/Spider_XHS](https://github.com/cv-cat/Spider_XHS)（MIT License）
- 牛客 API 参考 [jackYin888/nowcoder-mcp](https://github.com/jackYin888/nowcoder-mcp)

---

**⭐ 如果对你有帮助，欢迎 Star！**
