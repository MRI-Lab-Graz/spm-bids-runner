# Rename to `spm-bids-runner` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Everything that is ours stops being called "bidspm" (CLI, GUI, env vars, venv, user data folder, titles, URLs) and is called `spm-bids-runner`, without losing the user's saved projects.

**Architecture:** A repo-wide guard test (red first) lists every old "ours" name; a mechanical `git mv` + `sed` pass fixes the bulk; a small `lib/data_dir.py` owns the user data folder and its one-time move from `~/.bidspm`; scripts and prose get hand edits; real runs verify.

**Tech Stack:** Python 3.12 (uv, `.bidspm` venv until Task 5 rebuilds it as `.venv`), pytest, bash/GNU sed, Flask GUI, Docker image (labels only).

Spec: `docs/superpowers/specs/2026-11-02-rename-spm-bids-runner-design.md` (branch `rename-spm-bids-runner`).

## Global Constraints

- Display name "SPM BIDS Runner"; identifiers `spm-bids-runner` / `spm_bids_runner` / `SPM_BIDS_RUNNER_*`.
- CLI `spm_bids_runner.py`, GUI `spm_bids_runner_gui.py`, activate script `scripts/activate.sh`, venv `.venv` (uv default, no `UV_PROJECT_ENVIRONMENT`), user data folder `~/.spm-bids-runner`.
- Renamed env vars (host side only): `PORT`, `VENV`, `PYTHON`, `TEST_IMAGE`, `PROJECT_ROOT`, `WIZARD_CONTEXT`, `TRANSFORMER_CONTEXT` (`SPM_BIDS_RUNNER_<NAME>`).
- **Kept (upstream or image interface):** the `bidspm` command in the image, `BIDSPM_TAG`, tag `v4.0.0`, `bidspm-preproc/`, `bidspm-stats/`, `Model.Software.bidspm`, `bidspm_overrides/`, `bidspm_version`, the log line `bidspm runner overrides:`, `LICENSE`/NOTICE credits, and the container-side env vars `BIDSPM_SKIP_RESULTS`, `BIDSPM_IGNORE_FIELDMAPS`, `BIDSPM_IGNORE_FIGURES`, `BIDSPM_SKIP_INTENDEDFOR_CHECK`, `BIDSPM_SKIP_ATLAS_INIT`, `BIDSPM_BMS_WORKER_ID` (an old image would silently ignore renamed ones).
- Not rewritten: `docs/superpowers/**`, `docs/roadmap-*.md` (history).
- TDD (CLAUDE.md): failing test first. Tests: `.bidspm/bin/python -m pytest -q tests` until Task 5 rebuilds the venv, then `.venv/bin/python -m pytest -q tests`.
- Never push, never publish an image, never rename the local checkout folder. Commit footer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Importing `lib` runs the data-folder migration (Task 3). The controller already stopped GUIs and made the backup `~/.bidspm.backup-2026-11-02` before dispatching (Task 6 Step 1's backup is therefore done; implementers must not repeat it or delete it). Tasks 2-5 run only the focused tests listed; the full suite is Task 6.

---

### Task 1: Correct the spec

The spec listed `BIDSPM_SKIP_RESULTS` as renamed. It is read by the image's `cliStats.m`, so it must stay.

**Files:**
- Modify: `docs/superpowers/specs/2026-11-02-rename-spm-bids-runner-design.md`

- [ ] **Step 1: Edit the env-var row and the kept list**

In the "Renamed" table replace the env-var row with:

```
| `BIDSPM_*` env vars of ours on the host (`PORT`, `VENV`, `PYTHON`, `TEST_IMAGE`, `PROJECT_ROOT`, `WIZARD_CONTEXT`, `TRANSFORMER_CONTEXT`) | `SPM_BIDS_RUNNER_*` |
```

In "Kept" add the bullet:

```
- Container-side env vars read by the image (`BIDSPM_SKIP_RESULTS`, `BIDSPM_IGNORE_FIELDMAPS`, `BIDSPM_IGNORE_FIGURES`, `BIDSPM_SKIP_INTENDEDFOR_CHECK`, `BIDSPM_SKIP_ATLAS_INIT`, `BIDSPM_BMS_WORKER_ID`) and the log line `bidspm runner overrides:`: they are an interface with the image; an older image would silently ignore a renamed variable.
```

In the Risks bullet about `docs/superpowers/` change "(old plans/specs)" to "(old plans/specs and `docs/roadmap-*.md`)".

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-11-02-rename-spm-bids-runner-design.md
git commit -m "docs: rename spec keeps container-side BIDSPM_ env vars" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Guard test (red)

**Files:**
- Create: `tests/test_naming.py`

**Interfaces:**
- Produces: `tests/test_naming.py` with `OLD_NAMES`, `EXEMPT_FILES`, `EXEMPT_PREFIXES`; two tests that fail until Task 4/5 finish. Task 3 adds `lib/data_dir.py` and `tests/test_data_dir_migration.py` to `EXEMPT_FILES` (already listed here).

- [ ] **Step 1: Write the test**

```python
"""What is ours is called spm-bids-runner; "bidspm" is only upstream's name.

Fails when a tracked (or new, unignored) file still uses an old name of ours. Upstream names are not listed
here, so they pass: the bidspm command, bidspm-preproc/, bidspm-stats/, Model.Software.bidspm, bidspm_overrides/,
the container-side BIDSPM_* variables, cpp-lln-lab/bidspm.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD_NAMES = [
    ("old script/module name", r"bidspm_gui|\bbidspm\.py\b|^\s*(import|from) bidspm\b"),
    ("old log/run name", r"run_bidspm"),
    ("old venv/data folder", r"(?<![\w-])\.bidspm\b"),
    ("old package name", r"bidspm[-_]runner"),
    ("old product name", r"BIDSPM [Rr]unner"),
    ("old host env var",
     r"BIDSPM_(PORT|VENV|PYTHON|TEST_IMAGE|PROJECT_ROOT|WIZARD_CONTEXT|TRANSFORMER_CONTEXT)\b"),
    ("old activate script", r"activate_bidspm"),
    ("old localStorage key", r"bidspm_validator_mode_"),
    ("old repo URL", r"MRI-Lab-Graz/bidspm\b"),
    ("old checkout folder", r"\bcd bidspm\b|\$\{HOME\}/bidspm\b|~/bidspm\b"),
]
OLD_PATHS = re.compile(r"(^|/)(bidspm\.py|bidspm_gui\.py|activate_bidspm\.sh|test_bidspm_\w+\.py)$")

# lib/data_dir.py and its test must name the old folder; this file lists the old names.
EXEMPT_FILES = {"lib/data_dir.py", "tests/test_data_dir_migration.py", "tests/test_naming.py", ".gitignore"}
# history is left as written; vendored files are not ours
EXEMPT_PREFIXES = ("docs/superpowers/", "docs/roadmap-", "static/vendor/")


def _files():
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split("\n")
    return [f for f in out if f and (ROOT / f).is_file()
            and f not in EXEMPT_FILES and not f.startswith(EXEMPT_PREFIXES)]


def test_no_old_names_in_file_contents():
    compiled = [(label, re.compile(rx)) for label, rx in OLD_NAMES]
    hits = []
    for f in _files():
        try:
            lines = (ROOT / f).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue  # binary (png, woff2)
        for n, line in enumerate(lines, 1):
            hits += [f"{f}:{n}: [{label}] {line.strip()[:90]}" for label, rx in compiled if rx.search(line)]
    assert not hits, f"{len(hits)} old names:\n" + "\n".join(hits[:60])


def test_no_old_names_in_file_paths():
    hits = [f for f in _files() if OLD_PATHS.search(f)]
    assert not hits, "files still carry an old name:\n" + "\n".join(hits)
```

- [ ] **Step 2: Run it and confirm it fails with many hits**

Run: `.bidspm/bin/python -m pytest -q tests/test_naming.py`
Expected: 2 FAILED; the first lists hundreds of lines such as `bidspm_gui.py:...`, `README.md:...: [old venv/data folder] ...`; the second lists `bidspm.py`, `bidspm_gui.py`, `scripts/activate_bidspm.sh`, `tests/test_bidspm_*.py`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_naming.py
git commit -m "test: guard against old bidspm names of ours (red)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: User data folder and its one-time move

**Files:**
- Create: `lib/data_dir.py`
- Create: `tests/test_data_dir_migration.py`
- Modify: `lib/project_manager.py:26` and the docstring at `lib/project_manager.py:158`
- Modify: `lib/utils.py:18-19`

**Interfaces:**
- Produces: `lib.data_dir.OLD_NAME = ".bidspm"`, `NEW_NAME = ".spm-bids-runner"`, `migrate_legacy_data_dir(home: Path) -> bool` (True when it moved), `resolve_data_dir(home: Path | None = None) -> Path` (migrates, returns `home/NEW_NAME`), `DATA_DIR: Path`.
- Consumes: nothing. `lib/project_manager.py` and `lib/utils.py` import `DATA_DIR` from it; the global `project_manager = ProjectManager()` (`lib/project_manager.py:430`) creates folders at import, which is why the move must happen inside `lib.data_dir` at import, before that line.

- [ ] **Step 1: Write the failing tests**

```python
import json

from lib.data_dir import NEW_NAME, OLD_NAME, migrate_legacy_data_dir, resolve_data_dir


def _make_old(home):
    old = home / OLD_NAME
    proj = old / "projects" / "proj_1"
    proj.mkdir(parents=True)
    (proj / "project.json").write_text(json.dumps({"dir": f"{old}/projects/proj_1", "bids": f"{home}/study/rawdata"}))
    (old / "logs").mkdir()
    (old / "logs" / "a.log").write_text(f"see {old}/projects")
    return old


def test_moves_folder_and_rewrites_own_paths_in_json(tmp_path):
    old = _make_old(tmp_path)
    assert migrate_legacy_data_dir(tmp_path) is True
    new = tmp_path / NEW_NAME
    assert not old.exists()
    data = json.loads((new / "projects/proj_1/project.json").read_text())
    assert data["dir"] == f"{new}/projects/proj_1"
    assert data["bids"] == f"{tmp_path}/study/rawdata"  # paths outside the folder are untouched
    assert (new / "logs/a.log").read_text() == f"see {old}/projects"  # only *.json is rewritten


def test_never_touches_an_existing_new_folder(tmp_path):
    old = _make_old(tmp_path)
    new = tmp_path / NEW_NAME
    new.mkdir()
    (new / "keep.txt").write_text("x")
    assert migrate_legacy_data_dir(tmp_path) is False
    assert old.is_dir() and (new / "keep.txt").read_text() == "x"


def test_nothing_to_do_without_old_folder(tmp_path):
    assert migrate_legacy_data_dir(tmp_path) is False
    assert not (tmp_path / NEW_NAME).exists()


def test_second_call_is_a_noop(tmp_path):
    _make_old(tmp_path)
    assert migrate_legacy_data_dir(tmp_path) is True
    assert migrate_legacy_data_dir(tmp_path) is False


def test_resolve_data_dir_migrates_and_returns_new_path(tmp_path):
    _make_old(tmp_path)
    assert resolve_data_dir(tmp_path) == tmp_path / NEW_NAME
    assert (tmp_path / NEW_NAME / "projects").is_dir()


def test_project_manager_and_utils_share_one_data_dir():
    from lib import project_manager as pm, utils
    assert pm.DATA_DIR.name == NEW_NAME
    assert utils.LOG_DIR == pm.GLOBAL_LOG_DIR
```

- [ ] **Step 2: Run, expect failure**

Run: `.bidspm/bin/python -m pytest -q tests/test_data_dir_migration.py`
Expected: collection ERROR `ModuleNotFoundError: No module named 'lib.data_dir'`.

- [ ] **Step 3: Implement**

`lib/data_dir.py`:

```python
"""The per-user data folder (projects, logs) and its one-time move from the old name."""
import shutil
from pathlib import Path
from typing import Optional

OLD_NAME = ".bidspm"
NEW_NAME = ".spm-bids-runner"


def migrate_legacy_data_dir(home: Path) -> bool:
    """Move <home>/.bidspm to <home>/.spm-bids-runner once. Saved project files hold absolute paths into the folder,
    so every *.json below it gets the old folder path replaced by the new one. Never merges or overwrites: if the new
    folder exists nothing happens. Returns True when it moved.
    ponytail: a crash between the move and the rewrite leaves stale paths in some project files; rerun is not
    automatic (the old folder is gone). Fix by hand if it ever happens."""
    old, new = home / OLD_NAME, home / NEW_NAME
    if not old.is_dir() or new.exists():
        return False
    shutil.move(str(old), str(new))
    for path in new.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if str(old) in text:
            path.write_text(text.replace(str(old), str(new)), encoding="utf-8")
    return True


def resolve_data_dir(home: Optional[Path] = None) -> Path:
    home = Path(home) if home else Path.home()
    migrate_legacy_data_dir(home)
    return home / NEW_NAME


DATA_DIR = resolve_data_dir()
```

`lib/project_manager.py:26` replace `DATA_DIR = Path.home() / ".bidspm"` with `from lib.data_dir import DATA_DIR` (put it with the other `from lib...` imports near line 23 and delete line 26). In the docstring at line 158 write `~/.spm-bids-runner/projects/<project_id>/`.

`lib/utils.py:18-19`:

```python
from lib.data_dir import DATA_DIR

LOG_DIR = DATA_DIR / "logs"  # global fallback; project-scoped runs use project_manager instead
LOG_FILE = str(LOG_DIR / "run_bidspm.log")
```

(Move the import to the import block at the top of the file; `run_bidspm.log` is renamed in Task 4.)

- [ ] **Step 4: Run, expect pass; run the project-manager tests**

Run: `.bidspm/bin/python -m pytest -q tests/test_data_dir_migration.py tests/test_project_manager_extra.py`
Expected: all PASS. Warning: this import-time run migrates the real `~/.bidspm` if it still exists. Do Task 6 Step 1 (backup, stop old GUI) **first** if it does.

- [ ] **Step 5: Commit**

```bash
git add lib/data_dir.py lib/project_manager.py lib/utils.py tests/test_data_dir_migration.py
git commit -m "feat: user data folder is ~/.spm-bids-runner, moved once from ~/.bidspm with saved paths rewritten" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Mechanical rename

**Files:**
- Rename: `bidspm.py` -> `spm_bids_runner.py`, `bidspm_gui.py` -> `spm_bids_runner_gui.py`, `scripts/activate_bidspm.sh` -> `scripts/activate.sh`, `tests/test_bidspm_cli.py` -> `tests/test_spm_bids_runner_cli.py`, `tests/test_bidspm_gui_helpers.py` -> `tests/test_spm_bids_runner_gui_helpers.py`, `tests/test_bidspm_gui_helpers_extra.py` -> `tests/test_spm_bids_runner_gui_helpers_extra.py`
- Modify: about 150 files by `sed` (list from `git ls-files`)

**Interfaces:**
- Produces: all old names of ours gone from file contents except those fixed by hand in Task 5.

- [ ] **Step 1: Move the files**

```bash
git mv bidspm.py spm_bids_runner.py
git mv bidspm_gui.py spm_bids_runner_gui.py
git mv scripts/activate_bidspm.sh scripts/activate.sh
git mv tests/test_bidspm_cli.py tests/test_spm_bids_runner_cli.py
git mv tests/test_bidspm_gui_helpers.py tests/test_spm_bids_runner_gui_helpers.py
git mv tests/test_bidspm_gui_helpers_extra.py tests/test_spm_bids_runner_gui_helpers_extra.py
```

- [ ] **Step 2: Replace the names in file contents**

Order matters (long names first; `~/.bidspm` before the bare `.bidspm`, which is only ever the venv outside of `~/`).

```bash
FILES=$(git ls-files -co --exclude-standard \
  | grep -vE '^(docs/superpowers/|docs/roadmap-|static/vendor/|lib/data_dir\.py$|tests/test_data_dir_migration\.py$|tests/test_naming\.py$)' \
  | grep -vE '\.(png|woff2|ico|jpg)$')
sed -i -E \
  -e 's/bidspm_gui/spm_bids_runner_gui/g' \
  -e 's/\bbidspm\.py\b/spm_bids_runner.py/g' \
  -e 's/BIDSPM_SCRIPT/RUNNER_SCRIPT/g; s/bidspm_script/runner_script/g' \
  -e 's/run_bidspm/run_spm_bids_runner/g' \
  -e 's/activate_bidspm/activate/g' \
  -e 's/bidspm_validator_mode_/spm_bids_runner_validator_mode_/g' \
  -e 's/bidspm-runner/spm-bids-runner/g; s/bidspm_runner/spm_bids_runner/g' \
  -e 's/BIDSPM ([Rr])unner/SPM BIDS \1unner/g' \
  -e 's/BIDSPM_(PORT|VENV|PYTHON|TEST_IMAGE|PROJECT_ROOT|WIZARD_CONTEXT|TRANSFORMER_CONTEXT)\b/SPM_BIDS_RUNNER_\1/g' \
  -e 's#MRI-Lab-Graz/bidspm\b#MRI-Lab-Graz/spm-bids-runner#g' \
  -e 's#^cd bidspm$#cd spm-bids-runner#' \
  -e 's#\$\{HOME\}/bidspm\b#${HOME}/spm-bids-runner#g; s#~/bidspm\b#~/spm-bids-runner#g' \
  -e 's#~/\.bidspm#~/.spm-bids-runner#g' \
  -e 's#(^|[^[:alnum:]_-])\.bidspm\b#\1.venv#g' \
  $FILES
```

`.gitignore` is in `$FILES` (so `run_bidspm.log` and `bidspm_runner.egg-info/` are renamed), but the sed turns its line `.bidspm/` into `.venv/`, which is already ignored. The old venv `.bidspm/` still exists in every pre-rename checkout (and is the test interpreter until Task 5), so ignore it again, otherwise `git add -A` stages the whole venv. `.gitignore` is exempt from the guard test for this reason:

```bash
printf '\n# venv of checkouts made before the rename\n.bidspm/\n' >> .gitignore
git status --short | grep -c '^?? .bidspm' || true   # expect 0
```

- [ ] **Step 3: Fix the module name in the tests that `import bidspm`**

`bidspm.` was not replaced by Step 2 (only `bidspm.py`). Apply to exactly these seven files; the pattern skips `Software.bidspm.Results` (a dot before `bidspm`).

```bash
sed -i -E \
  -e 's/^(\s*)import bidspm\s*$/\1import spm_bids_runner/' \
  -e 's/patch\.object\(bidspm,/patch.object(spm_bids_runner,/g' \
  -e 's/(^|[^.[:alnum:]_])bidspm\.([A-Za-z_])/\1spm_bids_runner.\2/g' \
  tests/test_spm_bids_runner_cli.py tests/test_config_paths.py tests/test_preflight_cli.py \
  tests/test_preflight_progress.py tests/test_run_results.py tests/test_standalone_wiring.py \
  tests/test_stats_workers_validation.py
grep -nE '\bbidspm\b' tests/test_spm_bids_runner_cli.py tests/test_config_paths.py tests/test_preflight_cli.py \
  tests/test_preflight_progress.py tests/test_run_results.py tests/test_standalone_wiring.py \
  tests/test_stats_workers_validation.py
```

Expected: the grep prints nothing (or only comments you can read and judge); every remaining line must be about upstream bidspm.

- [ ] **Step 4: Run the guard test**

Run: `.bidspm/bin/python -m pytest -q tests/test_naming.py`
Expected: path test PASS. Content test may still list hits from files that need the hand edits in Task 5 (`UV_PROJECT_ENVIRONMENT=.venv` is not a hit; look for anything else). Fix any other hit by hand, rerun until only Task 5 items remain or it passes.

- [ ] **Step 5: Run the focused tests that exercise the renamed code**

Run:

```bash
.bidspm/bin/python -m pytest -q tests/test_spm_bids_runner_cli.py tests/test_spm_bids_runner_gui_helpers.py \
  tests/test_spm_bids_runner_gui_helpers_extra.py tests/test_config_paths.py tests/test_run_results.py \
  tests/test_standalone_wiring.py tests/test_stats_workers_validation.py tests/test_preflight_cli.py \
  tests/test_web_routes.py tests/test_image_licences.py tests/test_start_gui_script.py
```

Expected: all PASS. If `test_spm_bids_runner_gui_helpers_extra.py` fails on the interpreter-resolution tests, check `resolve_python_executable` in `spm_bids_runner_gui.py` now looks for `.venv/bin/python` and the test builds `.venv` (Step 2 handled both).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: rename bidspm runner to spm-bids-runner (files, modules, env vars, titles, URLs)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Hand edits, venv rebuild, real GUI start

**Files:**
- Modify: `scripts/setup.sh`, `scripts/setup_apple_silicon.sh`, `scripts/start_gui.sh`, `README.md`, `docs/walkthrough.md`, `spm_bids_runner_gui.py`, `.gitignore`

- [ ] **Step 1: Remove `UV_PROJECT_ENVIRONMENT` (uv's default environment is `.venv`)**

```bash
grep -rn UV_PROJECT_ENVIRONMENT scripts README.md docs/walkthrough.md
```

Expected before: `scripts/setup.sh` (`if ! UV_PROJECT_ENVIRONMENT=.venv ./build/uv sync --managed-python; then`), `scripts/setup_apple_silicon.sh` (`UV_PROJECT_ENVIRONMENT=.venv "$UV_BIN" sync ...`), and two README lines. Delete the `UV_PROJECT_ENVIRONMENT=.venv ` prefix in each (leave the rest of the command). Re-run the grep: it must print nothing.

- [ ] **Step 2: Name the GUI in the port-conflict message**

In `spm_bids_runner_gui.py`, function `kill_existing_on_port`, change `f"bidspm GUI, so it was not stopped...` to `f"SPM BIDS Runner GUI, so it was not stopped...`, and the `--port` help text `an older bidspm GUI on that port is stopped first` to `an older SPM BIDS Runner GUI on that port is stopped first`. In README.md line ~146 change `If an older bidspm GUI already listens` the same way. The existing `test_spm_bids_runner_gui_helpers.py` tests for `kill_existing_on_port` check the process-name match (`'spm_bids_runner_gui.py' not in command`), which Step 2 of Task 4 already renamed.

- [ ] **Step 3: README prose around the install steps and an upgrade note**

In `README.md`:
- Title line `# SPM BIDS Runner` (check it reads that after the sed), and under Overview add: `Built on [bidspm](https://github.com/cpp-lln-lab/bidspm) (CPP Lab), SPM and GNU Octave; we patched bidspm and added a runner and a GUI. Formerly named "bidspm" in this repository.`
- Under Installation add a short note:

```
**Upgrading from an older checkout** (this repo was renamed `spm-bids-runner`): `git pull`, then
`./scripts/setup.sh --force` (the environment is now `.venv`). Your saved projects move to `~/.spm-bids-runner`
automatically the first time the program starts.
```

- [ ] **Step 4: Residual review**

```bash
grep -rniE '\bbidspm\b' README.md docs/walkthrough.md scripts templates webapp static/js lib spm_bids_runner.py spm_bids_runner_gui.py \
  | grep -viE 'bidspm-(stats|preproc)|cpp-lln-lab|Model\.Software|"bidspm"|bidspm_overrides|bidspm_version|bidspm v|bidspm \$\{|upstream|bidspm\(' | cut -c1-170
```

Read each remaining line. Rule: a sentence about the upstream tool stays; a sentence that names *our* program (for example "bidspm GUI", "the bidspm runner", "bidspm.py") is rewritten to "SPM BIDS Runner" / the new file name. Also confirm `README.md` still says `bidspm-preproc` and `bidspm-stats` where it describes output folders.

- [ ] **Step 5: Guard test and uv lock check**

Run: `.bidspm/bin/python -m pytest -q tests/test_naming.py && ./build/uv lock --check --offline`
Expected: test PASS; `uv lock --check` exits 0 (if it reports the lock needs updating only because of the project name, run `./build/uv lock --offline` and look at `git diff uv.lock`: only the `name = "spm-bids-runner"` line may change).

- [ ] **Step 6: Rebuild the venv under the new name and start the GUI for real**

```bash
./scripts/setup.sh --force
git status --short uv.lock      # expect clean (or only the name line); if modified beyond that: git checkout uv.lock
.venv/bin/python -c "import flask, jsonschema, nibabel; print('deps ok')"
SPM_BIDS_RUNNER_PORT=5199 ./scripts/start_gui.sh --no-browser > /tmp/claude-1002/-data-local-software-bidspm/5228811b-eb40-47a8-9d53-18c74c59a8aa/scratchpad/gui.log 2>&1 &
sleep 8
curl -s http://127.0.0.1:5199/projects | grep -o '<title>[^<]*</title>'
```

Expected: `deps ok`; the title contains `SPM BIDS Runner`. Read the start of `gui.log`: the "Pre-flight check" lists the interpreter as `.../.venv/bin/python`. Stop the GUI with `kill $(ss -tlnp 'sport = :5199' | grep -o 'pid=[0-9]*' | cut -d= -f2)`.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: setup scripts, README and messages use the new name; upgrade note" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Full verification with the real data folder

- [ ] **Step 1: Protect the real data**

```bash
ss -tlnp 'sport = :5100' ; pgrep -af 'bidspm_gui|spm_bids_runner_gui'   # stop any old GUI first (kill <pid>)
ls -d ~/.bidspm ~/.spm-bids-runner 2>&1
cp -a ~/.bidspm ~/.bidspm.backup-2026-11-02     # not matched by the migration (different name)
```

Expected: no GUI listening; `~/.bidspm` exists, `~/.spm-bids-runner` does not (if Task 3 Step 4 already migrated it, skip the copy and use `cp -a ~/.spm-bids-runner ~/.spm-bids-runner.backup-2026-11-02` instead).

- [ ] **Step 2: Run the full suite**

Run: `.venv/bin/python -m pytest -q tests` (about 5 minutes; imports `lib`, so the real folder migrates here if it has not yet)
Expected: all PASS, same skip count as before this branch (compare with `git stash`-free baseline: run the same command on `main` in a second worktree only if a failure looks unrelated).

- [ ] **Step 3: Check the migration result on the real projects**

```bash
ls ~/.spm-bids-runner ~/.spm-bids-runner/projects
grep -rl '/\.bidspm' ~/.spm-bids-runner --include='*.json' | head   # expect nothing
grep -rc '\.spm-bids-runner/projects/proj_' ~/.spm-bids-runner/projects/*/project.json
```

Expected: both projects present; first grep prints nothing; the third shows the rewritten paths.

- [ ] **Step 4: Real GUI and CLI**

```bash
SPM_BIDS_RUNNER_PORT=5199 ./scripts/start_gui.sh --no-browser > /tmp/claude-1002/-data-local-software-bidspm/5228811b-eb40-47a8-9d53-18c74c59a8aa/scratchpad/gui2.log 2>&1 &
sleep 8
curl -s http://127.0.0.1:5199/projects | grep -c 'proj_20260405_080243_92f9ae49'   # the existing project is listed (count >= 1)
.venv/bin/python spm_bids_runner.py --check-environment
.venv/bin/python spm_bids_runner.py --help | head -5
```

Expected: project listed; environment check shows Docker and the image present; help prints the "SPM BIDS Runner" banner. Stop the GUI as in Task 5 Step 6. Report to the user that opening an existing project and starting a run in a browser was not done by Claude unless it was.

---

### Task 7: Review and hand-off

- [ ] **Step 1: Ponytail review (CLAUDE.md)**

Run `/ponytail:ponytail-review` on the branch diff (`git diff main...HEAD`). Resolve or consciously defer each finding; record deferrals in the commit message of the fix commit.

- [ ] **Step 2: Report to the user, do not merge or push**

Tell the user: branch name, test results (counts), the backup folder `~/.bidspm.backup-2026-11-02` they can delete, that `main` locally is one commit ahead of the remote (`e0fa40f`), and these user-only steps: push the branch and merge, ask colleagues to run `git pull && ./scripts/setup.sh --force`, optional local folder rename (last; saved project settings hold paths into the checkout), next publish of the image carries the new label URLs (no rebuild needed for function).

---

## Self-review

- **Spec coverage:** renamed table (repo URL, CLI/GUI files, titles, pyproject, env vars, venv, activate script, data folder) -> Tasks 3, 4, 5; kept list -> Global Constraints and the unlisted-by-guard design; migration -> Task 3 with tests for move, rewrite, no-overwrite, no-op, idempotent; process steps 1-5 -> Tasks 2, 4-7; GitHub rename already done.
- **Placeholders:** none; every code step has the code or exact command.
- **Name consistency:** `migrate_legacy_data_dir`, `resolve_data_dir`, `DATA_DIR`, `OLD_NAME`, `NEW_NAME` are used identically in tests and implementation; `RUNNER_SCRIPT`/`runner_script` replace `BIDSPM_SCRIPT`/`bidspm_script` in `spm_bids_runner_gui.py` and `webapp/web_execution_api.py` by the same sed line.
- **Known limits:** the guard cannot tell prose about our program from prose about upstream; Task 5 Step 4 is the human check for that.
