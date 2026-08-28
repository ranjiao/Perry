# TASK-201 — the gate now sees Chinese, and a dropped fragment is no longer silent

**From `coding/task-201` @ `0262445`.** Rung **V3**, priority **P0**.
`perry/` unmodified.

## My spec sent it after a defect that did not exist

I wrote that `scan_spec_escalations` reads the three headings literally and told
it to *"find out whether the scan can go through `heading_is` / `alias` rather
than through literal strings"*.

**It already did, and always had:**

```python
:3390   hits = matching_escalations(_section(body, *alias("headings", label)), fragments)
:3395   disclaims = matching_escalations(_section(body, *alias("headings", ESCALATION_DISCLAIMS)), …)
```

`ESCALATION_TOUCHES` / `ESCALATION_DISCLAIMS` are canonical **names** handed to
the i18n path, not match strings. **The defect was entirely in the data** — three
missing glossary rows — and the fix is **zero lines of code** for that half.

The second translation table my spec was afraid of was never a temptation. It
added a comment at the constants so the next reader does not re-diagnose it the
way I did.

## What the gate was actually doing

Same throwaway project, `bin/perry-state --root … --escalation-scan`. Hook
declares `` `production` ``, `` `deploy` ``, `` `下单` ``, `` `平仓` ``; the
spec has `## 涉及文件` / `## 交付物` (containing `` `production` ``) /
`## 不在范围`.

| | union | touches | verdict | exit |
|---|---|---|---|---|
| **before** | `["production","deploy"]` | `{}` | **pass** | 0 |
| **after** | `["production","deploy","下单","平仓"]` | `{"Deliverable":["production"]}` | **refuse** | 3 |

**Read the `union` column, not the verdict.** The gate did not merely fail to
read Chinese headings — `下单` and `平仓` had never entered the union at all,
because the `len > 2` floor dropped them. It was not loaded, and it was not
aiming.

Glossary rows added: `涉及文件`, `交付物`, `不在范围` — the spellings TASK-200
measured, and `交付物` is what gimegime-pmo's real specs use.

## The floor, and the sentence that settles it

```python
return len(frag) > (2 if frag.isascii() else 1)
```

> `escalate_unextractable` … used to ask "does this line contain a backtick"
> instead, which is **a different question with the same answer only in ASCII.**

ASCII stays at 2 because an edge guard cannot save `go` from the English word
*go*, and `sh`, `-f`, `*` are noise — **a gate that cries wolf gets waved
through**, which is TASK-107's finding. One CJK character is refused for the
mirror reason: it is a morpheme inside a large share of surrounding compounds,
with no boundary available to guard it.

The two decisions now agree instead of contradicting. `_ESC_WORD` was written
ASCII-only *on purpose* so a CJK fragment reaches the matcher unguarded; a flat
floor of 2 undid that from the other end, because **a fragment that never
extracts never reaches the matcher to be unguarded at all.**

## Defect 2, and the linter line that came with it

`line_fragments(line)` split out of `escalation_fragments`, so *"did this line
contribute anything"* is answerable and `escalate_unextractable` asks it.
`bin/perry-lint`'s message changed too — it asserted *"has no backticked span"*,
which the fix makes false.

Measured on a role card carrying `` 任何 `下单` 动作 `` and
`` shell 里的 `sh` 调用 ``:

```
before   0 findings   — both lines have backticks, both contribute nothing
after    1 finding    — the `sh` line, correctly; `下单` now extracts,
                        so it is correctly NOT reported
```

## Mutation: 13 written, 13 killed, 0 survived

Five for the glossary half — drop each `zh` entry, make `touches` read
literally, make `disclaims` read literally. Eight for the extraction half,
including four separate floors (`> 2` flat, `> 1` flat, `> 0`, always-true).

17 new tests, all built in temp projects through the real `--root` seam.
**The glossary test is written per declared language rather than for `zh`**, so
adding a language without these three rows re-opens the hole loudly.

## Left, named, not fixed

- **The hook side has no `not-extractable` check at all** — only role cards get
  one, and the hook is the half *every* project has. TASK-200 measured a real
  project whose hook contributes 3 fragments where its bullets name more.
  **Opened as TASK-202.**
- `green_lit` does not de-duplicate across `touches` sections while `refuse`
  does.
- A heading with a numbering prefix — `## §8. Executor 交付物`, which
  gimegime-pmo actually uses — still does not resolve. `_section` matches by
  prefix, so this is **equally true in English**: a decision, not a patch.
- **`下单` still fires on `系统永不下单`.** Named in the code rather than
  hidden: a boundary-free script cannot express polarity. That is the same wall
  TASK-200 hit from the other side.
- `schema/roles-list-contract.md § must_escalate.unextractable` **already
  documented the corrected meaning**, so no contract bump was warranted.
- `bin/perry-state:1954` untouched, as instructed.

## Verification

Suite **88 modules · 2631 tests · one red** (`test_diagnose`, pre-existing).
`perry-lint` 0 errors, 3 warnings, 0 rows drifted, risks store 4 records 0
drifted. It also caught that the store reads **195**, not the 194 my spec
pinned — confirmed by stashing its diff and re-running, so the number was
HEAD's own and my spec was one commit stale.
