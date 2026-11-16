# The confounds file

For every run, fMRIPrep writes a table of nuisance signals next to the preprocessed data:

```text
sub-<label>/func/sub-<label>_task-<task>_desc-confounds_timeseries.tsv
sub-<label>/func/sub-<label>_task-<task>_desc-confounds_timeseries.json
```

The `.tsv` has **one row per volume** and **one column per signal**; the `.json` describes the columns. You can open the
`.tsv` in any spreadsheet program or `head` it in a terminal.

## What is in it

| Column(s) | Meaning |
|---|---|
| `trans_x`, `trans_y`, `trans_z` | head translation in mm (the three motion axes) |
| `rot_x`, `rot_y`, `rot_z` | head rotation in radians |
| `framewise_displacement` | how far the head moved between two volumes |
| `*_derivative1`, `*_power2`, `*_derivative1_power2` | the motion columns' temporal derivative, square and squared derivative |
| `a_comp_cor_*`, `global_signal`, `csf`, `white_matter`, ... | physiological and tissue signals |

The first row of derivative columns and of `framewise_displacement` is `n/a`: there is no previous volume to compare with.
That is normal.

## Why the model needs it

Head motion produces signal changes that look like activation. Adding the motion signals to the model as **nuisance
regressors** removes the part of the signal they explain. In the BIDS Stats Model they are the column names listed after the
intercept (`1`) in `X`, see The BIDS Stats Model.

## The wizard's presets

The model wizard offers these presets in its nuisance step. The default is `none`.

| Preset | Columns |
|---|---|
| `none` | no nuisance regressors |
| `motion6` | `trans_x`, `trans_y`, `trans_z`, `rot_x`, `rot_y`, `rot_z` |
| `motion24` | `motion6` plus, for each of the six, `_derivative1`, `_power2` and `_derivative1_power2` (24 columns) |
| `motion6_fd` | `motion6` plus `framewise_displacement` |

Instead of a preset you can type your own comma-separated list of column names. A name that fMRIPrep did not write is
reported as a warning in the wizard and as a problem by the readiness check.

## What the tool does with the file

The smoothing step copies the confounds file (`.tsv` and `.json`) from fMRIPrep into `bidspm-preproc/`, because the statistics step
reads only that folder. This copy matters: the engine itself only logs a warning when it cannot find a confounds file, so
a model once ran **without motion regressors** and nobody noticed. The copy is now always made, and the readiness check
reports these as errors before a run starts:

- no confounds file for a run when the model uses nuisance columns;
- a confounds file that does not have the same number of rows as the BOLD has volumes (it belongs to another run);
- non-numeric values (other than `n/a`).

The fix is nearly always the same: re-run fMRIPrep for that subject.
