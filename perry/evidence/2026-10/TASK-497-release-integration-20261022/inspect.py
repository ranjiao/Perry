from pathlib import Path
import subprocess,json,hashlib,re
run=Path(__file__).parent
root=Path('/Users/bytedance/.codex/worktrees/design024-release-integration/Perry')
base='3f663a10379a9bf9d2b33678e8950456bddfbbdf';source='3fb8839723c7b744ff610d837f3ab47c3adc33b9';sourcebase='89219446bb50cb7faef2249708d48e9225b5422b';head='c4fbc75de7ea067e9360d9df7a74b7ebe3fe5934'
def git(*args):return subprocess.check_output(['git',*args],cwd=root)
def blob(ref,p):return git('show',f'{ref}:{p}')
prior=json.loads((root/'perry/evidence/2026-10/TASK-497-conformance/review-round-2/independent-static.json').read_text());paths=prior['product_paths']
protected=git('ls-tree','-r','--name-only','-z',sourcebase,'kernel','bin','tools','templates/process','ARCHITECTURE.md','.perry/safety.json').decode().rstrip('\0').split('\0')
report={'base':base,'source_base':sourcebase,'source':source,'candidate':head,'tree':git('rev-parse',f'{head}^{{tree}}').decode().strip(),'product_paths':paths,'source_identity':{p:{'sha256':hashlib.sha256(blob(source,p)).hexdigest(),'identical':blob(source,p)==blob(head,p)}for p in paths},'protected_count':len(protected),'protected_mismatches':[p for p in protected if blob(sourcebase,p)!=blob(head,p)],'criteria':{k:{'sha256':hashlib.sha256(blob(head,f'perry/evidence/2026-10/{k}-spec.md')).hexdigest(),'unchanged':blob(source,f'perry/evidence/2026-10/{k}-spec.md')==blob(head,f'perry/evidence/2026-10/{k}-spec.md')} for k in ['TASK-497','TASK-498','TASK-499','TASK-500']},'main_archive_changed':[p for p in git('diff','--name-only',base,head,'perry').decode().splitlines()],'old_release_bytes_preserved':blob(head,'release/records.jsonl').startswith(blob(base,'release/records.jsonl'))}
changed=git('diff','--name-only',base,head).decode().splitlines();report['changed_paths']=changed;report['unexpected_paths']=sorted(set(changed)-set(paths)-{'VERSION','CHANGELOG.md','release/records.jsonl'})
links=[]
for p in paths:
 for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',(root/p).read_text()):
  target=target.split('#')[0]
  if not target or ':' in target or target.startswith('{'):continue
  links.append({'source':p,'target':target,'exists':(root/p).parent.joinpath(target).exists()})
report['local_links']=links
(run/'source-identity.json').write_text(json.dumps(report,indent=2)+'\n')
assert len(paths)==24 and len(protected)==74 and all(v['identical'] for v in report['source_identity'].values()) and not report['protected_mismatches'] and not report['unexpected_paths'] and not report['main_archive_changed'] and report['old_release_bytes_preserved'] and all(v['unchanged'] for v in report['criteria'].values()) and all(x['exists']for x in links)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_identity','local_links','criteria','product_paths','changed_paths']},indent=2));print('product24 protected74 links',len(links))
