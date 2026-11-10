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
