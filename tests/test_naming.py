"""What is ours is called spm-bids-runner; "bidspm" is only upstream's name.

Fails when a tracked (or new, unignored) file still uses an old name of ours. Upstream names are not listed
here, so they pass: the bidspm command, bidspm-preproc/, bidspm-stats/, Model.Software.bidspm, bidspm_overrides/,
the container-side BIDSPM_* variables, cpp-lln-lab/bidspm.
A line containing the marker `guard:allow` is skipped (the README upgrade note has to name the old things).
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
    ("old UI text", r"Welcome to BIDSPM|all in the bidspm image"),
    ("old export file name", r"bidspm_config_"),
    ("old report title", r"\bbidspm (processing |group )?report\b(?! templates)"),
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
            if "guard:allow" in line:
                continue
            hits += [f"{f}:{n}: [{label}] {line.strip()[:90]}" for label, rx in compiled if rx.search(line)]
    assert not hits, f"{len(hits)} old names:\n" + "\n".join(hits[:60])


def test_no_old_names_in_file_paths():
    hits = [f for f in _files() if OLD_PATHS.search(f)]
    assert not hits, "files still carry an old name:\n" + "\n".join(hits)
