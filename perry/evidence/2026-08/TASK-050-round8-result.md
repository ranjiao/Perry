# TASK-050 round 8 — result: **SUPERSEDED, and retracted in the parts named below**

> The result of record for this row is
> **`perry/evidence/2026-08/TASK-050-round9-result.md`**.
>
> This file is deliberately not kept alongside it as a second account. Round 8
> FAILed its V4 review, three of its numbers were wrong, and a document that
> states them next to a document that corrects them is two documents
> disagreeing. What is left here is the retraction, which is the only part of
> round 8 that is still load-bearing. The round 8 review that produced it is at
> `perry/evidence/2026-08/TASK-050-round8-v4-review.md` and is unchanged; the
> code it reviewed is at commit `c158418` and is in the history.

## What round 8 claimed that was not true

1. **"planted readers caught: 30 of 30"**, against a corpus described as *"the
   UNION of every shape the round 5 and round 7 reviews name"* and *"a superset
   of round 7's corpus"*. It was neither. Round 7's Finding 2 names *"a scalar
   header-row test"* and *"P23–P25, round 4's `_is_python` hole"* among its
   escapes; none was in the corpus, and the labels `P23`–`P25` had been re-used
   for three different shapes, so the omission did not show in the numbering.
   The reviewer re-derived the missing shapes, planted them with a control at
   the same paths, and **all five escaped both nets**. The honest figure was
   *30 of at least 33*.
   Round 9 rebuilt the corpus from the reviews' own prose, with the source line
   quoted for every entry and a test that refuses a re-used label.

2. **"`ROW_NAMES` is no longer the gate and has not been extended."** Both
   clauses are true and neither is the claim that matters. Emptied, the
   harness dropped from 30 of 30 to **22 of 30**: eight catches were the
   allowlist, not the dataflow. A second name allowlist survived at
   `tests/header_rule.py:357-360`. Round 9 deleted both, and the shape net they
   belonged to.

3. **"`python3 -m unittest discover -s tests` disagrees with `bash tests/run`
   by 3 on this repository."** True — but nobody had measured it, on either
   tree, and `68e63cf` retracted it in a new § 6.9 while leaving the sentence
   standing in § 5. Round 9 measured it on three trees. It is 3, and the three
   are `test_risks_store.TestTheReadersAreOneFunction`.

4. **"67 call sites across 10 files now reach `header_index`."** The table
   directly beneath it summed to 58. Measured on a `git archive` export of
   `68e63cf`: **58**. The table was right; 67 is not derivable from anything.

5. **`bin/perry-diagnose § md_table` listed among the readers the closing test
   watches.** It contributed zero recorded folds, because it pre-stripped
   decoration before calling `header_index`. Round 9 fixed the reader and made
   the reader list an assertion.

## What round 8 got right, and round 9 kept

`viewer/tables.py § header_index` and the conversion of the readers onto it.
Round 8's reviewer verified it independently — nine mutations with md5-verified
restores, the `parsers.py` KR proof case, `alias`-after-fold shown exact, no
site where the `list` subclass changes behaviour, and criterion 5 driven
end-to-end through four CLIs on a 64-cell half-bolded fixture, byte-identical.
None of that was disturbed. Round 9's changes are two further live conversions,
the deletion of the shape net, a rebuilt corpus and a widened runtime watch.
