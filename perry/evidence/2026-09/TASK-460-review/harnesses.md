# Archived independent review harnesses

The reviewer originally ran these external Python files; the code blocks preserve them without introducing executable product files into the evidence tree.

## boundaries.py

```python
import sys, pathlib, subprocess, json, unittest, datetime
ROOT = pathlib.Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/review-task-460')
sys.path.insert(0, str(ROOT / 'tests'))
import test_next_section as t
class FixtureOwner(unittest.TestCase): pass
owner = FixtureOwner()
root = t.build(owner, 'closable_phase')
store = root / 'linkage.jsonl'
base = [r for r in map(json.loads, store.read_text().splitlines()) if r['kind'] in ('objective','kr')]
k1, k2, ks = [r['id'] for r in base if r['kind'] == 'kr']
for r in base:
    if r['kind'] == 'kr': r.update(current=1702, target=400)
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
def ck(k, direction='at_most', cid='c'):
    return t.check(cid, kr=k, direction=direction, target=1 if direction == 'done' else 400,
                   baseline=0 if direction == 'increase' else 1702 if direction == 'decrease' else None)
def ms(k,v,cid='c',due=False):
    return t.measurement(v, kr=k, cid=cid, asserted_at='2020-01-01T00:00:00Z' if due else stamp)
def run(name, extra, expected, closed=False, states=None):
    store.write_text(t.jsonl(base + extra))
    p = subprocess.run([str(ROOT/'bin/perry-state'), '--root', str(root), '--json'], capture_output=True, text=True)
    assert p.returncode == 0, (name,p.stderr)
    data = json.loads(p.stdout)
    counts, why = t.STATE.next_kr_progress(data)
    assert counts == dict(zip(('commit_total','measured','met','unmeasured'),expected)), (name,counts)
    assert ('R-phase-closable' in t.recommended(data['next'])) == closed, name
    actual = [(k['state'],k['met']) for o in data['linkage']['objectives'] for k in o['krs']]
    if states: assert actual[:len(states)] == states, (name,actual)
    print(json.dumps(dict(case=name,counts=counts,states=actual,closable=closed)),flush=True)
try:
    run('legacy_only', [], (2,0,0,2), states=[('undeclared',None)]*2)
    run('zero_measured', [ck(k1),ck(k2)], (2,0,0,2), states=[('unmeasured',None)]*2)
    run('half_measured', [ck(k1),ck(k2),ms(k1,400)], (2,1,1,1))
    run('all_met_with_due_and_unmeasured_stretch', [ck(k1),ck(k2),ms(k1,400),ms(k2,399,due=True),ck(ks)], (2,2,2,0), True, [('measured',True),('due',True)])
    for d in ('at_most','decrease','at_least','increase','done'):
        for v in (1702,400,399,1,0):
            met = v <= 400 if d in ('at_most','decrease') else v == 1 if d == 'done' else v >= 400
            run(f'{d}_{v}', [ck(k1,d),ms(k1,v),ck(k2),ms(k2,400)], (2,2,1+int(met),0), met)
    run('missing_required_check_with_other_KR_met', [ck(k1),ms(k1,400),ck(k1,cid='b'),ck(k2),ms(k2,400)], (2,1,1,1), states=[('unmeasured',None)])
    run('one_failed_check', [ck(k1),ms(k1,400),ck(k1,cid='b'),ms(k1,1702,'b'),ck(k2),ms(k2,400)], (2,2,1,0))
    run('all_checks_met', [ck(k1),ms(k1,400),ck(k1,cid='b'),ms(k1,399,'b'),ck(k2),ms(k2,400)], (2,2,2,0), True)
    for name, content in [('invalid_json','{invalid\n'),('missing_store',None),('wrong_phase', t.jsonl([dict(r,phase='002-other') for r in base]))]:
        if content is None: store.unlink()
        else: store.write_text(content)
        p = subprocess.run([str(ROOT/'bin/perry-state'),'--root',str(root),'--json'],capture_output=True,text=True)
        assert p.returncode == 0, (name,p.stderr)
        data=json.loads(p.stdout)
        assert 'R-phase-closable' not in t.recommended(data['next']),name
        print(json.dumps(dict(case=name,exit=p.returncode,counts=t.STATE.next_kr_progress(data))),flush=True)
    (root/'phase'/'CURRENT').unlink()
    p=subprocess.run([str(ROOT/'bin/perry-state'),'--root',str(root),'--json'],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    data=json.loads(p.stdout)
    assert 'R-phase-closable' not in t.recommended(data['next'])
    print(json.dumps(dict(case='no_phase',exit=p.returncode,counts=t.STATE.next_kr_progress(data))),flush=True)
finally:
    owner.doClassCleanups()

```

## mutate.py

```python
import ast, pathlib, subprocess, hashlib, shutil, time, json
root=pathlib.Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/review-task-460')
out=pathlib.Path('/tmp/perry-scratch/review-task-460/phase004')
base='7ffcc6337bc5c8b31d2e8992c251e23299bff1ea'
head='cb310d87587e4c4fb841620d38209b2394e0e618'
p=root/'bin/perry-state'
def committed(ref): return subprocess.check_output(['git','show',f'{ref}:bin/perry-state'],cwd=root)
def span(s):
    nodes=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='next_kr_progress']
    assert len(nodes)==1
    return nodes[0].lineno-1,nodes[0].end_lineno
def caches():
    for folder in root.rglob('__pycache__'): shutil.rmtree(folder)
    time.sleep(1.1)
truth=committed(head)
assert p.read_bytes()==truth
old=committed(base).decode(); new=truth.decode()
a,b=span(new); c,d=span(old)
mutated=''.join(new.splitlines(keepends=True)[:a]+old.splitlines(keepends=True)[c:d]+new.splitlines(keepends=True)[b:])
print(json.dumps(dict(mutation='replace only next_kr_progress from base',candidate_lines=[a+1,b],base_lines=[c+1,d],head=head,base=base)),flush=True)
try:
    p.write_text(mutated)
    caches()
    with (out/'mutation-affected.log').open('w') as log:
        rc=subprocess.run(['python3','tests/parallel','--tier','affected','--base',base,'-j','4'],cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
    print(f'mutation_affected_exit={rc}',flush=True)
    assert rc != 0, 'mutation survived affected tier'
finally:
    p.write_bytes(committed(head))
    caches()
    reference=committed(head)
    assert p.read_bytes()==reference
    print(json.dumps(dict(restored_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),git_show_sha256=hashlib.sha256(reference).hexdigest())),flush=True)
with (out/'restored-targeted.log').open('w') as log:
    rc=subprocess.run(['python3','tests/parallel','test_next_section','test_kr_checks','-j','4'],cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
print(f'restored_targeted_exit={rc}',flush=True)
assert rc==0

```
