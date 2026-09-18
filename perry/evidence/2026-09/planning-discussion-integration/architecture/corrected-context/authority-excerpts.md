# Corrected duration authorities at 17b7e23b8b3441fd50233c37183e8e9b30e7c8a4

## ARCHITECTURE.md

Blob: `169dc2ff91d62b585de4fb47f6b384e70938688b`

```text
129: ### `tests/` — 136 modules
130: - **Purpose**: the contract, executable. Includes `tests/tree_guard.py`, which
131:   fails the suite if a run changed the checkout it ran in.
132: - **Owns**: whether a claim in this repository is true.
```

## perry/design/DESIGN-021-test-tiers.md

Blob: `e4fc0d5e859f5e461a45fdddf3634c05c6749891`

```text
1: # DESIGN-021: Every round runs the whole suite, and nothing stops it getting slower
2:
3: > Status: locked
4: > Date: 2026-09-15 · Locked: 2026-09-15
5: > Author: Perry maintainer   · Implementation owner: TBD
6: > Linked OKR: —
7: > Supersedes: —   · Superseded by: —
8: > Revisits: `tests/run`, `tests/parallel`, `tests/merge-check`, `tests/durations.json`, `tests/test_durations_provenance.py`, `work/reference/dispatch.md` (the brief and the merge steps), `work/reference/review.md`, `goals/reference/phases.md § score-phase`, `perry/decisions/ADR-018-verification-is-calibrated-to-blast-radius.md § C`
9: > Sign-off: User Decisions 1–5 answered by Ran Jiao in session on 2026-09-15. Moved `draft` → `locked` without an `in_review` hold, as `DESIGN-013`, `DESIGN-014` and `DESIGN-020` did. The lock-time `reference/input-quality.md § 3` pass raised 3.6 (unlisted surfaces: `tests/test_durations_provenance.py`, `phases.md § score-phase`, the dispatch merge steps) and an undated measured number (§ 5.1's ≈ 150 s); both were fixed before lock at the user's choice — the Revisits line, § 7's new row, and § 5.1.
```

```text
178: ### 5.3 The merge gate
179:
180: Before merging a branch, the primary checkout runs `tests/merge-check` for that
181: one candidate against `main`'s tip: `--tier full` on the merge result. Green →
182: `--record` refreshes `tests/durations.json` in the merge commit, so no task
183: commit re-times modules by hand again. Red → the existing attribution names
184: whether the red is pre-existing, the candidate's, or an interaction. `DESIGN-017
185: § 5.2`'s architecture rules run here as part of `full`.
186:
187: ### 5.4 The ratchet (decision 4)
188:
189: `tests/durations.json` gains a `budget` block:
190:
191: ```json
192: "budget": {"total_sec": 1054, "module_sec": 30,
193:            "exceptions": {"test_tree_guard.py": "USER-NNN — why it may exceed"}}
194: ```
195:
196: - **At merge:** a module whose recorded time exceeds `module_sec` with no
197:   exception, or a total above `total_sec` by more than the noise margin, is
198:   reported in the merge evidence. It does not block the merge.
199: - **At phase close:** a quiet re-record runs; the same conditions fail. Raising a
200:   budget or adding an exception is an ask, answered by the user.
201: - `total_sec` starts at today's 1,054 and is lowered, never raised, when a phase
202:   closes under it.
203:
204: ### 5.5 What each role is told
205:
206: | Role | Runs | Written in |
207: |---|---|---|
208: | Executor | `--tier affected --base <pinned base>` each round; the printed selection in its result | `work/reference/dispatch.md` brief |
209: | V4 reviewer | `--tier affected` plus its mutations, on the same base | `work/reference/review.md` |
210: | Primary checkout | `tests/merge-check --tier full` before merge; `--record` | `work/reference/dispatch.md § merge` |
211: | Phase close | `--tier slow` and the ratchet's re-record | `goals/reference/phases.md § score-phase` |
```

## work/reference/dispatch.md

Blob: `ad47dd16ddbc0e016a65c44a8a902290e4aa7877`

```text
358: ## What the executor runs each round (`DESIGN-021 § 5.5`)
359:
360: > **The brief tells the agent to run `bash tests/run --tier affected --base <the
361: > pinned base SHA>` at the end of every round, and to paste the printed
362: > selection block into its result.** Not the whole suite: the whole suite is
363: > 964 module-seconds, and an executor that pays it on every round pays it four
364: > or five times for a change that touches a handful of modules.
365:
366: **The sentence that goes in the prompt, and it goes in whole:**
367:
368: ```
369: Run `bash tests/run --tier affected --base <base SHA>` at the end of every
370: round. It runs the smoke checks — the schema drift guard, every shipped script
371: compiling and answering --help, and the tree guard — plus the test modules
372: your change selects, and it prints which modules it selected and the rule that
373: selected each. Paste that selection block into your RESULT.
374:
375: A red in `affected` is a red: fix it before you report.
376: A green in `affected` is NOT a green suite. It ran the modules your change
377: selects and nothing else, so it cannot tell you that the rest of the suite
378: still passes. Say "green for --tier affected" in your result, never "the suite
379: is green", and quote the module count you actually ran.
380: ```
381:
382: **The other three names**, for a round that wants them: `--tier smoke` (the
383: cheap checks alone, ≤ 30 s), `--tier full` (every module except the harness
384: self-tests — exactly what bare `tests/run` has always run), and `--tier slow`
385: (the harness self-tests too, the old `--slow`). Bare `tests/run` is unchanged
386: and still means `--tier full`; `--lint`, `--serial`, `--only` and `--slow` all
387: keep their meaning. Add `--dry-run` to any of them to print the selection and
388: run nothing.
389:
390: **Full merge acceptance runs on an isolated candidate.** From the primary
391: checkout, resolve the current base and candidate, then run the supported gate:
392:
393: ```bash
394: env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/merge-check \
395:   --base main delivery=<candidate-branch> --tier full --record <new-external-dir>
396: ```
397:
398: Use a unique scratch directory outside the checkout (the scratch rule above),
399: not a shared name. This invokes every `tests/run` full stage, including syntax/help
400: and the tree guard. `--checks` is diagnosis only. Any full failure refuses
401: acceptance, including a pre-existing base failure; attribution explains it but
402: does not excuse it. Full timings update measured modules only; deferred slow
403: modules keep their prior source. A new test module is initially registered as
404: `sec: null, source: null` in the existing duration inventory; the coding task need
405: not measure it by hand. The gate records measurements, not inventory discovery.
406: `--tier slow` is the full run plus harness tests,
407: not an automatic side effect of requesting a record.
408:
409: The record directory holds exact input refs/SHAs, tested tree, outcome and emitted
410: `durations.json` hash. The main integrator coordinates its import on the tested
411: integration tree; the authorized Coding Agent commits that product artifact on
412: an integration branch. PMO does not write product files in the primary checkout.
413: Do not invent a future merge SHA: timing provenance cites existing base/candidate
414: commits and the tested tree. Keep the named input refs unchanged during this step.
415:
416: After that artifact-only commit, in the clean integration checkout run:
417:
418: ```bash
419: python3 tests/merge-check --verify-receipt <new-external-dir>/receipt.json
420: env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME bash tests/run --tier slow
421: ```
422:
423: Receipt verification requires the same code tree except for the exact recorded
424: artifact, checks current input refs and runs duration provenance validation.
425: The separate slow gate verifies the final recorded artifact and harness; retain
426: both receipts. If either input ref moves, any other code changes, or a check
427: fails, regenerate/revalidate the affected candidate before acceptance. Immediately
428: before the authorized merge, recheck the receipt and exact base/candidate refs;
429: merge only the verified integration branch/tree. Neither command merges or writes
430: main, and local checks do not install remote branch protection. Existing release
431: record rules still apply; an agent's green `affected` is never this acceptance.
432: Also complete § Architecture review on the exact final integration candidate;
433: the test receipt does not supply the independent architecture judgment.
```

## tests/merge-check

Blob: `47c904b5f177f8f83e1eda8230d1609a7a41316d`

```text
77: stage/guard failures refuse without guessing their cause.
78:
79: --record DIR emits an external receipt.json and durations.json after a green
80: run. It does not modify the caller, stage files, create a product commit or merge.
81: New modules first register sec/source as null in the existing inventory; no
82: manual retiming is needed. Full refreshes only measured modules; slow entries retain their prior
83: provenance. The coding/integration role imports the artifact on the exact tested
84: code tree, commits only that artifact, then runs --verify-receipt DIR/receipt.json
85: and the separate slow gate. Verification requires unchanged input refs, identical
86: code outside durations.json and the exact emitted artifact. A moved input ref
87: invalidates the receipt. No future merge commit identity is invented.
```

```text
375: def code_identity(repo):
376:     raw = sh(["git", "ls-tree", "-rz", "HEAD"], cwd=repo).stdout
377:     entries = [item for item in raw.split("\0") if item and
378:                item.partition("\t")[2] != "tests/durations.json"]
379:     return hashlib.sha256("\0".join(entries).encode()).hexdigest()
380:
381:
382: def inputs_current(repo, receipt):
383:     return all(resolve_local(repo, item["ref"]) == item["sha"]
384:                for item in [receipt["base"], *receipt["candidates"]])
385:
386:
387: def record_artifact(scr, output, results, receipt):
388:     data = json.loads(results.read_text())
389:     if data.get("schema") != 1 or not data.get("modules"):
390:         raise RuntimeError("missing module timing transport; no record accepted")
391:     rows = data["modules"]
392:     if any(r["rc"] != 0 or r["ran"] <= 0 or not isinstance(r["sec"], (int, float))
393:            or not math.isfinite(r["sec"]) or r["sec"] < 0 for r in rows):
394:         raise RuntimeError("invalid or failing module timings; no record accepted")
395:     doc = json.loads((scr.dir / "tests/durations.json").read_text())
396:     live = {p.name for p in (scr.dir / "tests").glob("test_*.py")}
397:     names = [r["mod"] for r in rows]
398:     if len(set(names)) != len(names) or sorted(names) != data.get("selected"):
399:         raise RuntimeError("timing transport omitted or duplicated selected modules")
400:     if set(names) | set(data.get("deferred", [])) != live:
401:         raise RuntimeError("timing transport does not account for every module")
402:     if set(doc["modules"]) != live or any(r["mod"] not in live for r in rows):
403:         raise RuntimeError("duration module inventory differs from tested tree")
404:     stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
405:     source = "merge-" + receipt["tree"][:12] + "-" + stamp
406:     doc["sources"][source] = {"kind": "merge-result", "ref": receipt["candidates"][0]["sha"],
407:         "base": receipt["base"]["sha"], "tree": receipt["tree"], "taken": stamp,
408:         "workers": data["workers"], "tier": receipt["tier"],
409:         "note": "Measured isolated merge tree; ref/base are existing inputs, not a future merge commit."}
410:     for row in rows:
411:         doc["modules"][row["mod"]] = {"sec": round(row["sec"], 3), "source": source}
412:     artifact = (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode()
413:     (output / "durations.json").write_bytes(artifact)
414:     receipt["artifact_sha256"] = hashlib.sha256(artifact).hexdigest()
415:     receipt["measured_modules"] = [r["mod"] for r in rows]
416:     receipt["unmeasured_modules"] = sorted(live - set(receipt["measured_modules"]))
417:     receipt["artifact_verified"] = False  # import + verify is a separate real operation
418:
419:
420: def verify_receipt(repo, path):
421:     receipt = json.loads(path.read_text())
422:     if receipt.get("status") != "green" or receipt.get("tier") not in ("full", "slow"):
423:         raise RuntimeError("receipt is not a successful full/slow gate")
424:     if not inputs_current(repo, receipt):
425:         raise RuntimeError("base or candidate moved; rerun the merge gate")
426:     if sh(["git", "status", "--porcelain"], cwd=repo).stdout.strip():
427:         raise RuntimeError("receipt verification requires a clean committed integration checkout")
428:     if code_identity(repo) != receipt["code_identity"]:
429:         raise RuntimeError("integration code differs from tested code outside durations.json")
430:     artifact = (repo / "tests/durations.json").read_bytes()
431:     if hashlib.sha256(artifact).hexdigest() != receipt.get("artifact_sha256"):
432:         raise RuntimeError("recorded duration artifact differs from emitted bytes")
433:     command = ["python3", "tests/parallel", "test_durations_provenance"]
434:     p = sh(command, cwd=repo, check=False)
435:     print(p.stdout + p.stderr)
436:     if p.returncode:
437:         raise RuntimeError("imported artifact failed duration provenance checks")
438:     if not inputs_current(repo, receipt):
439:         raise RuntimeError("base or candidate moved during artifact verification")
440:     if (sh(["git", "status", "--porcelain"], cwd=repo).stdout.strip()
441:             or code_identity(repo) != receipt["code_identity"]
442:             or hashlib.sha256((repo / "tests/durations.json").read_bytes()).hexdigest()
443:             != receipt["artifact_sha256"]):
444:         raise RuntimeError("integration checkout changed during artifact verification")
445:     print("VERIFIED recorded artifact on " + resolve_local(repo, "HEAD") +
446:           "; run/check the slow gate separately before acceptance")
447:     return 0
```

## tests/test_durations_provenance.py

Blob: `723257bb3d34a48332cc40ba4c5093b9cbac0b2e`

```text
29: ## What is red here, and what is only reported
30:
31: Red — drift, the two directions of "this file is not about this tree":
32:
33: * a module on disk that the file does not mention,
34: * a recorded module that no longer exists,
35: * an entry whose `source` names a block the file does not define.
36:
37: Reported, never red — provenance and staleness:
38:
39: * how many figures carry a ref, how many are stale, how many are unstamped.
40:
41: That split is deliberate. **Every figure the file inherited is unstamped**, so
42: a check that reddened on unstamped entries would have to be disabled on the day
43: it landed, and a guard that ships switched off is not a guard. Making the count
44: visible on every run is what TASK-304 asked for; re-measuring 108 modules under
45: a load average that has been above 20 all evening would substitute one wrong
46: number for another and is explicitly out of that row's bound.
```

```text
111: class TestTheFileIsAboutThisTree(unittest.TestCase):
112:     """Drift, both directions. This is the red gate.
113:
114:     Both conditions were silent before TASK-304 and both are named here, with
115:     the offending module in the message — "durations.json is wrong" is not
116:     something anyone can act on.
117:     """
118:
119:     def test_no_recorded_module_has_been_deleted(self):
120:         """`test_migrate.py` at 97.25 held the head of this file's ranking.
121:
122:         A deleted module's time is not a stale hint, it is a fossil: there is
123:         no run it could ever describe again.
124:         """
125:         mods, doc = _live()
126:         report = _audit(mods, doc)
127:         self.assertEqual(
128:             report["phantom"], [],
129:             "tests/durations.json records modules that are not on disk: "
130:             f"{report['phantom']}. Delete the entries — a deleted module's "
131:             "recorded time can never again describe a run.")
132:
133:     def test_every_module_on_disk_is_listed(self):
134:         """Seven were not, at `d49964e`.
135:
136:         Listing a module with `sec: null` is a complete answer: it says
137:         "nobody has measured this", it still sorts as `inf` and runs first,
138:         and it is distinguishable from an entry somebody removed. What is not
139:         allowed is silence.
140:         """
141:         mods, doc = _live()
142:         report = _audit(mods, doc)
143:         self.assertEqual(
144:             report["unlisted"], [],
145:             "these modules exist and tests/durations.json does not mention "
146:             f"them: {report['unlisted']}. Each will sort as inf and run first "
147:             "by accident rather than by decision. Add an entry — `sec: null` "
148:             "is a valid one and means exactly 'not measured'.")
149:
150:     def test_merge_result_sources_declare_existing_inputs_and_tested_tree(self):
151:         mods, doc = _live()
152:         self.assertEqual(_audit(mods, doc)["invalid_sources"], [],
153:                          "merge-result stamps need full input SHAs, tested tree and full/slow tier")
154:
155:     def test_every_entry_names_a_source_the_file_defines(self):
156:         """Provenance that cannot be dereferenced is not provenance."""
157:         mods, doc = _live()
158:         report = _audit(mods, doc)
159:         self.assertEqual(
160:             report["dangling"], [],
161:             "these entries name a source block the file does not define: "
162:             f"{report['dangling']}")
163:
164:     def test_the_live_file_parses_into_the_declared_shape(self):
165:         mods, doc = _live()
166:         self.assertIsNone(doc["unreadable"], "tests/durations.json is not "
167:                                              "readable as JSON")
168:         self.assertFalse(doc["legacy"], "tests/durations.json is still in the "
169:                                         "pre-TASK-304 flat shape, which "
170:                                         "cannot carry provenance")
171:         self.assertEqual(doc["schema"], P.SCHEMA)
172:         self.assertEqual(sorted(doc["modules"]), sorted(set(mods) |
173:                                                         set(doc["modules"])))
174:
175:
176: class TestTheHintIsStillOnlyAHint(unittest.TestCase):
177:     """TASK-304 changed the file's SHAPE. It may not have changed its power.
178:
179:     `tests/test_parallel_runner.py` holds "a hint may reorder the work, never
180:     select it" against the old shape. The same line is re-asserted here
181:     against the new one, because a richer file is exactly the kind of change
182:     that turns a sort key into a source of truth by accident.
183:     """
184:
185:     def test_reading_the_new_shape_yields_only_a_sort_key(self):
186:         mods, doc = _live()
187:         got = P.schedule(mods, P.load_durations())
188:         self.assertEqual(sorted(got), sorted(mods))
189:         self.assertEqual(len(got), len(mods))
```
