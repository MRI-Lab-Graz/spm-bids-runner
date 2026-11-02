# Rename the repo and product to `spm-bids-runner`

Date: 2026-11-02. Status: draft for review. First of four sub-projects (see "What comes after").

## Why

We did not invent bidspm; we patched it and built a GUI and runner around it. Calling our repo and product "bidspm" /
"BIDSPM Runner" misattributes the work and will confuse students who also meet the real bidspm. The container is already
`ghcr.io/mri-lab-graz/spm-bids-runner`; the repo, CLI and GUI should carry the same name. One name everywhere:
**`spm-bids-runner`** (display name "SPM BIDS Runner").

## Scope

### Renamed (ours)

| Now | After |
|---|---|
| GitHub repo `MRI-Lab-Graz/bidspm` | `MRI-Lab-Graz/spm-bids-runner` (GitHub redirects the old URL; the 14 mentions of the old URL are updated) |
| `bidspm.py`, `bidspm_gui.py` | `spm_bids_runner.py`, `spm_bids_runner_gui.py` |
| "BIDSPM Runner" (GUI title, README, templates, messages) | "SPM BIDS Runner" |
| `pyproject.toml` name `bidspm-runner` | `spm-bids-runner` |
| `BIDSPM_*` env vars of ours (`PORT`, `VENV`, `PYTHON`, `SKIP_RESULTS`, `TEST_IMAGE`, `TRANSFORMER_CONTEXT`, `WIZARD_CONTEXT`) | `SPM_BIDS_RUNNER_*` |
| venv `.bidspm` (+ `UV_PROJECT_ENVIRONMENT=.bidspm`) | uv's default `.venv`; `setup.sh`, `start_gui.sh`, `activate_bidspm.sh`, README, tests follow |
| `scripts/activate_bidspm.sh` | `scripts/activate.sh` |
| user data folder `~/.bidspm` (projects, logs) | `~/.spm-bids-runner` (migration below) |

### Kept (upstream's, or accurate as is)

- The `bidspm` command in the image (`ENTRYPOINT ["bidspm"]`), `BIDSPM_TAG`, the pinned upstream tag `v4.0.0`.
- Output folders `bidspm-preproc/` and `bidspm-stats/`: the pipeline name in BIDS derivatives, written by upstream bidspm.
- `Model.Software.bidspm` in the BIDS-StatsModel and everything else that names upstream bidspm in messages and credits.
- `bidspm_overrides/` (mirrors upstream's tree 1:1) and `containers/dockerfile/patches/*`.
- `LICENSE`, the image NOTICE, `docs/third-party-licenses.md`, the Acknowledgments section.
- Existing git history, tags and the already published image tags `v2.1.0`, `v2.1.1`, `latest`.
- The stale GHCR image named `bidspm`: untouched (the README already says not to use it).

## Data folder migration

`~/.bidspm/` holds `projects/`, `logs/` and `current_project.json` (`lib/project_manager.py:26`, `lib/utils.py:18`). Saved
project JSON files contain **absolute paths into that folder** (about 25 occurrences in the two existing projects:
`<home>/.bidspm/projects/proj_.../...`), so moving the folder alone would leave them stale.

On GUI/CLI start, if `~/.bidspm` exists and `~/.spm-bids-runner` does not:

1. move the folder to `~/.spm-bids-runner`;
2. in every `*.json` below it, replace the exact prefix `<home>/.bidspm/` with `<home>/.spm-bids-runner/`.

If the new folder exists, nothing happens (never merge, never overwrite). The code lives in one function called from the one
place that defines the data directory (today two constants, `DATA_DIR` and `LOG_DIR`; they collapse to one). It is removable
once everyone has started the new version.

Paths that point at the repo checkout (`/data/.../bidspm/...` in saved settings) are user data and are not rewritten; they stay
valid as long as the checkout folder is not renamed.

## Process (CLAUDE.md)

1. Branch `rename-spm-bids-runner` off `main`.
2. **Failing tests first:**
   - a repo-wide test that fails while any tracked file still contains an "ours" name from the table above; allow-list for the
     kept names (a regex per kept item, so a new use of an old name fails the test);
   - migration tests on a temp home: moves once, rewrites the prefix in nested JSON, leaves an existing new folder untouched,
     does nothing when no old folder exists.
3. Do the rename until the tests pass; run `python -m pytest -q tests` (about 5 min, includes the browser tests).
4. Run the GUI once for real (`start_gui.sh`, open the projects page, existing projects listed and runnable).
5. `/ponytail:ponytail-review` on the branch diff, resolve or defer findings, then merge.
6. **Already done (2026-11-02):** the GitHub repo is renamed (the old URL redirects) and the local `origin` points at
   `git@github.com:MRI-Lab-Graz/spm-bids-runner.git`. Still the user's, optional: rename the local checkout folder
   (saved projects hold paths into it, so do that last and expect to edit them).

## Risks

- A missed reference breaks a script silently. Mitigation: the repo-wide test plus one real GUI start and one real CLI
  `--check-environment`.
- Colleagues with old clones: GitHub's redirect handles `git pull`; their `~/.bidspm` migrates on first start; their old
  `.bidspm` venv keeps working until they re-run `setup.sh`, which will build `.venv`.
- Text changes inside `docs/superpowers/` history (old plans/specs) are left as written; the repo-wide test excludes them.

## What comes after (decided in the same conversation, each gets its own spec, plan and branch)

- **C. Two images, one per architecture.** `spm-bids-runner:<version>-amd64` and `:<version>-arm64`, each built on a native
  runner (`ubuntu-latest`, `ubuntu-24.04-arm`) by an extended manual `docker-publish.yml`, plus the combined tags
  `:<version>` and `:latest`. The Dockerfile has no amd64-specific parts. The user presses "run workflow"; the iMac
  (Apple Silicon, Docker Desktop) is the test machine for arm64.
- **A. Tutorial data.** `scripts/fetch_tutorial_data.py` downloads a few subjects of OpenNeuro `ds000102` (Flanker): raw
  events and sidecars from `ds000102`, MNI152NLin2009cAsym preprocessed BOLD, mask and confounds from
  `OpenNeuroDerivatives/ds000102-fmriprep` (about 0.5 GB per subject), over anonymous HTTPS from the public S3 buckets.
- **B. Read the Docs.** `spm-bids-runner.readthedocs.io` (slug free on 2026-11-02), style of prism-studio: Shibuya theme
  with green accent, MyST Markdown, `fail_on_warning`. Sidebar: Concepts, Installation (macOS Apple Silicon),
  Tutorial (Flanker, chapters 0-6 with time estimates), Reference, Troubleshooting. Students' platform: Apple Silicon Macs.
