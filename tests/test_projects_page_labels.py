"""Wording a first-time student reads in the New/Edit project dialogs (both dialogs, so every check counts 2)."""
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "templates" / "projects.html").read_text(encoding="utf-8")


def test_the_output_folder_is_called_working_directory_like_on_the_analysis_page():
    assert "Output Folder" not in HTML
    assert HTML.count(">Working Directory</label>") == 2


def test_the_fmriprep_folder_is_not_called_optional_because_an_analysis_needs_it():
    assert "(optional)" not in HTML
    assert HTML.count("fMRIPrep output, needed to run an analysis") == 2


def test_the_container_image_may_be_left_empty_and_sif_is_for_apptainer_only():
    assert HTML.count("Leave empty to use the standard image") == 2
    assert 'placeholder="Path to .sif or Docker image name"' not in HTML
