# Install and first start

## What you need

- **Docker** (Docker Desktop on a Mac or Windows; on Linux your user must be in the `docker` group), or Apptainer on a cluster.
- About **3.5 GB** of disk for the image and **0.7 GB** for the Python environment.
- An internet connection for the first setup.
- A finished fMRIPrep dataset and its BIDS raw data: see the [prerequisites](prerequisites/index.md).

You do not need Python: the setup script downloads its own.

:::{note}
**Apple Silicon Macs.** Docker Desktop's memory limit (Settings, Resources) decides how many subjects the tool can process
in parallel; the GUI suggests a number of workers from it. Keep Docker running during a run and do not restart it when the
run looks silent: model estimation prints nothing for a long time. An update of Docker Desktop in the middle of a run restarts
its engine and stops the run.
:::

## Steps

```bash
git clone https://github.com/MRI-Lab-Graz/spm-bids-runner.git
cd spm-bids-runner
```

**1. Get the image** (once). Pull it:

```bash
docker pull ghcr.io/mri-lab-graz/spm-bids-runner:latest
```

If the pull reports no matching platform for your machine, the image for your architecture is not published yet; build it
instead (about 5 minutes, needs internet):

```bash
docker build -f containers/dockerfile/dockerfile -t ghcr.io/mri-lab-graz/spm-bids-runner:latest .
```

**2. Set up the Python environment** (once):

```bash
./scripts/setup.sh
```

**3. Start the GUI:**

```bash
./scripts/start_gui.sh
```

The script prints a "Pre-flight check" (what is ready and what is missing, for example *Docker image ... missing* when the image
is not pulled or built yet) and then `Open in browser: http://localhost:5100`. Open that address.

If port 5100 is taken by another program: `SPM_BIDS_RUNNER_PORT=5101 ./scripts/start_gui.sh`.

:::{warning}
The GUI has no login. It listens on your own computer only; never expose its port. On a server, forward it instead:
`ssh -L 5100:localhost:5100 you@server`, then open `http://localhost:5100` on your own machine.
:::

## Check that it works

```bash
docker images ghcr.io/mri-lab-graz/spm-bids-runner
```

should list the image. In the GUI, create a project and open the readiness check: it tells you what is still missing (for
example *Docker is not answering* when Docker Desktop is stopped).

## If setup broke

`./scripts/setup.sh --force` rebuilds the environment (a plain re-run does nothing once a setup has succeeded).
