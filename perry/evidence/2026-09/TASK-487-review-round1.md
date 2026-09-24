# TASK-487 — review round 1: V4 and architecture, on b47cd005

Candidate: `c1e3f38ca2706f00e106ddf976a5ae435115416b..b47cd005d34a0f2bd6ea7c710ebd6566078d10ae`
(`coding/task-487-kernel-core`). Criteria: `TASK-487-spec.md` at c1e3f38c.
Each reviewer ran in a fresh context, in its own isolated worktree. Neither is
the author, and neither was given the author's verdict. At the end of the round
the reviewer's worktree was clean, and `.git/perry` (the live store) was absent.

## V4 review — condensed; the verdict block is verbatim

The reviewer ran 48 mutants of its own:
- **41 caught.** All 41 also turned `--tier affected` red.
- **7 survived:**
  - M08 — the import gap check;
  - M15, M17, M19 — `expect` on create, move and attach;
  - M24 — dead code;
  - M38 — the `run.py` live-store verdict;
  - M45 — the `bin/lib` side of the `$PERRY_PROJECT` clause.

It also demonstrated the following:
- the md-free suite passes, 145/145;
- live-store detection works end to end: a leak from the run's own session exits 1, a leak from another session exits 0 and is reported;
- a crash inside the transaction (`os._exit`) leaves nothing written;
- `--help`, invoked 8 ways, writes no files;
- export / import / export is byte-identical.

**Findings outside the Bound.** None of these is a criterion failure.

- **F1, user-reachable:** `item create` with `relations:[{kind:parent, from:X}]`
  gives X a second parent. The check at `commands.py:527` counts only
  `src == new_id`. Reproduced.
- **F2:** `expect` is untested at `commands.py:498`, `:604` and `:674`. The code
  behaves correctly at all 7 write commands, but mutants M15, M17 and M19
  survive.
- **F3:** the import gap check at `commands.py:1058` is untested. With the check
  mutated, a gapped history imports with `verified: true`.
- **F4:** the `ok_live` exit verdict at `kernel/tests/run.py:75` is untested.
- **F5:** the resolver-agreement test pins 3 of the 4 differences that the § 3
  sunset lists.
- **F6:** `init` (`commands.py:335` and `:348`) and `import` (`:1038` and
  `:1078`) each check before the transaction starts. Under a concurrent `init`
  they return `internal`, exit 3.
- **F7:** `ARCHITECTURE.md:181` says the kernel's resolver is "the only second
  implementation". That is false: `bin/perry-state:3338` and
  `viewer/parsers.py:695` both predate it.
- **F8, scope:** b47cd005 edits `bin/ARCHITECTURE.md` and three root lines that
  are outside the written Bound. Most of them are the stale-text fixes the user
  directed.

Minor findings:
- `guards.py:99–100` is dead code.
- A self-transition that changes nothing returns `unchanged` without running
  its guards.
- A lone surrogate in text returns `internal`.
- A crash during export leaves a `.tmp` file behind, and every later export is
  then refused with `export_dir_foreign`.

```
=== VERDICT ===
task: TASK-487
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-487-spec.md
checked: criteria 1-8 and 10-12, the carried items and the Bound, at b47cd005; --tier affected at baseline (23 modules, 583 tests, green; NOT a green suite); kernel suite 145/145; 48 mutants of my own, anchored by line, restored and verified against git show, each followed by the kernel suite and --tier affected in the worktree and run again in a scratch copy: 41 caught, 7 survived (M08 import gap check, M15/M17/M19 expect on create/move/attach, M24 dead code at guards.py:99, M38 run.py:75 live-store verdict, M45 bin/lib side of the PERRY_PROJECT clause); criterion 2 on a git-archive copy with 1,210 *.md deleted (145/145); criterion 1 end to end (own-session leak exits 1, other session exits 0 and is reported); a crash inside the transaction via os._exit (nothing lands); --help 8 ways (exit 0, no files); expect on all 7 write commands; export twice and export/import/export byte-identical; init and import racing a concurrent init; a gapped history that replays cleanly (refused, and accepted under M08); root § 3 "only second implementation" enumerated; .git/perry absent at the end; worktree clean
not-checked: --tier full, bash tests/run and tests/merge-check (green on base is not green merged); the author's own 19 mutations and its 17 readings; criterion 8 against a real perry.json (it does not exist; I used DESIGN-023 § 5.4's list and a 30-word grep); crash atomicity for rel, attach, template, import and export, and real power loss; concurrency beyond two processes; Python other than 3.11.15 and SQLite other than 3.50.4; a line-by-line diff of describe against the § 5.6 table; the 8b3f825a approval itself (taken from the brief and b5a53bf1); F1-F8, which are outside the Bound and belong to new rows
proof: every criterion holds: 41 of 48 mutants caught and all 41 reddened the tier; criterion 2 145/145 with no *.md; criterion 1 demonstrated end to end; export/import/export byte-identical. Outside the Bound: F1 kernel/perry_kernel/commands.py:527 (item create gives an item a second parent); F2 commands.py:498, :604, :674 have no test; F3 commands.py:1058 has no test; F4 kernel/tests/run.py:75 has no test; F6 commands.py:335/348 and :1038/1078; F7 ARCHITECTURE.md:181
=== END VERDICT ===
```

## Architecture review — condensed

**Triggers:** a new bin executable and edits to the root and module
architecture documents are true. Boundary paths, a new top-level directory and
a contract-version change are false.

**Decision: PASS.** No decided section is contradicted.

**Corrections required:**

1. **Code — contradicts NN-K4 and NN-K5, which are proposed.** An empty
   `--root ""`, `--root=` or `--store ""` is accepted at `cli.py:86–100` and then
   ignored by truth tests at `paths.py:41` and `:116`. Resolution then falls
   through to the environment, or to the derived shared store.
   - This is the defect DESIGN-016 § 1.1 measured.
   - `ROOT_READERS` at `test_bin_argument_contract.py:817` cannot see
     `bin/perry-kernel`.
2. **Descriptive mismatches:**
   - root § 5, for exit 3 and for `SURFACE`;
   - root § 8, which omits the round-2 edits;
   - `bin/ARCHITECTURE.md` § 2 (its diagram omits `perry-kernel`), § 4, § 5
     (exit 3) and § 8;
   - `bin/README.md` lines 30 ("thirteen"), 62 ("Seven tools write"), 94 and 118;
   - kernel § 3:94 and § 5.8:450, which say "nothing but import reads the
     export", when `export` reads it to decide `unchanged`;
   - kernel § 5.7:420–423, which says "the suite fails" on another session's
     events;
   - kernel § 8:589.
   - Root § 2 and the § 3 diagram's "136 modules" was already stale before this
     change.

**User decisions required.** Neither blocks the merge.

- **(a)** Root § 3:181 says the kernel's resolver is "the only second
  implementation". That is false, and the claim that "the test pins the
  difference" leaves out the `$PERRY_PROJECT` case. Narrow the sentence?
- **(b)** `bin/ARCHITECTURE.md` NN-B3 is user-confirmed and has no matching
  exception. Carry the § 3 sunset into it? And update OQ-B1's "thirteen"?

The full COMPLIANCE block is in the session transcript. It is bound to
b47cd005, so a changed candidate needs a fresh review.
