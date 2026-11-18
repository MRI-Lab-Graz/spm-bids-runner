# Read the Docs site (structure first)

Date: 2026-11-16. Status: approved design, spec for review. Fourth of the student-release sub-projects (rename and multi-arch image are merged; tutorial data comes after this).

## Why

Students have the README (800 lines, written for maintainers) and `docs/walkthrough.md`, which uses a lab study they cannot
download. They need a site that first explains **how the tool is built** (what they must have, which folders and files exist, who
creates them) and says plainly that the **engine is bidspm**. They also need to understand the four **prerequisites** before
they click anything: a finished fMRIPrep dataset, fMRIPrep's confounds file, the BIDS events file, and above all the
**BIDS Stats Model file**, which decides what is analysed. The step-by-step walkthrough must use an **openly available
dataset that is not ours**; that dataset (probably OpenNeuro ds000102 Flanker) is a separate sub-project, so this round builds
the site and the explanatory pages only.

## Scope

In: Read the Docs configuration, a Sphinx site skeleton, seven pages (Home, Credits and citing, The gears, a Prerequisites
section of four pages, Install and first start), a README link and badge.
Out: the walkthrough and tutorial data (next sub-project), a complete reference of every BIDS Stats Model field (the model page
teaches the concepts and links upstream for the rest), API docs, moving content out of the README.
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
     and the BIDS-StatsModel JSON (the wizard writes it for you). Each item links to its prerequisite page below.
   - *What the tool creates and where*: `~/.spm-bids-runner/` (projects, logs), the working directory contents (`bidspm-preproc/`,
     `bidspm-stats/`, models, logs), the run settings files; one table with columns "thing / who provides it / where it lives / what breaks if missing".
4. **Prerequisites** (`prerequisites/`, four pages in the order a student meets them; the toctree marks the last one as the key page).
   Each page has the same shape: what it is, what the tool does with it, how to look at it yourself, what goes wrong.
   Written from the code (`lib/preflight.py`, `lib/utils.py`, `lib/fast_smooth.py`, `lib/model_wizard.py`) and checked against a real run.
   1. **`fmriprep.md` (fMRIPrep must be finished).** This tool does **no preprocessing**: it starts from fMRIPrep output. What "ready"
      means (the derivatives folder, the output space such as `MNI152NLin2009cAsym` and its `desc-preproc_bold` files, one set per
      subject and run), why SPM's own preprocessing is not used, what to do if you have raw data only (link to and cite fMRIPrep;
      running it is outside this tool). What the tool does next: the smoothing step copies the BOLD file and the confounds file
      into `bidspm-preproc/`.
   2. **`confounds.md` (The confounds file).** fMRIPrep's `*_desc-confounds_timeseries.tsv` (+ `.json`): one row per volume,
      one column per nuisance signal. The columns students meet (motion `trans_*`/`rot_*`, `framewise_displacement`, `a_comp_cor_*`, ...),
      what the wizard's nuisance presets select (e.g. `motion6`, the default is `none`) and how a custom column list works, how
      to open the file and read the `.json`. The gotcha that motivated a fix: engine-side, a confounds file that could not be found only logged a
      warning, so a model once ran **without motion regressors** (the fast smoothing path now copies the file into `bidspm-preproc/`).
      The readiness check reports as errors: no confounds file for a run when the model needs nuisance columns, a confounds file with
      a different number of rows than the BOLD has volumes, and non-numeric values.
   3. **`events.md` (The events file).** BIDS `*_events.tsv`: `onset` and `duration` in seconds, `trial_type` and any extra columns; this
      is the paradigm. Where it lives per run and the BIDS inheritance rule (a dataset-level `task-<task>_events.tsv`); what the
      wizard reads from it (the `trial_type` values and other columns become the conditions you can keep, split or modulate); the
      zero-duration and `n/a` cases; what the readiness check reports when events are missing or do not match the run.
   4. **`stats-model.md` (The BIDS Stats Model: the most important page, and the longest).**
      - What it is: the JSON file that tells the engine *what to analyse*: the design (which regressors from the events and the
        confounds), the contrasts, and how runs, subjects and the dataset are combined. Link to the BIDS Stats Models specification and
        to bidspm's own model documentation; credit bidspm for the SPM implementation.
      - Anatomy: `Name`/`BIDSModelVersion`, `Input` (task, space), `Nodes` at the levels Run, Subject, Dataset, and in each node `Model`
        (`X`, HRF), `Transformations`, `DummyContrasts`/`Contrasts`, `Options`. An **annotated example** that the repo itself produces.
      - How the names flow: condition in the events file, then the regressor name, then the contrast name, then the `con_`/`spmT_` image
        in the output; why renaming a condition breaks a contrast.
      - How to make one: the wizard (five steps and the four recipes: valid only, split by column, merge/rename, parametric
        modulator), then the model editor for weighted and F contrasts, or by hand.
      - How to configure it: where it is saved (`models/` in the derivatives folder, else the working directory), how a project
        picks it (the model setting in the project, `MODELS_FILE` / `--model` on the CLI), and that its task and space must match the
        data. What the runner validates before it starts, and the typical error messages.
5. **`install.md` (Install and first start).** Prerequisites, Docker Desktop on Apple Silicon first, `git clone`, `docker pull`
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
7. The annotated example model on `stats-model.md` is not hand-typed: a test builds the same model with the wizard code
   (`lib/model_wizard.py`) and asserts the page's JSON block equals it, and that the runner's model validation accepts it. The page
   cannot drift from what the tool produces.
8. The prerequisites pages exist, are in the toctree in the order above, and the gears page links to each of them.

The merge gate from CLAUDE.md applies unchanged: `python -m pytest -q tests`, `/ponytail:ponytail-review`, `/security-review`.

## Decisions and ceilings

- **Single dependency list** (`docs/requirements.txt`): the build test uses Sphinx from the running interpreter when the docs packages
  are installed and otherwise runs it through `uv run --no-project --with-requirements docs/requirements.txt`, so the merge gate needs
  no manual install. It skips only when neither the packages nor uv exist. Ceiling: the first run downloads the packages.
- **Link, do not copy**, upstream's author list and docs: less to maintain, one source of truth.
- **No Sphinx autodoc / API pages**: students use the GUI; the CLI is documented in the README.
- **Accuracy risk** is the gears page and the four prerequisite pages. Folder names, column names, preset contents and the
  "what breaks" statements are checked against the code and a real run output before each page is written; a page names no file or
  setting the code does not use.
- **Examples come from the tool, not from a lab study.** The annotated model is generated by the wizard from a tiny synthetic
  fixture (no real subject data, nothing of ours). The Flanker data replaces it in the walkthrough later.
- **Concepts, not a field reference** for the Stats Model: the full specification belongs to upstream and is linked.

## Next

After this: tutorial data (open dataset, downloaded and run end to end), then the walkthrough page with fresh screenshots, then
group-level and contrast-builder (F contrast) pages if students ask for them.
