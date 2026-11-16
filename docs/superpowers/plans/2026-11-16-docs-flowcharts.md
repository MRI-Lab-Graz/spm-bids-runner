# Docs flowcharts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three Mermaid flowcharts on the Read the Docs site: how the prerequisites interact, how a condition name flows to a result, and what a run does.

**Architecture:** `sphinxcontrib-mermaid` renders MyST `{mermaid}` fences in the browser. Each diagram sits in its page with an "In words" paragraph for readers without JavaScript. Tests in `tests/test_docs_site.py` read the Mermaid sources and keep them in step with the code (the runner's real `--action` choices) and with the page text.

**Tech Stack:** Sphinx + MyST + Shibuya (already used), `sphinxcontrib-mermaid` (new, docs only), pytest.

Spec: `docs/superpowers/specs/2026-11-16-docs-flowcharts-design.md`. Branch: `feat/docs-flowcharts` (already created off `main`, spec committed). The sibling plan for the site itself is `docs/superpowers/plans/2026-11-16-rtd-docs.md` (merged).

## Global Constraints

- Site source stays in `docs/source/`; Sphinx + MyST pages; `docs/requirements.txt` is the only docs dependency list (`pyproject.toml` and `uv.lock` are not touched).
- The `-W` (warnings as errors) build stays green at every commit: no link to a page that does not exist.
- Diagrams are Mermaid `flowchart` blocks written as MyST fences ```` ```{mermaid} ````; each is followed immediately by a paragraph that starts with `**In words:**`.
- Every label uses names the code or the pages already use (the `--action` choices `smooth`, `stats`, `dataset`, `report`; folder names `bidspm-preproc/`, `bidspm-stats/`, `reports/`; file names `con_NNNN.nii`, `spmT_NNNN.nii`). A diagram adds no claim the text does not already make; claims come from the code (see `docs/repository_notes.md` section 4, the code map).
- No lab-study mentions (`study 141`, `crom`, `sub-141`) or `/data/local`, `/home/mri` paths on any page (guarded by an existing test).
- `tests/test_naming.py` scans every tracked file: never write the lowercase old report title it rejects.
- Do not mention the `bms` action in a diagram; one sentence on the gears page says it exists for comparing competing models.
- TDD: the failing test comes first in every task. Every subagent runs on `sonnet`. Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Never push.

## File Structure

| File | Change |
|---|---|
| `docs/requirements.txt` | add `sphinxcontrib-mermaid` |
| `docs/source/conf.py` | add the extension |
| `docs/source/prerequisites/index.md` | diagram 1 (how the prerequisites interact) |
| `docs/source/prerequisites/stats-model.md` | diagram 2 (how names flow) |
| `docs/source/gears.md` | diagram 3 (what a run does), a fifth step, one `bms` sentence |
| `tests/test_docs_site.py` | helpers + one test per diagram |

---

### Task 1: Mermaid setup and diagram 1 (how the prerequisites interact)

**Files:**
- Modify: `tests/test_docs_site.py`, `docs/requirements.txt`, `docs/source/conf.py`, `docs/source/prerequisites/index.md`

**Interfaces:**
- Produces (used by Tasks 2 and 3, in `tests/test_docs_site.py`): `_mermaid_blocks(page: str) -> list[str]` (the diagram sources of a page under `docs/source/`), `_balanced(block: str) -> bool`, `_in_words(page: str) -> str` (the text after the page's first diagram).

- [ ] **Step 1: Write the failing test and the helpers** (append to `tests/test_docs_site.py`)

```python
def _mermaid_blocks(page):
    """The Mermaid diagram sources of a page (MyST ```{mermaid} fences)."""
    return re.findall(r"```\{mermaid\}\n(.*?)\n```", (SRC / page).read_text(), re.S)


def _balanced(block):
    """A cheap syntax guard (the real check is the browser): brackets and quotes pair up."""
    return all(block.count(a) == block.count(b) for a, b in ("[]", "{}", "()")) and block.count('"') % 2 == 0


def _in_words(page):
    """The text after the page's first diagram."""
    return (SRC / page).read_text().split("```{mermaid}", 1)[1].split("\n```\n", 1)[1]


def test_prerequisites_diagram_shows_how_the_prerequisites_interact():
    (block,) = _mermaid_blocks("prerequisites/index.md")
    assert block.startswith("flowchart") and _balanced(block)
    for label in ("Raw BIDS dataset", "fMRIPrep", "confounds", "events", "Model wizard", "BIDS Stats Model", "Readiness check"):
        assert label in block, label
    assert _in_words("prerequisites/index.md").lstrip().startswith("**In words:**")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest -q tests/test_docs_site.py -k prerequisites_diagram`
Expected: FAIL with `ValueError: not enough values to unpack` (no diagram on the page yet).

- [ ] **Step 3: Add the dependency and the extension**

`docs/requirements.txt` gets a fourth line:

```text
sphinxcontrib-mermaid>=1.0
```

In `docs/source/conf.py` change the extensions line to:

```python
extensions = ["myst_parser", "sphinxcontrib.mermaid"]
```

In `tests/test_docs_site.py`, the fast path of `_sphinx_cmd` must also require the new package, or a machine that has the old three would fail the build with a missing module instead of falling back to `uv`. Add this helper above `_sphinx_cmd`:

```python
def _has(module):
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:  # a missing parent package
        return False
```

and replace the line

```python
    if all(importlib.util.find_spec(m) for m in ("sphinx", "myst_parser", "shibuya")):
```

with

```python
    if all(_has(m) for m in ("sphinx", "myst_parser", "shibuya", "sphinxcontrib.mermaid")):
```

- [ ] **Step 4: Add diagram 1 to `docs/source/prerequisites/index.md`**

Insert the following between the table (ending with the row that starts `| 4 |`) and the line ```` ```{toctree} ````, with a blank line before and after:

`````markdown
```{mermaid}
flowchart TD
    raw["Raw BIDS dataset<br/>with events files"]
    fmriprep["fMRIPrep<br/>(runs before this tool)"]
    out["fMRIPrep output<br/>preprocessed BOLD, confounds, brain mask"]
    wizard["Model wizard"]
    model["BIDS Stats Model<br/>(a JSON file)"]
    check{"Readiness check"}
    run["Run:<br/>smooth, stats, dataset"]
    raw --> fmriprep --> out
    raw -- "events: the conditions" --> wizard
    out -- "confounds: the nuisance columns" --> wizard
    wizard --> model
    raw -- "events" --> check
    out --> check
    model --> check
    check -- "errors block Run in the GUI" --> run
```

**In words:** the events files belong to the raw dataset. fMRIPrep, which runs before this tool, turns the raw data into the
fMRIPrep output: the preprocessed BOLD, the confounds file and the brain mask. The model wizard reads the events (the conditions
you can model) and the confounds columns (the nuisance presets) and writes the BIDS Stats Model. The readiness check then
compares the events, the fMRIPrep output and the model, and in the GUI its errors block the run.
`````

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest -q tests/test_docs_site.py tests/test_naming.py tests/test_readme_paths.py`
Expected: all pass, including the `-W` build (the first run installs the new package through `uv`).

- [ ] **Step 6: Commit**

```bash
git add docs/requirements.txt docs/source/conf.py docs/source/prerequisites/index.md tests/test_docs_site.py
git commit -m "feat(docs): Mermaid setup and the prerequisites flowchart

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Diagram 2 (how names flow)

**Files:**
- Modify: `tests/test_docs_site.py`, `docs/source/prerequisites/stats-model.md`

**Interfaces:**
- Consumes: `_mermaid_blocks`, `_balanced`, `_in_words` from Task 1.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_stats_model_diagram_follows_a_condition_name_to_the_results():
    (block,) = _mermaid_blocks("prerequisites/stats-model.md")
    assert block.startswith("flowchart") and _balanced(block)
    for label in ("trial_type = faces", "trial_type.faces", "ConditionList", "con_NNNN.nii", "spmT_NNNN.nii", "confounds"):
        assert label in block, label
    assert _in_words("prerequisites/stats-model.md").lstrip().startswith("**In words:**")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest -q tests/test_docs_site.py -k stats_model_diagram`
Expected: FAIL with `ValueError: not enough values to unpack`.

- [ ] **Step 3: Replace the text flow in `docs/source/prerequisites/stats-model.md`**

In the section `## How names flow through the analysis`, the sentence "A condition name travels from your data to your results, and every link has to match:" stays. Replace the whole ```` ```text ```` block that follows it (the five lines from `events file:   trial_type = faces` to `group:         one result per contrast name`) with:

`````markdown
```{mermaid}
flowchart LR
    ev["events file<br/>trial_type = faces"]
    reg["model: trial_type.faces<br/>in X and HRF.Variables<br/>(SPM calls it faces)"]
    con["contrast<br/>Name, ConditionList, Weights"]
    img["per subject<br/>con_NNNN.nii, spmT_NNNN.nii"]
    grp["group level<br/>one result per contrast"]
    conf["confounds file<br/>trans_x, rot_x, ..."]
    ev --> reg --> con --> img --> grp
    conf -- "nuisance columns in X" --> reg
```

**In words:** a value in the `trial_type` column of your events file (for example `faces`) becomes the regressor
`trial_type.faces` in `X` and in `HRF.Variables`; SPM calls it `faces`. A contrast lists it in its `ConditionList`. Each
contrast gives `con_NNNN.nii` and `spmT_NNNN.nii` for each subject, and the group level gives one result per contrast. The
confounds columns join `X` as nuisance regressors but never appear in a contrast.
`````

Leave the paragraph that starts "If you rename a condition in the events file" unchanged.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q tests/test_docs_site.py tests/test_naming.py tests/test_readme_paths.py`
Expected: all pass. (The existing stats-model needle test still passes: it does not look at the removed text block.)

- [ ] **Step 5: Commit**

```bash
git add docs/source/prerequisites/stats-model.md tests/test_docs_site.py
git commit -m "feat(docs): the names-flow flowchart on the stats-model page

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Diagram 3 (what a run does)

**Files:**
- Modify: `tests/test_docs_site.py`, `docs/source/gears.md`

**Interfaces:**
- Consumes: `_mermaid_blocks`, `_balanced`, `_in_words` from Task 1; `spm_bids_runner.parse_arguments()` (reads `sys.argv`, exits with `SystemExit` on an invalid `--action` choice).

- [ ] **Step 1: Write the failing tests** (append)

```python
def test_gears_diagram_uses_the_runners_real_actions(monkeypatch):
    import spm_bids_runner
    (block,) = _mermaid_blocks("gears.md")
    assert block.startswith("flowchart") and _balanced(block)
    for action in ("smooth", "stats", "dataset", "report"):
        assert f'"{action}<br/>' in block, action
        monkeypatch.setattr(sys, "argv", ["spm_bids_runner.py", "--action", action])
        assert spm_bids_runner.parse_arguments().action == [action]   # SystemExit if the runner no longer has it
    for label in ("Readiness check", "bidspm-preproc/", "bidspm-stats/", "bidspm-groupStats/", "reports/"):
        assert label in block, label
    assert _in_words("gears.md").lstrip().startswith("**In words:**")
    assert "`bms`" in (SRC / "gears.md").read_text()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest -q tests/test_docs_site.py -k gears_diagram`
Expected: FAIL with `ValueError: not enough values to unpack`.

- [ ] **Step 3: Replace the section `## The order of a run` in `docs/source/gears.md`**

Replace everything from the line `## The order of a run` up to, but not including, the final line `Next: the four [prerequisites](prerequisites/index.md), then [install](install.md).` with:

`````markdown
## The order of a run

```{mermaid}
flowchart TD
    check["Readiness check<br/>reads your data and model, lists what is missing"]
    smooth["smooth<br/>reads the fMRIPrep BOLD and confounds"]
    pre[("bidspm-preproc/<br/>BOLD copy, smoothed BOLD, confounds copy")]
    stats["stats<br/>adds the brain mask, fits the model"]
    st[("bidspm-stats/<br/>per subject: SPM.mat, con_NNNN.nii, spmT_NNNN.nii")]
    dataset["dataset<br/>group-level test"]
    grp[("bidspm-stats/derivatives/<br/>bidspm-groupStats/")]
    report["report<br/>HTML reports"]
    rep[("reports/")]
    check -- "errors block Run in the GUI" --> smooth
    smooth --> pre --> stats --> st --> dataset --> grp
    st --> report
    grp --> report
    report --> rep
```

**In words:** the steps run one after the other, and each reads what the one before wrote:

1. **Readiness check**: reads your data and your model and lists what is missing.
2. **Smooth**: smooths the preprocessed BOLD and copies the confounds into `bidspm-preproc/`.
3. **Stats**: copies the brain mask into `bidspm-preproc/`, then fits the model for every subject (the slow step; estimation
   is silent for a long time, which is normal; do not restart Docker).
4. **Dataset**: the group-level test across subjects.
5. **Report**: writes HTML reports for each subject and for the group to `reports/`.

A separate action, `bms`, compares competing models; it is not part of a normal run.

`````

(Keep the blank line before the final `Next: ...` line.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q tests/test_docs_site.py tests/test_naming.py tests/test_readme_paths.py`
Expected: all pass. The other gears tests (needles, links) still pass because the section keeps its text.

- [ ] **Step 5: Commit**

```bash
git add docs/source/gears.md tests/test_docs_site.py
git commit -m "feat(docs): the run flowchart on the gears page

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Verify the diagrams render, merge gate, publish (controller steps)

This task is done by the controller with the user, not by an implementer subagent.

- [ ] **Step 1: Render the diagrams in a real browser.** Build the site to a scratch folder (`python -m sphinx -W -b html docs/source <scratch>/html`, through `uv run --no-project --with-requirements docs/requirements.txt` if needed), open each of the three pages with Playwright's headless Chromium (installed for the browser tests), wait for the Mermaid script, and assert every `.mermaid` element contains an `<svg>` and no "Syntax error" text; save a screenshot of each diagram and look at them. Nothing from this step is committed. If a diagram fails to render, fix its source through a fix round on the owning task.
- [ ] **Step 2: Merge gate (CLAUDE.md).** `python -m pytest -q tests` is green; `/ponytail:ponytail-review` on the branch diff; `/security-review` on the branch diff; resolve findings or defer them with the reason in the merge message.
- [ ] **Step 3: Publish.** With the user's go: push `feat/docs-flowcharts`; the user activates that version on Read the Docs and confirms the build is green and the diagrams show; then merge into local `main` with the gate results in the merge message; push `main` only after asking the user again.
