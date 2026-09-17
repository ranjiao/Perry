#!/bin/bash
set -u
export PERRY_HOME=/private/tmp/perry-scratch/Perry/okr-isolated-20260917/planning-discussion
export TMPDIR=/private/tmp/perry-scratch/planning-discussion/20260917/tmp
unset PERRY_PROJECT PYTHONPATH
out=/private/tmp/perry-scratch/planning-discussion/20260917
label=$1
shift
manifest="$out/tmp/$label-tree.json"
log="$out/logs/$label.log"
{
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  git rev-parse HEAD
  printf 'Command:'
  printf ' %q' "$@"
  printf '\n'
  python3 tests/tree_guard.py snapshot "$PERRY_HOME" "$manifest" || exit 1
  "$@"
  test_rc=$?
  python3 tests/tree_guard.py verify "$PERRY_HOME" "$manifest"
  guard_rc=$?
  printf 'test_exit=%s guard_exit=%s\n' "$test_rc" "$guard_rc"
  [ "$test_rc" = 0 ] && [ "$guard_rc" = 0 ]
} > "$log" 2>&1
rc=$?
tail -18 "$log"
exit "$rc"
