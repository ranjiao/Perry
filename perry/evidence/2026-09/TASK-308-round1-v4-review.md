# TASK-308 round 1 — V4 fresh-context review

- **Reviewer**: fresh-context V4 reviewer (did not write this code)
- **Branch**: `review/task-308-v4`, cut from `main`
- **Under review**: `perry/evidence/2026-09/TASK-308-result.md`, merged to `main` at `48015283`
- **Criteria**: `perry/evidence/2026-09/TASK-308-spec.md` § Verification

## Criterion 1 — the before-state, re-derived — **MET**

I re-derived the census from the filesystem with my own matcher, not the round's.

```
$ ls perry/evidence/*/*-spec.md | wc -l
     148
$ python3 -c "import glob,re; specs=sorted(glob.glob('perry/evidence/*/*-spec.md')); \
  rx=re.compile(r'^#{2,}\s*Bound\s*$',re.M); b=[p for p in specs if rx.search(open(p).read())]; \
  print('total',len(specs),'bound',len(b),'unbound',len(specs)-len(b))"
total 148 bound 25 unbound 123
```

`bin/perry-lint --root .` prints, today:

```
· bounds: 123 of 148 spec(s) carry no `## Bound` — a round against those has no
          finite set to check and no last element (`perry-lint --specs --json`
          names every one)
```

**123 of 148 — exactly what the PMO saw on 2026-09-03.** My independent regex
(`^#{2,}\s*Bound\s*$`) and the lint's own `_BOUND_RE` (`^#{2,}\s*Bound\b`,
`bin/perry-lint:2184`) agree on the count, so the census does not depend on the
matcher being lenient.

**Every historical figure in the spec and the result also re-derives.** I walked
each cited ref with `git ls-tree` + `git show`, reading nothing from either
document:

| ref | specs | bound | unbound | claimed by | matches |
|---|---|---|---|---|---|
| `47fa45a` | 144 | 17 | 127 | spec § Why this row exists | yes |
| `548f206` | 146 | 19 | 127 | result § Before-state | yes |
| `9c9670e` | 147 | 20 | 127 | result § Notes 4 | yes |

The result corrected the spec's stale 144/17 to 146/19 and said the *missing*
count was unchanged at 127. Both halves of that are true. This is the opposite
of the copy-forward failure the brief warned about: the round re-measured and
published the correction.

**`criteria-unbounded` reporting 0 also reproduces.** I extracted the pre-change
binary and ran it against today's tree:

```
$ git show 548f206:bin/perry-lint > /tmp/old-perry-lint.py   # copied to bin/ to resolve `lib`
$ python3 bin/old-perry-lint-tmp --root .        →  0 error(s), 26 warning(s)
    grep -c criteria-unbounded  → 0
    grep -c spec-unbounded      → 0
$ python3 bin/old-perry-lint-tmp --root . --reviews | grep -c criteria-unbounded → 0
$ ./bin/perry-lint --root .                      →  0 error(s), 37 warning(s)
```

26 → 37 is +11 = 10 named + 1 remainder, exactly the after-state the result
claims. The cause is structural and I read it myself: in the pre-change file the
`criteria-unbounded` finding at `:2466` sits inside
`for fields, line in parse_verdicts(text):` at `:2412` — it cannot execute for a
spec no verdict block cites. (Temp copy removed; tree clean.)

## Criterion 2 — the property: unbounded spec reported with no review document anywhere

NOT YET CHECKED

## Criterion 3 — the control: a bounded spec is silent

NOT YET CHECKED

## Criterion 4 — the verdict-side check at `:2458` still fires, both documented

NOT YET CHECKED

## Criterion 5 — severity chosen and justified

NOT YET CHECKED

## Criterion 6 — presence and shape only, no quality judgement

NOT YET CHECKED

## Criterion 7 — full suite; `perry-lint --root .` at 0 errors

NOT YET CHECKED

## Mutations re-run independently

NOT YET CHECKED

## The spec's false `## Bound` claim about TASK-067

NOT YET CHECKED

## Verdict

NOT YET CHECKED
