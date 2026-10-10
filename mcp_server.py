#!/usr/bin/env python3
"""
面经猎手 MCP Server。

该服务复用命令行报告入口，因此 MCP、命令行和一键运行使用同一份分类器
配置、来源过滤、动态分批与失败语义。

配置方法（~/.cursor/mcp.json）：
{
  "mcpServers": {
    "interview-spider": {
      "command": "python3",
      "args": ["/path/to/interview-experience-spider/mcp_server.py"]
    }
  }
}
"""

import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "❌ 未安装或版本不兼容的 mcp 库，请运行: pip3 install -r requirements.txt（需要 mcp 1.x）",
        file=sys.stderr,
    )
    raise SystemExit(1)


mcp = FastMCP("面经猎手 Interview Spider")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")


def _load_config() -> dict:
    """读取统一配置；配置错误交由具体工具返回中文错误。"""

    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return config if isinstance(config, dict) else {}


def _output_dir(config: dict) -> str:
    return config.get("output", {}).get("dir", "output")


def _report_error(error: Exception) -> str:
    from generate_report import ReportGenerationError

    if isinstance(error, ReportGenerationError):
        return f"❌ {error}"
    return f"❌ 生成失败: {error}"


@mcp.tool()
def search_nowcoder(
    query: str,
    pages: int = 3,
    output_file: str = "output/nowcoder.json",
) -> str:
    """搜索牛客网面经并保存 JSON。"""

    try:
        from scrape_nowcoder import run

        posts = run(
            queries=[query],
            max_pages=pages,
            delay=0.8,
            output_file=output_file,
            verbose=False,
        )
        titles = [f"• {post['title'][:40]}" for post in posts[:5]]
        return (
            f"✅ 牛客网搜索完成\n关键词：{query}\n共找到 {len(posts)} 篇面经\n"
            f"保存到：{os.path.abspath(output_file)}\n\n前5篇标题：\n"
            + "\n".join(titles)
        )
    except Exception as exc:
        return f"❌ 搜索失败: {exc}"


@mcp.tool()
def search_xiaohongshu(
    query: str,
    pages: int = 3,
    output_file: str = "output/xiaohongshu.json",
) -> str:
    """搜索小红书面经；Cookie 仍从 config.json 读取。"""

    config = _load_config()
    cookies = config.get("xiaohongshu", {}).get("cookies", {})
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
            verbose=False,
        )
        titles = [f"• {post['title'][:40]}" for post in posts[:5]]
        return (
            f"✅ 小红书搜索完成\n关键词：{query}\n共找到 {len(posts)} 篇\n"
            f"保存到：{os.path.abspath(output_file)}\n\n前5篇标题：\n"
            + "\n".join(titles)
        )
    except Exception as exc:
        return f"❌ 搜索失败: {exc}"


@mcp.tool()
def generate_report(
    title: str = "",
    nc_file: str = "output/nowcoder.json",
    xhs_file: str = "output/xiaohongshu.json",
    filter_mode: str = "all",
) -> str:
    """使用 config.json 的统一分类器配置生成 MD 与 HTML 报告。"""

    config = _load_config()
    output_config = config.get("output", {})
    report_title = title or output_config.get("title", "面经备考手册")
    output_dir = _output_dir(config)
    try:
        from generate_report import run

        results = run(
            nc_file=nc_file,
            xhs_file=xhs_file,
            output_dir=output_dir,
            title=report_title,
            filter_mode=filter_mode,
            formats=output_config.get("formats", ["md", "html"]),
            config=config,
            verbose=False,
        )
        lines = ["✅ 报告生成完成"]
        lines.extend(f"  {fmt.upper()} → {os.path.abspath(path)}" for fmt, path in results.items())
        return "\n".join(lines)
    except Exception as exc:
        return _report_error(exc)


@mcp.tool()
def collect_all(
    company: str = "字节飞书",
    position: str = "后端实习",
    filter_mode: str = "all",
) -> str:
    """一键搜索牛客与小红书，并使用同一份配置生成报告。"""

    config = _load_config()
    try:
        from generate_report import build_classifier

        build_classifier(config)
    except Exception as exc:
        return _report_error(exc)
    cookies = config.get("xiaohongshu", {}).get("cookies", {})
    has_xhs = bool(cookies.get("a1") and "填入" not in cookies.get("a1", ""))
    output_dir = _output_dir(config)
    os.makedirs(output_dir, exist_ok=True)
    nc_file = os.path.join(output_dir, "nowcoder.json")
    xhs_file = os.path.join(output_dir, "xiaohongshu.json")
    queries = [
        f"{company}{position}",
        f"{company} {position} 面经",
        f"{company} {position} golang",
        f"{company} {position} 一面 二面",
    ]
    summary = [f"🚀 开始收集：{company} {position}\n"]

    try:
        from scrape_nowcoder import run as nc_run

        nc_config = config.get("nowcoder", {})
        posts = nc_run(
            queries=queries,
            max_pages=nc_config.get("max_pages", 3),
            delay=nc_config.get("delay_seconds", 0.8),
            output_file=nc_file,
            verbose=False,
        )
        summary.append(f"✅ 牛客网：{len(posts)} 篇")
    except Exception as exc:
        summary.append(f"❌ 牛客网失败: {exc}")

    if has_xhs:
        try:
            from scrape_xhs import run as xhs_run

            xhs_config = config.get("xiaohongshu", {})
            posts = xhs_run(
                queries=queries,
                cookies=cookies,
                max_pages=xhs_config.get("max_pages", 3),
                delay=xhs_config.get("delay_seconds", 0.8),
                output_file=xhs_file,
                verbose=False,
            )
            summary.append(f"✅ 小红书：{len(posts)} 篇")
        except Exception as exc:
            summary.append(f"❌ 小红书失败: {exc}")
    else:
        summary.append("⚠️  小红书未配置 Cookie，已跳过")

    output_config = config.get("output", {})
    try:
        from generate_report import run

        results = run(
            nc_file=nc_file,
            xhs_file=xhs_file,
            output_dir=output_dir,
            title=f"{company} {position} 面经备考手册",
            filter_mode=filter_mode,
            formats=output_config.get("formats", ["md", "html"]),
            config=config,
            verbose=False,
        )
        summary.extend(f"📄 {fmt.upper()} → {os.path.abspath(path)}" for fmt, path in results.items())
    except Exception as exc:
        summary.append(_report_error(exc))
    return "\n".join(summary)


@mcp.tool()
def list_collected(source: str = "all") -> str:
    """查看已经收集的面经数据摘要。"""

    output_dir = _output_dir(_load_config())
    lines = []
    files = {
        "nowcoder": os.path.join(output_dir, "nowcoder.json"),
        "xiaohongshu": os.path.join(output_dir, "xiaohongshu.json"),
    }
    for source_name, path in files.items():
        if source not in ("all", source_name):
            continue
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                lines.append(f"📁 {source_name} → 数据文件无法读取（{path}）")
                continue
            lines.append(f"📁 {source_name}（{len(data)} 篇）→ {os.path.abspath(path)}")
            for index, item in enumerate(data[:5], start=1):
                lines.append(f"   {index}. {item.get('title', '无标题')[:45]}")
            if len(data) > 5:
                lines.append(f"   ... 共 {len(data)} 篇")
        else:
            lines.append(f"📁 {source_name} → 暂无数据（{path} 不存在）")
        lines.append("")
    return "\n".join(lines) if lines else "暂无已收集的数据"


if __name__ == "__main__":
    mcp.run()
