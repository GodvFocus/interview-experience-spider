#!/usr/bin/env python3
"""
牛客网面经爬虫
用法：
  python3 scrape_nowcoder.py                          # 使用 config.json
  python3 scrape_nowcoder.py --query "字节飞书" --pages 5
  python3 scrape_nowcoder.py --output output/nc.json
"""
import re, time, json, argparse, sys, os

try:
    import requests
except ImportError:
    print("❌ 缺少依赖，请先运行: pip3 install requests")
    sys.exit(1)

SEARCH_API  = "https://gw-c.nowcoder.com/api/sparta/pc/search"
DISCUSS_API = "https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail"
FEED_URL    = "https://www.nowcoder.com/feed/main/detail"

HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def html_to_text(html: str) -> str:
    if not html:
        return ""
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"</?(p|div|br|h[1-6]|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    for old, new in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                     ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("\xa0", " ")]:
        html = html.replace(old, new)
    html = re.sub(r"\n\s*\n", "\n\n", html)
    return html.strip()


def search(query: str, max_pages: int = 3, delay: float = 0.8) -> list:
    """搜索牛客网面经，返回帖子元信息列表"""
    results = []
    seen = set()
    for page in range(1, max_pages + 1):
        try:
            payload = {
                "type": "all",
                "query": query,
                "page": page,
                "tag": [{"name": "面经", "id": 818, "count": None}],
                "order": "create",
                "gioParams": {"searchFrom_var": "顶部导航栏", "searchEnter_var": "主站"},
            }
            resp = requests.post(SEARCH_API, json=payload, headers=HEADERS, timeout=15)
            data = resp.json()
            if not data.get("success"):
                break
            records = data.get("data", {}).get("records", [])
            if not records:
                break
            for r in records:
                rc_type = r.get("rc_type", 0)
                rd = r.get("data", {})
                if rc_type == 201:
                    md = rd.get("momentData", {})
                    if md:
                        uid   = md.get("uuid", "")
                        title = md.get("title", "")
                        if uid and uid not in seen:
                            seen.add(uid)
                            results.append({"rc_type": 201, "uuid": uid, "title": title, "query": query})
                elif rc_type == 207:
                    cd = rd.get("contentData", {})
                    if cd:
                        cid   = str(cd.get("id", ""))
                        title = cd.get("title", "")
                        if cid and cid not in seen:
                            seen.add(cid)
                            results.append({"rc_type": 207, "content_id": cid, "title": title, "query": query})
            total_page = data.get("data", {}).get("totalPage", 1)
            if page >= total_page:
                break
            time.sleep(delay)
        except Exception as e:
            print(f"  ⚠️  搜索第{page}页出错: {e}")
            break
    return results


def fetch_feed(uuid: str) -> dict | None:
    """抓取 Feed 类型帖子正文"""
    try:
        resp = requests.get(
            f"{FEED_URL}/{uuid}",
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=15
        )
        html = resp.text
        if "内容不存在" in html:
            return None
        title_m = re.search(r'"title":"([^"]+)"', html)
        title   = title_m.group(1) if title_m else ""
        content = ""
        cm = re.search(
            r'<div[^>]*class="[^"]*feed-content-text[^"]*"[^>]*>(.*?)</div>',
            html, re.DOTALL | re.IGNORECASE
        )
        if cm:
            content = html_to_text(cm.group(1))
        if not content:
            for m in re.findall(r'"content":"([^"]{100,})"', html):
                content = m.replace("\\n", "\n").replace("\\u002F", "/").replace("\\t", "\t")
                break
        return {"title": title, "content": content, "url": f"{FEED_URL}/{uuid}"}
    except Exception as e:
        print(f"  ⚠️  Feed 抓取失败 {uuid}: {e}")
        return None


def fetch_discuss(content_id: str) -> dict | None:
    """抓取 Discuss 类型帖子正文"""
    try:
        resp = requests.get(
            f"{DISCUSS_API}/{content_id}",
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=15
        )
        data = resp.json()
        if not data.get("success"):
            return None
        cd    = data.get("data", {})
        rich  = cd.get("richText", "") or cd.get("content", "")
        return {
            "title":   cd.get("title", ""),
            "content": html_to_text(rich),
            "url":     f"https://www.nowcoder.com/discuss/{content_id}",
        }
    except Exception as e:
        print(f"  ⚠️  Discuss 抓取失败 {content_id}: {e}")
        return None


def run(queries: list, max_pages: int = 3, delay: float = 0.8,
        output_file: str = "output/nowcoder.json", verbose: bool = True) -> list:
    """主函数：搜索 + 抓取正文，返回结果列表"""
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # 第一步：搜索，去重
    all_posts = {}
    for q in queries:
        if verbose:
            print(f"🔍 搜索: {q}")
        results = search(q, max_pages=max_pages, delay=delay)
        new = 0
        for r in results:
            key = r.get("uuid") or r.get("content_id")
            if key and key not in all_posts:
                all_posts[key] = r
                new += 1
        if verbose:
            print(f"   新增 {new} 条（累计 {len(all_posts)} 条）")
        time.sleep(1)

    if verbose:
        print(f"\n📄 共 {len(all_posts)} 条，开始抓取正文...\n")

    # 第二步：抓取正文
    collected = []
    for i, (key, info) in enumerate(all_posts.items()):
        title_short = (info.get("title") or key)[:50]
        if verbose:
            print(f"[{i+1}/{len(all_posts)}] {title_short}")

        if info["rc_type"] == 201:
            detail = fetch_feed(info["uuid"])
        else:
            detail = fetch_discuss(info["content_id"])

        if detail and len(detail.get("content", "")) > 80:
            collected.append({
                "title":   detail["title"] or info["title"],
                "content": detail["content"],
                "url":     detail["url"],
                "query":   info["query"],
                "source":  "nowcoder",
            })
            if verbose:
                print(f"   ✅ {len(detail['content'])} 字")
        else:
            if verbose:
                print(f"   ❌ 无正文")
        time.sleep(delay)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"\n✅ 牛客面经抓取完成：{len(collected)}/{len(all_posts)} 篇有效")
        print(f"📁 保存到: {output_file}")

    return collected


def main():
    parser = argparse.ArgumentParser(description="牛客网面经爬虫")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--query",  help="单个搜索关键词（覆盖 config.json）")
    parser.add_argument("--pages",  type=int, help="每个关键词搜索页数")
    parser.add_argument("--output", default="output/nowcoder.json", help="输出 JSON 文件路径")
    args = parser.parse_args()

    queries   = [args.query] if args.query else None
    max_pages = args.pages

    if not queries:
        if os.path.exists(args.config):
            with open(args.config, encoding="utf-8") as f:
                cfg = json.load(f)
            queries   = cfg.get("nowcoder", {}).get("queries", ["字节飞书面经"])
            max_pages = max_pages or cfg.get("nowcoder", {}).get("max_pages", 3)
            delay     = cfg.get("nowcoder", {}).get("delay_seconds", 0.8)
            output    = cfg.get("output", {}).get("dir", "output") + "/nowcoder.json"
        else:
            print(f"⚠️  未找到 {args.config}，使用默认关键词")
            queries   = ["字节飞书后端实习"]
            max_pages = 3
            delay     = 0.8
            output    = args.output
    else:
        max_pages = max_pages or 3
        delay     = 0.8
        output    = args.output

    run(queries=queries, max_pages=max_pages, delay=delay, output_file=output)


if __name__ == "__main__":
    main()
