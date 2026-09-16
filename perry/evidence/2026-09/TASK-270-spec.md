# TASK-270 — spec

> Row: perry-config unset can empty the config store at exit 0, after which every writer refuses with a false cause and perry-lint calls the store valid
> Priority P1 · Owner Coding Agent · Rung V3 · Track intake (queue, SLA 5 d; 13 days over)
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Touches architecture: (none expected — say so if the fix needs one)

## Why

Read `perry/evidence/2026-09/TASK-270-reproduction-2026-09-16.md` first: the row
was re-measured before dispatch, and what it now describes is narrower than its
original finding. The trigger is gone and the store is recoverable, but a user
can still empty `.perry/config.jsonl` with Perry's own command, exit 0 at every
step, and then be given three messages of which two are false and none names the
way out.

## Deliverable — four outcomes

1. **The writers' refusal tells the truth.** A writer that refuses because the
   config store is empty must say the store is *empty*, not that it "holds records
   that do not validate", and must name the recovery: `perry-config set <label>
   <value>`, or `perry-config track` if tracks are what is missing.
2. **The writer and the linter agree on whether an empty store is usable.** Today
   `perry-lint` says `0 record(s), all valid` and every writer refuses. Pick ONE
   rule and hold both tools to it. Decide it from the refusal's own stated reason,
   which is that writing "would stamp DESIGN-003's implicit `main` over whatever
   this project actually declares and lose that track's mode, stages, WIP and SLA":
   ask whether that reason applies when nothing is declared. Write the rule and its
   reason into the result, and make it one predicate both tools call — not two
   copies that can drift.
3. **`NS-01` does not call a Perry-written config store foreign.** An empty
   `.perry/config.jsonl` produced by `perry-config unset` is Perry's own file.
4. **`perry-config unset` does not empty the store silently.** When it removes the
   last record it says so and says what that means for the writers. Whether it
   should also refuse is part of outcome 2's rule — decide them together.

## Investigate and report, do not fix

While reproducing, check what `perry-config unset "State root"` does on a project
whose state root is `perry/`: does the next write land at the project root instead?
If it does, that is a second, larger hazard (writes silently relocate). **Report
it with a reproduction; do not fix it in this row** — moving where a project's
state lives is the claim surface, and the user decides.

## Files in scope

- `bin/perry-config`
- the one place the writers' config-store refusal is raised (find it; `bin/perry-task` and `bin/perry-goals` share it or should)
- `bin/perry-lint` — only the config-store check and `NS-01`'s treatment of this file
- `bin/lib/__init__.py` if the shared predicate belongs there
- tests: a new or existing module covering the four outcomes, with `COVERS` declared
- `perry/evidence/2026-09/TASK-270-result.md`

## Bound

```
Enumeration:  the four outcomes above, plus the one State-root investigation
Size:         4 fixes, 1 report
Last element: the State-root reproduction in the result
```

## What it must not do

1. **Must not change `schema/state-schema.json`.** It is the claim surface.
2. **Must not change where state lives** or how `State root` resolves.
3. **Must not make a non-empty invalid store writable.** The existing refusal for
   records that genuinely do not validate stays exactly as strict.
4. Tests write under temporary roots only (`NN-5`).

## Verification

1. Base check as the brief states.
2. `bash tests/run --tier affected --base <base>` each round; the full
   `bash tests/run` on the final commit with `PERRY_PROJECT` and `PERRY_HOME`
   unset. Quote both.
3. **The reproduction, re-run end to end** on a copy of
   `tests/fixtures/sample-project`, quoting each tool's output: unset every
   setting → the writer's message → `perry-lint` → `perry-config set` → a write.
4. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - the writer's empty-store message restored to "holds records that do not validate";
   - the shared predicate forked so the writer and the linter disagree again;
   - `NS-01` flagging the empty config store again;
   - a genuinely invalid non-empty config store accepted by a writer.
   A green mutation is a finding.
5. The State-root investigation's reproduction, quoted.

## Subjective verification

(none)

## Out of scope

The State-root hazard's fix; `TASK-271`, `TASK-275`, `TASK-289`, `TASK-291`.
