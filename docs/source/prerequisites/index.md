# Prerequisites

Four things must be true before the tool can analyse your data. They are listed in the order you meet them; the last one
is the most important.

| # | You need | Who makes it | Page |
|---|---|---|---|
| 1 | a finished **fMRIPrep** dataset | you, with fMRIPrep, before this tool | [fMRIPrep must be finished](fmriprep.md) |
| 2 | fMRIPrep's **confounds file** for every run | fMRIPrep | [The confounds file](confounds.md) |
| 3 | a BIDS **events file** for every run (your paradigm) | you, with your stimulus software | [The events file](events.md) |
| 4 | a **BIDS Stats Model** (what to analyse): the key page | the model wizard, with you | [The BIDS Stats Model](stats-model.md) |

```{toctree}
:maxdepth: 1

fmriprep
confounds
events
stats-model
```
