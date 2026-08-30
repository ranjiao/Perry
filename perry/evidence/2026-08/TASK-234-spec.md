# TASK-234 — .perry/conformance.md is a pure ledger with a hand-rolled table parser, and its phantom row has nowhere to record provenance

> Consolidated from the board row 2026-08-30. The row's own fields are the
> acceptance criteria; this file is where a V4 reviewer reads them.

## Why this row exists

Measured 2026-08-29 at a30e103. The file is 38 lines: a 10-line prose header that is ALREADY a constant in the writer (bin/perry-conform:406 HEADER) and 24 rows of four regular columns — File, Shape version, Declared, Route — with not one word of per-row prose. render() at bin/perry-conform:423 rebuilds the whole file from the declarations on every write_atomic, so unlike .perry/config.md this one already round-trips from its own records. It has exactly ONE reader (viewer/parsers.py:394 read_conformance, placed there deliberately so lint, conform and any front-end cannot disagree) and ONE writer (bin/perry-conform:474), so the blast radius is two functions rather than a directory. Parsing that table has already cost twice, and both are TASK-050's defect class: parsers.py:415 records its split_row as 'the SIXTH implementation of this, found by a V4 reviewer after five were unified — it reads a row out of a regex group rather than off a line, which is why every sweep looking for strip(|).split(|) at the start of a line walked past it', and the line below it uses squash rather than .lower() because a bolded | **File** | header row was once read as a declaration.

## Deliverable

—

## Verification — V4

V4

## Out of scope

—

## Where to start

Blocked until TASK-050 lands: converting this reader removes one of the markdown tables TASK-050's header_index() has to cover, so doing it first means TASK-050 converts a site that is about to be deleted. TWO THINGS TO SETTLE BEFORE WRITING CODE, both real. (1) BOOTSTRAP ORDER: this file gates every write under ADR-004's enforce gate, including the write that migrates it — the migration path must not require the gate to be passable mid-migration. (2) SELF-REFERENCE: schema/state-schema.json:2053 already states, deliberately, that .perry/conformance.md is NOT a files[] entry because 'it is a record of the user's decisions ABOUT state, not state, and listing it here would make it declarable-conformant about itself'. That reasoning carries over to the jsonl unchanged and must be moved across EXPLICITLY, not dropped in the format change. (3) NOTE FOR THE GOALS LANE, not this row's to write: P003-O1-KR1, KR2 and KR3 are all phrased 'of 6' over the six stores in claims[]. A seventh claimed store moves that denominator. Whether conformance.jsonl joins claims[] at all is the same question as (2).
