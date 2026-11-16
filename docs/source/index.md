# SPM BIDS Runner

Run first-level and group-level fMRI analyses on a BIDS dataset without MATLAB. You work in a web page on your own
computer (or with one command); the analysis itself runs inside a Docker image.

:::{note}
**The engine is bidspm.** Every analysis step is done by [bidspm](https://bidspm.readthedocs.io/en/latest/) (CPP Lab),
which drives SPM and GNU Octave. This project adds a runner, a web GUI, a readiness check and a model wizard around it.
Please read [Credits and citing](credits.md) before you publish results.
:::

```{toctree}
:maxdepth: 2
:caption: Contents

credits
prerequisites/index
```
