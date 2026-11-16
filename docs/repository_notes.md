# Repository Notes

## 1) Architecture direction: object-oriented when it helps

- Prefer object-oriented design for new stateful features.
- Keep small pure utilities as functions when that is simpler and clearer.
- Encapsulate mutable state in classes instead of growing global state.
- Favor dataclasses for structured domain/config objects.
- For larger features, separate concerns:
  - route/controller layer (Flask endpoint)
  - service layer (business logic)
  - data model layer (typed objects)

Practical rule:
- If a feature has lifecycle/state/coordination across multiple functions, implement a class.
- If logic is a single pure transformation, keep it functional.

## 2) Testing policy for new features

- Keep tests under tests/.
- Every new feature should include tests in the same change.
- Add at least:
  - one success-path test
  - one failure/edge-path test
- For API features, use Flask test client tests.
- Keep tests fast and deterministic (no network and no external services).

Definition of done for feature work:
- behavior implemented
- tests added/updated
- docs/notes updated when behavior changes

## 3) Near-term refactor targets (OO migration candidates)

- Move endpoint-specific parsing/normalization code into dedicated service classes.
- Isolate model editor state/update logic behind an explicit model service.
- Reduce module-level mutable globals where possible.

## 4) Handing work to subagents (token-optimised)

A subagent gets a **slice**, never the whole repo, plan or spec: re-reading everything is the main cost of delegated work.

**Model**: every subagent (implementer, reviewer, re-review, final review) runs on `sonnet`, passed explicitly in the dispatch (an
omitted model inherits the session's model); nobody switches models. This overrides the tiered model advice of workflow skills
(cheapest tier for transcription, the most capable model for the final review or for stalled fix rounds): a heavy task, the key
docs page or the final review stay on `sonnet` too. If a fix loop stalls, start a fresh `sonnet` implementer or ask the user.

**A dispatch contains** (about 15 lines): one line on where the task fits; the path of the **task brief** (the task's own text
from the plan, with the exact values); interface names/signatures from earlier tasks that the brief cannot know; the path of the
**report file**; the focused test command. No history of earlier tasks and no pasted file contents: hand over paths.

**A subagent reads**: its brief, this section, and the files its task names. It does **not** read: the whole plan or spec,
`README.md` (800 lines), `docs/walkthrough.md`, other tasks' briefs or reports, or `git log` beyond its own commits.

**A subagent returns** at most 15 lines: status, commit SHAs and subjects, a one-line test summary, concerns, the report path. The
detail goes into the report file. A reviewer gets the **diff file** (the full diff with context, written once by the controller),
not git commands, and does not re-run the suite: the implementer's report carries the test evidence.

**Where the artifacts live**: `.superpowers/sdd/<plan-basename>/` (git-ignored, never committed): `progress.md` (the controller's
ledger), `task-N-brief.md`, `task-N-report.md`, `review-<base>..<head>.diff`.

**Test cadence**: the focused test file while iterating. The full suite (`python -m pytest -q tests`, about 6.5 minutes) runs once
at the merge gate. A docs-only task runs `tests/test_docs_site.py`, `tests/test_naming.py` and `tests/test_readme_paths.py`.

### Fact sheet (so nobody re-derives it)

- **Rules**: TDD (failing test first); work on the branch you are given; never push; never touch GHCR; stage specific paths; end
  commit messages with the `Co-Authored-By` line the task gives; `.superpowers/` stays untracked.
- **Environment**: `python` is the FSL interpreter, not the project `.venv`. The docs build needs Sphinx, MyST and Shibuya; the test
  provisions them through `uv` (`_sphinx_cmd` in `tests/test_docs_site.py`). Use absolute paths: a `cd` can reset the working
  directory between shell calls.
- **Naming guard**: `tests/test_naming.py` scans every tracked file for old names of this project (it also rejects the old
  lowercase report title listed there). Upstream names such as `bidspm-preproc/`, `bidspm-stats/`, `bidspm_overrides/` are fine.
- **The docs site** is `docs/source/` (Sphinx + MyST + Shibuya); `.readthedocs.yaml` has `fail_on_warning`. Every commit keeps the
  `-W` build green, so a page never links to a page that does not exist yet.

| Area | Where (function names, line numbers drift) |
|---|---|
| Readiness check: events, confounds, preprocessed BOLD, model | `lib/preflight.py`: `check_subject_task`, `check_model`, `run_preflight`; check ids such as `events_missing`, `confounds_missing`, `preproc_missing`, `confound_rows` |
| Model wizard | `lib/model_wizard.py`: `build_model`, `NUISANCE_PRESETS`, `RECIPE_CATALOG`, `scan_events` |
| Model validation and lookup | `lib/core.py` `validate_bids_model`; `lib/model_path.py` `resolve_model_file` (the config setting looks in `<derivatives>/models/` first, `--model` in the current folder first) |
| Smoothing and the confounds copy | `lib/fast_smooth.py`: `copy_confounds_from_fmriprep` |
| Brain-mask copy | `lib/core.py` `_copy_brain_mask`, called by the **statistics** step only |
| Pipeline and CLI | `lib/core.py` `Pipeline`; `spm_bids_runner.py`; `webapp/` only triggers CLI commands |
| Settings | `lib/config.py` (`Config`, `DEFAULT_DOCKER_IMAGE`); per-user data in `~/.spm-bids-runner` (`lib/data_dir.py`); project fields in `lib/project_manager.py` (e.g. `models_file`) |

**Output layout** (under the derivatives folder, which defaults to the working directory): `bidspm-preproc/sub-*/[ses-*/]func/`
(preprocessed BOLD copy, `desc-smth<FWHM>_bold`, confounds copy, the brain mask after the statistics step);
`bidspm-stats/sub-*/task-<task>_space-<space>_FWHM-<n>/` (`SPM.mat`, `beta_*`, `con_*`, `spmT_*`);
`bidspm-stats/derivatives/bidspm-groupStats/` (group level); `models/`; `reports/`.
