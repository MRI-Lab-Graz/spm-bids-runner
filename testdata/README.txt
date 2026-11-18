Test data for SPM BIDS Runner: ONE subject of study 141, task "crom"
=====================================================================

For checking the program (and the arm64 image) on an Apple Silicon Mac. One subject is a technical test, not an analysis:
a group result needs more subjects, so skip the "Dataset" action here.

What is in here (3.4 GB)
  rawdata/                 BIDS raw data: sub-141A332C, ses-1, task-crom (bold image, sidecar, events)
  derivatives/fmriprep/    fMRIPrep 25.2.5 output in MNI152NLin2009cAsym space (preprocessed BOLD, brain mask, confounds)

Removed on purpose: patient name/ID/birth date/sex/height/weight/age, scan UIDs and date-times from the JSON sidecars; the other
participants and their demographics; anatomical, diffusion, fieldmap, physio and resting-state data. The subject label
(141A332C) is a study code. Do not pass this folder on without checking with the study lead; delete it when you are done.

Create the project in the GUI (Projects -> New Project)
  BIDS Folder         <this folder>/rawdata
  Working Directory   any empty folder, e.g. ~/spm-bids-runner-output
  fMRIPrep Folder     <this folder>/derivatives/fmriprep
  Space               MNI152NLin2009cAsym   (read from the fMRIPrep folder)
  Container Type      Docker, image field empty (the standard image; build it locally first when testing a new image)
Folders stage: tick the task "crom", FWHM 6.

Model (wizard, "Create Model")
  Step 1: untick fixation (baseline) and button_press (zero duration); keep item, rating, verbal_response
  Step 2: optional recipe "Only valid/correct trials": condition item, column response_validity, keep value valid (52 of 57)
  Step 3: confound preset motion6
  Step 4: contrasts as generated
  Step 5: name it, "Check readiness", "Save and open"

Run
  Options: tick Smooth and Stats (not Dataset: one subject). Parallel subjects: 1.
  "Check readiness" should end with verdict "warnings" (about 12 BIDS validator warnings: short README, no authors,
  undescribed events columns). Errors would block the run; warnings are fine.
  Timing on the lab server (x86, Octave engine): smoothing about 40 s, first-level estimation about 30 minutes for this
  1006-volume run. Expect the Mac to be slower or similar; Docker Desktop needs at least 8 GB of memory (Settings -> Resources).

Expected outputs (in the working directory)
  bidspm-preproc/sub-141A332C/ses-1/func/..._desc-smth6_bold.nii
  bidspm-stats/sub-141A332C/task-crom_space-MNI152NLin2009cAsym_FWHM-6/   SPM.mat, beta_*.nii, con_*.nii, spmT_*.nii
