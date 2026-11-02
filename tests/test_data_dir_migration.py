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
    import importlib
    # lib/__init__ rebinds `lib.project_manager` to the ProjectManager instance, so import the modules by name
    pm = importlib.import_module("lib.project_manager")
    utils = importlib.import_module("lib.utils")
    assert pm.DATA_DIR.name == NEW_NAME
    assert utils.LOG_DIR == pm.GLOBAL_LOG_DIR
