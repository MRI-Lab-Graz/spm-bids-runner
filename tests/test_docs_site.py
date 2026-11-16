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


def test_credits_cite_bidspm_clearly():
    text = (SRC / "credits.md").read_text()
    for needle in ("10.5281/zenodo.3554331", "https://github.com/cpp-lln-lab/bidspm",
                   "https://bidspm.readthedocs.io/en/latest/", "CITATION.cff", "SPM", "Octave"):
        assert needle in text, needle


def test_home_credits_the_engine_and_links_the_credits_page():
    text = (SRC / "index.md").read_text()
    assert "The engine is bidspm" in text
    assert "(credits.md)" in text
    assert "https://bidspm.readthedocs.io/en/latest/" in text


def test_fmriprep_page_names_what_the_readiness_check_looks_for():
    text = (SRC / "prerequisites" / "fmriprep.md").read_text()
    for needle in ("desc-preproc_bold.nii.gz", "desc-confounds_timeseries.tsv", "desc-brain_mask",
                   "--output-spaces", "bidspm-preproc", "no preprocessing"):
        assert needle in text, needle


def test_confounds_page_lists_every_wizard_preset_and_its_columns():
    from lib.model_wizard import NUISANCE_PRESETS
    text = (SRC / "prerequisites" / "confounds.md").read_text()
    for name, columns in NUISANCE_PRESETS.items():
        assert f"`{name}`" in text, name
    for column in NUISANCE_PRESETS["motion6_fd"]:           # motion6 + framewise_displacement
        assert f"`{column}`" in text, column
    assert "motion24" in text and "derivative1_power2" in text


def test_confounds_page_mentions_the_checks_the_readiness_check_makes():
    text = (SRC / "prerequisites" / "confounds.md").read_text()
    for needle in ("desc-confounds_timeseries.tsv", "same number of rows", "bidspm-preproc", "without motion regressors"):
        assert needle in text, needle


def test_events_page_covers_columns_inheritance_and_checks():
    text = (SRC / "prerequisites" / "events.md").read_text()
    for needle in ("onset", "duration", "trial_type", "task-<task>_events.tsv", "n/a", "tab-separated",
                   "negative onset", "split_by_column"):
        assert needle in text, needle
