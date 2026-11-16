"""The Read the Docs site builds without warnings and cannot drift from what the tool does (nuisance presets,
recipes, the example model). Sources are in docs/source/; the pages are for students."""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "source"
REQS = ROOT / "docs" / "requirements.txt"
PAGES = sorted(SRC.rglob("*.md"))


def _sphinx_cmd():
    """Sphinx from this interpreter when the docs packages are installed, else through uv (it installs them for the run)."""
    if all(importlib.util.find_spec(m) for m in ("sphinx", "myst_parser", "shibuya")):
        return [sys.executable, "-m", "sphinx"]
    if shutil.which("uv"):
        return ["uv", "run", "--no-project", "--with-requirements", str(REQS), "python", "-m", "sphinx"]
    return None


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    cmd = _sphinx_cmd()
    if cmd is None:
        pytest.skip("neither the docs packages (docs/requirements.txt) nor uv is available")
    out = tmp_path_factory.mktemp("docs_html")
    proc = subprocess.run(cmd + ["-W", "--keep-going", "-q", "-b", "html", str(SRC), str(out)],
                          capture_output=True, text=True, timeout=900)
    return proc, out


def test_rtd_config_points_at_the_site():
    rtd = (ROOT / ".readthedocs.yaml").read_text()
    assert re.search(r"^version: 2$", rtd, re.M)
    assert "configuration: docs/source/conf.py" in rtd
    assert re.search(r"fail_on_warning: true", rtd)
    assert "requirements: docs/requirements.txt" in rtd
    assert (SRC / "conf.py").is_file() and REQS.is_file()


def test_site_builds_without_warnings(html):
    proc, out = html
    assert proc.returncode == 0, (proc.stdout + proc.stderr)[-3000:]
    assert (out / "index.html").is_file()


def test_no_lab_study_or_local_paths_in_the_pages():
    pattern = re.compile(r"study 141|\bcrom\b|sub-141|/data/local|/home/mri", re.I)
    hits = [f"{p.relative_to(SRC)}: {m.group()}" for p in PAGES for m in pattern.finditer(p.read_text())]
    assert not hits, hits
