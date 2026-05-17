#!/usr/bin/env python3
"""
MD/HTML 报告生成器
用法：
  python3 generate_report.py                                    # 使用 config.json
  python3 generate_report.py --nc output/nc.json --xhs output/xhs.json
  python3 generate_report.py --title "字节飞书备考" --filter backend
"""
import json, re, os, sys, argparse

try:
    import markdown as md_lib
except ImportError:
    print("❌ 缺少依赖: pip3 install markdown")
    sys.exit(1)

BACKEND_KWS = ["后端", "golang", "go语言", "服务端", "backend", "全栈", "开发工程师"]
EXCLUDE_KWS = ["运营", "销售", "ux设计", "产品经理", "数据分析", "市场营销", "人力资源"]


def filter_posts(posts: list, mode: str = "all") -> list:
    if mode == "backend":
        return [d for d in posts if any(
            kw in (d.get("title", "") + d.get("content", "")).lower()
            for kw in BACKEND_KWS
        )]
    else:  # all
        return [d for d in posts if not any(
            kw in (d.get("title", "") + d.get("content", "")).lower()
            for kw in EXCLUDE_KWS
        )]


def build_md(nc_posts: list, xhs_posts: list, title: str,
             max_len: int = 2000) -> str:
    lines = []
    L = lines.append

    nc_cnt  = len(nc_posts)
    xhs_cnt = len(xhs_posts)

    L(f"# {title}")
    L("")
    L(f"> 牛客网 **{nc_cnt}** 篇 + 小红书 **{xhs_cnt}** 篇，共 **{nc_cnt + xhs_cnt}** 篇真实面经")
    L("")
    L("---")
    L("")

    # 高频考点
    L("## 第一部分：高频考点速查")
    L("")

    topics = [
        ("Golang / Go", [
            "GMP 调度模型（G/M/P 的含义 + work stealing）",
            "Goroutine vs 线程的区别",
            "Channel 底层实现（hchan 结构 + 阻塞原理）",
            "map 并发不安全 → sync.Map / Mutex 方案",
            "GC 三色标记法 + 写屏障",
            "slice 扩容规则（<256 翻倍，>256 增长 1.25）",
            "defer LIFO + 闭包陷阱",
            "interface 底层 iface/eface",
            "内存逃逸分析",
        ]),
        ("MySQL", [
            "B+ 树索引结构 + 为什么不用 B 树",
            "聚簇索引 vs 非聚簇索引（回表/覆盖索引）",
            "联合索引最左前缀 + 索引失效场景",
            "MVCC 原理（undo log + read view）",
            "四种隔离级别 + 幻读解决方案",
            "redo log / undo log / bin log 区别",
            "行锁 / 表锁 / 间隙锁 / Next-Key Lock",
            "慢 SQL 排查：explain + 索引优化",
        ]),
        ("Redis", [
            "为什么快：单线程 + IO多路复用 + 内存操作",
            "五种数据结构底层实现",
            "缓存穿透/击穿/雪崩 三问 ★★★",
            "RDB vs AOF 持久化",
            "分布式锁：SET NX EX + Redlock",
            "内存淘汰：LRU vs LFU",
            "热 Key / 大 Key 处理",
            "集群：主从/哨兵/Cluster",
        ]),
        ("计算机网络", [
            "TCP 三次握手/四次挥手 ★★★",
            "TIME_WAIT（2MSL 原因）",
            "TCP 可靠传输：序号/确认/重传/流控/拥塞控制",
            "HTTP 1.0/1.1/2.0/3.0 区别",
            "HTTPS TLS 握手过程",
            "URL → 页面全流程 ★★★",
            "DNS 解析（UDP 53 端口）",
        ]),
        ("操作系统", [
            "进程/线程/协程区别",
            "IO 多路复用：select/poll/epoll 区别",
            "虚拟内存 + 缺页中断",
            "死锁四条件 + 预防",
        ]),
        ("系统设计", [
            "秒杀系统设计（防超卖）★★★",
            "分布式 ID（雪花算法）",
            "限流：令牌桶/漏桶/滑动窗口",
            "短链服务设计",
            "敏感词过滤（Trie）",
        ]),
        ("算法（手撕）", [
            "★★★ LC3 无重复最长子串（滑动窗口）",
            "★★★ LC128 最长连续序列（HashSet O(n)）",
            "★★★ LC25 K个一组翻转链表",
            "★★★ LC146 LRU 缓存",
            "★★ LC102 二叉树层序遍历",
            "★★ LC76 最小覆盖子串",
        ]),
    ]

    for i, (topic, qs) in enumerate(topics):
        L(f"### {i+1}. {topic}")
        L("")
        for q in qs:
            L(f"- {q}")
        L("")

    L("---")
    L("")

    # 牛客面经
    L(f"## 第二部分：牛客网面经（共 {nc_cnt} 篇，节选30篇原文）")
    L("")
    for i, d in enumerate(nc_posts[:30]):
        title   = d.get("title", "无标题")
        url     = d.get("url", "")
        content = d.get("content", "").strip()
        if len(content) > max_len:
            content = content[:max_len] + "\n\n...（内容截断，完整见原链接）"
        L(f"### {i+1}. {title}")
        L("")
        if url:
            L(f"> 来源：[{url}]({url})")
            L("")
        L(content)
        L("")
        L("---")
        L("")

    # 小红书面经
    L(f"## 第三部分：小红书面经（共 {xhs_cnt} 篇，节选30篇原文）")
    L("")
    for i, d in enumerate(xhs_posts[:30]):
        title   = d.get("title", "无标题")
        url     = d.get("url", "")
        content = d.get("content", "").strip()
        if len(content) > max_len:
            content = content[:max_len] + "\n\n...（内容截断）"
        L(f"### {i+1}. {title}")
        L("")
        if url:
            L(f"> 来源：[小红书]({url})")
            L("")
        L(content)
        L("")
        L("---")
        L("")

    # 附录
    L("## 附录：全部面经索引")
    L("")
    L(f"### 牛客网（{nc_cnt} 篇）")
    L("")
    for i, d in enumerate(nc_posts):
        L(f"{i+1}. [{d.get('title','无标题')}]({d.get('url','')})")
    L("")
    L(f"### 小红书（{xhs_cnt} 篇）")
    L("")
    for i, d in enumerate(xhs_posts):
        L(f"{i+1}. [{d.get('title','无标题')}]({d.get('url','')})")

    return "\n".join(lines)


_CSS = """
:root{--bg:#0f1117;--sb:#161b22;--card:#1c2128;--bdr:#30363d;--tx:#e6edf3;--mt:#8b949e;--ac:#58a6ff;--ac2:#3fb950;--ac3:#d29922;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--tx);display:flex;min-height:100vh;font-size:15px;line-height:1.7;}
#sb{width:270px;min-width:270px;background:var(--sb);border-right:1px solid var(--bdr);position:fixed;top:0;left:0;bottom:0;overflow-y:auto;padding:16px 0;z-index:100;}
#sbh{padding:0 14px 14px;border-bottom:1px solid var(--bdr);margin-bottom:6px;}
#sbh h2{font-size:12px;color:var(--mt);text-transform:uppercase;letter-spacing:.8px;}
#sb ul{list-style:none;}
#sb a{display:block;padding:5px 14px;color:var(--mt);text-decoration:none;font-size:13px;border-left:3px solid transparent;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:all .15s;}
#sb a:hover,#sb a.on{color:var(--ac);background:rgba(88,166,255,.07);border-left-color:var(--ac);}
.h2a{font-weight:600;color:var(--tx)!important;}
.h3a{padding-left:26px!important;font-size:12px!important;}
#mn{margin-left:270px;flex:1;max-width:940px;padding:36px 48px;}
.hero{background:linear-gradient(135deg,#1a2a4a,#0d1b2e);border:1px solid #1f6feb;border-radius:12px;padding:22px 26px;margin-bottom:28px;}
.hero-t{font-size:20px;color:var(--ac);font-weight:700;margin-bottom:6px;}
.badge{display:inline-block;padding:3px 9px;border-radius:20px;font-size:12px;font-weight:600;margin:3px 3px 0 0;}
.bb{background:rgba(88,166,255,.15);color:#58a6ff;border:1px solid rgba(88,166,255,.3);}
.bg{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.3);}
.by{background:rgba(210,153,34,.15);color:#d29922;border:1px solid rgba(210,153,34,.3);}
h1{display:none;}
h2{font-size:19px;color:var(--ac);margin:36px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--bdr);scroll-margin-top:20px;}
h3{font-size:15px;color:var(--ac2);margin:22px 0 10px;scroll-margin-top:20px;}
p{margin:0 0 10px;}
ul,ol{padding-left:20px;margin:7px 0 10px;}
li{margin:3px 0;}
a{color:var(--ac);text-decoration:none;}
a:hover{text-decoration:underline;}
hr{border:none;border-top:1px solid var(--bdr);margin:28px 0;}
blockquote{border-left:3px solid var(--ac3);padding:7px 14px;background:rgba(210,153,34,.07);border-radius:0 6px 6px 0;color:var(--mt);margin:10px 0;font-size:14px;}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;}
th{background:var(--card);color:var(--ac);padding:8px 11px;border:1px solid var(--bdr);text-align:left;}
td{padding:8px 11px;border:1px solid var(--bdr);vertical-align:top;}
tr:nth-child(even) td{background:rgba(255,255,255,.015);}
code{font-family:'JetBrains Mono','Fira Code',Consolas,monospace;font-size:13px;background:var(--card);border:1px solid var(--bdr);padding:2px 5px;border-radius:4px;color:#e3b341;}
pre{background:var(--card);border:1px solid var(--bdr);border-radius:8px;padding:14px 18px;overflow-x:auto;margin:10px 0 14px;}
pre code{background:none;border:none;padding:0;color:#e6edf3;}
#srch{width:100%;padding:7px 11px;background:var(--bg);border:1px solid var(--bdr);border-radius:6px;color:var(--tx);font-size:13px;margin-bottom:10px;outline:none;}
#srch:focus{border-color:var(--ac);}
#top{position:fixed;bottom:22px;right:22px;background:var(--ac);color:#000;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:bold;box-shadow:0 3px 10px rgba(0,0,0,.4);text-decoration:none;opacity:.8;}
#top:hover{opacity:1;transform:scale(1.1);}
#prog{position:fixed;top:0;left:270px;right:0;height:3px;background:linear-gradient(90deg,var(--ac),var(--ac2));transform-origin:left;transform:scaleX(0);transition:transform .1s;z-index:200;}
@media(max-width:768px){#sb{display:none;}#mn{margin-left:0;padding:18px;}#prog{left:0;}}
"""

_JS = """
window.addEventListener('scroll',()=>{
  const d=document.documentElement;
  document.getElementById('prog').style.transform=`scaleX(${d.scrollTop/(d.scrollHeight-d.clientHeight)||0})`;
});
const hs=document.querySelectorAll('h2,h3');
const ls=document.querySelectorAll('#sb a');
hs.forEach(h=>new IntersectionObserver(es=>{es.forEach(e=>{
  if(e.isIntersecting){ls.forEach(l=>l.classList.remove('on'));
    const a=document.querySelector(`#sb a[href="#${e.target.id}"]`);
    if(a){a.classList.add('on');a.scrollIntoView({block:'nearest'});}
  }
});},{rootMargin:'-20px 0px -80% 0px'}).observe(h));
function fs(q){q=q.toLowerCase();document.querySelectorAll('#sb li').forEach(li=>{
  li.style.display=(!q||li.textContent.toLowerCase().includes(q))?'':'none';
});}
"""


def build_html(md_text: str, title: str, nc_cnt: int, xhs_cnt: int) -> str:
    html_body = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
        extension_configs={"toc": {"toc_depth": "2-3"}}
    )
    toc_items = []
    for m in re.finditer(r'<h([23])[^>]*id="([^"]*)"[^>]*>(.*?)</h\1>', html_body, re.DOTALL):
        lv, anc, txt = m.group(1), m.group(2), m.group(3)
        clean = re.sub(r"<[^>]+>", "", txt).strip()
        cls   = "h2a" if lv == "2" else "h3a"
        toc_items.append(f'<li><a href="#{anc}" class="{cls}">{clean}</a></li>')
    toc = "<ul>" + "".join(toc_items) + "</ul>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<div id="prog"></div>
<nav id="sb">
  <div id="sbh">
    <h2>📚 目录导航</h2>
    <input id="srch" type="text" placeholder="搜索章节..." oninput="fs(this.value)">
  </div>
  {toc}
</nav>
<main id="mn">
  <div class="hero">
    <div class="hero-t">{title}</div>
    <p style="margin-top:7px">
      <span class="badge bb">牛客网：{nc_cnt} 篇</span>
      <span class="badge bg">小红书：{xhs_cnt} 篇</span>
      <span class="badge by">合计：{nc_cnt + xhs_cnt} 篇</span>
    </p>
  </div>
  {html_body}
</main>
<a href="#" id="top" title="返回顶部">↑</a>
<script>{_JS}</script>
</body>
</html>"""


def run(nc_file: str, xhs_file: str, output_dir: str, title: str,
        filter_mode: str = "all", max_len: int = 2000,
        formats: list = None, verbose: bool = True) -> dict:
    """生成报告"""
    formats = formats or ["md", "html"]
    os.makedirs(output_dir, exist_ok=True)

    nc_posts  = json.load(open(nc_file,  encoding="utf-8")) if os.path.exists(nc_file)  else []
    xhs_posts = json.load(open(xhs_file, encoding="utf-8")) if os.path.exists(xhs_file) else []

    nc_posts  = filter_posts(nc_posts,  filter_mode)
    xhs_posts = filter_posts(xhs_posts, filter_mode)

    if verbose:
        print(f"📊 过滤模式: {filter_mode}")
        print(f"   牛客: {len(nc_posts)} 篇 | 小红书: {len(xhs_posts)} 篇")

    md_text = build_md(nc_posts, xhs_posts, title, max_len)
    results = {}

    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)

    if "md" in formats:
        md_path = os.path.join(output_dir, f"{safe_title}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        results["md"] = md_path
        if verbose:
            print(f"✅ MD  → {md_path} ({len(md_text)//1024}KB)")

    if "html" in formats:
        html_text = build_html(md_text, title, len(nc_posts), len(xhs_posts))
        html_path = os.path.join(output_dir, f"{safe_title}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        results["html"] = html_path
        if verbose:
            print(f"✅ HTML → {html_path} ({len(html_text)//1024}KB)")

    return results


def main():
    parser = argparse.ArgumentParser(description="MD/HTML 报告生成器")
    parser.add_argument("--config",  default="config.json")
    parser.add_argument("--nc",      default="output/nowcoder.json",     help="牛客数据 JSON")
    parser.add_argument("--xhs",     default="output/xiaohongshu.json",  help="小红书数据 JSON")
    parser.add_argument("--title",   help="报告标题")
    parser.add_argument("--filter",  choices=["all", "backend"], default="all")
    parser.add_argument("--output",  help="输出目录")
    args = parser.parse_args()

    cfg = {}
    if os.path.exists(args.config):
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)

    title      = args.title or cfg.get("output", {}).get("title", "面经备考手册")
    output_dir = args.output or cfg.get("output", {}).get("dir", "output")
    formats    = cfg.get("output", {}).get("formats", ["md", "html"])
    filter_m   = cfg.get("filter", {}).get("mode", args.filter)
    max_len    = cfg.get("output", {}).get("max_content_length", 2000)

    run(nc_file=args.nc, xhs_file=args.xhs, output_dir=output_dir,
        title=title, filter_mode=filter_m, max_len=max_len, formats=formats)


if __name__ == "__main__":
    main()
