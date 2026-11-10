# Working agreements

- **TDD, always** (`superpowers:test-driven-development`): write a failing test first, then the code. Applies to every feature and bugfix. Throwaway spikes (e.g. probing whether a tool runs) are exempt, but anything kept gets a test.
- **Every session starts with `superpowers:using-superpowers`**: invoke it first, before any reply or tool use, and then use the matching superpowers skill (brainstorming, debugging, TDD, ...) for the task.
- **Before merging to main, all of these are required** (no merge until each is done and its findings are resolved or consciously deferred, with the reason written in the merge message):
  1. `python -m pytest -q tests` is green.
  2. **Ponytail assessment**: `/ponytail:ponytail-review` on the branch diff, plus `/ponytail:ponytail-audit` for larger changes.
  3. **Security check**: `/security-review` on the branch diff. The GUI runs commands and reads files on the user's machine, so look especially at path handling, subprocess/docker arguments and anything that exposes the port beyond `127.0.0.1`.
- The GUI only triggers `spm_bids_runner.py` CLI commands; pipeline logic belongs in the CLI/`lib/`, not in `webapp/`.
- Tests: `python -m pytest -q tests`.
