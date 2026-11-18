#!/usr/bin/env bash
# End-to-end test of SPM BIDS Runner on this one-subject slice of study 141 (task crom), without the GUI.
#
#   ./run_test.sh [--quick] [REPO_DIR]
#
#   --quick    check Docker, image and data, run the readiness check and SMOOTHING only (about 2 minutes);
#              without it the first-level stats run too (about 30 minutes)
#   REPO_DIR   the spm-bids-runner checkout (default: the folder above this one)
#   OUT=...    where results go (default ~/spm-bids-runner-output/141)
#
# Needs: ./scripts/setup.sh done in REPO_DIR (it creates .venv), Docker running, the image built or pulled.
# Exit code 0 = every step passed.

set -u
QUICK=0
if [ "${1:-}" = "--quick" ]; then QUICK=1; shift; fi
DATA="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "${1:-$DATA/..}" && pwd)"
OUT="${OUT:-$HOME/spm-bids-runner-output/141}"
PY="$REPO/.venv/bin/python"
SUB="141A332C"
FAILED=0
T0=$(date +%s)

say()  { printf '\n== %s\n' "$*"; }
ok()   { printf '  PASS  %s\n' "$*"; }
bad()  { printf '  FAIL  %s\n' "$*"; FAILED=1; }
stop() { bad "$*"; printf '\nStopped: fix the failure above and run again.\n'; exit 1; }

say "1. Environment"
[ -f "$REPO/spm_bids_runner.py" ] || stop "$REPO is not an spm-bids-runner checkout (pass its folder as the argument)"
[ -x "$PY" ] || stop "no Python environment at $PY: run ./scripts/setup.sh in $REPO first"
ok "checkout $REPO"
docker info >/dev/null 2>&1 || stop "Docker is not answering: start Docker Desktop and wait until it says it is running"
ok "Docker is running"
IMAGE="$(cd "$REPO" && "$PY" -c 'from lib.config import DEFAULT_DOCKER_IMAGE; print(DEFAULT_DOCKER_IMAGE)')"
ARCH_IMG="$(docker image inspect "$IMAGE" --format '{{.Architecture}}' 2>/dev/null)" || stop "image $IMAGE is not on this machine (build or pull it, see the README)"
ARCH_HOST="$(uname -m)"
printf '  host %s, image %s\n' "$ARCH_HOST" "$ARCH_IMG"
if [ "$ARCH_HOST" = "arm64" ] && [ "$ARCH_IMG" != "arm64" ]; then
  stop "this is an Apple Silicon Mac but the image is $ARCH_IMG (it would run emulated and slowly): build the arm64 image"
fi
ok "image $IMAGE ($ARCH_IMG)"
# integer arithmetic on purpose: awk prints "7,7" instead of "7.7" under a German (decimal comma) locale
MEM_MB="$(docker info --format '{{.MemTotal}}' 2>/dev/null | awk '{printf "%d", $1/1048576}')"
MEM_MB="${MEM_MB:-0}"
MEM_GB="$((MEM_MB / 1024)).$(( (MEM_MB % 1024) * 10 / 1024 ))"
# Docker Desktop shows 7.7 GB for its 8 GB setting, so the limit is 7.5
if [ "$MEM_MB" -ge 7680 ]; then ok "Docker memory ${MEM_GB} GB"; else bad "Docker memory is only ${MEM_GB} GB: set at least 8 GB in Docker Desktop (Settings, Resources), the stats step may be killed otherwise"; fi

say "2. Data (checksums)"
if (cd "$DATA" && { command -v shasum >/dev/null && shasum -a 256 -c SHA256SUMS || sha256sum -c SHA256SUMS; } >/tmp/sbr_sums.$$ 2>&1); then
  ok "$(grep -c ': OK' /tmp/sbr_sums.$$) files match SHA256SUMS"
else
  grep -v ': OK' /tmp/sbr_sums.$$ | head -5; rm -f /tmp/sbr_sums.$$; stop "the copied data differs from the original: copy it again"
fi
rm -f /tmp/sbr_sums.$$

say "3. Settings and model"
mkdir -p "$OUT/models"
cp "$DATA/model_crom.json" "$OUT/models/model_crom.json"
CFG="$OUT/settings.json"
"$PY" - "$CFG" "$OUT" "$DATA" "$SUB" <<'EOF'
import json, sys
cfg, out, data, sub = sys.argv[1:]
json.dump({"WD": out, "BIDS_DIR": data + "/rawdata", "DERIVATIVES_DIR": out,
           "FMRIPREP_DIR": data + "/derivatives/fmriprep", "SPACE": "MNI152NLin2009cAsym", "FWHM": 6,
           "MODELS_FILE": "model_crom.json", "TASKS": ["crom"], "SUBJECTS": [sub]}, open(cfg, "w"), indent=2)
EOF
ok "settings written to $CFG, output goes to $OUT"

say "4. Readiness check (same check as the GUI's 'Check readiness')"
cd "$REPO" || exit 1
"$PY" spm_bids_runner.py --preflight -s "$CFG" -c containers/container.json --validator bids >"$OUT/preflight.json" 2>"$OUT/preflight.err"
"$PY" - "$OUT/preflight.json" <<'EOF'
import json, sys
t = open(sys.argv[1]).read()
d = json.loads(t[t.index("{"):])
for c in d["checks"]:
    print(f"    {c['severity']:5} {c['id']}: {c['message'][:110]}")
print("  verdict:", d["verdict"])
sys.exit(1 if d["verdict"] == "blocked" else 0)
EOF
[ $? -eq 0 ] && ok "no blocking errors (warnings from the BIDS validator are expected)" || stop "readiness check is blocked, see above"

say "5. Run: $( [ $QUICK = 1 ] && echo smooth || echo 'smooth + stats' ) (the log follows)"
ACTIONS="smooth stats"; [ $QUICK = 1 ] && ACTIONS="smooth"
T1=$(date +%s)
# shellcheck disable=SC2086
"$PY" spm_bids_runner.py -s "$CFG" -c containers/container.json --action $ACTIONS --stats-workers 1 --skip-validator 2>&1 | tee "$OUT/run.log"
RC=${PIPESTATUS[0]}
printf '  run took %s s\n' "$(( $(date +%s) - T1 ))"
[ "$RC" -eq 0 ] && ok "pipeline exit code 0" || bad "pipeline exit code $RC"
LOG="$(grep -m1 'Log file:' "$OUT/run.log" | sed 's/.*Log file: *//')"
if [ -n "$LOG" ] && [ -f "$LOG" ]; then
  if "$PY" scripts/check_run_log.py "$LOG" >"$OUT/check_run_log.txt" 2>&1; then ok "run log has no unexpected errors or warnings"; else bad "run log has unexpected lines (see $OUT/check_run_log.txt)"; head -5 "$OUT/check_run_log.txt"; fi
else
  # a smoothing-only run prints a log name but writes no such file; the console output (saved as run.log) is all there is
  "$PY" scripts/check_run_log.py "$OUT/run.log" >"$OUT/check_run_log.txt" 2>&1 && ok "console output has no unexpected errors or warnings" || { bad "console output has unexpected lines (see $OUT/check_run_log.txt)"; head -5 "$OUT/check_run_log.txt"; }
fi

say "6. Outputs"
SMOOTH="$(find "$OUT/bidspm-preproc" -name '*desc-smth6_bold.nii' 2>/dev/null | head -1)"
[ -n "$SMOOTH" ] && ok "smoothed image: $(basename "$SMOOTH")" || bad "no smoothed image under $OUT/bidspm-preproc"
if [ $QUICK = 0 ]; then
  STATS="$(find "$OUT/bidspm-stats" -name SPM.mat -path "*sub-$SUB*" 2>/dev/null | head -1)"
  [ -n "$STATS" ] || stop "no SPM.mat under $OUT/bidspm-stats"
  SDIR="$(dirname "$STATS")"
  ok "SPM.mat: $SDIR"
  "$PY" - "$SDIR" <<'EOF' || FAILED=1
import glob, os, sys
import nibabel as nib, numpy as np
d = sys.argv[1]
cons, ts = sorted(glob.glob(d + "/con_*.nii")), sorted(glob.glob(d + "/spmT_*.nii"))
print(f"    {len(cons)} con images, {len(ts)} spmT images")
bad = 0
for f in ts:
    a = nib.load(f).get_fdata()
    n = int(np.count_nonzero(np.isfinite(a) & (a != 0)))
    print(f"    {os.path.basename(f)}: {n} non-zero voxels, max |t| = {np.nanmax(np.abs(a)):.2f}")
    bad += n < 1000 or not np.isfinite(a).any()
sys.exit(1 if bad or len(cons) < 4 or len(ts) < 4 else 0)
EOF
  [ $? -eq 0 ] && ok "first-level images look populated" || bad "first-level images are missing or empty"
  if [ -d "$DATA/reference" ]; then
    say "7. Compare with the lab server's result (x86 Octave) - arm64 should agree to rounding"
    "$PY" - "$SDIR" "$DATA/reference" <<'EOF' && ok "all compared images agree" || bad "images differ from the reference (see above)"
import glob, os, sys
import nibabel as nib, numpy as np
out, ref = sys.argv[1:]
bad = 0
for r in sorted(glob.glob(ref + "/*.nii")):
    name, o = os.path.basename(r), os.path.join(out, os.path.basename(r))
    if not os.path.exists(o):
        print("    MISSING", name); bad += 1; continue
    a, b = nib.load(o).get_fdata(), nib.load(r).get_fdata()
    if a.shape != b.shape or (np.isnan(a) != np.isnan(b)).any():
        print("    DIFF   ", name, "(shape or NaN pattern)"); bad += 1; continue
    m = np.isfinite(b)
    rel = float(np.abs(a[m] - b[m]).max() / (np.abs(b[m]).max() or 1))
    good = rel < 1e-4
    bad += not good
    print(f"    {'OK  ' if good else 'DIFF'}   {name}: max|diff| / max|ref| = {rel:.1e}")
sys.exit(1 if bad else 0)
EOF
  fi
fi

printf '\n== Done in %s s: ' "$(( $(date +%s) - T0 ))"
if [ $FAILED -eq 0 ]; then echo "ALL PASSED"; else echo "SOMETHING FAILED (scroll up for FAIL lines)"; fi
exit $FAILED
