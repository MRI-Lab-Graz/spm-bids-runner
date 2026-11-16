# Credits and citing

**The engine of this tool is [bidspm](https://bidspm.readthedocs.io/en/latest/).** We did not invent it. Everything that
turns your data into statistical maps is bidspm, which drives SPM; we wrapped it so that you can run it without MATLAB and
without writing a script.

## What the upstream projects do

| Project | What it does for you | Licence |
|---|---|---|
| [bidspm](https://github.com/cpp-lln-lab/bidspm) (CPP Lab, UCLouvain and collaborators) | reads a BIDS dataset and a BIDS Stats Model and runs the first-level, subject-level and group-level analyses with SPM | GPL-3.0 |
| [SPM](https://www.fil.ion.ucl.ac.uk/spm/) | the statistics: GLM estimation, contrasts, group tests | GPL |
| [GNU Octave](https://octave.org/) | runs SPM and bidspm in place of MATLAB | GPL |
| [fMRIPrep](https://fmriprep.org/) | the preprocessing that has to be finished before you start (see [fMRIPrep must be finished](prerequisites/fmriprep.md)) | Apache-2.0 |

The Docker image of this project contains bidspm, SPM and Octave; the exact versions are build arguments in
`containers/dockerfile/dockerfile` (`BIDSPM_TAG`, `SPM_TAG`).

## What this project adds

- a command-line runner (`spm_bids_runner.py`) and a local web GUI around bidspm;
- a **readiness check** that reads your data and your model and tells you what is missing before a long run starts;
- a **model wizard** that writes a first-level BIDS Stats Model for you;
- a few **patched bidspm files** (`bidspm_overrides/`), baked into the image, with a note on what is patched and why;
- a fast Python smoothing step and an optional estimation in SPM's compiled standalone;
- HTML reports for each subject and for the group.

## How to cite

Cite what you used. If you publish results obtained with this tool:

1. **bidspm**, as its authors ask: see their
   [`CITATION.cff`](https://github.com/cpp-lln-lab/bidspm/blob/main/CITATION.cff) (the author list lives there, so it
   stays correct). Releases are archived on Zenodo under the concept DOI
   [10.5281/zenodo.3554331](https://doi.org/10.5281/zenodo.3554331).
2. **SPM** and **GNU Octave**, following their own citation pages.
3. **fMRIPrep** (Esteban et al., 2019, *Nature Methods*, [doi:10.1038/s41592-018-0235-4](https://doi.org/10.1038/s41592-018-0235-4)),
   if you used it for preprocessing.
4. **This runner**: MRI-Lab-Graz, *SPM BIDS Runner*, version you used,
   <https://github.com/MRI-Lab-Graz/spm-bids-runner> (GPL-3.0-only).

The model file you analysed with follows the [BIDS Stats Models](https://bids-standard.github.io/stats-models/)
specification on the [BIDS](https://bids.neuroimaging.io/) standard.
