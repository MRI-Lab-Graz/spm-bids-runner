"""The per-user data folder (projects, logs) and its one-time move from the old name."""
import shutil
from pathlib import Path
from typing import Optional

OLD_NAME = ".bidspm"
NEW_NAME = ".spm-bids-runner"


def migrate_legacy_data_dir(home: Path) -> bool:
    """Move <home>/.bidspm to <home>/.spm-bids-runner once. Saved project files hold absolute paths into the folder,
    so every *.json below it gets the old folder path replaced by the new one. Never merges or overwrites: if the new
    folder exists nothing happens. Returns True when it moved.
    ponytail: a crash between the move and the rewrite leaves stale paths in some project files; rerun is not
    automatic (the old folder is gone). Fix by hand if it ever happens."""
    old, new = home / OLD_NAME, home / NEW_NAME
    if not old.is_dir() or new.exists():
        return False
    shutil.move(str(old), str(new))
    for path in new.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if str(old) in text:
            path.write_text(text.replace(str(old), str(new)), encoding="utf-8")
    return True


def resolve_data_dir(home: Optional[Path] = None) -> Path:
    home = Path(home) if home else Path.home()
    migrate_legacy_data_dir(home)
    return home / NEW_NAME


DATA_DIR = resolve_data_dir()
