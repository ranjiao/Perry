# Executed integration helper

```python
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess
s=Path('/private/tmp/perry-scratch/integrate-okr-first/phase004')
root=Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/integrate-okr-first').resolve()
assert Path.cwd().resolve()==root
allocation=json.loads((s/'allocation.json').read_text())
base=allocation['base']
head=(s/'duration-commit.txt').read_text().strip()
full=json.loads((s/'full-invocation.json').read_text())
slow=json.loads((s/'slow-invocation.json').read_text())
assert full['exit_code']==0 and slow['exit_code']==0
receipt=json.loads((s/'merged-full/receipt.json').read_text())
assert receipt['base']=={'ref':base,'sha':base}
assert receipt['candidates']==[{'name':'delivery','ref':allocation['frozen_ref'],'sha':allocation['allocation']}]
def git(*args): return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
assert git('rev-parse','HEAD')==head
assert git('status','--porcelain')==''
assert git('rev-parse','main')==base
assert git('rev-parse',allocation['frozen_ref'])==allocation['allocation']
env=os.environ.copy()
env['TMPDIR']=slow['TMPDIR']
commands={
 'release-check-final.log':['env','-u','PYTHONPATH','-u','PERRY_PROJECT','-u','PERRY_HOME','python3','release/manage.py','check','--base',base,'--ref','HEAD'],
 'receipt-verification-final.log':['env','-u','PYTHONPATH','-u','PERRY_PROJECT','-u','PERRY_HOME','python3','tests/merge-check','--verify-receipt',str(s/'merged-full/receipt.json')],
 'diff-check-final.log':['git','diff','--check',base,head]}
checks={}
for name,cmd in commands.items():
 with (s/name).open('x') as log:
  p=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 checks[name]={'command':cmd,'exit_code':p.returncode}
 print(name+': exit '+str(p.returncode),flush=True)
 print((s/name).read_text(),flush=True)
 if p.returncode: raise SystemExit(p.returncode)
artifact=(root/'tests/durations.json').read_bytes()
assert artifact==(s/'merged-full/durations.json').read_bytes()
assert hashlib.sha256(artifact).hexdigest()==receipt['artifact_sha256']
prior=subprocess.check_output(['git','show',allocation['candidate']+':release/records.jsonl'])
assert (root/'release/records.jsonl').read_bytes().startswith(prior)
assert git('diff','--name-only',allocation['candidate'],head).splitlines()==['CHANGELOG.md','VERSION','release/records.jsonl','tests/durations.json']
assert subprocess.check_output(['git','diff','--no-ext-diff','--binary','--full-index','--find-renames',base,head])==(s/'final.diff').read_bytes()
assert git('status','--porcelain')==''
assert git('rev-parse','HEAD')==head and git('rev-parse','main')==base
assert git('rev-parse',allocation['frozen_ref'])==allocation['allocation']
checks.update(head=head,base=base,frozen=allocation['allocation'],main_unchanged=True,clean_tree=True,artifact_sha256=receipt['artifact_sha256'],time=datetime.datetime.now(datetime.timezone.utc).isoformat())
(s/'final-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
ansi=re.compile(r'\x1b\[[0-9;]*m')
def summary(name):
 text=ansi.sub('',(s/name).read_text())
 return next(line for line in text.splitlines() if re.match(r'^\d+ modules · \d+ tests · ',line))
slow_results=json.loads((s/'slow-results.json').read_text())
assert slow_results['workers']==4
assert all(m['rc']==0 for m in slow_results['modules'])
full_summary=summary('merged-full.log')
slow_summary=summary('slow.log')
report=f"""# First-OKR integration support result

Outcome: PASS for the requested release allocation, merged-full gate, artifact import, receipt verification and separate slow gate. Candidate prepared on the isolated integration branch; main integration remains PMO responsibility.

## Exact references

- Repository checkout: `{root}`
- Branch: `codex/integrate-okr-first-20260917`
- Actual main/base: `{base}` (unchanged)
- Supplied candidate: `{allocation['candidate']}`
- Release allocation commit: `{allocation['allocation']}`
- Frozen ref: `{allocation['frozen_ref']}` -> `{allocation['allocation']}` (created once, never moved)
- Final head / duration-only commit: `{head}`
- Full tested tree: `{receipt['tree']}`

## Release allocation and scope

Allocated exactly one patch: **0.1.8 -> 0.1.9**, date `2026-09-17`, phase `004-guided`, task `TASK-466`, delivery `TASK-466-first-okr-response-propagation-20260917`, integrator `pmo-agent`. Existing allocations 0.1.6/TASK-447, 0.1.7/TASK-455 and 0.1.8/TASK-446 were retained, never allocated again. All previous canonical record bytes were preserved.

Authored notes: First-OKR conversations now carry user corrections through dependent KR, threshold and commitment proposals, preserve accepted facts and rejected suggestions, and choose the next consequential unresolved gap. Replacement targets remain proposals until accepted, within the existing eight-question draft budget.

Upgrade: `None.` Breaking: `None.` This delivery claims no persisted editable planning drafts or phase-route implementation.

Only `release/records.jsonl`, `VERSION`, `CHANGELOG.md` were changed by `release/manage.py` and committed in the allocation commit. Only `tests/durations.json` was changed in the second commit, copied byte-for-byte from the successful full receipt's artifact. The complete session delta from the supplied candidate is exactly those four paths. No implementation or PMO state writes.

## Gate receipts

| Gate | Outcome | Count / evidence |
|---|---|---|
| Merged full, one invocation | PASS, exit 0 | {full_summary}; [log](merged-full.log), [invocation](full-invocation.json), [receipt](merged-full/receipt.json) |
| Receipt after import | PASS, exit 0 | 1 module / 27 tests; [log](receipt-verification-after-import.log) |
| Separate slow, one invocation | PASS, exit 0 | {slow_summary}; [log](slow.log), [typed results](slow-results.json), [invocation](slow-invocation.json) |
| Final release check against exact base | PASS, exit 0 | [log](release-check-final.log) |
| Final receipt verification at final head | PASS, exit 0 | [log](receipt-verification-final.log) |
| Full diff whitespace check | PASS, exit 0 | [log](diff-check-final.log) |

Full and slow ran sequentially with four workers, each under an isolated canonical TMPDIR. All suite stages including schema, script checks, sample-project lint and the tree guard passed. Fixture lint warnings remain visible in the logs; no failed gate was waived or attributed away. The documented receipt verifier internally prints its default pool capacity of eight, but selects one provenance module and submits one worker job; it ran separately from both suites. No additional full run occurred.

Full command:

```text
{' '.join(full['command'])}
```

Slow command:

```text
{' '.join(slow['command'])}
```

The exact receipt mapping remains `base={base}` and `delivery={allocation['frozen_ref']}@{allocation['allocation']}`. The documented verification command is:

```text
{' '.join(commands['receipt-verification-final.log'])}
```

The original emitted receipt is retained unchanged; its original `artifact_verified: false` field is not rewritten. Successful post-import and final verification are evidenced by the separate verifier logs and `final-checks.json`.

Duration SHA-256: `{receipt['artifact_sha256']}`. The emitted and committed files match exactly. Full refreshed 154 measured modules and preserved four deferred harness-module entries; slow tested all 158 modules without re-recording timings.

## Final diff evidence

- [Complete binary-capable full-index diff](final.diff)
- [Name/status](final-name-status.txt), [modes and object IDs](final-modes.txt), [summary](final-summary.txt), [stat](final-stat.txt)
- [Base tree](final-tree-base.txt), [head tree](final-tree-head.txt)
- [Final checks](final-checks.json)

Diff SHA-256: `{hashlib.sha256((s/'final.diff').read_bytes()).hexdigest()}`. There are 15 modified paths across the inherited candidate plus these two commits, no additions/deletions/renames, and no mode changes. The long-cell repair `d403e9cb5775c968b6249fa186f6b3b91658a5ba` and first-OKR response change `33c88200590b991765dc0a98fb32be0d98585c7c` are ancestors of the final head.

## Architecture trigger selection

"""
report+=(s/'architecture-triggers.md').read_text().split('Authority:',1)[1]
report+="""

## Handoff boundary

Final worktree is clean. Main remains at the exact supplied base, and the frozen ref remains at the allocation commit. No push, tag, publication, main merge, real human interview, task closure, V5 or self-awarded compliance occurred. PMO owns final main integration and any newly required independent review if the candidate changes.
"""
with (s/'result.md').open('x') as f: f.write(report)
print(full_summary,flush=True)
print(slow_summary,flush=True)
print('Result: '+str(s/'result.md'),flush=True)

```
