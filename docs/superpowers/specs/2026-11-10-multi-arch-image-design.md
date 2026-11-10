# Multi-arch image (amd64 + arm64)

Date: 2026-11-10. Status: approved design, spec for review. Second of four student-release sub-projects (rename done; then tutorial data, Read the Docs).

## Why

Students use Apple Silicon Macs. The published `ghcr.io/mri-lab-graz/spm-bids-runner:latest` (v2.1.1) is linux/amd64 only, so
`docker pull` on an M-series Mac fails with "no matching manifest" and `setup_apple_silicon.sh` only warns. Nothing in the
runner passes `--platform`, so a native arm64 image is picked up automatically once it exists.

## Design

`.github/workflows/docker-publish.yml` stays **manual** (`workflow_dispatch`, inputs `version` and `latest`): publishing is a decision.

1. **`build` job, matrix of two native runners**: `amd64` on `ubuntu-latest`, `arm64` on `ubuntu-24.04-arm` (free for public repos). No emulation.
   Each leg: checkout, buildx, build with `load: true`, run `tests/test_image_smoke.py` against the loaded image
   (`SPM_BIDS_RUNNER_TEST_IMAGE`), and only then push `IMAGE:<version>-<arch>` (`provenance: false`, so each per-arch tag is a plain manifest).
2. **`merge` job, `needs: build`**: `docker buildx imagetools create -t IMAGE:<version> [-t IMAGE:latest] IMAGE:<version>-amd64 IMAGE:<version>-arm64`.
   `latest` moves only when the box is ticked and both builds passed. A failed arm64 build cannot publish a half-multi-arch `latest`.
3. **Runner and installer code does not change.** `docker pull ...:latest` resolves to the host architecture.

## Rollout (never push to GHCR unasked)

1. The user dispatches a trial version with `latest` unticked (e.g. `v2.2.0-rc1`).
2. On an Apple Silicon Mac: `docker pull ...:v2.2.0-rc1`, run the smoke test and one real analysis.
3. Then dispatch the real version with `latest` ticked. The existing `v2.1.1`/`latest` stay untouched until then.

## Tests (TDD)

Text tests on the workflow, next to `tests/test_publish_workflow.py`: still manual-only; the matrix contains `amd64` and `arm64` with the
`ubuntu-24.04-arm` runner; the smoke test runs before any push; `merge` `needs: build`; the tags are `<version>-<arch>`, `<version>`, `latest`
(only when ticked). `tests/test_default_image.py` (image name in sync) keeps passing.

## Out of scope / known limits

- Build caching (a cold build is ~5 min on 32 cores; add `cache-from/to: type=gha` if CI turns out slow).
- Emulated arm64 fallback.
- The arm64 build itself cannot be run on the lab server (no QEMU); the first proof is the CI run plus the Mac check.
- arm64 Octave/BLAS gives floating-point results that differ slightly (about 1e-8) from amd64; not bit-identical to the lab server.
