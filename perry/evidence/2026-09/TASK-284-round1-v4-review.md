# TASK-284 — round 1, V4 review

- **Criteria**: `perry/evidence/2026-09/TASK-284-spec.md` (read from
  `coding/task-247-config-predicate`)
- **Under review**: `cbc2d8f`, `f4ae08f` on `coding/task-284-spec-scannability`,
  base `d49964e`
- **Reviewer**: fresh context, isolated worktree, did not write this code
- **Method**: every tree extracted with `git archive` into a private scratch
  directory and worked on there. The repository under review was not modified,
  and no fixture was planted into it.
- **Result**: **FAIL**, on the criteria's own binding sentence. The
  measurement work in this change is correct and I re-derived all of it
  independently — the FAIL is about what the round delivers, not about what it
  reports.

---

## What I verified independently, and it holds

I re-derived each of these from the trees rather than reading the author's
account of them. All four came back exactly as claimed.

### 1 · The census, on three trees

I ran `_section` / `alias("headings", …)` / `ESCALATION_TOUCHES` myself over
every `*-spec.md` under `perry/evidence/`, with each tree's own
`viewer/parsers.py`, and classified the unscannable ones by shape:

| tree measured | specs | scannable | **unscannable** | bullet | `###` | no section |
|---|---|---|---|---|---|---|
| `d49964e` (base) | 119 | 74 | **45** | **0** | 19 | 26 |
| `coding/task-284-spec-scannability` | 119 | 74 | **45** | **0** | 19 | 26 |
| `coding/task-247-config-predicate` (live, today) | 134 | 89 | **45** | **0** | 19 | 26 |

**45 is confirmed on all three trees, and the 19 / 26 split is confirmed.**

**The author's refutation of the spec's premise is correct.** The spec asserted
the 45 use the bullet shape `perry-task add` renders. **Zero of the 45 do.**
Nineteen use `### Deliverable`, twenty-six carry no such section in any shape.
Fix 2 (widen `_section` to read bullets) would therefore have closed **none of
the 45** — the spec's own description of fix 2 as "Fixes the 45 at once" is
wrong, and the author was right to say so rather than implement it. That is
the strongest single piece of work in this round.

Which tree, and a caveat on the totals: I measure the live branch at
**134 / 89 / 45** today, where the author reported 132 / 87 / 45. Two specs
have been added to `coding/task-247-config-predicate` since the author
measured; both are sectioned. The number the criteria bind — 45 — is
unaffected, and moves on none of the three trees.

### 2 · `verdict` really is unchanged — proven by differential and mutation, not by reading

I loaded `d49964e`'s `scan_spec_escalations` and the branch's side by side in
one process and compared **only** the keys the author claims are unchanged
(`verdict`, `touches`, `disclaims`, `green_lit`, `refuse`, `armed`) across:

- 416 markdown files from the live tree (every `*-spec.md` plus 400 more
  `perry/**/*.md`), × 4 fragment sets — the live 35-fragment union, the empty
  list, a single non-matching fragment, and an over-broad set including
  `the` / `a` / `perry` / `md`;
- 12 hand-built edge inputs — empty string, bare heading, heading with only
  whitespace, `Out of scope` alone, `### Deliverable`, the bullet shape,
  scope inside an HTML comment, a heading-with-suffix, and the localized
  `## 交付物`.

**1712 comparisons, 0 mismatches.** The base result additionally never carries
`scanned` / `scope_scanned` and the branch result always does, asserted on
every comparison.

**The mutation that proves the harness is a check.** I inserted, line-anchored
at `viewer/parsers.py:4403` in the scratch copy, a line making `refuse` depend
on `scope_scanned`. The same harness went to **999 mismatches** — `verdict`
flipping `pass` → `refuse` on exactly the inputs the change is about. Reverted
by byte-comparison against a backup, `__pycache__` cleared, past the second
boundary; the re-run returned to **0 mismatches**. The parity is real and the
harness can see a moved gate.

End-to-end, on the same spec through the real binary:
`bin/perry-state --escalation-scan perry/evidence/2026-08/TASK-015-spec.md`
returns `verdict: pass`, exit **0** on base and exit **0** on the branch. The
JSON gains two keys and loses none.

### 3 · The gate is armed and the fixtures are real

The live union is **35** fragments, as claimed. Control pair, same scope text,
same tree, branch code:

| spec shape | `scope_scanned` | `verdict` | exit |
|---|---|---|---|
| `## Deliverable` + "`git push origin main`, `rm -rf`, `gh release`" | `["Deliverable"]` | `refuse` | **3** |
| the same words under the bullet schema `add-task` step 3 prescribes | `[]` | `pass` | **0** |

### 4 · The suite

Run in the scratch copies, machine load average 9.38 at start, 8 workers:

- `d49964e`: **108 modules · 3003 tests · 332.6s · all green**
- branch: **109 modules · 3016 tests · 365.3s · all green**

`+1 module, +13 tests, 0 failures either side` — confirmed, and the 13 is the
count of test methods in `tests/test_spec_scannability.py`. `test_parsers` is
**green** on both of these trees; the TASK-292 redness noted in the criteria
is not present at this base.

`perry-lint --specs` on the branch reports **45 of 119**, matching my
independent census file-for-file; `--strict` exits 1; `--json` carries every
one of the 45.

---

## Finding — the report is not reachable by any reader, so the binding sentence is not met

The criteria's Deliverable section ends with the sentence that binds whichever
fix is taken:

> Whichever is chosen, **a spec must not be able to present zero scope to the
> gate without something saying so.**

and describes fix 3, the one taken, as:

> **Report-side** — `perry-lint` reports a spec whose scanned sections are
> absent, so a silent empty scan becomes a visible finding. Does not prevent
> it; **makes it impossible to miss.**

After this change, an empty scan is still entirely missable. Enumerated, not
sampled:

**a. Nothing in the repository invokes `--specs`.** I grepped every directory
that carries procedure or execution — `work/`, `modes/`, `decide/`, `goals/`,
`reference/`, `packs/`, `SKILL.md`, `AGENTS.md`, and `tests/run`. Every other
lint mode is invoked from at least one of them (`--reviews` 7 times,
`--verification` 4, `--provenance` 4, `--knowledge` 3, `--glossary` 2,
`--claims` 2, `--templates` from `tests/run` itself). `--specs` appears **zero
times** outside `bin/perry-lint`'s own source and its own test file.

**b. The default lint run does not report it.** `perry-lint --root .` on the
branch, against a tree holding 45 unscannable specs, prints
`0 error(s), 5 warning(s)` and **zero** `spec-scope-unscannable` lines. The
mode returns early from `main()` and is reachable only by typing the flag.

This is a sharper version of the failure the criteria's own P0 argument is
about. The five warnings that *do* print are the NS-01 lines this board has
trained itself to scroll past — and those at least print. The new finding
prints on no run anyone makes.

**c. `dispatch.md` was not amended, and it tells the dispatcher not to look.**
`work/reference/dispatch.md:12` — the pre-flight step that runs this gate —
says:

> **Exit code is the verdict — 0 proceed, 3 refuse, 4 unarmed** … The JSON
> names `refuse`, `green_lit` and `origins` so a refusal can be quoted back to
> the user.

The exit code is unchanged at 0. The three JSON keys the dispatcher is told to
read are unchanged. `scanned` / `scope_scanned` are neither named there nor
anywhere else in `work/`. A dispatcher following the documented procedure
verbatim is routed past the new information.

**d. The asymmetry the change itself names is the asymmetry it leaves in
place.** `viewer/parsers.py:4419-4420`:

```python
"verdict": ("unarmed" if not fragments
            else "refuse" if refuse else "pass"),
```

`verdict` branches on the **hook** side being empty and not on the **spec**
side being empty. The docstring three lines above says so in the author's own
words — "The two halves are the same rule and only one of them was
implemented" — and the empty-hook half was given a distinct exit code (4), a
dedicated `dispatch.md` paragraph, and a mandatory explicit go-ahead in chat.
The empty-spec half was given two JSON keys no procedure reads and a flag
nothing runs.

### The behaviour, on an input a user can produce

I wrote the spec the criteria's Verification item 2 asks for — following
`work/reference/subcommands.md § add-task` step 3 verbatim, whose text is
unchanged on this branch, and reproducing the schema block `bin/perry-task`
renders at `cmd_add`'s `definition` (`- **Deliverable**: …`). Its Deliverable
names three fragments of the armed 35:

```
- **Deliverable**: run `git push origin main` and `rm -rf state/cache`,
  then `gh release` the bundle
```

Branch code, real binary, in a scratch copy:

```
$ bin/perry-state --root . --escalation-scan <that spec>
{ "armed": true, "scanned": [], "scope_scanned": [], "touches": {},
  "refuse": [], "verdict": "pass", "fragments_scanned": 35 }
EXIT=0
```

Exit 0. `dispatch.md` step 4: proceed. The same words under `## Deliverable`
exit 3 and refuse on five fragments. **A P0 auto-dispatch that force-pushes and
`rm -rf`s runs unsupervised, and the only thing in the tree that would say
otherwise is a command no procedure calls.** That is the defect TASK-284 was
filed for, reachable today, by the same documented procedure, on the branch
under review.

### Why this is a FAIL and not the round's authorised remainder

The strongest case against this FAIL, stated so round 2 does not re-derive it:
the criteria offer three fixes and say *take one*; they describe fix 3 as one
that "does not prevent it"; and the `## Bound` ends the round when the census
"is driven to 0 **or made visible**", which `perry-lint --specs` does. Under
that reading the author scoped honestly and this is a PASS.

I do not think it survives, for two reasons drawn from the criteria and not
from my own bar:

1. **Verification item 2 is a written acceptance check and it is unmet.** "A
   spec written by following `add-task` verbatim, from scratch, scans with a
   non-empty `touches` when its scope names a high-stakes fragment. Write one
   and show it." I wrote one. It scans `touches: {}`. The author states
   plainly that fix 3 does not satisfy this, which is honest, but honesty
   about an unmet criterion does not meet it.

2. **"Made visible" and "something saying so" require a reader, and there is
   none.** A report that no procedure invokes, that the default run of its own
   tool suppresses, and whose two new JSON keys the consuming procedure is
   told not to read, is visible only to somebody who already knows to look —
   which is the population that did not need the check. This is the same class
   of defect as the drift census two ADRs condemned, and the criteria's own
   framing of fix 3 is "makes it impossible to miss", not "makes it possible
   to find".

**Crucially, this FAIL is finishable inside the existing bound.** It does not
ask for a fourth fix, and it does not ask the author to also take fix 1 or
fix 2. Any one of these completes fix 3 as the criteria describe it:

- give the empty-spec case its own exit code from
  `bin/perry-state:2657 SCAN_EXIT`, the way the empty-hook case has 4, and add
  the matching `dispatch.md` step 4 clause; or
- leave the exit code alone and amend `dispatch.md` step 4 to name
  `scope_scanned` alongside `refuse` / `green_lit` / `origins`, with the
  one-line instruction for what a `[]` means; or
- wire `--specs` into something that runs — the default `perry-lint` pass, or
  `tests/run`, or a named step in a `work/reference/` procedure.

---

## Observations — not the FAIL, and not to be folded into round 2's verdict

Recorded because `review.md` routes each of these to a filing rather than to a
FAIL, and because round 2 should not spend context re-finding them.

1. **`bin/perry-lint:4303` states a false causal claim.** The comment says
   `load_glossary(schema)` "Arms `alias("headings", …)`". It does not.
   `load_glossary` populates `perry-lint`'s own `HEADING_ALIASES` table;
   `P.alias` reads `parsers._i18n()`, which self-loads from `_SCHEMA_PATH`
   independently. I confirmed the localized path works — `## 交付物` scans and
   refuses — and that my own census, which never called `load_glossary`,
   returned the identical 45. **The behaviour is correct; the comment's
   explanation of why is wrong.** A documentation defect with its own ID.

2. **The advisory has no recorded promotion trigger.** The change cites
   DESIGN-003 decision 4 as its precedent, and that citation is accurate — but
   decision 4 reads "**Advisory first release, hard gate next**" with a stated
   plan. `spec-scope-unscannable` is advisory with no condition recorded
   anywhere for when it stops being advisory.

3. **The census is tree- and time-dependent in its totals.** 119 / 74 / 45 at
   the base, 134 / 89 / 45 live today, 132 / 87 / 45 when the author measured.
   Any future statement of this census should carry the ref it was taken at.

4. **`green_lit` still does not de-duplicate across `touches` sections** while
   `refuse` does. `.perry/events.jsonl` carries a deferred intake row whose
   stated condition is "the next change to `scan_spec_escalations`" — which
   this is. Cosmetic today; the condition has now fired.

---

## What I did not check

Stated so round 2 does not re-cover this ground and does not skip what I
skipped.

- **The 45 specs' contents.** I classified them by heading shape only. I did
  not read them to see how many would actually have refused had they been
  scannable — i.e. the real blast radius of the 45 is unmeasured, and it is
  the number that would tell you whether the advisory default is right.
- **The other 15 `_section` call sites.** The author reports 16 across 5
  consumers and reports `hook_escalation_lines` among them. I confirmed only
  that `scan_spec_escalations` is `_section`'s caller in the path under
  review, and that fix 2 was not taken — so no `_section` caller could have
  changed answer. I did not enumerate the 16 myself. This mattered only to
  fix 2, which was rejected.
- **`bin/perry-lint --specs` on a project whose state root is not the project
  root**, and on a project with a non-English document language end to end. I
  tested localized heading matching at the parser only.
- **`--specs` under `--quiet`**, and its interaction with `--state-root`.
- **Concurrency / dispatch-limit behaviour** and every other `dispatch.md`
  pre-flight step besides step 4.
- **Windows or any non-macOS path handling.**
- **Whether the author's claimed mutation on the real TASK-233 spec was
  performed.** It is not in `tests/test_spec_scannability.py` — that file's
  mutation uses the `SECTION_SPEC` fixture — and no result document for
  TASK-284 exists on either branch. I performed my own real-spec equivalent
  instead (the control pair in § 3 above), so the property is verified even
  though the author's specific exhibit is not.
- **Any suite run on `coding/task-247-config-predicate`.** Both baselines
  above are the branch under review and its own base.

=== VERDICT ===
task: TASK-284
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-284-spec.md
checked: census re-derived independently on three trees — 45 unscannable on all of them, 19 `###` / 26 no-section / 0 bullet, so fix 2 would have closed none and the spec's premise is correctly refuted; verdict/touches/disclaims/green_lit/refuse parity base-vs-branch over 1712 comparisons (416 files x 4 fragment sets + 12 edge inputs), 0 mismatches, and the same harness returns 999 mismatches under a line-anchored mutation at viewer/parsers.py:4403 that makes refuse depend on scope_scanned, reverted by byte-comparison with __pycache__ cleared past the second boundary; live union is 35 fragments; --escalation-scan exit 0 on base and branch for the same spec; control pair — identical scope text exits 3 under `## Deliverable` and 0 under the bullet schema; perry-lint --specs reports 45 of 119 matching my census file-for-file, --strict exits 1; suites in scratch copies at load 9.38, 8 workers — d49964e 108 modules/3003 tests/332.6s all green, branch 109/3016/365.3s all green; grep of work/ modes/ decide/ goals/ reference/ packs/ SKILL.md AGENTS.md tests/run for every lint mode; default `perry-lint --root .` output on the branch; a verbatim add-task-step-3 spec naming git push/origin/rm -rf/gh release, written into a scratch copy, not the repository
not-checked: the contents of the 45 specs, so the real blast radius of the empty scans is unmeasured; the other 15 `_section` call sites (only relevant to fix 2, which was rejected); --specs against a state root separate from the project root, under --quiet, and with --state-root; end-to-end localized-project behaviour beyond parser-level heading matching; every dispatch.md pre-flight step other than step 4; Windows/non-macOS paths; whether the author's claimed TASK-233 real-spec mutation was performed, since it is in no test and no result document exists; any suite run on coding/task-247-config-predicate
proof: viewer/parsers.py:4419 computes `verdict` from `fragments` only and never from `scope_scanned`, so an unscannable spec exits 0 via bin/perry-state:2657, and work/reference/dispatch.md:12 reads exit 0 as proceed while naming only `refuse`/`green_lit`/`origins` as the JSON to read; the compensating report at bin/perry-lint:4298-4347 is invoked by nothing — `--specs` occurs zero times in work/, modes/, decide/, goals/, reference/, packs/, SKILL.md, AGENTS.md or tests/run, and `perry-lint --root .` on the branch prints 0 spec-scope-unscannable findings over 45 unscannable specs
=== END VERDICT ===
