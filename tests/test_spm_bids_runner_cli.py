import unittest
from unittest.mock import patch

import spm_bids_runner
from lib.core import PipelineResult


class TestBidspmCli(unittest.TestCase):
    def test_stats_workers_defaults_to_four(self):
        with patch("sys.argv", ["spm_bids_runner.py"]):
            args = spm_bids_runner.parse_arguments()
        self.assertEqual(args.stats_workers, 4)

    def test_stats_workers_accepts_override(self):
        with patch("sys.argv", ["spm_bids_runner.py", "--stats-workers", "1"]):
            args = spm_bids_runner.parse_arguments()
        self.assertEqual(args.stats_workers, 1)

    def test_main_threads_stats_workers_into_pipeline_options(self):
        captured_options = {}

        fake_result = PipelineResult(
            success=True,
            subjects_processed=["01"],
            subjects_failed=[],
            actions_completed=["stats"],
            log_file="log.txt",
            errors=[],
            warnings=[],
        )

        class _FakePipeline:
            def __init__(self, options):
                captured_options["options"] = options

            def run(self):
                return fake_result

        with patch("sys.argv", [
            "spm_bids_runner.py", "--action", "stats", "--stats-workers", "7", "--dry-run",
        ]), patch("spm_bids_runner.Pipeline", _FakePipeline):
            with self.assertRaises(SystemExit) as exit_ctx:
                spm_bids_runner.main()

        self.assertEqual(exit_ctx.exception.code, 0)
        self.assertEqual(captured_options["options"].stats_workers, 7)


    def test_models_flag_accepted_as_list(self):
        with patch("sys.argv", ["spm_bids_runner.py", "--action", "bms",
                                 "--models", "a.json", "b.json"]):
            args = spm_bids_runner.parse_arguments()
        self.assertEqual(args.models, ["a.json", "b.json"])

    def test_models_dir_still_accepted(self):
        with patch("sys.argv", ["spm_bids_runner.py", "--action", "bms",
                                 "--models-dir", "/some/dir"]):
            args = spm_bids_runner.parse_arguments()
        self.assertEqual(args.models_dir, "/some/dir")

    def test_name_by_confounds_flag_parsed(self):
        with patch('sys.argv', ['spm_bids_runner.py', '--action', 'stats', '--name-by-confounds']):
            args = spm_bids_runner.parse_arguments()
        self.assertTrue(args.name_by_confounds)

    def test_name_by_confounds_defaults_false(self):
        with patch('sys.argv', ['spm_bids_runner.py', '--action', 'stats']):
            args = spm_bids_runner.parse_arguments()
        self.assertFalse(args.name_by_confounds)


if __name__ == "__main__":
    unittest.main()


class TestCheckEnvironmentImage(unittest.TestCase):
    def _output(self, present):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("lib.preflight._image_present", lambda image: present), \
             patch("shutil.which", lambda name: "/usr/bin/" + name), \
             patch("subprocess.run", return_value=type("R", (), {"returncode": 0})()), \
             redirect_stdout(buf), self.assertRaises(SystemExit):
            spm_bids_runner.handle_check_environment()
        return buf.getvalue()

    def test_reports_a_missing_image(self):
        out = self._output(False)
        self.assertIn("not on this machine", out)

    def test_reports_a_present_image(self):
        out = self._output(True)
        self.assertIn("Image", out)
        self.assertNotIn("not on this machine", out)
