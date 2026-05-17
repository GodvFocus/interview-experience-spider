#!/usr/bin/env python3
"""
小红书面经爬虫（需要 Cookie + Spider_XHS 签名）
用法：
  python3 scrape_xhs.py                          # 使用 config.json
  python3 scrape_xhs.py --query "字节飞书" --config config.json
  python3 scrape_xhs.py --output output/xhs.json
如何获取 Cookie？见 docs/get-xhs-cookies.md
"""
import re, time, json, argparse, sys, os

try:
    import requests
except ImportError:
    print("❌ 缺少依赖，请先运行: pip3 install requests")
    sys.exit(1)

# 设置 Spider_XHS_signing 路径
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SIGNING_DIR  = os.path.join(SCRIPT_DIR, "Spider_XHS_signing")
NODE_MODULES = os.path.join(SIGNING_DIR, "node_modules")

if not os.path.exists(NODE_MODULES):
    print("❌ 未找到 Spider_XHS_signing/node_modules")
    print("   请先运行: cd Spider_XHS_signing && npm install")
    sys.exit(1)

sys.path.insert(0, SIGNING_DIR)
os.environ["NODE_PATH"] = NODE_MODULES

try:
    from xhs_utils.xhs_util import generate_xs_xs_common, generate_search_id
except ImportError as e:
    print(f"❌ 导入签名工具失败: {e}")
    print("   请确保已安装 PyExecJS: pip3 install PyExecJS")
    sys.exit(1)


def build_headers(a1: str, api_path: str, data_str: str = "", method: str = "POST",
                  extra_cookies: dict = None) -> dict:
    xs, xt, xs_common = generate_xs_xs_common(a1, api_path, data_str, method)
    cookies = {
        "a1":          a1,
        "web_session": extra_cookies.get("web_session", ""),
        "webId":       extra_cookies.get("webId", ""),
        "gid":         extra_cookies.get("gid", ""),
    }
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items() if v)
    return {
        "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer":         "https://www.xiaohongshu.com/",
        "Origin":          "https://www.xiaohongshu.com",
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type":    "application/json;charset=UTF-8",
        "Cookie":          cookie_str,
        "x-s":             xs,
        "x-t":             str(xt),
        "x-s-common":      xs_common,
    }


def search_notes(keyword: str, page: int = 1, page_size: int = 20,
                 cookies: dict = None) -> dict | None:
    """搜索小红书笔记"""
    api = "/api/sns/web/v1/search/notes"
    payload = {
        "keyword":   keyword,
        "page":      page,
        "page_size": page_size,
        "search_id": generate_search_id(),
        "sort":      "general",
        "note_type": 0,
    }
    data_str = json.dumps(payload, separators=(",", ":"))
    headers = build_headers(cookies.get("a1", ""), api, data_str, "POST", cookies)
    try:
        resp = requests.post(
            f"https://edith.xiaohongshu.com{api}",
            data=data_str,
            headers=headers,
            timeout=15
        )
        return resp.json()
    except Exception as e:
        print(f"  ⚠️  搜索异常: {e}")
        return None


def fetch_note(note_id: str, xsec_token: str = "", cookies: dict = None) -> dict | None:
    """获取笔记详情"""
    api = "/api/sns/web/v1/feed"
    payload = {
        "source_note_id": note_id,
        "image_formats":  ["jpg", "webp", "avif"],
        "extra":          {"need_body_topic": "1"},
        "xsec_source":    "pc_search",
        "xsec_token":     xsec_token,
    }
    data_str = json.dumps(payload, separators=(",", ":"))
    headers = build_headers(cookies.get("a1", ""), api, data_str, "POST", cookies)
    try:
        resp = requests.post(
            f"https://edith.xiaohongshu.com{api}",
            data=data_str,
            headers=headers,
            timeout=15
        )
        result = resp.json()
        if result.get("success"):
            items = result.get("data", {}).get("items", [])
            if items:
                note = items[0].get("note_card", {})
                return {
                    "title":   note.get("title", ""),
                    "content": note.get("desc", ""),
                }
        return None
    except Exception as e:
        print(f"  ⚠️  笔记抓取异常 {note_id}: {e}")
        return None


def is_relevant(title: str, content: str, keywords: list) -> bool:
    """判断内容是否相关"""
    text = (title + content).lower()
    return any(kw.lower() in text for kw in keywords)


def run(queries: list, cookies: dict, max_pages: int = 3, delay: float = 0.8,
        filter_keywords: list = None, output_file: str = "output/xiaohongshu.json",
        verbose: bool = True) -> list:
    """主函数：搜索 + 抓取正文，返回结果列表"""
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    if not cookies.get("a1"):
        print("❌ 未配置小红书 Cookie，请在 config.json 中填写")
        print("   见 docs/get-xhs-cookies.md")
        return []

    # 第一步：搜索
    all_notes = {}
    for kw in queries:
        if verbose:
            print(f"🔍 搜索: {kw}")
        for page in range(1, max_pages + 1):
            result = search_notes(kw, page=page, page_size=20, cookies=cookies)
            if not result:
                break
            if not result.get("success"):
                code = result.get("code", "?")
                msg  = result.get("msg", "")
                if verbose:
                    print(f"   ❌ code={code} msg={msg}")
                if code == 461:
                    print("   ⚠️  Cookie 已过期，请重新获取！见 docs/get-xhs-cookies.md")
                break
            items = result.get("data", {}).get("items", [])
            new = 0
            for item in items:
                nid        = item.get("id", "")
                note_card  = item.get("note_card", {})
                title      = note_card.get("display_title") or note_card.get("title", "")
                xsec_token = item.get("xsec_token", "")
                if nid and nid not in all_notes:
                    all_notes[nid] = {"note_id": nid, "title": title,
                                      "xsec_token": xsec_token, "keyword": kw}
                    new += 1
            if verbose:
                print(f"   页{page}: {len(items)} 条，新增 {new}（累计 {len(all_notes)}）")
            if len(items) < 20:
                break
            time.sleep(delay)
        time.sleep(1)

    if verbose:
        print(f"\n📄 共 {len(all_notes)} 条，开始抓取正文...\n")

    # 第二步：抓取正文
    collected = []
    for i, (nid, info) in enumerate(all_notes.items()):
        short = (info.get("title") or nid)[:50]
        if verbose:
            print(f"[{i+1}/{len(all_notes)}] {short}")

        detail = fetch_note(nid, info.get("xsec_token", ""), cookies)
        if detail and len(detail.get("content", "")) > 30:
            title   = detail["title"] or info.get("title", "")
            content = detail["content"]
            # 如果设置了过滤关键词，只保留相关内容
            if filter_keywords and not is_relevant(title, content, filter_keywords):
                if verbose:
                    print(f"   - 不相关，跳过")
                time.sleep(0.3)
                continue
            collected.append({
                "title":   title,
                "content": content,
                "url":     f"https://www.xiaohongshu.com/explore/{nid}",
                "source":  "xiaohongshu",
                "keyword": info.get("keyword", ""),
            })
            if verbose:
                print(f"   ✅ {len(content)} 字")
        else:
            if verbose:
                print(f"   ❌ 无正文")
        time.sleep(delay)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"\n✅ 小红书面经抓取完成：{len(collected)}/{len(all_notes)} 篇有效")
        print(f"📁 保存到: {output_file}")

    return collected


def main():
    parser = argparse.ArgumentParser(description="小红书面经爬虫")
    parser.add_argument("--config",  default="config.json", help="配置文件路径")
    parser.add_argument("--query",   help="单个搜索关键词")
    parser.add_argument("--pages",   type=int, help="每个关键词搜索页数")
    parser.add_argument("--output",  default="output/xiaohongshu.json", help="输出 JSON 路径")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"❌ 未找到配置文件: {args.config}")
        print(f"   请先执行: cp config.example.json config.json 并填入 Cookie")
        sys.exit(1)

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    cookies    = cfg.get("xiaohongshu", {}).get("cookies", {})
    queries    = [args.query] if args.query else cfg.get("xiaohongshu", {}).get("queries", [])
    max_pages  = args.pages or cfg.get("xiaohongshu", {}).get("max_pages", 3)
    delay      = cfg.get("xiaohongshu", {}).get("delay_seconds", 0.8)
    output     = args.output
    filter_kws = None  # 不过滤，全部保留

    run(queries=queries, cookies=cookies, max_pages=max_pages, delay=delay,
        filter_keywords=filter_kws, output_file=output)


if __name__ == "__main__":
    main()
