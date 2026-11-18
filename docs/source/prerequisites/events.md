# The events file

The events file is your **paradigm**: what happened, when, and for how long. It belongs to the raw
[BIDS](https://bids.neuroimaging.io/) dataset, not to fMRIPrep:

```text
rawdata/sub-<label>/func/sub-<label>_task-<task>_run-<n>_events.tsv
```

It is a **tab-separated** text file, one row per event (a trial, a block, a button press).

## Columns

| Column | Required | Meaning |
|---|---|---|
| `onset` | yes | seconds from the start of the run (the first volume) to the start of the event |
| `duration` | yes | seconds the event lasted; `0` is allowed for instantaneous events |
| `trial_type` | for the wizard | the condition name, for example `congruent` |
| anything else | no | extra information per event, for example `response_validity` or `rt` |

```text
onset	duration	trial_type	response_validity	rt
10.0	2.0	congruent	valid	0.52
14.0	2.0	incongruent	invalid	n/a
```

`n/a` marks a missing value. It is allowed in the extra columns but **not** in `onset` or `duration`.

## One file per run, or one for all

The tool uses the most specific events file that applies to a run. If a subject has no events file of its own, the
dataset-level file `task-<task>_events.tsv` in the top folder of the dataset is used (BIDS inheritance). The file must not
quote its fields.

## What the tool does with it

- The **model wizard** reads the events of all subjects. The `trial_type` values become the conditions you can keep or
  leave out; the other columns are what recipes work on, for example `split_by_column` splits a condition by
  `response_validity`, `parametric_modulator` uses a numeric column such as `rt`. See
  [The BIDS Stats Model](stats-model.md).
- The **readiness check** reads them before a run and reports, per subject:
  - no events file for the task;
  - no `onset` or `duration` column, a duplicate column, or a file that is not UTF-8 text;
  - an `onset` or `duration` that is not a number, or a negative `duration` (the row is named by its line number);
  - a negative onset (a warning: BIDS allows it, but check that the events are aligned to the scan);
  - events that run past the end of the scan (a warning);
  - a condition that the model uses but a subject never has.

## Things that go wrong

- A column you filter on that is `n/a` in every row makes the analysis fail for that subject; the wizard flags such
  columns.
- Events in milliseconds instead of seconds give a model that fits nothing.
- A condition name with spaces or other special characters: the recipes that filter, split or merge on a condition allow
  letters, digits, `_` and `-` only; a column name a recipe uses allows letters, digits and `_` only.
