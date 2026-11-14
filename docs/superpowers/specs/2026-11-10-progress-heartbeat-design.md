# Progress heartbeat for long silent steps

Date: 2026-11-10. Status: design approved by the user, spec awaiting review.

## Problem

On the arm64 Mac test (study 141, one subject) the first-level estimation prints nothing for about 30 minutes
(SPM reports no progress while it works) and fast smoothing prints nothing while it decompresses and smooths a
2.4 GB file. The run looks stuck. During the Mac test the user opened Docker Desktop to look and installed an
update, which restarted the Docker VM and killed the run. The pipeline was healthy; the silence caused the
intervention.

## Scope

- Show that a long step is alive, how long it has been running, and that silence is normal there.
- Console and GUI together: the GUI streams the CLI's stdout (`/stream/<id>`), so the change lives in `lib/`
  and nothing in `webapp/` changes.
- Not in scope: real percent progress. SPM prints nothing during estimation; deriving a percentage would mean
  watching SPM's files, which is fragile across SPM versions.

## Design

### 1. Container steps: heartbeat in `run_command` (`lib/utils.py`)

`run_streaming_command` already has an unused `on_idle(idle_seconds)` hook (`idle_timeout_seconds`). `run_command`
passes an `on_idle` that prints

    ⏳ still running, 12 min elapsed (no output is normal for this step)

after every `HEARTBEAT_SECONDS` (60, module constant so tests can shrink it) of silence. Elapsed time is measured
from the command's start. The line goes to stdout only, not the log file. Every container step goes through
`run_command` (per-subject stats, dataset stats, smoothing via SPM), so all get it.

### 2. Estimation: expectation line (`lib/core.py`, stats step)

Directly after `>>> Stats: subject X, task Y` log one line:

    First-level estimation is slow (about 30 min for a 1000-volume run) and prints nothing while it works.
    This is normal. Please do not restart Docker meanwhile.

### 3. Fast smoothing: heartbeat in `smooth_subjects_parallel` (`lib/fast_smooth.py`)

The work runs in worker processes, so the parent reports. Replace the `as_completed` loop with
`concurrent.futures.wait(pending, timeout=HEARTBEAT_SECONDS, return_when=FIRST_COMPLETED)` and, whenever a wait
times out with subjects still pending, print

    ⏳ still smoothing 2 of 3 subject(s), 4 min elapsed (copying/decompressing and smoothing large files takes a while)

Result collection and error handling stay exactly as they are.

## Testing (TDD, tests first)

- `run_command` on a Python child that sleeps with `HEARTBEAT_SECONDS` patched to 1: stdout contains the
  "still running" line; a fast command prints none; return values and failure markers are unchanged
  (existing `tests/test_run_command_markers.py` stays green).
- Stats step in dry-run: the expectation line is logged.
- `smooth_subjects_parallel` with a patched slow `smooth_subject` and `HEARTBEAT_SECONDS` patched to 1: the
  "still smoothing" line appears and results are identical to the no-heartbeat case.

## Decisions

- Heartbeat interval 60 s: frequent enough to look alive, about 30 lines for a 30 min step.
- stdout only, so the log file does not fill with heartbeat lines.
- ponytail: the "about 30 min / 1000 volumes" figure is a fixed sentence from the server benchmark (28 min total
  for the study 141 test); make it data-driven only if users report it being badly wrong.
