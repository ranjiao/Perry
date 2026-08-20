# TASK-028 implementation round 2

Date: 2026-08-19

Mode detection now enumerates implicit `main` when either a board row or a
commitment has a blank `Track`. Blank-track records are attributed to `main`,
and repository-wide evidence reaches only an actual project-mode track rather
than a sole declared pipeline, queue, or inquiry track.

`tests/test_track_attribution.py` covers untracked commitments, false project
scoring, and a sole non-project track.

Verification:

- `python3 -m unittest tests.test_track_attribution tests.test_diagnose` —
  107 passed.
- `git diff --check` — clean.

Fresh V4 review remains required.
