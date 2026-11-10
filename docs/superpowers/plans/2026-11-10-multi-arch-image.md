# Multi-arch image (amd64 + arm64) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docker pull ghcr.io/mri-lab-graz/spm-bids-runner:latest` works on Apple Silicon Macs, by publishing one multi-arch manifest built from two natively built, smoke-tested images.

**Architecture:** The manual-only publish workflow gets a `build` job in a two-leg matrix (amd64 on `ubuntu-latest`, arm64 on `ubuntu-24.04-arm`; each builds natively, loads the image locally, runs `tests/test_image_smoke.py` against it and only then pushes `<version>-<arch>`), and a `merge` job (`needs: build`) that creates `<version>` and, if ticked, `latest` with `docker buildx imagetools create`. No runner/installer code changes.

**Tech Stack:** GitHub Actions, docker buildx, Python `unittest`/pytest text tests on the workflow file.

Spec: `docs/superpowers/specs/2026-11-10-multi-arch-image-design.md`.

## Global Constraints

- The workflow stays **manual only** (`workflow_dispatch`, inputs `version` and `latest`); no `push:`, `pull_request:`, `schedule:`, `tags:` triggers (`tests/test_publish_workflow.py`).
- `IMAGE: ghcr.io/mri-lab-graz/spm-bids-runner` must equal `lib/config.py` `DEFAULT_DOCKER_IMAGE` without its tag; `permissions: contents: read` + `packages: write`; build args `IMAGE_VERSION=${{ inputs.version }}` and `GIT_REVISION=${{ github.sha }}` stay (`tests/test_default_image.py`).
- Tags: `<version>-amd64`, `<version>-arm64`, `<version>`, and `latest` only when the `latest` input is ticked.
- Nothing is pushed to GHCR before its smoke test passed; `latest` is never moved by a half-failed run.
- Never push to GHCR from this plan: the user dispatches the workflow.
- TDD: failing test first (CLAUDE.md). Gate before merging to main: `python -m pytest -q tests`, `/ponytail:ponytail-review`, `/security-review`, reasons in the merge message.
- Run tests with `.venv/bin/python -m pytest -q -p no:cacheprovider <path>` from the repo root (`/data/local/software/spm-bids-runner`).

## File Structure

- Modify `.github/workflows/docker-publish.yml`: the whole pipeline (build matrix + merge).
- Modify `tests/test_publish_workflow.py`: text tests of the workflow's shape (one new class).
- Modify `README.md`: a short "Publishing the image (maintainers)" section and the pull-or-build wording.

---

### Task 1: Multi-arch publish workflow

**Files:**
- Modify: `tests/test_publish_workflow.py` (append a class)
- Modify: `.github/workflows/docker-publish.yml` (rewrite `jobs:`)

**Interfaces:**
- Consumes: workflow inputs `version`, `latest`; `tests/test_image_smoke.py` (reads env `SPM_BIDS_RUNNER_TEST_IMAGE`, skips itself when it is unset or docker is missing).
- Produces: GHCR tags `IMAGE:<version>-amd64`, `IMAGE:<version>-arm64`, `IMAGE:<version>`, optional `IMAGE:latest`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_publish_workflow.py` (the file already defines `re`, `unittest`, `Path`, `WORKFLOW`; keep `if __name__` block, if any, last):

```python
def _step(name):
    """The text of the workflow step whose name starts with `name` (up to the next step)."""
    return next(c for c in re.split(r"\n      - name: ", WORKFLOW) if c.startswith(name))


def _script(name):
    return _step(name).split("run:", 1)[1]


class TestMultiArchPublish(unittest.TestCase):
    def test_one_native_runner_per_architecture(self):
        self.assertRegex(WORKFLOW, r"arch: amd64\n\s+runner: ubuntu-latest")
        self.assertRegex(WORKFLOW, r"arch: arm64\n\s+runner: ubuntu-24\.04-arm")
        self.assertIn("runs-on: ${{ matrix.runner }}", WORKFLOW)

    def test_nothing_is_pushed_before_the_smoke_test_passed(self):
        self.assertNotIn("push: true", WORKFLOW)          # the build step only loads into the local store
        self.assertIn("load: true", WORKFLOW)
        self.assertLess(WORKFLOW.index("tests.test_image_smoke"), WORKFLOW.index("docker push"))
        self.assertIn("SPM_BIDS_RUNNER_TEST_IMAGE: ${{ env.IMAGE }}:${{ env.ARCH_TAG }}", WORKFLOW)

    def test_a_skipped_smoke_test_fails_the_step(self):
        script = _script("Smoke test the built image")
        self.assertIn("grep -q skipped smoke.log", script)
        self.assertIn("exit 1", script)
        self.assertNotIn("! grep", script)                # `!` is exempt from `set -e`, the step would still pass

    def test_per_arch_tags_are_plain_manifests(self):
        self.assertIn("provenance: false", WORKFLOW)      # no attestation entries to confuse imagetools create
        self.assertIn("ARCH_TAG: ${{ inputs.version }}-${{ matrix.arch }}", WORKFLOW)

    def test_merge_needs_both_builds_and_moves_latest_only_when_ticked(self):
        merge = WORKFLOW.split("\n  merge:\n", 1)[1]
        self.assertIn("needs: build", merge)
        script = _script("Create the multi-arch tags")
        self.assertIn('docker buildx imagetools create', script)
        self.assertIn('"${IMAGE}:${VERSION}-amd64"', script)
        self.assertIn('"${IMAGE}:${VERSION}-arm64"', script)
        self.assertIn('if [ "${LATEST}" = "true" ]', script)

    def test_inputs_reach_scripts_through_env_not_by_interpolation(self):
        for name in ("Smoke test the built image", "Push", "Create the multi-arch tags"):
            self.assertNotIn("${{", _script(name), name)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_publish_workflow.py`
Expected: the six new tests FAIL (e.g. `AssertionError` on `arch: amd64`, `StopIteration` from `_step`); the existing `test_only_manual_trigger` still passes.

- [ ] **Step 3: Rewrite the workflow's jobs**

In `.github/workflows/docker-publish.yml` keep the header (`name:`, the comment, the whole `on:` block, `env:`) exactly as it is and replace everything from `jobs:` to the end of the file with:

```yaml
jobs:
  build:
    name: build ${{ matrix.arch }}
    # One native runner per architecture, no emulation (the arm64 runner is free for public repos).
    strategy:
      matrix:
        include:
          - arch: amd64
            runner: ubuntu-latest
          - arch: arm64
            runner: ubuntu-24.04-arm
    runs-on: ${{ matrix.runner }}
    permissions:
      contents: read
      packages: write
    env:
      ARCH_TAG: ${{ inputs.version }}-${{ matrix.arch }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Built into the local image store only: nothing reaches GHCR until the smoke test passed.
      # OCI labels (title, licences, source, upstream versions) come from the Dockerfile itself.
      - name: Build
        uses: docker/build-push-action@v6
        with:
          context: .
          file: containers/dockerfile/dockerfile
          load: true
          provenance: false
          tags: ${{ env.IMAGE }}:${{ env.ARCH_TAG }}
          build-args: |
            IMAGE_VERSION=${{ inputs.version }}
            GIT_REVISION=${{ github.sha }}

      - name: Smoke test the built image
        shell: bash
        env:
          SPM_BIDS_RUNNER_TEST_IMAGE: ${{ env.IMAGE }}:${{ env.ARCH_TAG }}
        run: |
          python3 -m unittest -v tests.test_image_smoke 2>&1 | tee smoke.log
          if grep -q skipped smoke.log; then echo "the smoke test was skipped, so it proved nothing"; exit 1; fi

      - name: Push ${{ matrix.arch }}
        run: docker push "${IMAGE}:${ARCH_TAG}"

  merge:
    name: publish the multi-arch tags
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Create the multi-arch tags
        shell: bash
        env:
          VERSION: ${{ inputs.version }}
          LATEST: ${{ inputs.latest }}
        run: |
          TAGS=(-t "${IMAGE}:${VERSION}")
          if [ "${LATEST}" = "true" ]; then TAGS+=(-t "${IMAGE}:latest"); fi
          docker buildx imagetools create "${TAGS[@]}" "${IMAGE}:${VERSION}-amd64" "${IMAGE}:${VERSION}-arm64"
          docker buildx imagetools inspect "${IMAGE}:${VERSION}"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_publish_workflow.py tests/test_default_image.py`
Expected: all PASS (the old `test_publish_workflow_uses_the_setting` still finds `IMAGE:`, the permissions regex, the inputs regexes and both build args).

- [ ] **Step 5: Lint the workflow with actionlint (it cannot be run locally)**

Run: `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:latest -color .github/workflows/docker-publish.yml`
Expected: no output, exit 0. If it reports a real problem (for example the `ubuntu-24.04-arm` label unknown to an old actionlint), fix the workflow; an "unknown runner label" for `ubuntu-24.04-arm` from an outdated actionlint is the only finding that may be ignored, and the reason must go in the commit message.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/docker-publish.yml tests/test_publish_workflow.py
git commit -m "feat: publish a multi-arch (amd64 + arm64) image from native runners

Each architecture is built natively, smoke-tested before anything is pushed, then a merge
job creates <version> (and latest when ticked) from the two per-arch tags.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: README: how maintainers publish, and what students pull

**Files:**
- Modify: `README.md` (the Installation image step around line 128-148, and a new section before `## Contributing`)
- Test: `tests/test_readme_paths.py` (existing; must still pass)

**Interfaces:**
- Consumes: the tag scheme from Task 1.
- Produces: documentation only.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_publish_workflow.py`:

```python
README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


class TestPublishingIsDocumented(unittest.TestCase):
    def test_readme_explains_the_trial_then_real_rollout(self):
        section = README.split("## Publishing the image (maintainers)", 1)[1].split("\n## ", 1)[0]
        self.assertIn("latest", section)
        self.assertIn("-rc1", section)                     # a trial version with `latest` unticked first
        self.assertIn("smoke", section.lower())
        self.assertIn("arm64", section)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_publish_workflow.py::TestPublishingIsDocumented`
Expected: FAIL with `IndexError` (the section does not exist yet).

- [ ] **Step 3: Add the README section and fix the install wording**

Insert before `## Contributing` in `README.md`:

```markdown
## Publishing the image (maintainers)

The image on GHCR is multi-arch (amd64 for the lab server, arm64 for Apple Silicon Macs). It is published by hand:
GitHub, Actions, "Publish Docker image", Run workflow.

1. **Trial first.** Run it with `version` = `v2.2.0-rc1` (any new version) and `latest` **unticked**. Each architecture is built
   on its own native runner and smoke-tested (`tests/test_image_smoke.py`) before it is pushed; the multi-arch tag
   `v2.2.0-rc1` is created only if both pass.
2. **Check it on an Apple Silicon Mac:** `docker pull ghcr.io/mri-lab-graz/spm-bids-runner:v2.2.0-rc1`, run the smoke test
   (`SPM_BIDS_RUNNER_TEST_IMAGE=<that tag> python -m pytest -q tests/test_image_smoke.py`) and one real analysis.
3. **Then publish for real:** run the workflow again with the final version and `latest` **ticked**. `latest` is moved only
   by a run where both architectures passed.

Old tags (`v2.1.1`, and `latest` until step 3) are amd64 only and stay untouched. arm64 Octave/BLAS results differ from
amd64 at the floating-point level (about 1e-8), so they are not bit-identical to the lab server.
```

In the Installation block, change the comment line `# get the image, EITHER pull it from GHCR (once it is published there):` to `# get the image, EITHER pull it from GHCR (amd64 and arm64):`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_publish_workflow.py tests/test_readme_paths.py tests/test_default_image.py`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_publish_workflow.py
git commit -m "docs: how maintainers publish the multi-arch image (trial, Mac check, then latest)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Gate and merge (no publishing)

**Files:**
- None created. Read the branch diff.

**Interfaces:**
- Consumes: Tasks 1-2.
- Produces: the branch merged into local `main`.

- [ ] **Step 1: Full test suite**

Run: `.venv/bin/python -m pytest -q -p no:cacheprovider tests`
Expected: all pass (about 5 minutes; 16 skipped is normal). If `tests/test_xss_browser.py` or another browser test fails, run it on its own first and read the error; do not call it a flake without evidence.

- [ ] **Step 2: Ponytail review**

Invoke `/ponytail:ponytail-review` on `git diff main...HEAD`. Resolve or defer every finding, with the reason.

- [ ] **Step 3: Security review**

Invoke `/security-review` on the same diff. Points to check: `GITHUB_TOKEN` scope is `packages: write` only where needed, no `${{ inputs.* }}` inside `run:` scripts, actions pinned to major versions already used in the repo.

- [ ] **Step 4: Merge with the gate results in the message**

```bash
git checkout main
git merge --no-ff feat/multi-arch-image -m "Merge feat/multi-arch-image: amd64 + arm64 publish workflow

Gate: pytest <N passed, M skipped>. Ponytail: <result>. Security: <result>.
Not yet published: the user dispatches the trial run (README, Publishing the image).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

Do not push unless the user asks. Do not dispatch the workflow: publishing to GHCR is the user's decision.

- [ ] **Step 5: Hand over the rollout**

Tell the user the three steps from the README section (trial `v2.2.0-rc1` with `latest` unticked, check on the Mac, then the real version with `latest` ticked), and that the workflow only exists on GitHub once `main` is pushed.

---

## Self-review (against the spec)

- Manual-only workflow, same inputs: kept (header untouched; existing test).
- Matrix of native amd64 + arm64 runners, no emulation: Task 1 (`test_one_native_runner_per_architecture`).
- Smoke test before push, load-only build: Task 1 (`test_nothing_is_pushed_before_the_smoke_test_passed`); skipped-test guard added because `test_image_smoke.py` skips silently when its env is missing.
- `provenance: false` and `<version>-<arch>` tags: Task 1.
- `merge` job `needs: build`, `imagetools create`, `latest` only when ticked: Task 1.
- No runner/installer code change: none planned.
- Rollout and `latest` untouched until proven; arm64 float caveat documented: Task 2.
- Tests listed in the spec: all in Tasks 1-2; `tests/test_default_image.py` kept green in both.
- Out of scope respected: no cache, no emulation fallback.
- Names are consistent: `ARCH_TAG`, `VERSION`, `LATEST`, step names used by `_step`/`_script` match the YAML above ("Smoke test the built image", "Push ${{ matrix.arch }}" matched by prefix "Push", "Create the multi-arch tags").
