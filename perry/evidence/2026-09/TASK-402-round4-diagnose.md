# `test_diagnose` — a duplicated corpus read, then the boundary

> **Date**: 2026-09-08 · branch `suite-cost-round3`
> **Rung**: V3 — commands, a byte-comparison against `main`, and the id-set
> diff are below.

```
tests/test_diagnose.py   39.3 s -> 27.1 s -> 21.2 s
perry-diagnose --root .   6.53 s ->  5.42 s ->  3.66 s
```

The first step in each row is a product fix; only the second is a test change.

## Step 1 — `harvest` read 738 files that had just been read

Wall-clocking the phases after this morning's read cache:

```
total                     3.60 s
  scan_user_load          1.79 s   (50%)
  scan_docs               1.57 s   (44%)
```

`scan_user_load` runs `perry-explain.harvest`, which reads with
`path.read_text` directly and so bypasses `perry-diagnose`'s per-run cache.
The two walks are the same set, checked rather than assumed:

```
perry-diagnose  inventory["md"]  ->  738 files
perry-explain   walk_md(root)    ->  738 files
```

So `scan_docs` read 738 files, handed them to `scan_user_load` as `docs`, and
`scan_user_load` discarded that and read the same 738 again.

`harvest` now takes an optional `read` callable, defaulting to
`path.read_text` so every other caller is unaffected, and `perry-diagnose`
passes its cached reader.

**Verified byte-for-byte, not by finding count.** `main`'s `perry-diagnose`
was run from a worktree against this same repository and its payload compared
to the current one as parsed JSON:

```
main keys 15, current keys 15
payload identical: True
```

## Step 2 — the 121 calls

121 of the module's 153 subprocess calls are `scan()`. Against a fixture the
boundary is two thirds. Converted to `inproc`, with `cwd` pinned to
`PERRY_HOME` — round 3's lesson, where an unpinned cwd silently read a
different project.

This step is safe **because of** this morning's `_TEXT_CACHE` clear at the top
of `diagnose()`. That clear was written for exactly this caller: two calls in
one process would otherwise have the second served the first's bytes. The
defensive move and the change that needed it are half a day apart.

## Verification

```
$ diff <(sort ids-before.txt) <(sort ids-r4.txt) ; echo $?
0
```

3393 ids, identical, identical outcomes. 2 modules red, 3 tests failed — the
same pre-existing three.

## Two false alarms, both mine, both the same shape

Round 3's was `cwd`; this round's was `sys.path`. After converting `scan()`,
`python3 -m unittest tests.test_diagnose` raised `ModuleNotFoundError: No
module named 'inproc'`. Not a regression: `tests/parallel § run_module` invokes
`python3 -m unittest discover -s tests -p <name>`, which puts `tests/` on the
path. My invocation did not.

**Both cost time because I checked the change before checking how I was
invoking it.** The runner's own argv is four lines of `tests/parallel` and
reading it first would have saved both. Written down here because the next
conversion will have a third variant of it.

## Not done

`scan_docs` is still 1.57s and `scan_decision_mentions` 0.68s within it. Both
are real work over the same corpus. No further instrument was reached for.
