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
