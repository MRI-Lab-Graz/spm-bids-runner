"""Long silent steps must show they are alive (the Mac test looked stuck during ~30 min of silent estimation)."""
import contextlib
import io
import sys
import unittest
from unittest.mock import patch

import lib.utils as utils


def _capture(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        result = fn()
    return result, buf.getvalue()


class TestFmtElapsed(unittest.TestCase):
    def test_seconds_under_a_minute(self):
        self.assertEqual(utils.fmt_elapsed(45), "45 s")

    def test_minutes_from_one_minute(self):
        self.assertEqual(utils.fmt_elapsed(60), "1 min")
        self.assertEqual(utils.fmt_elapsed(725), "12 min")


class TestRunCommandHeartbeat(unittest.TestCase):
    def test_silent_command_prints_still_running(self):
        cmd = [sys.executable, "-c", "import time; time.sleep(2.5)"]
        with patch.object(utils, "HEARTBEAT_SECONDS", 1):
            ok, out = _capture(lambda: utils.run_command(cmd))
        self.assertTrue(ok)
        self.assertIn("still running", out)
        self.assertIn("no output is normal", out)

    def test_fast_command_prints_no_heartbeat(self):
        ok, out = _capture(lambda: utils.run_command([sys.executable, "-c", "print('hi')"]))
        self.assertTrue(ok)
        self.assertNotIn("still running", out)

    def test_failure_exit_code_still_fails_with_heartbeat(self):
        cmd = [sys.executable, "-c", "import time, sys; time.sleep(1.5); sys.exit(3)"]
        with patch.object(utils, "HEARTBEAT_SECONDS", 1):
            ok, _ = _capture(lambda: utils.run_command(cmd))
        self.assertFalse(ok)


import time
from concurrent.futures import ThreadPoolExecutor

import lib.fast_smooth as fs


class TestSmoothHeartbeat(unittest.TestCase):
    """ThreadPoolExecutor stands in for the process pool so the patched worker is visible (spawn on macOS)."""

    def _run(self):
        def slow(config, subject, task, force):
            time.sleep(2.5 if subject == "02" else 0.1)
            return {"status": "ok", "message": ""}
        with patch.object(fs, "ProcessPoolExecutor", ThreadPoolExecutor), \
                patch.object(fs, "smooth_subject", slow), \
                patch.object(utils, "HEARTBEAT_SECONDS", 1):
            return _capture(lambda: fs.smooth_subjects_parallel(None, ["01", "02"], "t", max_workers=2))

    def test_prints_still_smoothing_while_a_subject_is_pending(self):
        _, out = self._run()
        self.assertIn("still smoothing 1 of 2 subject(s)", out)

    def test_results_are_unchanged(self):
        results, _ = self._run()
        self.assertEqual(results, {"01": {"status": "ok", "message": ""}, "02": {"status": "ok", "message": ""}})


import tempfile
from pathlib import Path

import lib.core as core
from lib.config import ContainerConfig
from tests.test_core_helpers import _make_config


class TestEstimationNote(unittest.TestCase):
    def test_stats_step_says_silence_is_normal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.json"
            model.write_text("{}", encoding="utf-8")
            pipeline = core.Pipeline(core.PipelineOptions(actions=["stats"], force=True, dry_run=True))
            pipeline.config = _make_config(root)
            pipeline.model_file_path = model
            pipeline.container_config = ContainerConfig(container_type="docker", docker_image="bidspm/test:latest")
            pipeline.setup = lambda: True
            pipeline.get_subjects_to_process = lambda: ["01"]
            logged = []
            with patch.object(core.Pipeline, "_log", lambda self, msg: logged.append(msg)), \
                    patch("lib.core.validate_space_availability", return_value=True), \
                    patch("lib.core.validate_events_availability", return_value=True), \
                    patch("lib.core.ensure_derivatives_dataset_description"), \
                    patch("lib.core.cleanup_tmp_directories"):
                pipeline.run()
        note = [m for m in logged if "Estimation is slow" in m]
        self.assertEqual(len(note), 1)
        self.assertIn("do not restart Docker", note[0])
