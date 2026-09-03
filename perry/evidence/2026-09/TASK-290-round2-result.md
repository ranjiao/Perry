# TASK-290 — round 2

**Branch**: `coding/task-290-path-char-fix`
**Base commit**: `2f4c4355bdf18946495aecb13ed4fa891c33d66b` (`main`)

The worktree this round was cut in arrived at `d49964e`, 224 commits behind
`main`. The branch was created explicitly at `2f4c435` before any work started;
`git merge-base HEAD main` is `2f4c435` and `git rev-list --count HEAD..main`
is 0.

## Status

STUB — work in progress. Sections below are filled in as each step lands.

## Defect

`_PATH_CHAR` at `viewer/parsers.py:4344` admits characters that cannot appear
in a path component. `_discount_reason` measures rule 1's enclosing component
from that token, so an admitted non-filename character adjacent to the match
makes the component longer than the fragment and the occurrence is discounted
as `names-a-longer-file`.

## Reproduction

(pending)

## Fix

(pending)

## Controls

(pending)
