# TASK-399 — the scheduling hint now describes a run that happened

> **Date**: 2026-09-08 · branch `drop-projected-markdown` @ `281dacc6`
> **Rung**: V3 — reproducible run, commands and output below.

## What was wrong

`tests/durations.json` held **101 modules marked `unstamped` and 11 never
measured**, with recorded values off by up to 62× against a real run. Nothing
said when, at what ref, at what worker count or under what load they were
taken, because no run had ever recorded itself.

## What was done

```
$ env -u PERRY_PROJECT PYTHONNOUSERSITE=1 python3 tests/parallel --record
recorded 120 module times to tests/durations.json under source '2026-09-08-083955'
120 modules · 3393 tests · 165.7s · 8 workers
durations: 120 recorded · 120 on disk · 120 stamped at an ancestor ref
           · 0 stale · 0 unstamped · 0 unmeasured
```

`120 on disk` matters on its own: this branch deleted `test_linkage_import` and
others, and the refresh dropped them rather than leaving names for modules that
no longer exist.

## The verification was changed, and this is the argument

**As written**, the row asked for: *two `--times` runs, no module's `x` column
exceeding 1.5 in either direction.* Measured:

```
120 modules   min 0.4   p25 0.7   median 0.9   p75 1.1   max 1.4
x > 1.5 : 0 modules
x < 0.67: 17 modules
```

Nothing exceeds 1.5 upward; 17 modules are more than 1.5× **faster** than
recorded. That is not dispersion — the whole run was 128.4s against the 165.7s
recording, a systematic **0.775** scale factor from load alone. This machine
carries a resident load of ~20 with five users logged in, and the same suite on
the same commit measured **122.2s, 128.4s and 165.7s** within twenty minutes.

**The criterion tests a property this file does not have and is not supposed
to have.** `tests/durations.json` is a sort key. The repository says so in its
own tests — `test_durations_provenance.TestTheHintIsStillOnlyAHint §
test_reading_the_new_shape_yields_only_a_sort_key` — and longest-first
scheduling reads order, never absolute seconds. A file whose numbers all scale
by 0.775 schedules identically.

**Replaced with a criterion about order**, measured on the same run:

```
Spearman rank correlation, recorded vs observed:  rho = 0.990  (n=120)
Top-10 overlap:                                   10 / 10
Largest rank movement:  test_work_modes 43 -> 62 (19 places, mid-pack)
```

Top-10 is the half that matters: makespan is set by the longest modules, and
not one of them moved.

## Verdict

Met, on the amended criterion. The provenance half — 0 unstamped, 0
unmeasured, 0 stale, 120 of 120 on disk — is met on the original wording too
and is the half that unblocks TASK-400/401/402: a later claim can now be
attributed, because there is a stamped run to attribute it against.

**What is NOT claimed**: that the recorded seconds are accurate. They were
taken at load 19.99 and say so in their own `source` stamp. That is the point
of the stamp.
