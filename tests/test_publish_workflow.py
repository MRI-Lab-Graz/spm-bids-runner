"""Publishing an image is a decision, not a side effect of tagging: the workflow runs only when dispatched by hand."""
import re
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "docker-publish.yml").read_text()


class TestPublishWorkflow(unittest.TestCase):
    def test_only_manual_trigger(self):
        on_block = re.search(r"^on:\n(.*?)(?=^\S)", WORKFLOW, re.S | re.M).group(1)
        self.assertIn("workflow_dispatch", on_block)
        for trigger in ("push:", "pull_request:", "schedule:", "tags:"):
            self.assertNotIn(trigger, on_block)


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
