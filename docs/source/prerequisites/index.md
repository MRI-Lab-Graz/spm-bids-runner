# Prerequisites

Four things must be true before the tool can analyse your data. They are listed in the order you meet them; the last one
is the most important.

| # | You need | Who makes it | Page |
|---|---|---|---|
| 1 | a finished **fMRIPrep** dataset | you, with fMRIPrep, before this tool | [fMRIPrep must be finished](fmriprep.md) |
| 2 | fMRIPrep's **confounds file** for every run | fMRIPrep | [The confounds file](confounds.md) |
| 3 | a BIDS **events file** for every run (your paradigm) | you, with your stimulus software | [The events file](events.md) |
| 4 | a **BIDS Stats Model** (what to analyse): the key page | the model wizard, with you | [The BIDS Stats Model](stats-model.md) |

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

```{toctree}
:maxdepth: 1

fmriprep
confounds
events
stats-model
```
