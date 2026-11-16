# SPM BIDS Runner

Run first-level and group-level fMRI analyses on a BIDS dataset without MATLAB. You work in a web page on your own
computer (or with one command); the analysis itself runs inside a Docker image.

## What it is for

You have fMRI data that fMRIPrep has already preprocessed, and you want statistics: a first-level analysis for every subject
and a group-level analysis across subjects, without writing SPM scripts. You describe the analysis once, in a **BIDS Stats
Model** (a JSON file that a wizard helps you write). The tool checks that everything is in place, runs the analysis and writes
the results and HTML reports into one folder.

:::{note}
**The engine is bidspm.** Every analysis step is done by [bidspm](https://bidspm.readthedocs.io/en/latest/) (CPP Lab),
which drives SPM and GNU Octave. This project adds a runner, a web GUI, a readiness check and a model wizard around it.
Please read [Credits and citing](credits.md) before you publish results.
:::

## The pipeline at a glance

```{mermaid}
flowchart LR
    bring["You bring<br/>fMRIPrep output, events files, a BIDS Stats Model"]
    check{"Readiness check"}
    smooth["smooth"]
    stats["stats<br/>one model per subject"]
    dataset["dataset<br/>group level"]
    report["report<br/>HTML for each subject"]
    bring --> check --> smooth --> stats --> dataset
    stats --> report
```

**In words:** you bring the fMRIPrep output, the events files and a BIDS Stats Model. The readiness check tells you what is
missing. Then the run smooths the images (`smooth`), fits the model for every subject (`stats`) and tests across subjects
(`dataset`); `report` writes an HTML report for each subject from the statistics results.

## Where to start

1. [The gears](gears.md): how the tool is built, and where everything is written.
2. [Prerequisites](prerequisites/index.md): the four things you need before a run. The BIDS Stats Model is the most important.
3. [Install and first start](install.md).
4. [Credits and citing](credits.md).

A step-by-step walkthrough on an open dataset will follow.

```{toctree}
:maxdepth: 2
:caption: Contents

credits
gears
prerequisites/index
install
```
