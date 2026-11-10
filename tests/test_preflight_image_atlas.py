"""Readiness items for the image: image_missing (the run cannot start) and atlas_missing (none ships, licences)."""
import subprocess
from unittest.mock import patch

from lib import preflight
from lib.preflight import check_atlases, check_image, docker_image_present, run_preflight_from_config, signature
from tests.preflight_support import make_trees


def _ids(items, severity=None):
    return [i["id"] for i in items if severity in (None, i["severity"])]


def test_present_is_docker_image_inspect_with_a_timeout():
    with patch("lib.preflight.subprocess.run") as run:
        run.return_value.returncode = 0
        assert docker_image_present("img:1") is True
    cmd, kw = run.call_args[0][0], run.call_args[1]
    assert cmd == ["docker", "image", "inspect", "img:1"] and kw["timeout"] == 10


def _docker_says(stderr):
    return subprocess.CompletedProcess(["docker"], 1, b"", stderr.encode())


def test_absent_image():
    with patch("lib.preflight.subprocess.run", return_value=_docker_says("Error response from daemon: No such image: img:1")):
        assert docker_image_present("img:1") is False


def test_daemon_not_running_is_not_an_absent_image():
    # Docker Desktop closed: `docker image inspect` also exits 1, but the image may well be there
    for msg in ("Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?",
                "failed to connect to the docker API at unix:///x.sock; check if the path is correct and if the daemon is running",
                "permission denied while trying to connect to the Docker daemon socket"):
        with patch("lib.preflight.subprocess.run", return_value=_docker_says(msg)):
            assert docker_image_present("img:1") is None


def test_docker_trouble_never_crashes_and_is_not_reported_as_missing():
    for exc in (subprocess.TimeoutExpired("docker", 10), OSError("no docker")):
        with patch("lib.preflight.subprocess.run", side_effect=exc):
            assert docker_image_present("img:1") is None


def test_missing_docker_image_is_an_error_with_build_and_pull_fix():
    with patch("lib.preflight.shutil.which", return_value="/usr/bin/docker"), \
         patch("lib.preflight._image_present", return_value=False):
        items = check_image("docker", "old/name:latest")
    assert _ids(items, "error") == ["image_missing"]
    fix = items[0]["fix"]
    assert "docker build -f containers/dockerfile/dockerfile -t old/name:latest ." in fix
    assert "docker pull old/name:latest" in fix


def test_no_image_item_when_present_unknown_without_docker_or_not_docker():
    with patch("lib.preflight.shutil.which", return_value="/usr/bin/docker"):
        with patch("lib.preflight._image_present", return_value=True):
            assert check_image("docker", "x") == []
    with patch("lib.preflight.shutil.which", return_value=None), \
         patch("lib.preflight._image_present", side_effect=AssertionError("must not run")):
        assert check_image("docker", "x") == []  # the existing 'container' warning covers it
    assert check_image("apptainer", "/x.sif") == [] and check_image("docker", "") == []


def test_docker_not_answering_says_start_docker_not_build_the_image():
    with patch("lib.preflight.shutil.which", return_value="/usr/bin/docker"), \
         patch("lib.preflight._image_present", return_value=None):
        items = check_image("docker", "x")
    assert _ids(items, "error") == ["docker_not_running"]
    assert "Docker Desktop" in items[0]["fix"]
    assert "build" not in items[0]["fix"] and "image_missing" not in _ids(items)


def test_atlas_missing_for_the_report_action():
    items = check_atlases({}, ["stats", "report"])
    assert _ids(items, "warn") == ["atlas_missing"]
    assert "licence" in items[0]["message"] and "Atlases" in items[0]["fix"]
    assert check_atlases({}, ["stats"]) == [] and check_atlases({}, None) == []


def test_atlas_missing_for_roi_settings():
    items = check_atlases({"ROI": True, "ROI_CONFIG": {"roi_atlas": "wang"}}, ["stats"])
    assert _ids(items, "warn") == ["atlas_missing"]
    assert "wang" in items[0]["message"] and "not used" in items[0]["message"]
    assert check_atlases({"ROI": False}, ["stats"]) == []


def test_wired_into_the_readiness_check(tmp_path):
    bids, fmriprep = make_trees(tmp_path)
    cfg = {"BIDS_DIR": str(bids), "FMRIPREP_DIR": str(fmriprep), "SPACE": "MNI", "TASKS": ["x"],
           "container_type": "docker", "docker_image": "old/name:latest", "ROI": True}
    with patch("lib.preflight.shutil.which", return_value="/usr/bin/docker"), \
         patch("lib.preflight._image_present", return_value=False) as present, \
         patch("lib.core.validate_bids_model", return_value={"valid": True}):
        report = run_preflight_from_config(cfg, validator="skip", actions=["stats", "report"])
    present.assert_called_once_with("old/name:latest")
    assert report["verdict"] == "blocked"
    assert {"image_missing", "atlas_missing"} <= set(_ids(report["checks"]))


def test_signature_tracks_roi_settings_but_never_probes_docker():
    with patch("lib.preflight.subprocess.run", side_effect=AssertionError("no docker call")):
        assert signature({"BIDS_DIR": "/b", "ROI": True}, "", "skip", [], False) != \
            signature({"BIDS_DIR": "/b"}, "", "skip", [], False)
