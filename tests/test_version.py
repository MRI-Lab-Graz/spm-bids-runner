import tomllib
from pathlib import Path

import spm_bids_runner_gui

ROOT = Path(__file__).resolve().parent.parent


def test_version_is_single_sourced_from_pyproject():
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert declared == "2.1.1"
    assert spm_bids_runner_gui.__version__ == declared
    assert spm_bids_runner_gui.app.config["APP_VERSION"] == declared


def test_footer_shows_the_version():
    html = spm_bids_runner_gui.app.test_client().get("/projects").get_data(as_text=True)
    assert "v2.1.1" in html
