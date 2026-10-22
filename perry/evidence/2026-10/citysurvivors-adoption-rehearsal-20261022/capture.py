import collections, datetime, hashlib, json, os, re, shutil, subprocess
from pathlib import Path

RUN=Path(__file__).parent
SRC=Path('/Users/bytedance/proj/wargame/CitySurvivors')
OUT=RUN/'source-capture'
FILES=['AGENTS.md','README.md','todo.md','docs/README.md',
 'docs/tech/README.md','docs/tech/todo.md','docs/art/README.md','docs/art/todo.md',
 'docs/design/README.md','docs/design/prototype-scope.md','docs/design/game-design.md',
 'docs/decisions/README.md','docs/production/documentation-standard.md',
 'docs/production/project-structure.md','docs/production/documentation-handoff.md',
 'docs/tech/current-build.md','docs/tech/cbd-path-recovery.md',
 'docs/tech/cbd-pressure.md','docs/tech/m1-cbd-integration.md',
 'docs/production/m1-cbd-handoff.md','docs/production/m1-rule-fixes-handoff.md',
 'docs/art/evidence/2026-10-22-documentation-review.md',
 'docs/tech/evidence/2026-10-22-documentation-review.md',
 'docs/tech/evidence/classification.md',
 'docs/design/m1-combat-test-matrix.md','docs/qa/2026-10-21-cbd-pressure-validation.md',
 'docs/tech/asset-integration.md','docs/tech/ui-layout-contract.md',
 'docs/tech/hud-layout-editor.md','docs/art/asset-delivery.md',
 'docs/decisions/ADR-013-first-milestone-wave-defense.md',
 'docs/decisions/ADR-022-documentation-governance.md',
 'docs/decisions/ADR-024-six-character-attack-mechanics.md',
 'game/README.md','game/assets/runtime-manifest.json','assets/manifest.md']

def git(*args):
 p=subprocess.run(['git','-C',str(SRC),*args],capture_output=True)
 assert p.returncode==0,p.stderr
 return p.stdout

OUT.mkdir(exist_ok=False)
status=git('status','--no-renames','--porcelain','-z')
(RUN/'source-status-before.bin').write_bytes(status)
records=[]; unavailable=[]
for rel in FILES:
 p=SRC/rel
 if not p.is_file():unavailable.append(rel);continue
 assert not p.is_symlink() and p.resolve().is_relative_to(SRC.resolve()),rel
 b=p.read_bytes();target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 records.append({'path':rel,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),
                 'untracked':bool(git('ls-files','--others','--exclude-standard','--',rel))})
changed=[r['path'] for r in records if hashlib.sha256((SRC/r['path']).read_bytes()).hexdigest()!=r['sha256']]
manifest={'source_root':str(SRC),'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'head':git('rev-parse','HEAD').decode().strip(),'source_status_sha256':hashlib.sha256(status).hexdigest(),
 'entries':records,'unavailable':unavailable,'changed_during_capture':changed,
 'bounds':'Finite governance/task/reference capture only. All selected tracked/untracked bytes retained. This is not a full code/asset backup or engine acceptance subject; excluded .git, binary assets, generated output, credentials and unrelated files. Live activation requires a new coherent comparison and separately bounded backup.'}
assert not changed,changed
(RUN/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

tables=[]
for file,prefix in [('todo.md','CS'),('docs/art/todo.md','ART'),('docs/tech/todo.md','DEV')]:
 lines=(OUT/file).read_text().splitlines();header=None;section='';rows=[]
 for n,line in enumerate(lines,1):
  if line.startswith('## '):section=line[3:];header=None
  if not line.startswith('|'):continue
  cells=[x.strip() for x in re.split(r'(?<!\\)\|',line)[1:-1]]
  if cells and cells[0]=='ID':header=cells;continue
  if not cells or not re.fullmatch(prefix+r'-\d+',cells[0]):continue
  assert header is not None,(file,n)
  assert len(cells)==len(header),(file,n,header,cells)
  d=dict(zip(header,cells));rows.append({'scope':file,'id':cells[0],'line':n,'section':section,'cells':d,'raw':line})
 tables+=rows
 (RUN/(prefix+'-rows.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(file,len(rows),'rows',len({r['id'] for r in rows}),'unique')
 for r in rows:
  d=r['cells'];state=next((v for k,v in d.items() if k.startswith('状态')),None)
  title=next((v for k,v in d.items() if '任务' in k or k in ['工作','所属包／工作','本批任务']), '')
  print(r['id'],r['line'],r['section'][:14],str(state)[:100],title[:45])
(RUN/'source-rows.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2)+'\n')
print('captured',len(records),'unavailable',unavailable)
