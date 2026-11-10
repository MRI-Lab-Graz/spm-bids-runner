# Progress heartbeat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Long silent steps (container runs, fast smoothing, estimation) show they are alive, how long they have run, and that silence is normal.

**Architecture:** `lib/utils.py` gets one constant `HEARTBEAT_SECONDS = 60`, a formatter `fmt_elapsed`, and passes an `on_idle` to `run_streaming_command` from `run_command`. `lib/fast_smooth.py` replaces its `as_completed` loop with `concurrent.futures.wait(timeout=...)`. `lib/core.py` logs one expectation line at the start of the stats step. Output is stdout only; `webapp/` is untouched.

**Tech Stack:** Python stdlib, unittest (`python -m pytest -q tests`).

## Global Constraints

Spec: `docs/superpowers/specs/2026-11-10-progress-heartbeat-design.md`.
- Heartbeat interval 60 s, a module constant so tests can shrink it; read at call time (`utils.HEARTBEAT_SECONDS`).
- Heartbeat lines go to stdout only, never to the log file.
- Return values, failure markers and error handling of `run_command` and `smooth_subjects_parallel` stay unchanged.
- Tests first (CLAUDE.md); `python -m pytest -q tests` green before merge.

---

### Task 1: Heartbeat in `run_command`

**Files:**
- Modify: `lib/utils.py` (`run_command`, new `HEARTBEAT_SECONDS`, `fmt_elapsed`)
- Test: `tests/test_progress_heartbeat.py` (create)

**Interfaces:**
- Produces: `lib.utils.HEARTBEAT_SECONDS: float`, `lib.utils.fmt_elapsed(seconds: float) -> str` ("45 s" under a minute, else "12 min").

- [ ] **Step 1: Write the failing tests** (`tests/test_progress_heartbeat.py`)

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest -q tests/test_progress_heartbeat.py`
Expected: FAIL (`fmt_elapsed` / `HEARTBEAT_SECONDS` missing).

- [ ] **Step 3: Implement** in `lib/utils.py`, above `run_command`

```python
HEARTBEAT_SECONDS = 60  # silence before a "still running" line; tests shrink it


def fmt_elapsed(seconds: float) -> str:
    return f"{int(seconds // 60)} min" if seconds >= 60 else f"{int(seconds)} s"
```

and in `run_command`, replace the `run_streaming_command(...)` call with

```python
    started = time.monotonic()

    def beat(_idle: float) -> None:
        print(f"⏳ still running, {fmt_elapsed(time.monotonic() - started)} elapsed "
              "(no output is normal for this step)", flush=True)

    result = run_streaming_command(cmd_list, capture_output=capture_output,
                                   on_output=watch if failure_markers else None,
                                   on_idle=beat, idle_timeout_seconds=HEARTBEAT_SECONDS)
```

- [ ] **Step 4: Verify**

Run: `python -m pytest -q tests/test_progress_heartbeat.py tests/test_run_command_markers.py`
Expected: PASS.

- [ ] **Step 5: Commit** `git add lib/utils.py tests/test_progress_heartbeat.py && git commit -m "feat: run_command prints a still-running heartbeat during silent steps"`

### Task 2: Fast-smoothing heartbeat

**Files:**
- Modify: `lib/fast_smooth.py` (`smooth_subjects_parallel`, imports)
- Test: `tests/test_progress_heartbeat.py`

**Interfaces:**
- Consumes: `lib.utils.HEARTBEAT_SECONDS`, `lib.utils.fmt_elapsed`.

- [ ] **Step 1: Failing test** (append to `tests/test_progress_heartbeat.py`)

```python
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
```

- [ ] **Step 2: Run** `python -m pytest -q tests/test_progress_heartbeat.py -k Smooth` → FAIL (no heartbeat line).

- [ ] **Step 3: Implement** in `lib/fast_smooth.py`: imports `import time`, `from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait`, `from . import utils`; replace the loop

```python
        started = time.monotonic()
        pending = set(futures)
        while pending:
            done, pending = wait(pending, timeout=utils.HEARTBEAT_SECONDS, return_when=FIRST_COMPLETED)
            if not done:
                print(f"⏳ still smoothing {len(pending)} of {len(futures)} subject(s), "
                      f"{utils.fmt_elapsed(time.monotonic() - started)} elapsed "
                      "(copying/decompressing and smoothing large files takes a while)", flush=True)
            for future in done:
                subject = futures[future]
                try:
                    results[subject] = future.result()
                except Exception as exc:
                    results[subject] = {"status": "error", "message": str(exc)}
```

- [ ] **Step 4: Verify** `python -m pytest -q tests/test_progress_heartbeat.py tests/test_fast_smooth.py` → PASS.
- [ ] **Step 5: Commit** `git commit -am "feat: fast smoothing prints a still-smoothing heartbeat"` (add the test file too).

### Task 3: Estimation expectation line

**Files:**
- Modify: `lib/core.py` (stats step in `_process_subject`)
- Test: `tests/test_progress_heartbeat.py`

- [ ] **Step 1: Failing test** (append; mirrors the dry-run harness in `tests/test_core_helpers.py`)

```python
import tempfile

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
```

- [ ] **Step 2: Run** `-k Estimation` → FAIL (no such line).
- [ ] **Step 3: Implement** in `lib/core.py`: module constant

```python
_ESTIMATION_NOTE = ("Estimation is slow (about 30 min for a 1000-volume run) and prints nothing while it works. "
                    "This is normal; please do not restart Docker meanwhile.")
```

and right after `self._log(f">>> Stats: subject {subject}, task {task}")` add `self._log(_ESTIMATION_NOTE)`.

- [ ] **Step 4: Verify** `python -m pytest -q tests` → all green.
- [ ] **Step 5: Commit** `git commit -am "feat: stats step says up front that silent estimation is normal"`.

### Wrap-up

Merge gate (CLAUDE.md): pytest green, `/ponytail:ponytail-review`, `/security-review` on the branch diff; findings resolved or deferred in the merge message.
