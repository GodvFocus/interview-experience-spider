"""复用已有题目升级当前 HTML 报告，不重新抓取或分类。"""

import hashlib
import re
from pathlib import Path
import sys
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from generate_report import (
    Article,
    ClassifiedQuestion,
    _FAVORITE_BUTTON_HTML,
    _FAVORITES_NAV_HTML,
    _FAVORITES_SECTION_HTML,
    _INTERACTION_JS,
    _LIGHT_CSS,
    _favorite_key,
)


def question_snapshot(soup):
    result = []
    for card in soup.select("[data-domain-section] .question-card"):
        heading = BeautifulSoup(str(card.select_one(".question-text")), "html.parser")
        for element in heading.select(".question-number, .favorite-question"):
            element.decompose()
        source = card.select_one(".source-link")
        result.append((card["data-question-id"], card["data-domain"], heading.get_text(), source.get_text(), source.get("href")))
    return result


def upgrade(path):
    original = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(original, "html.parser")
    if soup.select_one("#favorites"):
        updated = re.sub(r'<style>.*?</style>', lambda _: f"<style>{_LIGHT_CSS}</style>", original, count=1, flags=re.S)
        updated = re.sub(r'<script>.*?</script>', lambda _: f"<script>{_INTERACTION_JS}</script>", updated, count=1, flags=re.S)
        assert question_snapshot(BeautifulSoup(updated, "html.parser")) == question_snapshot(soup)
        if updated != original:
            temporary = path.with_suffix(".html.tmp")
            temporary.write_text(updated, encoding="utf-8")
            temporary.replace(path)
        print(f"已同步收藏样式与交互：{path.name}")
        return
    before = question_snapshot(soup)
    keys = {}
    cards_by_id = {card["data-question-id"]: card for card in soup.select("[data-domain-section] .question-card")}
    for question_id, domain, question_text, source_text, url in before:
        card = cards_by_id[question_id]
        source_id = card["data-source-id"]
        host = urlsplit(url or "").hostname or ""
        platform = "nowcoder" if host.endswith("nowcoder.com") else "xiaohongshu"
        article = Article(source_id, platform, source_text.removeprefix("来源："), url or "", "")
        question = ClassifiedQuestion(source_id, question_text, domain, (domain,))
        keys[question_id] = _favorite_key(question, article)

    def add_key(match):
        opening = match.group(0)
        question_id = re.search(r'data-question-id="([^"]+)"', opening).group(1)
        return opening[:-1] + f' data-favorite-key="{keys[question_id]}" data-favorited="false">'

    updated = re.sub(r'<article class="question-card"[^>]+>', add_key, original)
    updated, stars = re.subn(r'(<h3 class="question-text">.*?)(</h3>)', lambda match: match[1] + _FAVORITE_BUTTON_HTML + match[2], updated, flags=re.S)
    updated, styles = re.subn(r'<style>.*?</style>', lambda _: f"<style>{_LIGHT_CSS}</style>", updated, count=1, flags=re.S)
    updated, scripts = re.subn(r'<script>.*?</script>', lambda _: f"<script>{_INTERACTION_JS}</script>", updated, count=1, flags=re.S)
    overview = '<a class="nav-link" href="#summary">概览</a>'
    section = '<section aria-labelledby="domain-title">'
    status = '<span class="toolbar-status" id="cleanup-status" aria-live="polite"></span>'
    assert all(marker in updated for marker in (overview, section, status))
    updated = updated.replace(overview, overview + _FAVORITES_NAV_HTML, 1)
    updated = updated.replace(section, _FAVORITES_SECTION_HTML + "\n    " + section, 1)
    updated = updated.replace(status, status + '\n      <span class="toolbar-status" id="favorite-status" aria-live="polite" hidden></span>', 1)
    report_id = hashlib.sha256(soup.title.get_text().encode("utf-8")).hexdigest()
    updated = updated.replace("</head>", f'<meta name="interview-report-id" content="{report_id}">\n</head>', 1)
    after = BeautifulSoup(updated, "html.parser")
    assert question_snapshot(after) == before, "升级不应改变已有题目、领域、编号或来源"
    assert stars == len(before) and styles == scripts == 1
    assert len(after.select(".favorite-question")) == len(before)
    temporary = path.with_suffix(".html.tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(path)
    print(f"已升级 {path.name}：{len(before)} 道题，题目与来源校验一致")


if __name__ == "__main__":
    for name in ("面经.html", "面试备考手册.html"):
        upgrade(ROOT / "output" / name)
