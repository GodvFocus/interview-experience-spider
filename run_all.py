#!/usr/bin/env python3
"""
🚀 一键运行：搜索 + 抓取 + 生成报告
用法：
  python3 run_all.py                  # 使用 config.json
  python3 run_all.py --filter backend # 只保留后端/Go 相关
  python3 run_all.py --skip-nc        # 跳过牛客，只爬小红书
  python3 run_all.py --skip-xhs       # 跳过小红书，只爬牛客
"""
import os, sys, json, argparse, subprocess

def check_env():
    """检查运行环境"""
    print("🔍 检查运行环境...")

    # Python 依赖
    missing = []
    for pkg in ["requests", "execjs", "markdown"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"❌ 缺少 Python 依赖: {', '.join(missing)}")
        print(f"   请运行: pip3 install {' '.join(missing)}")
        sys.exit(1)

    # Node.js 依赖（小红书签名需要）
    node_modules = os.path.join(os.path.dirname(__file__), "Spider_XHS_signing", "node_modules")
    if not os.path.exists(node_modules):
        print("⚠️  小红书签名模块未初始化")
        print("   正在自动初始化...")
        signing_dir = os.path.join(os.path.dirname(__file__), "Spider_XHS_signing")
        result = subprocess.run(["npm", "install"], cwd=signing_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ npm install 失败: {result.stderr}")
            print(f"   请手动运行: cd Spider_XHS_signing && npm install")
        else:
            print("   ✅ Node.js 依赖安装完成")

    # config.json
    if not os.path.exists("config.json"):
        print("⚠️  未找到 config.json")
        if os.path.exists("config.example.json"):
            print("   提示：请先执行 cp config.example.json config.json 并填写配置")
        sys.exit(1)

    print("✅ 环境检查通过\n")


def main():
    parser = argparse.ArgumentParser(description="面经猎手 - 一键运行")
    parser.add_argument("--config",   default="config.json")
    parser.add_argument("--filter",   choices=["all", "backend"], help="过滤模式（覆盖 config.json）")
    parser.add_argument("--skip-nc",  action="store_true", help="跳过牛客网爬取")
    parser.add_argument("--skip-xhs", action="store_true", help="跳过小红书爬取")
    parser.add_argument("--report-only", action="store_true", help="只生成报告（用已有数据）")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    check_env()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    output_dir = cfg.get("output", {}).get("dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    nc_file  = os.path.join(output_dir, "nowcoder.json")
    xhs_file = os.path.join(output_dir, "xiaohongshu.json")

    # ===== 步骤1：爬取牛客 =====
    if not args.report_only and not args.skip_nc:
        print("=" * 50)
        print("📥 步骤1：爬取牛客网面经")
        print("=" * 50)
        from scrape_nowcoder import run as nc_run
        queries   = cfg.get("nowcoder", {}).get("queries", ["字节飞书面经"])
        max_pages = cfg.get("nowcoder", {}).get("max_pages", 3)
        delay     = cfg.get("nowcoder", {}).get("delay_seconds", 0.8)
        nc_run(queries=queries, max_pages=max_pages, delay=delay, output_file=nc_file)
        print()
    else:
        print("⏭️  跳过牛客网爬取\n")

    # ===== 步骤2：爬取小红书 =====
    if not args.report_only and not args.skip_xhs:
        xhs_cfg = cfg.get("xiaohongshu", {})
        if xhs_cfg.get("enabled", True):
            cookies = xhs_cfg.get("cookies", {})
            if not cookies.get("a1") or "填入" in cookies.get("a1", ""):
                print("⚠️  小红书 Cookie 未配置，跳过小红书爬取")
                print("   配置方法见 docs/get-xhs-cookies.md\n")
            else:
                print("=" * 50)
                print("📥 步骤2：爬取小红书面经")
                print("=" * 50)
                from scrape_xhs import run as xhs_run
                queries   = xhs_cfg.get("queries", ["字节飞书面试"])
                max_pages = xhs_cfg.get("max_pages", 3)
                delay     = xhs_cfg.get("delay_seconds", 0.8)
                xhs_run(queries=queries, cookies=cookies, max_pages=max_pages,
                        delay=delay, output_file=xhs_file)
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

    title      = cfg.get("output", {}).get("title", "面经备考手册")
    formats    = cfg.get("output", {}).get("formats", ["md", "html"])
    max_len    = cfg.get("output", {}).get("max_content_length", 2000)
    filter_m   = args.filter or cfg.get("filter", {}).get("mode", "all")

    results = report_run(
        nc_file=nc_file, xhs_file=xhs_file,
        output_dir=output_dir, title=title,
        filter_mode=filter_m, max_len=max_len, formats=formats
    )

    print()
    print("=" * 50)
    print("🎉 全部完成！")
    print("=" * 50)
    for fmt, path in results.items():
        print(f"   {fmt.upper()} → {os.path.abspath(path)}")

    # 自动用浏览器打开 HTML
    if "html" in results:
        import subprocess
        try:
            subprocess.Popen(["open", results["html"]])
            print("\n   已自动在浏览器打开 HTML 文件 🚀")
        except Exception:
            pass


if __name__ == "__main__":
    main()
