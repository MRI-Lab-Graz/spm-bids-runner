# fMRIPrep must be finished

This tool does **no preprocessing**. It starts from the output of [fMRIPrep](https://fmriprep.org/). bidspm can also
preprocess with SPM, but this runner does not use that: the steps it runs are smoothing, first-level statistics and
group-level statistics.

## What "ready" means

For every subject and every run of the task you want to analyse, the fMRIPrep output folder must contain, under
`sub-<label>/func/` (or `sub-<label>/ses-<n>/func/`):

| File (pattern) | Used for |
|---|---|
| `*task-<task>_*space-<space>_*desc-preproc_bold.nii.gz` | the preprocessed BOLD series that gets smoothed and analysed |
| `*task-<task>_*desc-confounds_timeseries.tsv` (and its `.json`) | nuisance regressors such as motion, see [The confounds file](confounds.md) |
| `*task-<task>_*space-<space>_*desc-brain_mask.nii.gz` | the brain mask that limits the analysis to brain voxels |

`<space>` is the output space in the file name, for example `MNI152NLin2009cAsym`. The **Space** setting of your project must
be exactly that string, and all subjects must have the same space. If a subject has no preprocessed BOLD in that space, the
readiness check stops with *"has no preprocessed BOLD for task-… in space …"* and tells you to re-run fMRIPrep with
`--output-spaces <space>`.

The readiness check always looks for the preprocessed BOLD, looks for the confounds file only when your model uses nuisance
columns, and does **not** check the brain mask. If the mask is missing, SPM silently falls back to a looser mask and the
analysis gets slower, so make sure fMRIPrep wrote it.

## If you only have raw data

Run fMRIPrep first. It is a separate program with its own documentation and its own citation (see
[Credits and citing](../credits.md)); running it is outside this tool.

## What the tool does with it

Your fMRIPrep folder is read, never changed. The smoothing step writes into `bidspm-preproc/` of your derivatives folder
(the working directory unless you set another) a copy of the preprocessed BOLD, the smoothed BOLD (`desc-smth<FWHM>_bold`) and a
copy of the confounds file; the statistics step adds the brain mask. The statistics step then reads only `bidspm-preproc/`.
[The gears](../gears.md) page shows where everything lives.
