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

---

## Appendix, 2026-09-08 evening — what the stamp was for

Four cuts at the suite's cost landed after this row closed. Measuring them
against whole-suite wall failed twice, and the stamped baseline this row
produced is what finally made them computable.

### The two figures that were reported and are wrong

**`-21%`, from `128.4s -> 101.0s`.** The 128.4s was itself load-inflated. The
same commit measured 106s, 117s, 122s, 128s and 166s across one afternoon on
this machine, which carries a resident load near 20 with five users logged in.
Retracted in the merge commit.

**`-2.7% per test`, from `main` at 107.4s/3508 against the branch at
101.0s/3393.** Arithmetically true and meaningless: the two are not the same
suite. ADR-019 deleted modules, so part of that gap is 115 fewer tests rather
than faster ones.

### The figure that holds

`tests/parallel --times` compares each module against its entry in this file.
On the run of 2026-09-08 evening the **median `x` was 1.00** — this run and the
`--record` run were under comparable load — so the column reads directly as
improvement with no global scaling to subtract:

```
CPU before, as recorded here : 1278 s
CPU after,  measured         :  936 s
                               -------
                                343 s   -26.8%

pool time at 8 workers       :  160 s -> 117 s
```

Per module, everything more than 2x below the median ratio:

| module | before | after | |
|---|---|---|---|
| `test_glossary.py` | 52.3 s | 3.09 s | 17x |
| `test_rung_vocabulary.py` | 41.7 s | 4.06 s | 10x |
| `test_goals_writer.py` | 55.0 s | 19.12 s | 2.9x |
| `test_task_store.py` | 21.7 s | 7.08 s | 3.0x |
| `test_register_minters.py` | 19.7 s | 8.81 s | 2.2x |

**Two of those five were never touched.** `test_task_store` and
`test_register_minters` were not targeted by any of the four cuts; they got
faster because `perry-explain` did. A product fix spreads to callers nobody
enumerated. A test conversion reaches exactly the module it edits.

### Why this belongs on THIS row

None of the above is computable without a `durations.json` that describes a run
that happened. Before this row it held 101 unstamped modules, 11 never
measured, and values off by 62x — comparing against it would have produced a
number with no meaning, which is the same failure as the two retracted figures
above, one layer down.

The amended acceptance was about order, and order is what scheduling needs. The
recorded *seconds* turned out to be worth something too, on a condition nobody
specified at the time: **they are comparable when the median ratio comes back
near 1**, and the ratio itself is what says whether that condition held. A
stamp that carries the load is what makes that checkable rather than assumed.

