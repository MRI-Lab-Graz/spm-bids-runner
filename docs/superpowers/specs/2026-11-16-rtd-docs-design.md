# Read the Docs site (structure first)

Date: 2026-11-16. Status: approved design, spec for review. Fourth of the student-release sub-projects (rename and multi-arch image are merged; tutorial data comes after this).

## Why

Students have the README (800 lines, written for maintainers) and `docs/walkthrough.md`, which uses a lab study they cannot
download. They need a site that first explains **how the tool is built** (what they must have, which folders and files exist, who
creates them) and says plainly that the **engine is bidspm**. The step-by-step walkthrough must use an **openly available
dataset that is not ours**; that dataset (probably OpenNeuro ds000102 Flanker) is a separate sub-project, so this round builds
the site and the explanatory pages only.

## Scope

In: Read the Docs configuration, a Sphinx site skeleton, four pages (Home, Credits and citing, The gears, Install and first
start), a README link and badge.
Out: the walkthrough and tutorial data (next sub-project), a configuration reference, API docs, moving content out of the README.
`docs/walkthrough.md` and its screenshots stay in the repo untouched and are **not part of the site** (study 141 must not appear
in public docs).

## Design

### Layout

The site source lives in **`docs/source/`**. The rest of `docs/` holds engineering notes, roadmaps and `superpowers/` specs;
building it directly would need a long exclude list and fail under `fail_on_warning`. `docs/source/` is also bidspm's own layout.

- `.readthedocs.yaml` (repo root): `version: 2`, ubuntu-22.04, Python 3.11, `sphinx.configuration: docs/source/conf.py`,
  `fail_on_warning: true`, `python.install` from `docs/requirements.txt`.
- `docs/requirements.txt`: `sphinx`, `myst-parser`, `shibuya`, each with a lower bound. This is the only dependency list for the docs:
  the project dependencies are not installed on Read the Docs, and students' `uv sync` must not pull in Sphinx.
- `docs/source/conf.py`: project "SPM BIDS Runner", author "MRI-Lab-Graz", `myst_parser`, Shibuya theme with a green accent
  (decided 2026-11-10), `myst_enable_extensions = ["colon_fence"]`, heading anchors to level 3.
- Pages are Markdown (MyST). Diagrams are plain text trees and tables, no image toolchain.

### Pages

1. **`index.md` (Home).** What the tool is in one screen; a credit box ("the engine is bidspm") linking to the credits page and
   to <https://bidspm.readthedocs.io/en/latest/>; the toctree. Says the step-by-step walkthrough on an open dataset is coming.
2. **`credits.md` (Credits and citing).**
   - What upstream does: bidspm (CPP Lab, GPL-3.0) runs the pipelines; SPM does the statistics; GNU Octave replaces MATLAB.
   - What this project adds: the runner CLI, the local web GUI, the readiness check, the model wizard, the patched files in
     `bidspm_overrides/` (baked into the image), the optional SPM standalone estimation.
   - How to cite: bidspm via its Zenodo concept DOI `10.5281/zenodo.3554331`, its repository
     <https://github.com/cpp-lln-lab/bidspm> and its `CITATION.cff`. The author list is **linked, not copied**, so it cannot go stale.
     Plus SPM and Octave as "cite what you used"; a line for citing this runner (repository URL and version).
3. **`gears.md` (The gears).** Three parts, written from the code and from the listing of a real run, not from memory:
   - *The machine*: your computer, Docker (or Apptainer), the image (bidspm + SPM + Octave), the repo (`spm_bids_runner.py` CLI and the GUI on
     `localhost:5100`). A text diagram of who talks to whom; the GUI only triggers CLI commands.
   - *What you must bring*: the BIDS raw folder, the fMRIPrep derivatives folder (and the space inside it), a working directory,
     and the BIDS-StatsModel JSON (the wizard writes it for you).
   - *What the tool creates and where*: `~/.spm-bids-runner/` (projects, logs), the working directory contents (`bidspm-preproc/`,
     `bidspm-stats/`, models, logs), the run settings files; one table with columns "thing / who provides it / where it lives / what breaks if missing".
4. **`install.md` (Install and first start).** Prerequisites, Docker Desktop on Apple Silicon first, `git clone`, `docker pull`
   of the image, `./scripts/setup.sh`, `./scripts/start_gui.sh`, the port and the "never expose the port" warning. Adapted from the
   README and walkthrough section 1; no lab-specific paths.

### README and GitHub

- The README gets a docs badge and a one-line link under the title once the RTD project builds.
- The GitHub repo website field is set with `gh repo edit --homepage <url>` only **after the user confirms the site is live**
  (the edit is public immediately).
- Importing the project on Read the Docs (slug `spm-bids-runner`, repo `MRI-Lab-Graz/spm-bids-runner`) is done by the user in their account.
  The URL they gave earlier (`worldline-desktop`) belongs to another product and is not used.

### Branch

`feat/rtd-docs` off `main`, independent of the unmerged `feat/progress-heartbeat`.

## Tests (TDD, `tests/test_docs_site.py`)

Written first, red before the files exist:

1. `.readthedocs.yaml` parses; `sphinx.configuration` points at an existing file; `fail_on_warning` is true; the requirements file exists.
2. `sphinx-build -W` of `docs/source` succeeds (skipped with a clear reason when Sphinx, MyST or Shibuya is not importable;
   `uv pip install -r docs/requirements.txt` first, and the merge gate does that).
3. The Credits page contains the bidspm DOI, the bidspm repository URL and the bidspm docs URL.
4. The Home page links to the credits page (a credit box that is not reachable defeats its purpose).
5. No page under `docs/source/` mentions our lab study (`study 141`, `crom`, `sub-141`) or a `/data/local` path.
6. The README links to the docs site (after RTD exists; the test is added in the same commit as the badge).

The merge gate from CLAUDE.md applies unchanged: `python -m pytest -q tests`, `/ponytail:ponytail-review`, `/security-review`.

## Decisions and ceilings

- **Single dependency list** (`docs/requirements.txt`): the build test skips when those packages are absent, so on a machine
  without them the gate would not exercise the build. The merge gate installs them first. Upgrade path if it bites: a `docs` dependency
  group in `pyproject.toml` run with `uv run --group docs`.
- **Link, do not copy**, upstream's author list and docs: less to maintain, one source of truth.
- **No Sphinx autodoc / API pages**: students use the GUI; the CLI is documented in the README.
- **Accuracy risk** is the gears page. The folder names and the "what breaks" column are checked against a real run output
  before the page is written, and the page names no file the code does not create.

## Next

After this: tutorial data (open dataset, downloaded and run end to end), then the walkthrough page with fresh screenshots, then
a configuration reference if students ask for it.
