#!/usr/bin/env python3
"""
一键运行：搜索、抓取并生成按知识领域整理的报告。

用法：
  python3 run_all.py                  # 使用 config.json
  python3 run_all.py --filter backend # 只保留后端相关
  python3 run_all.py --skip-nc        # 跳过牛客，只爬小红书
  python3 run_all.py --skip-xhs       # 跳过小红书，只爬牛客
  python3 run_all.py --report-only    # 使用已有 JSON 只生成报告
"""

import argparse
import json
import os
import subprocess
import sys


def _open_in_browser(path: str) -> None:
    """尽力打开本地 HTML，不影响报告生成结果。"""

    try:
        if os.name == "nt":
            os.startfile(os.path.abspath(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def check_env(config_path: str, need_xhs: bool = True) -> None:
    """检查一键运行所需的依赖和配置文件。"""

    print("🔍 检查运行环境...")
    missing = []
    required_packages = ["requests"] + (["execjs"] if need_xhs else [])
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    if missing:
        print(f"❌ 缺少 Python 依赖: {', '.join(missing)}")
        print(f"   请运行: pip3 install {' '.join(missing)}")
        raise SystemExit(1)

    if need_xhs:
        node_modules = os.path.join(
            os.path.dirname(__file__), "Spider_XHS_signing", "node_modules"
        )
        if not os.path.exists(node_modules):
            print("⚠️  小红书签名模块未初始化")
            print("   正在自动初始化...")
            signing_dir = os.path.join(os.path.dirname(__file__), "Spider_XHS_signing")
            result = subprocess.run(
                ["npm", "install"], cwd=signing_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"   ❌ npm install 失败: {result.stderr}")
                print("   请手动运行: cd Spider_XHS_signing && npm install")
            else:
                print("   ✅ Node.js 依赖安装完成")

    if not os.path.exists(config_path):
        print(f"⚠️  未找到 {config_path}")
        if os.path.exists("config.example.json"):
            print("   提示：请先复制 config.example.json 为 config.json 并填写配置")
        raise SystemExit(1)

    print("✅ 环境检查通过\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="面经猎手 - 一键运行")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--filter", choices=["all", "backend"], help="覆盖配置中的过滤模式")
    parser.add_argument("--skip-nc", action="store_true", help="跳过牛客网爬取")
    parser.add_argument("--skip-xhs", action="store_true", help="跳过小红书爬取")
    parser.add_argument("--report-only", action="store_true", help="只生成已有数据的报告")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    check_env(args.config, need_xhs=not args.report_only and not args.skip_xhs)

    with open(args.config, encoding="utf-8") as handle:
        cfg = json.load(handle)

    from generate_report import DeepSeekClassifier, ReportGenerationError, get_deepseek_config

    try:
        DeepSeekClassifier.from_config(get_deepseek_config(cfg))
    except ReportGenerationError as exc:
        print(f"❌ 报告配置无效: {exc}", file=sys.stderr)
        return 1

    output_dir = cfg.get("output", {}).get("dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    nc_file = os.path.join(output_dir, "nowcoder.json")
    xhs_file = os.path.join(output_dir, "xiaohongshu.json")

    # ===== 步骤1：爬取牛客 =====
    if not args.report_only and not args.skip_nc:
        print("=" * 50)
        print("📥 步骤1：爬取牛客网面经")
        print("=" * 50)
        from scrape_nowcoder import run as nc_run

        nowcoder_config = cfg.get("nowcoder", {})
        nc_run(
            queries=nowcoder_config.get("queries", ["字节飞书面经"]),
            max_pages=nowcoder_config.get("max_pages", 3),
            delay=nowcoder_config.get("delay_seconds", 0.8),
            output_file=nc_file,
        )
        print()
    else:
        print("⏭️  跳过牛客网爬取\n")

    # ===== 步骤2：爬取小红书 =====
    if not args.report_only and not args.skip_xhs:
        xhs_config = cfg.get("xiaohongshu", {})
        if xhs_config.get("enabled", True):
            cookies = xhs_config.get("cookies", {})
            if not cookies.get("a1") or "填入" in cookies.get("a1", ""):
                print("⚠️  小红书 Cookie 未配置，跳过小红书爬取")
                print("   配置方法见 docs/get-xhs-cookies.md\n")
            else:
                print("=" * 50)
                print("📥 步骤2：爬取小红书面经")
                print("=" * 50)
                from scrape_xhs import run as xhs_run

                xhs_run(
                    queries=xhs_config.get("queries", ["字节飞书面试"]),
                    cookies=cookies,
                    max_pages=xhs_config.get("max_pages", 3),
                    delay=xhs_config.get("delay_seconds", 0.8),
                    output_file=xhs_file,
                )
                print()
        else:
            print("⏭️  config.json 中 xiaohongshu.enabled=false，跳过\n")
    else:
        print("⏭️  跳过小红书爬取\n")

    # ===== 步骤3：生成报告 =====
    print("=" * 50)
    print("📝 步骤3：生成 MD/HTML 报告")
    print("=" * 50)
    from generate_report import run as report_run

    output_config = cfg.get("output", {})
    title = output_config.get("title", "面经备考手册")
    formats = output_config.get("formats", ["md", "html"])
    filter_mode = args.filter or cfg.get("filter", {}).get("mode", "all")
    try:
        results = report_run(
            nc_file=nc_file,
            xhs_file=xhs_file,
            output_dir=output_dir,
            title=title,
            filter_mode=filter_mode,
            formats=formats,
            config=cfg,
        )
    except ReportGenerationError as exc:
        print(f"❌ 报告生成失败: {exc}", file=sys.stderr)
        return 1

    print()
    print("=" * 50)
    print("🎉 全部完成！")
    print("=" * 50)
    for fmt, path in results.items():
        print(f"   {fmt.upper()} → {os.path.abspath(path)}")

    if "html" in results:
        _open_in_browser(results["html"])
        print("\n   已尝试在浏览器打开 HTML 文件 🚀")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
