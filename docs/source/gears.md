# The gears: how the tool is built

Before you click anything, it helps to know the parts. There are three groups: the **machine** that runs the analysis,
**what you bring**, and **what the tool creates**.

## The machine

```text
your computer
├─ Docker Desktop (or Apptainer on a cluster)   runs the image
│  └─ the image  ghcr.io/mri-lab-graz/spm-bids-runner
│        bidspm  +  SPM  +  GNU Octave           <- the engine (see Credits)
├─ spm-bids-runner/                              the repository you cloned
│  ├─ spm_bids_runner.py                         the command-line runner: all the real work is triggered here
│  └─ the GUI, a web page at http://localhost:5100   it only starts runner commands
└─ ~/.spm-bids-runner/                           your saved projects (settings)
```

- The **image** holds the engine. You pull or build it once (about 3.5 GB). Nothing inside it is yours.
- The **runner** reads your data, builds the commands and starts the container; it also does the readiness check and the
  fast smoothing.
- The **GUI** is only a convenient way to call the runner. By default it listens on your own computer (`127.0.0.1`) and has
  no login: never expose its port.
- **`~/.spm-bids-runner/`** keeps one folder per project with the settings you entered. The run logs go to the project's output folder (your
  working directory); only a project without one keeps them here. Deleting `~/.spm-bids-runner/` removes your projects, never
  your data.

## What you bring

| You bring | What it is | Page |
|---|---|---|
| a **BIDS raw dataset** | `rawdata/sub-*/func/` with the events files (and the raw images) | [The events file](prerequisites/events.md) |
| the **fMRIPrep output** | `derivatives/fmriprep/sub-*/func/` with `desc-preproc_bold`, brain mask and confounds | [fMRIPrep must be finished](prerequisites/fmriprep.md), [The confounds file](prerequisites/confounds.md) |
| a **working directory** | an empty folder (or your derivatives folder) where everything the tool writes goes | below |
| a **model** | the BIDS Stats Model JSON; the wizard writes it for you | [The BIDS Stats Model](prerequisites/stats-model.md) |

## What the tool creates, and where

Everything is written to your working directory (the **derivatives** folder; it defaults to the working directory). Your raw
data and your fMRIPrep folder are never modified.

```text
<working directory>/
├─ models/                  the model files (the wizard saves here)
├─ bidspm-preproc/          smoothing output: smoothed BOLD and confounds copy per subject; the statistics step adds the brain mask
├─ bidspm-stats/            statistics output
│  ├─ sub-<label>/task-<task>_space-<space>_FWHM-<n>/    first level: SPM.mat, beta_*.nii, con_*.nii, spmT_*.nii
│  ├─ derivatives/bidspm-groupStats/                      group (dataset) level
│  ├─ reports/ and jobs/                                  bookkeeping and the model's citation text
│  └─ dataset_description.json
├─ reports/                 HTML reports for each subject and for the group
└─ logs/ and options/       the run logs and bidspm's run settings (options_*.json)
```

| Thing | Who provides it | Where it lives | What breaks if it is missing |
|---|---|---|---|
| raw BIDS data with events | you | `rawdata/` | the readiness check: *has no events file for task-…* |
| fMRIPrep output | you (with fMRIPrep) | `derivatives/fmriprep/` | *has no preprocessed BOLD for task-… in space …* |
| confounds file | fMRIPrep | next to the preprocessed BOLD | *has no confounds file for task-…* when the model uses nuisance columns |
| model | the wizard, with you | `<working directory>/models/` | the run does not start |
| smoothed data | the tool (smoothing step) | `bidspm-preproc/` | the statistics step has nothing to analyse |
| first-level results | the tool (statistics step) | `bidspm-stats/sub-*/` | no subject maps, so no group level |
| group results | the tool (dataset step) | `bidspm-stats/derivatives/bidspm-groupStats/` | no group maps |

## The order of a run

1. **Readiness check**: reads your data and your model and lists what is missing.
2. **Smooth**: smooths the preprocessed BOLD and copies the confounds into `bidspm-preproc/`.
3. **Stats**: copies the brain mask into `bidspm-preproc/`, then fits the model for every subject (the slow step; estimation
   is silent for a long time, which is normal; do not restart Docker).
4. **Dataset**: the group-level test across subjects.

Next: the four [prerequisites](prerequisites/index.md), then Install.
