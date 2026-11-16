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


def _has(module):
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:  # a missing parent package
        return False


def _sphinx_cmd():
    """Sphinx from this interpreter when the docs packages are installed, else through uv (it installs them for the run)."""
    if all(_has(m) for m in ("sphinx", "myst_parser", "shibuya", "sphinxcontrib.mermaid")):
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


EXAMPLE = SRC / "_examples" / "faces_houses_model.json"
EXAMPLE_SCAN = {"tasks": ["demo"], "columns": {"trial_type": ["faces", "houses"]}, "numeric": [],
                "confound_columns": ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]}
EXAMPLE_CHOICES = {"task": "demo", "name": "faces_houses", "recipes": [], "nuisance": "motion6", "exclude": [],
                   "contrasts": {"auto": True, "pairs": [{"name": "faces_gt_houses",
                                                          "positive": ["trial_type.faces"],
                                                          "negative": ["trial_type.houses"]}]}}


def test_example_model_is_what_the_wizard_produces():
    import json
    from lib.model_wizard import build_model
    assert json.loads(EXAMPLE.read_text()) == build_model(EXAMPLE_CHOICES, EXAMPLE_SCAN)["model"]


def test_example_model_passes_the_runners_validation():
    from lib.core import validate_bids_model
    result = validate_bids_model(EXAMPLE)
    assert result["valid"], result


def test_stats_model_page_includes_the_example_and_every_recipe():
    from lib.model_wizard import RECIPE_CATALOG
    text = (SRC / "prerequisites" / "stats-model.md").read_text()
    assert "_examples/faces_houses_model.json" in text
    for recipe in RECIPE_CATALOG:
        assert f"`{recipe['id']}`" in text, recipe["id"]
    for needle in ("Nodes", "Edges", "ConditionList", "Weights", "DummyContrasts", "MODELS_FILE", "models/",
                   "BIDS Stats Models", "bidspm.readthedocs.io"):
        assert needle in text, needle


def test_prerequisites_are_in_the_order_a_student_meets_them():
    text = (SRC / "prerequisites" / "index.md").read_text()
    toctree = re.search(r"```\{toctree\}\n(?::\w+:.*\n)*\n((?:\w[\w-]*\n)+)```", text).group(1).split()
    assert toctree == ["fmriprep", "confounds", "events", "stats-model"]


def test_gears_links_each_prerequisite_and_names_the_folders_the_tool_writes():
    text = (SRC / "gears.md").read_text()
    for page in ("fmriprep", "confounds", "events", "stats-model"):
        assert f"prerequisites/{page}.md" in text, page
    for needle in ("localhost:5100", "bidspm-preproc", "bidspm-stats", "models/", "~/.spm-bids-runner",
                   "bidspm-groupStats", "rawdata"):
        assert needle in text, needle


def test_pages_link_to_each_other():
    expect = {"credits.md": ["prerequisites/fmriprep.md"],
              "prerequisites/fmriprep.md": ["confounds.md", "../gears.md"],
              "prerequisites/confounds.md": ["stats-model.md"],
              "prerequisites/events.md": ["stats-model.md"],
              "prerequisites/index.md": ["fmriprep.md", "confounds.md", "events.md", "stats-model.md"]}
    for page, targets in expect.items():
        text = (SRC / page).read_text()
        for target in targets:
            assert f"]({target})" in text, (page, target)


def test_fmriprep_page_attributes_the_mask_to_the_statistics_step():
    text = (SRC / "prerequisites" / "fmriprep.md").read_text()
    assert "the statistics step adds the brain mask" in text
    assert "does **not** check the brain mask" in text


def test_install_page_has_the_commands_and_the_port_warning():
    text = (SRC / "install.md").read_text()
    for needle in ("git clone https://github.com/MRI-Lab-Graz/spm-bids-runner.git", "./scripts/setup.sh",
                   "./scripts/start_gui.sh", "http://localhost:5100", "SPM_BIDS_RUNNER_PORT",
                   "ghcr.io/mri-lab-graz/spm-bids-runner", "never expose"):
        assert needle in text, needle


def test_gears_links_to_the_install_page():
    assert "](install.md)" in (SRC / "gears.md").read_text()


def test_home_page_announces_the_walkthrough():
    assert "walkthrough" in (SRC / "index.md").read_text().lower()


def test_stats_model_page_names_the_parametric_modulator_output():
    assert "ParametricModulations" in (SRC / "prerequisites" / "stats-model.md").read_text()


RTD_URL = "https://spm-bids-runner.readthedocs.io/"


def test_readme_links_to_the_docs_site():
    readme = (ROOT / "README.md").read_text()
    assert RTD_URL in readme.split("## Overview")[0], "the docs link belongs right under the title"


def _mermaid_blocks(page):
    """The Mermaid diagram sources of a page (MyST ```{mermaid} fences)."""
    return re.findall(r"```\{mermaid\}\n(.*?)\n```", (SRC / page).read_text(), re.S)


def _balanced(block):
    """A cheap syntax guard (the real check is the browser): brackets and quotes pair up."""
    return all(block.count(a) == block.count(b) for a, b in ("[]", "{}", "()")) and block.count('"') % 2 == 0


def _in_words(page):
    """The text after the page's first diagram."""
    return (SRC / page).read_text().split("```{mermaid}", 1)[1].split("\n```\n", 1)[1]


def test_prerequisites_diagram_shows_how_the_prerequisites_interact():
    (block,) = _mermaid_blocks("prerequisites/index.md")
    assert block.startswith("flowchart") and _balanced(block)
    for label in ("Raw BIDS dataset", "fMRIPrep", "confounds", "events", "Model wizard", "BIDS Stats Model", "Readiness check"):
        assert label in block, label
    assert _in_words("prerequisites/index.md").lstrip().startswith("**In words:**")


def test_stats_model_diagram_follows_a_condition_name_to_the_results():
    (block,) = _mermaid_blocks("prerequisites/stats-model.md")
    assert block.startswith("flowchart") and _balanced(block)
    for label in ("trial_type = faces", "trial_type.faces", "ConditionList", "con_NNNN.nii", "spmT_NNNN.nii", "confounds"):
        assert label in block, label
    assert _in_words("prerequisites/stats-model.md").lstrip().startswith("**In words:**")


def test_gears_diagram_uses_the_runners_real_actions(monkeypatch):
    import spm_bids_runner
    (block,) = _mermaid_blocks("gears.md")
    assert block.startswith("flowchart") and _balanced(block)
    for action in ("smooth", "stats", "dataset", "report"):
        assert f'"{action}<br/>' in block, action
        monkeypatch.setattr(sys, "argv", ["spm_bids_runner.py", "--action", action])
        assert spm_bids_runner.parse_arguments().action == [action]   # SystemExit if the runner no longer has it
    for label in ("Readiness check", "bidspm-preproc/", "bidspm-stats/", "bidspm-groupStats/", "reports/"):
        assert label in block, label
    assert _in_words("gears.md").lstrip().startswith("**In words:**")
    assert "`bms`" in (SRC / "gears.md").read_text()
    assert "bms" not in block
