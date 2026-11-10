from pathlib import Path

SETUP = (Path(__file__).resolve().parent.parent / "scripts" / "setup.sh").read_text(encoding="utf-8")


def test_closing_message_uses_the_project_environment_and_names_the_gui_start():
    assert "python3 spm_bids_runner.py" not in SETUP  # system python lacks the dependencies
    assert "./scripts/start_gui.sh" in SETUP.split("Setup completed successfully", 1)[1]


APPLE = (Path(__file__).resolve().parent.parent / "scripts" / "setup_apple_silicon.sh").read_text(encoding="utf-8")


def test_apple_installer_tells_students_to_start_the_gui_not_a_cli_run_without_config():
    # `python spm_bids_runner.py --action smooth --pilot` on a fresh install dies with "Config file not found"
    assert "./scripts/start_gui.sh" in APPLE.split("setup complete!", 1)[1]
    assert "--pilot" not in APPLE


def _uv_target(os_name, machine):
    """Run setup.sh's own uv_target function (extracted from the file) the way install_uv calls it."""
    import re
    import subprocess
    func = re.search(r"^uv_target\(\) \{\n.*?^\}\n", SETUP, re.S | re.M)
    assert func, "setup.sh has no uv_target function"
    r = subprocess.run(["bash", "-c", f'{func.group(0)}\nuv_target "$1" "$2"', "bash", os_name, machine],
                       capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def test_uv_download_name_is_right_for_macos_and_linux():
    # astral-sh/uv release assets: uv-<triple>.tar.gz; the old name uv-aarch64-unknown-darwin-gnu 404s on a Mac
    assert _uv_target("Darwin", "arm64") == (0, "aarch64-apple-darwin")
    assert _uv_target("Darwin", "x86_64") == (0, "x86_64-apple-darwin")
    assert _uv_target("Linux", "x86_64") == (0, "x86_64-unknown-linux-gnu")
    assert _uv_target("Linux", "aarch64") == (0, "aarch64-unknown-linux-gnu")
    assert _uv_target("Linux", "arm64") == (0, "aarch64-unknown-linux-gnu")
    assert _uv_target("FreeBSD", "amd64")[0] != 0


def test_install_uv_downloads_the_asset_named_by_uv_target():
    assert 'uv-${TARGET}.tar.gz' in SETUP and "unknown-${OS}" not in SETUP
