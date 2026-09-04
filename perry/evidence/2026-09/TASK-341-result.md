# TASK-341 — a probe written into the live tree that a sibling module asserts about

Branch cut from `main` at `dda8d5f`. `BASE=$(git merge-base HEAD main)`.

## 1. Reproduction (before any fix)

`tests/test_one_choke_point.py:532` (`test_the_guard_sees_a_file_in_a_subdirectory`)
creates a real `bin/lib/rowprobe.py` inside the repository.
`tests/test_one_primitive.py:150` (`test_bin_lib_is_the_only_exemption`) asserts
`bin/lib` holds exactly `["bin/lib/__init__.py"]`.

### Attempt 1 — both modules started simultaneously, 15 times: NO red

Measured alone: `test_one_choke_point.py` 19 tests / 4.9s; `test_one_primitive.py`
6 tests / 0.14s. Started at the same instant the fast module is finished long
before the slow module reaches its probe, so a naive two-process start never
collides. **This is why the pair reads as "flaky" rather than as a determinate
bug** — and why `tests/parallel -j 4`, which schedules ~100 modules over 4 slots
and starts `test_one_primitive` at an arbitrary point in the run, hits it.

### Attempt 2 — schedules aligned: red on the FIRST outer run

`test_one_choke_point` run once; `test_one_primitive` looped for its duration.

    === primitive RED on loop iteration 19 while choke_point ran ===
    FAIL: test_bin_lib_is_the_only_exemption (test_one_primitive.TestOneImplementationPerPrimitive)
      File ".../tests/test_one_primitive.py", line 150, in test_bin_lib_is_the_only_exemption
        self.assertEqual(
    AssertionError: Lists differ: ['bin/lib/__init__.py', 'bin/lib/rowprobe.py'] != ['bin/lib/__init__.py']
    First extra element 1:
    'bin/lib/rowprobe.py'
    : bin/lib gained or lost a file — that is fine, but it is the only place
      exempt from the rule above, so it is worth noticing

Both lines confirmed. The red is in `test_one_primitive`, which is not the module
with the defect.

(census, direction and verification to follow)
