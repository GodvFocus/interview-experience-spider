import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_all


class EntrypointTests(unittest.TestCase):
    def test_run_all_passes_the_loaded_config_to_report_generator(self):
        config = {
            "classifier": {"provider": "deepseek"},
            "deepseek": {
                "api_key": "test-key",
                "base_url": "https://example.com",
                "model": "test-model",
                "batch_max_articles": 2,
                "batch_max_chars": 100,
            },
            "output": {
                "dir": "",
                "title": "统一入口",
                "formats": ["md", "html"],
            },
            "filter": {"mode": "backend"},
        }
        old_cwd = os.getcwd()
        old_argv = sys.argv[:]
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config["output"]["dir"] = str(Path(temp_dir) / "output")
            config_path.write_text(json.dumps(config), encoding="utf-8")
            captured = {}

            def fake_report_run(**kwargs):
                captured.update(kwargs)
                return {"md": "report.md", "html": "report.html"}

            try:
                sys.argv = [
                    "run_all.py",
                    "--report-only",
                    "--skip-xhs",
                    "--config",
                    str(config_path),
                ]
                with patch.object(run_all, "check_env"), patch.object(
                    run_all, "_open_in_browser"
                ), patch("generate_report.run", side_effect=fake_report_run):
                    self.assertEqual(run_all.main(), 0)
            finally:
                sys.argv = old_argv
                os.chdir(old_cwd)

        self.assertEqual(captured["config"], config)
        self.assertEqual(captured["filter_mode"], "backend")
        self.assertEqual(captured["output_dir"], config["output"]["dir"])

    def test_run_all_rejects_missing_deepseek_key_before_report_step(self):
        config = {
            "classifier": {"provider": "deepseek"},
            "deepseek": {"api_key": ""},
            "output": {"dir": "", "title": "缺 key", "formats": ["md", "html"]},
        }
        old_cwd = os.getcwd()
        old_argv = sys.argv[:]
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config["output"]["dir"] = str(Path(temp_dir) / "output")
            config_path.write_text(json.dumps(config), encoding="utf-8")
            try:
                sys.argv = [
                    "run_all.py",
                    "--report-only",
                    "--config",
                    str(config_path),
                ]
                with patch.object(run_all, "check_env"), patch(
                    "generate_report.run"
                ) as report_run:
                    self.assertEqual(run_all.main(), 1)
                    report_run.assert_not_called()
            finally:
                sys.argv = old_argv
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
