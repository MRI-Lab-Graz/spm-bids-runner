"""Suggest a sensible 'Parallel subjects' value for this machine (not everyone has 32 cores)."""
import re
import unittest

import subprocess
from unittest.mock import patch

from lib import utils
from lib.utils import suggest_stats_workers


class TestSuggestStatsWorkers(unittest.TestCase):
    def test_big_machine_is_capped(self):
        self.assertEqual(suggest_stats_workers(32, 146)["suggested"], 16)

    def test_leaves_headroom_for_the_system(self):
        self.assertEqual(suggest_stats_workers(8, 64)["suggested"], 6)
        self.assertEqual(suggest_stats_workers(4, 64)["suggested"], 3)

    def test_memory_can_be_the_limit(self):
        # ~4 GB per heavy worker
        self.assertEqual(suggest_stats_workers(8, 8)["suggested"], 2)

    def test_unknown_memory_is_ignored(self):
        self.assertEqual(suggest_stats_workers(8, None)["suggested"], 6)

    def test_tiny_or_unknown_machine_gets_one(self):
        self.assertEqual(suggest_stats_workers(1, 2)["suggested"], 1)
        self.assertEqual(suggest_stats_workers(None, None)["suggested"], 1)
        self.assertEqual(suggest_stats_workers(2, 1)["suggested"], 1)

    def test_reports_inputs(self):
        r = suggest_stats_workers(8, 64)
        self.assertEqual((r["cpus"], r["mem_available_gb"]), (8, 64))


class TestMemoryOnMacOs(unittest.TestCase):
    """macOS has no /proc/meminfo, and Docker Desktop's VM (not the Mac) is what the containers can use."""

    def test_docker_memory_is_read_from_docker_info_in_gb(self):
        done = subprocess.CompletedProcess(["docker"], 0, b"8589934592\n", b"")
        with patch("lib.utils.shutil.which", return_value="/usr/bin/docker"), \
             patch("lib.utils.subprocess.run", return_value=done) as run:
            self.assertEqual(utils.docker_memory_gb(), 8.0)
        self.assertEqual(run.call_args[0][0], ["docker", "info", "--format", "{{.MemTotal}}"])

    def test_docker_memory_unknown_when_docker_is_missing_stopped_or_odd(self):
        with patch("lib.utils.shutil.which", return_value=None):
            self.assertIsNone(utils.docker_memory_gb())
        with patch("lib.utils.shutil.which", return_value="/usr/bin/docker"):
            for result in (subprocess.CompletedProcess(["docker"], 1, b"", b"Cannot connect"),
                           subprocess.CompletedProcess(["docker"], 0, b"not a number", b"")):
                with patch("lib.utils.subprocess.run", return_value=result):
                    self.assertIsNone(utils.docker_memory_gb())
            with patch("lib.utils.subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 10)):
                self.assertIsNone(utils.docker_memory_gb())

    def test_without_proc_meminfo_the_docker_vm_sets_the_limit(self):
        with patch("lib.utils._proc_mem_available_gb", return_value=None), patch("lib.utils.docker_memory_gb", return_value=8.0), \
             patch("lib.utils.os.cpu_count", return_value=10):
            r = utils.system_resources()
            self.assertEqual(r["mem_available_gb"], 8.0)
            self.assertEqual(suggest_stats_workers(**r)["suggested"], 2)  # not 8 (cpus - 2)

    def test_the_smaller_of_host_and_docker_wins(self):
        for host, docker, want in ((4.0, 64.0, 4.0), (64.0, 8.0, 8.0), (16.0, None, 16.0), (None, None, None)):
            with patch("lib.utils._proc_mem_available_gb", return_value=host), patch("lib.utils.docker_memory_gb", return_value=docker):
                self.assertEqual(utils.system_resources()["mem_available_gb"], want)


class TestFormDefaultMatchesProjectDefault(unittest.TestCase):
    def test_html_and_js_fallbacks_use_the_project_default(self):
        from pathlib import Path
        from lib.project_manager import ProjectConfig
        root, n = Path(__file__).resolve().parent.parent, ProjectConfig().stats_workers
        html = (root / "templates" / "analysis.html").read_text(encoding="utf-8")
        js = (root / "static" / "js" / "analysis_project_form.js").read_text(encoding="utf-8")
        self.assertIn(f'id="stats_workers" name="stats_workers" value="{n}"', html)
        self.assertEqual(js.count(f"stats_workers')?.value) || {n}"), 2)
