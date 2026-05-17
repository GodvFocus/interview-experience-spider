#!/usr/bin/env python3
"""
面经猎手 MCP Server
让 Cursor / Claude 可以直接调用本工具

配置方法（~/.cursor/mcp.json）：
{
  "mcpServers": {
    "interview-spider": {
      "command": "python3",
      "args": ["/path/to/interview-experience-spider/mcp_server.py"]
    }
  }
}

然后在 Cursor 中说："帮我搜索字节飞书后端面经"
"""
import os, sys, json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ 缺少 mcp 库，请运行: pip3 install mcp", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("面经猎手 Interview Spider")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
OUTPUT_DIR  = "output"


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ===== Tool 1: 搜索牛客网 =====
@mcp.tool()
def search_nowcoder(
    query: str,
    pages: int = 3,
    output_file: str = "output/nowcoder.json"
) -> str:
    """
    搜索牛客网面经，并保存到 JSON 文件。
    
    参数:
      query       - 搜索关键词，如"字节飞书后端实习"
      pages       - 搜索页数（默认3页，每页约20条）
      output_file - 结果保存路径
    
    返回:
      抓取结果摘要
    """
    try:
        from scrape_nowcoder import run
        posts = run(
            queries=[query],
            max_pages=pages,
            delay=0.8,
            output_file=output_file,
            verbose=False
        )
        titles = [f"• {p['title'][:40]}" for p in posts[:5]]
        return (
            f"✅ 牛客网搜索完成\n"
            f"关键词：{query}\n"
            f"共找到 {len(posts)} 篇面经\n"
            f"保存到：{os.path.abspath(output_file)}\n\n"
            f"前5篇标题：\n" + "\n".join(titles)
        )
    except Exception as e:
        return f"❌ 搜索失败: {e}"


# ===== Tool 2: 搜索小红书 =====
@mcp.tool()
def search_xiaohongshu(
    query: str,
    pages: int = 3,
    output_file: str = "output/xiaohongshu.json"
) -> str:
    """
    搜索小红书面经（需要在 config.json 中配置 Cookie）。
    
    参数:
      query       - 搜索关键词，如"字节飞书面试"
      pages       - 搜索页数
      output_file - 结果保存路径
    
    Cookie 配置见 docs/get-xhs-cookies.md
    """
    cfg     = _load_config()
    cookies = cfg.get("xiaohongshu", {}).get("cookies", {})
    if not cookies.get("a1") or "填入" in cookies.get("a1", ""):
        return (
            "❌ 小红书 Cookie 未配置\n"
            "请编辑 config.json，填入 a1/web_session/webId/gid\n"
            "获取方法见 docs/get-xhs-cookies.md"
        )
    try:
        from scrape_xhs import run
        posts = run(
            queries=[query],
            cookies=cookies,
            max_pages=pages,
            delay=0.8,
            output_file=output_file,
            verbose=False
        )
        titles = [f"• {p['title'][:40]}" for p in posts[:5]]
        return (
            f"✅ 小红书搜索完成\n"
            f"关键词：{query}\n"
            f"共找到 {len(posts)} 篇\n"
            f"保存到：{os.path.abspath(output_file)}\n\n"
            f"前5篇标题：\n" + "\n".join(titles)
        )
    except Exception as e:
        return f"❌ 搜索失败: {e}"


# ===== Tool 3: 生成报告 =====
@mcp.tool()
def generate_report(
    title: str = "面经备考手册",
    nc_file: str = "output/nowcoder.json",
    xhs_file: str = "output/xiaohongshu.json",
    filter_mode: str = "all"
) -> str:
    """
    根据已抓取的面经数据，生成 MD + HTML 报告。
    
    参数:
      title       - 报告标题
      nc_file     - 牛客数据 JSON 路径
      xhs_file    - 小红书数据 JSON 路径
      filter_mode - "all"（全部）或 "backend"（只保留后端/Go相关）
    
    返回:
      生成的文件路径
    """
    try:
        from generate_report import run
        results = run(
            nc_file=nc_file,
            xhs_file=xhs_file,
            output_dir=OUTPUT_DIR,
            title=title,
            filter_mode=filter_mode,
            formats=["md", "html"],
            verbose=False
        )
        lines = ["✅ 报告生成完成"]
        for fmt, path in results.items():
            lines.append(f"  {fmt.upper()} → {os.path.abspath(path)}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 生成失败: {e}"


# ===== Tool 4: 一键全流程 =====
@mcp.tool()
def collect_all(
    company: str = "字节飞书",
    position: str = "后端实习",
    filter_mode: str = "all"
) -> str:
    """
    一键全流程：自动构建搜索关键词 → 爬取牛客+小红书 → 生成 HTML 报告。
    
    参数:
      company     - 公司名，如"字节飞书"、"腾讯微信"
      position    - 岗位名，如"后端实习"、"golang开发"
      filter_mode - "all" 或 "backend"
    
    用法示例：
      collect_all("字节飞书", "服务端实习")
      collect_all("腾讯", "C++客户端")
    """
    cfg     = _load_config()
    cookies = cfg.get("xiaohongshu", {}).get("cookies", {})
    has_xhs = bool(cookies.get("a1") and "填入" not in cookies.get("a1", ""))

    queries = [
        f"{company}{position}",
        f"{company} {position} 面经",
        f"{company} {position} golang",
        f"{company} {position} 一面 二面",
    ]

    results_summary = [f"🚀 开始收集：{company} {position}\n"]

    # 爬取牛客
    try:
        from scrape_nowcoder import run as nc_run
        nc_posts = nc_run(
            queries=queries,
            max_pages=cfg.get("nowcoder", {}).get("max_pages", 3),
            delay=0.8,
            output_file=f"output/nowcoder.json",
            verbose=False
        )
        results_summary.append(f"✅ 牛客网：{len(nc_posts)} 篇")
    except Exception as e:
        results_summary.append(f"❌ 牛客网失败: {e}")
        nc_posts = []

    # 爬取小红书
    if has_xhs:
        try:
            from scrape_xhs import run as xhs_run
            xhs_posts = xhs_run(
                queries=queries,
                cookies=cookies,
                max_pages=cfg.get("xiaohongshu", {}).get("max_pages", 3),
                delay=0.8,
                output_file=f"output/xiaohongshu.json",
                verbose=False
            )
            results_summary.append(f"✅ 小红书：{len(xhs_posts)} 篇")
        except Exception as e:
            results_summary.append(f"❌ 小红书失败: {e}")
    else:
        results_summary.append("⚠️  小红书未配置 Cookie，已跳过")

    # 生成报告
    try:
        from generate_report import run as report_run
        title   = f"{company} {position} 面经备考手册"
        results = report_run(
            nc_file="output/nowcoder.json",
            xhs_file="output/xiaohongshu.json",
            output_dir=OUTPUT_DIR,
            title=title,
            filter_mode=filter_mode,
            formats=["md", "html"],
            verbose=False
        )
        for fmt, path in results.items():
            results_summary.append(f"📄 {fmt.upper()} → {os.path.abspath(path)}")
    except Exception as e:
        results_summary.append(f"❌ 报告生成失败: {e}")

    return "\n".join(results_summary)


# ===== Tool 5: 查看已有数据 =====
@mcp.tool()
def list_collected(
    source: str = "all"
) -> str:
    """
    查看已收集的面经数据摘要。
    
    参数:
      source - "nowcoder"、"xiaohongshu" 或 "all"
    """
    lines = []
    files = {
        "nowcoder":    "output/nowcoder.json",
        "xiaohongshu": "output/xiaohongshu.json",
    }
    for src, path in files.items():
        if source not in ("all", src):
            continue
        if os.path.exists(path):
            data = json.load(open(path, encoding="utf-8"))
            lines.append(f"📁 {src}（{len(data)} 篇）→ {os.path.abspath(path)}")
            for i, d in enumerate(data[:5]):
                lines.append(f"   {i+1}. {d.get('title','无标题')[:45]}")
            if len(data) > 5:
                lines.append(f"   ... 共 {len(data)} 篇")
        else:
            lines.append(f"📁 {src} → 暂无数据（{path} 不存在）")
        lines.append("")
    return "\n".join(lines) if lines else "暂无已收集的数据"


if __name__ == "__main__":
    mcp.run()
