# TASK-068 — the branch that produced four instances of one defect

> Rung: **V3**. Every claim is a run or a mutation, on copies of
> `~/proj/gimegime-pmo` and `~/proj/PolyForge`.

## The branch

`is_header_block` had two ways to qualify a leading `>` block as Perry's
metadata:

1. it names a field the file's spec declares, in any declared spelling; **or**
2. *"it opens immediately under the H1, which is where the template puts it."*

The second is **position used as evidence**, and the same docstring's first
paragraph already ruled that out: *"Sentences are field-shaped; only the
vocabulary tells them apart."* The fallback said it anyway, and it is why
narrowing the field vocabulary three separate times never touched this.

`knowledge/auto-research/…全景综述_2026.md` opens with the author's seed thesis
in a blockquote directly under the H1. Perry appended `Id`, `Source`,
`Received` and `Status` to the end of that paragraph, and one of the four
arrived as `状态：—` beside three English labels. No character lost; the meaning
changed. `ADR-004`'s named failure mode: *"a board that still parses and no
longer reads like theirs."*

## The fix, and what it costs

**Deleted.** A block that names no declared field is not Perry's, and Perry
starts its own above the author's prose.

The cost, stated rather than discovered later: a genuine header block written
entirely in field names the schema does not know now gets a **second block
beside it** instead of being joined. Cosmetically worse, **never destructive**.
Between "sometimes two blocks" and "sometimes inside their sentence", the
guarantee `TASK-044-spec.md` asks for picks the first without hesitating.

## And a second bug the fix exposed

With Perry starting its own block, `Id` landed correctly — and `Source` and
`Received` still went into the author's paragraph.

`header_block_span`'s comment says *"the FIRST CONTIGUOUS run of `>` lines"* and
its loop **let a blank line through**. So once there were two quote blocks
separated by one, the span reached across into the author's, and every field
after the first went where the first was moved to avoid. A blank line now ends
the block.

That half was invisible until the first half landed. It is the reason the fix
was verified by reading the migrated files again rather than by re-running the
counts.

## Measured on the real project, before and after

| | before | after |
|---|---|---|
| lint errors | 59 | **15** |
| ids in tree | 297 | **312** (+15 minted, 0 lost) |
| files changed | — | 30 |
| provenance findings | 15 | **1** |
| Perry fields appended after a prose line | 1 | **0** |

The last row is a **diff-based** check: for every added field line, is the line
above it a long quoted line? A first attempt counted "blocks containing both a
field and a long line" and reported 62 — every one a false positive, author-owned
ADR headers whose `Sunset criteria` value is simply long and which migration
never touched. Comparing before against after rather than measuring the after
alone is what made the number honest.

PolyForge unchanged at 11.

## Mutations

3 on the branches, 3 red: restoring position as evidence, letting a blank line
through again, and removing the vocabulary branch entirely.

One test failure was **mine, not the code's**: `test_a_real_header_block_is_still_joined`
sliced `lines[first-3:first+4]` with `first == 2`, so a negative start wrapped
the slice and it looked at the wrong lines while the output was correct.
