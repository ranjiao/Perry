# TASK-454 — concrete confirmation proposal, not applied

Prepared 2026-09-17. No architecture edit, user confirmation or hash entry has been written. This question is queued behind the three live user decisions. TASK-453 already supplies the S7 mechanism; its current live result skips because no confirmed hash exists.

Proposed §3 replacement (aligns the blanket prohibition with existing NN-6):

```text
- **An agent changing a decided architecture section without user confirmation.**
  Descriptive edits follow §6 NN-6; decided changes require a recorded user answer.
```

It replaces exactly:

```text
- **An agent writing `ARCHITECTURE.md`.** This file is the user's.
```

The complete text whose confirmation is requested is preserved in [proposed decided text](TASK-454-proposed-decided-text.txt): §1 body, §3 Forbidden bullets and §6 body. No other decided text changes. Existing `tests/test_architecture_rules.py` functions `decided_text` and `decided_hash` generated this packet; no duplicate hashing/extraction algorithm was added.

- Current decided-text SHA-256: `2434ed7c23a505e9ab174e73855a8e2fba996854fb09fab0e0a8c02a6c837160`.
- Proposed decided-text SHA-256: `0266cf9c057e36ca82e91091a4b044d492fc1bf7c2a0b8f7478998e4f5bc1098`.
- Current S7: `skip`.

After an actual recorded user decision, apply only its authorized text and add a newest-first User-confirmed §8 entry carrying that exact hash and decision reference. Recompute from the final candidate. Prove matching hash passes and a one-line decided-text mutation fails; retain independent review and actual integration receipts. A stored proposal is not confirmation, and an agent cannot promote the current skip to pass.
