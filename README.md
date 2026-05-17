# 🕷️ 面经猎手 Interview Experience Spider

> 一键批量爬取**牛客网** + **小红书**的面试经验帖，自动生成带导航的 HTML 备考手册。

**完全开源 · 小白友好 · 支持 MCP（可在 Cursor/Claude 中直接调用）**

---

## 📸 效果预览

- 搜索关键词 → 自动抓取数十/数百篇面经原文
- 生成带侧边导航栏、代码高亮、暗色主题的离线 HTML 手册
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

### 第五步：一键运行

```bash
python3 run_all.py
```

运行完成后，在 `output/` 目录找到：
- `面经备考手册.md` — Markdown 格式
- `面经备考手册.html` — 可直接用浏览器打开的离线手册

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

---

## 📄 免责声明

本项目仅供**个人学习和研究**使用，请遵守各平台用户协议，不得用于商业目的。爬取频率请控制合理，避免对服务器造成压力。

---

## 🙏 致谢

- 签名算法来自 [cv-cat/Spider_XHS](https://github.com/cv-cat/Spider_XHS)（MIT License）
- 牛客 API 参考 [jackYin888/nowcoder-mcp](https://github.com/jackYin888/nowcoder-mcp)

---

**⭐ 如果对你有帮助，欢迎 Star！**
