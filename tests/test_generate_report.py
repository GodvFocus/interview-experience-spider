import json
import tempfile
import unittest
from pathlib import Path

from generate_report import (
    Article,
    ClassificationError,
    DeepSeekClassifier,
    ReportGenerationError,
    build_article_batches,
    run,
    validate_classification_result,
)


class DeterministicClassifier:
    def __init__(self, question_factory=None):
        self.calls = []
        self.question_factory = question_factory or self._default_questions

    def classify(self, articles):
        articles = list(articles)
        self.calls.append(articles)
        return {"questions": self.question_factory(articles)}

    @staticmethod
    def _default_questions(articles):
        questions = []
        for article in articles:
            questions.append(
                {
                    "article_id": article.article_id,
                    "question": f"如何分析 {article.title}",
                    "primary_domain": "Java",
                    "domains": ["Java", "Spring Boot"],
                }
            )
        return questions


def write_posts(directory, name, posts):
    path = Path(directory) / name
    path.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
    return str(path)


class GenerateReportTests(unittest.TestCase):
    def make_posts(self):
        return [
            {
                "title": "Java 面经 <标题>",
                "content": "明确问题：如何保证线程安全？\n" + "完整正文" * 100,
                "url": "https://example.com/java",
                "source": "nowcoder",
            },
            {
                "title": "Redis 场景面经",
                "content": "请设计一个缓存系统，并说明一致性处理。",
                "url": "https://example.com/redis",
                "source": "xiaohongshu",
            },
        ]

    def test_report_follows_fixed_domains_and_keeps_full_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = write_posts(temp_dir, "nc.json", self.make_posts()[:1])
            xhs_file = write_posts(temp_dir, "xhs.json", self.make_posts()[1:])
            output_dir = Path(temp_dir) / "reports"

            def questions(articles):
                return [
                    {
                        "article_id": articles[0].article_id,
                        "question": "设计缓存一致性方案",
                        "primary_domain": "场景题",
                        "domains": ["场景题", "Redis"],
                    },
                    {
                        "article_id": articles[0].article_id,
                        "question": "设计缓存一致性方案",
                        "primary_domain": "Redis",
                        "domains": ["Redis"],
                    },
                    {
                        "article_id": articles[1].article_id,
                        "question": "Spring Boot 启动流程",
                        "primary_domain": "Spring Boot",
                        "domains": ["Spring Boot", "Java"],
                    },
                ]

            classifier = DeterministicClassifier(questions)
            results = run(
                nc_file=nc_file,
                xhs_file=xhs_file,
                output_dir=str(output_dir),
                title="测试报告",
                max_len=10,
                formats=["md", "html"],
                classifier=classifier,
                config={"deepseek": {"batch_max_articles": 5, "batch_max_chars": 12000}},
                verbose=False,
            )

            markdown = Path(results["md"]).read_text(encoding="utf-8")
            html = Path(results["html"]).read_text(encoding="utf-8")
            self.assertLess(markdown.index("## Redis"), markdown.index("## Spring全家桶"))
            self.assertLess(markdown.index("## 场景题"), markdown.index("## 其他")) if "## 其他" in markdown else None
            self.assertEqual(markdown.count("设计缓存一致性方案"), 2)
            self.assertIn("完整正文" * 100, markdown)
            self.assertNotIn("高频考点速查", markdown)
            self.assertIn("#domain", markdown)
            self.assertIn("source-article-0001", markdown)
            self.assertIn("source-article-0002", markdown)
            self.assertIn("--bg: #f5f7fb", html)
            self.assertIn("Spring全家桶", html)
            self.assertIn("<details", html)
            self.assertEqual(html.count('id="source-article-0001"'), 1)
            self.assertEqual(html.count('id="source-article-0002"'), 1)
            self.assertIn("下载清理版 HTML", html)
            self.assertIn('class="delete-question"', html)
            self.assertIn('id="undo-delete"', html)
            self.assertIn("data-domain-section", html)
            self.assertIn("new Blob", html)
            self.assertIn("&lt;标题&gt;", html)

    def test_missing_api_key_fails_before_writing_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = write_posts(temp_dir, "nc.json", self.make_posts()[:1])
            xhs_file = write_posts(temp_dir, "xhs.json", [])
            output_dir = Path(temp_dir) / "reports"

            with self.assertRaisesRegex(ReportGenerationError, "API key"):
                run(
                    nc_file=nc_file,
                    xhs_file=xhs_file,
                    output_dir=str(output_dir),
                    title="不会生成",
                    config={"deepseek": {"api_key": ""}},
                    verbose=False,
                )
            self.assertFalse(output_dir.exists())

    def test_batch_limits_and_long_article_are_preserved(self):
        articles = (
            Article("article-0001", "nowcoder", "短一", "https://a", "1234"),
            Article("article-0002", "nowcoder", "短二", "https://b", "12"),
            Article("article-0003", "nowcoder", "长文", "https://c", "123456789"),
        )
        batches = list(build_article_batches(articles, max_articles=2, max_chars=6))
        self.assertEqual(
            [[article.article_id for article in batch] for batch in batches],
            [["article-0001", "article-0002"], ["article-0003"]],
        )
        self.assertEqual(batches[-1][0].content, "123456789")

    def test_failed_batch_is_retried_and_then_split(self):
        class SplitClassifier:
            def __init__(self):
                self.calls = []

            def classify(self, articles):
                articles = list(articles)
                self.calls.append([a.article_id for a in articles])
                if len(articles) > 1:
                    raise ClassificationError("批次暂时失败", retryable=True)
                return {
                    "questions": [
                        {
                            "article_id": articles[0].article_id,
                            "question": "明确问题",
                            "primary_domain": "Java语法",
                            "domains": ["Java语法"],
                        }
                    ]
                }

        classifier = SplitClassifier()
        articles = (
            Article("article-0001", "nowcoder", "文章一", "https://a", "正文一"),
            Article("article-0002", "nowcoder", "文章二", "https://b", "正文二"),
        )
        from generate_report import classify_articles

        questions = classify_articles(
            articles,
            classifier,
            max_articles=5,
            max_chars=12000,
        )
        self.assertEqual(len(questions), 2)
        self.assertEqual(classifier.calls[:3], [["article-0001", "article-0002"]] * 3)
        self.assertEqual(classifier.calls[3:], [["article-0001"], ["article-0002"]])

    def test_single_article_failure_stops_generation_without_leaking_key(self):
        class AlwaysFailClassifier:
            def classify(self, articles):
                raise ClassificationError("服务端拒绝", retryable=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = write_posts(
                temp_dir,
                "nc.json",
                [
                    {
                        "title": "失败文章",
                        "content": "正文",
                        "url": "https://example.com/failure",
                        "source": "nowcoder",
                    }
                ],
            )
            xhs_file = write_posts(temp_dir, "xhs.json", [])
            output_dir = Path(temp_dir) / "reports"
            with self.assertRaisesRegex(ReportGenerationError, "失败文章") as error:
                run(
                    nc_file=nc_file,
                    xhs_file=xhs_file,
                    output_dir=str(output_dir),
                    title="失败报告",
                    classifier=AlwaysFailClassifier(),
                    config={"deepseek": {}},
                    verbose=False,
                )
            self.assertNotIn("sk-secret", str(error.exception))
            self.assertFalse(output_dir.exists())

    def test_two_generations_call_classifier_twice_without_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = write_posts(temp_dir, "nc.json", self.make_posts()[:1])
            xhs_file = write_posts(temp_dir, "xhs.json", [])
            classifier = DeterministicClassifier()
            for index in (1, 2):
                run(
                    nc_file=nc_file,
                    xhs_file=xhs_file,
                    output_dir=str(Path(temp_dir) / f"reports-{index}"),
                    title=f"报告{index}",
                    classifier=classifier,
                    config={"deepseek": {}},
                    verbose=False,
                )
            self.assertEqual(len(classifier.calls), 2)

    def test_unknown_domain_is_not_published_and_other_is_valid(self):
        article = Article("article-0001", "nowcoder", "文章", "https://a", "正文")
        questions = validate_classification_result(
            {
                "questions": [
                    {
                        "article_id": "article-0001",
                        "question": "一个无法匹配的问题",
                        "primary_domain": "自定义领域",
                        "domains": ["自定义领域"],
                    },
                    {
                        "article_id": "article-0001",
                        "question": "另一个问题",
                        "primary_domain": "其他",
                        "domains": ["其他"],
                    },
                    {
                        "article_id": "article-0001",
                        "question": "带技术标签的方案题",
                        "primary_domain": "Redis",
                        "domains": ["Redis", "场景题"],
                    },
                ]
            },
            [article],
        )
        self.assertEqual(questions[0].primary_domain, "其他")
        self.assertEqual(questions[0].domains, ("其他",))
        self.assertEqual(questions[1].primary_domain, "其他")
        self.assertEqual(questions[2].primary_domain, "场景题")

    def test_deepseek_request_contains_complete_articles_without_exposing_key(self):
        class Response:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "choices": [
                        {
                            "message": {
                                "content": '{"questions": []}',
                            }
                        }
                    ]
                }

        class Session:
            def __init__(self):
                self.request = None

            def post(self, url, **kwargs):
                self.request = (url, kwargs)
                return Response()

        session = Session()
        classifier = DeepSeekClassifier(
            "sk-secret",
            base_url="https://example.com",
            model="test-model",
            session=session,
        )
        article = Article("article-0001", "nowcoder", "完整标题", "https://a", "完整正文" * 20)
        self.assertEqual(classifier.classify([article]), {"questions": []})
        url, request = session.request
        self.assertEqual(url, "https://example.com/chat/completions")
        self.assertIn("完整正文" * 20, request["json"]["messages"][1]["content"])
        self.assertIn("article-0001", request["json"]["messages"][1]["content"])
        self.assertNotIn("sk-secret", request["json"]["messages"][1]["content"])

    def test_untrusted_titles_questions_and_sources_are_escaped_in_html(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = write_posts(
                temp_dir,
                "nc.json",
                [
                    {
                        "title": "\"><script>alert(1)</script>",
                        "content": "<script>alert(2)</script> & 原文",
                        "url": "javascript:alert(3)",
                        "source": "nowcoder",
                    }
                ],
            )
            xhs_file = write_posts(temp_dir, "xhs.json", [])

            class UnsafeClassifier:
                def classify(self, articles):
                    return {
                        "questions": [
                            {
                                "article_id": articles[0].article_id,
                                "question": "<img src=x onerror=alert(4)>",
                                "primary_domain": "Java语法",
                                "domains": ["Java语法"],
                            }
                        ]
                    }

            result = run(
                nc_file=nc_file,
                xhs_file=xhs_file,
                output_dir=str(Path(temp_dir) / "reports"),
                title="安全测试",
                classifier=UnsafeClassifier(),
                config={"deepseek": {}},
                verbose=False,
            )
            html = Path(result["html"]).read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertNotIn("<script>alert(2)</script>", html)
            self.assertNotIn("<img src=x onerror=alert(4)>", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertIn("&lt;script&gt;alert(2)&lt;/script&gt;", html)
            self.assertNotIn("javascript:alert(3)", html)

    def test_invalid_result_is_retried_before_success(self):
        class FlakyClassifier:
            def __init__(self):
                self.calls = 0

            def classify(self, articles):
                self.calls += 1
                if self.calls == 1:
                    return {"questions": [{"article_id": "wrong", "question": "坏结果"}]}
                return {
                    "questions": [
                        {
                            "article_id": articles[0].article_id,
                            "question": "恢复后的问题",
                            "primary_domain": "其他",
                            "domains": ["其他"],
                        }
                    ]
                }

        from generate_report import classify_articles

        classifier = FlakyClassifier()
        questions = classify_articles(
            [Article("article-0001", "nowcoder", "文章", "https://a", "正文")],
            classifier,
        )
        self.assertEqual(classifier.calls, 2)
        self.assertEqual(questions[0].question, "恢复后的问题")

    def test_auth_failure_does_not_split_or_retry(self):
        class UnauthorizedResponse:
            status_code = 401

            @staticmethod
            def json():
                return {"error": {"message": "unauthorized"}}

        class Session:
            def __init__(self):
                self.calls = 0

            def post(self, *args, **kwargs):
                self.calls += 1
                return UnauthorizedResponse()

        from generate_report import classify_articles

        session = Session()
        classifier = DeepSeekClassifier("sk-secret", session=session)
        articles = [
            Article("article-0001", "nowcoder", "文章一", "https://a", "正文一"),
            Article("article-0002", "nowcoder", "文章二", "https://b", "正文二"),
        ]
        with self.assertRaisesRegex(ReportGenerationError, "API key"):
            classify_articles(articles, classifier)
        self.assertEqual(session.calls, 1)

    def test_invalid_source_json_is_reported_without_traceback_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nc_file = Path(temp_dir) / "nc.json"
            nc_file.write_text(json.dumps(["不是面经对象"]), encoding="utf-8")
            xhs_file = write_posts(temp_dir, "xhs.json", [])
            with self.assertRaisesRegex(ReportGenerationError, "非对象条目"):
                run(
                    nc_file=str(nc_file),
                    xhs_file=xhs_file,
                    output_dir=str(Path(temp_dir) / "reports"),
                    title="格式错误",
                    classifier=DeterministicClassifier(),
                    config={"deepseek": {}},
                    verbose=False,
                )


if __name__ == "__main__":
    unittest.main()
