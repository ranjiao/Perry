#!/bin/bash
set -eu
export PERRY_HOME=/private/tmp/perry-scratch/Perry/okr-isolated-20260917/planning-acceptance
unset PERRY_PROJECT PYTHONPATH
export TMPDIR=/private/tmp/perry-scratch/planning-acceptance/20260917/final/tmp
out=/private/tmp/perry-scratch/planning-acceptance/20260917/final
python3 tests/tree_guard.py snapshot "$PERRY_HOME" "$out/affected-tree-before.json"
finish() {
  rc=$?
  trap - EXIT
  set +e
  python3 tests/tree_guard.py verify "$PERRY_HOME" "$out/affected-tree-before.json" > "$out/affected-tree-guard.log" 2>&1
  guard_rc=$?
  printf 'affected_exit=%s\nguard_exit=%s\n' "$rc" "$guard_rc" > "$out/affected-status.txt"
  cat "$out/affected-status.txt"
  if [ "$guard_rc" != 0 ]; then cat "$out/affected-tree-guard.log"; exit "$guard_rc"; fi
  exit "$rc"
}
trap finish EXIT
python3 tests/parallel --tier affected --base 9051a43f78bb4e2f892c678c9b4ab54df8bfa376 -j 4 > "$out/affected.log" 2>&1
