"""离线建立收藏夹验收页面，不访问平台或分类模型。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from generate_report import Article, ClassifiedQuestion, ReportData, build_html


articles = (
    Article("article-0001", "nowcoder", "Java 并发面经", "https://www.nowcoder.com/discuss/123456789", "原文一"),
    Article("article-0002", "xiaohongshu", "Redis 面经", "https://www.xiaohongshu.com/explore/abcdef1234567890", "原文二"),
)
questions = (
    ClassifiedQuestion("article-0001", "如何保证线程安全？", "JUC", ("JUC",)),
    ClassifiedQuestion("article-0002", "Redis 如何避免缓存击穿？", "Redis", ("Redis",)),
    ClassifiedQuestion("article-0001", "如何保证线程安全？", "Java语法", ("Java语法",)),
    ClassifiedQuestion("article-0002", "如何保证线程安全？", "JUC", ("JUC",)),
)
directory = ROOT / "output" / "favorites-smoke"
directory.mkdir(exist_ok=True)
page = build_html(ReportData("收藏夹验收", articles, questions))

# 通过页面自身的验收入口检查下载内容，保留真实导出流程。
harness = """<script>
const originalCreateObjectURL = URL.createObjectURL;
URL.createObjectURL = function (blob) {
  blob.text().then((source) => {
    const frame = document.getElementById('export-preview');
    frame.srcdoc = source;
    const parsed = new DOMParser().parseFromString(source, 'text/html');
    document.getElementById('export-check').textContent = JSON.stringify({
      originals: parsed.querySelectorAll('[data-domain-section] .question-card').length,
      starred: parsed.querySelectorAll('[data-domain-section] [data-favorited="true"]').length,
      copies: parsed.querySelectorAll('#favorite-list .question-card').length
    });
  });
  return originalCreateObjectURL.call(URL, blob);
};
</script>
<p id="export-check" aria-live="polite"></p>
<iframe id="export-preview" title="导出报告预览" style="width:100%;height:700px"></iframe>
"""
(directory / "index.html").write_text(page.replace("</body>", harness + "</body>"), encoding="utf-8")
blocked = page.replace("<script>\n(function", "<script>\nObject.defineProperty(window, 'localStorage', {get() {throw new Error('测试存储被禁用');}});\n(function", 1)
(directory / "storage-blocked.html").write_text(blocked, encoding="utf-8")
corrupted = page.replace("<script>\n(function", "<script>\nlocalStorage.setItem('interview-report:favorites:v1:' + document.querySelector('meta[name=interview-report-id]').content, '{损坏数据');\n(function", 1)
(directory / "storage-corrupted.html").write_text(corrupted, encoding="utf-8")
seeded = build_html(ReportData("导出快照验收", articles, questions)).replace('data-favorited="false"', 'data-favorited="true"', 1)
(directory / "exported-snapshot.html").write_text(seeded, encoding="utf-8")
(directory / "empty.html").write_text(build_html(ReportData("空收藏夹验收", (), ())), encoding="utf-8")
print(f"已生成验收页面：{directory}")
