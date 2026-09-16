# Read-only slow-suite diagnostic — 2026-09-16

No project code or shared fixture edits. No parent processes signaled. Own
standalone import probe completed normally; no leftover process to stop.

- Parent full264 finished normally and proceeded to slow before inspection.
- Environment inherited PYTHONPATH='.:'. PERRY_HOME was unset by the tests,
  as was PERRY_PROJECT; they did not unset PYTHONPATH.
- tests/test_empty_config_store.py:89-99 deliberately launches children with
  cwd=tempfile.gettempdir(); related configuration tests do likewise.
- Live child88730, perry-goals commit with explicit --root to its own fixture:
  27s wall,21.25s CPU,69.6%CPU. One-second /usr/bin/sample captured594/785
  samples in __getdirentries64 underneath os_listdir under Python import
  machinery. Sample saved in slow-child.sample.
- Global TMPDIR had560126 entries during one read-only enumeration:
  460636 perry-task-*.lock files,99490 other entries; scan0.768s.
- bin/lib/__init__.py:176-177 creates a temp-root perry-task-<hash>.lock for
  every distinct state root. Its finally block closes/unlocks but keeps the
  path. No cleanup was attempted.
- Same global-temp cwd, perry-config --help, PERRY_HOME/PERRY_PROJECT/PYTHONPATH
  unset:0.079s then0.059s,exit0.
- Standalone python3 -c 'import json, pathlib' from the same cwd:
  inherited PYTHONPATH69.741s;unset PYTHONPATH2.828s;both exit0. The -c probe
  still has its intrinsic empty sys.path entry, unlike the script-form tools.
- Inference: inherited cwd import path repeatedly enumerates the huge temp
  directory, which concurrent fixture creation keeps changing. This is not
  simply Perry lock contention or state-root traversal. A fully idle-host
  benchmark was not performed; concurrent load can amplify the effect.

Action: clear PYTHONPATH as well as the two Perry variables for the final
suite invocation. Parent independently confirmed0.051s for a clean-env
command and restarted its own slow gate accordingly. The lock-file lifecycle
and any safe cleanup are separate work, not changes made by this diagnostic.
