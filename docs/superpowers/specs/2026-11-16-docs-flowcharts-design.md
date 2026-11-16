# Flowcharts for the Read the Docs site

Date: 2026-11-16. Status: design for review. Follow-up to the merged docs site (`docs/superpowers/specs/2026-11-16-rtd-docs-design.md`).

## Why

The site explains the prerequisites and the folders in text and box-drawing trees. Students still have to assemble the picture
themselves: how raw data, fMRIPrep output, the events file, the confounds file and the model feed the readiness check and the
run. Three diagrams show that structure at a glance.

## Scope

In: three diagrams drawn with **Mermaid**, each with a plain-text "In words" paragraph below it; the docs dependency and the Sphinx
setting for Mermaid; tests that keep the diagrams in step with the code.
Out: restructuring the pages, image files, interactive diagrams, a diagram of the model's internal nodes (the stats-model page already
reads them from the example file).

## Design

### Tool

`sphinxcontrib-mermaid` (added to `docs/requirements.txt`, `extensions` in `docs/source/conf.py`). Diagrams are MyST fences
```` ```{mermaid} ```` in the Markdown pages, so they stay editable text. Mermaid is rendered in the reader's browser (the build only
copies the script), so the `-W` build needs no network at render time. Ceiling: a reader without JavaScript or internet sees no
diagram; that is why every diagram is followed by an "In words" paragraph that says the same thing. The Shibuya theme's light and dark
mode is not styled per diagram (default Mermaid theme).

### The three diagrams

1. **`prerequisites/index.md`: how the prerequisites interact.** Top to bottom: the raw BIDS dataset with its **events** files; fMRIPrep
   (outside this tool) turning raw data into the fMRIPrep output (preprocessed BOLD, **confounds**, brain mask); the **model wizard**
   reading the events (conditions), offering the nuisance presets (static; it reads the confounds columns only to warn about unknown custom names) and writing the **model JSON**; the **readiness check**
   reading events, fMRIPrep output and model; its verdict gating the run.
2. **`prerequisites/stats-model.md`: how names flow.** An events value (`trial_type = faces`) becomes the regressor `trial_type.faces`
   in `X` and in `HRF.Variables`, then the contrast (`ConditionList`, `Weights`), then the per-subject images (`con_*`, `spmT_*`), then the
   group result per contrast; the confounds columns join `X` as nuisance regressors but not the contrasts.
3. **`gears.md`: what a run does.** Readiness check, then the actions in the order the runner uses them, `smooth`, `stats`, `dataset`,
   `report`, each box saying what it reads and writes (`bidspm-preproc/`, `bidspm-stats/sub-*/`, `bidspm-stats/derivatives/bidspm-groupStats/`,
   `reports/`). The `bms` action (model comparison) is not drawn; one sentence says it exists for comparing competing models.

All labels use names the code uses (the `--action` choices, folder names, file patterns already on the pages). The facts come from the
code and the pages that were fact-checked; a diagram adds no claim the text does not already make.

### Placement

Each diagram goes right under the first heading of its page's relevant section, before the prose that explains it, followed by "In
words". No page is reordered.

## Tests (TDD, `tests/test_docs_site.py`)

1. The build stays warning-free with the extension (the existing `-W` build test covers it; it fails if the extension is missing or
   misconfigured).
2. Each of the three pages contains a `{mermaid}` fence and an "In words" paragraph after it.
3. The gears diagram names every action of the runner's run sequence: `smooth`, `stats`, `dataset`, `report`, and each is a valid
   choice of the CLI's `--action` argument (read from `spm_bids_runner.py`'s parser, so a renamed action fails the test).
4. The prerequisites diagram mentions the four prerequisites by the names used in the toctree titles (fMRIPrep, confounds, events, model).
5. Mermaid blocks are syntactically complete: every block starts with `flowchart` and has balanced brackets (a cheap guard; the real
   syntax check is the browser, see Decisions).
6. The pages keep the forbidden-string guard (no lab study, no local paths); it already scans all pages.

## Decisions and ceilings

- **No headless Mermaid render in tests**: that needs Node and a browser. Syntax errors would show on the live page, which is checked by
  eye after the Read the Docs build of the branch (the same preview step used for the site). Upgrade path: `mermaid-cli` in CI if
  diagrams multiply.
- **Mermaid script source**: `sphinxcontrib-mermaid` default (a CDN). If the docs must work offline, vendor the script later.
- **Lower-bound pin only** for the new dependency, like the others (the `fail_on_warning` risk is already noted for the docs
  requirements).

## Rollout

Branch `feat/docs-flowcharts` off `main`. Merge gate as in CLAUDE.md. Verify the branch version on Read the Docs (the user activates it) before
merging to `main`; pushing is the user's decision.
