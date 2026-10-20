from pathlib import Path
import hashlib,json,os,subprocess,sys,tarfile,uuid
candidate=Path('/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry')
sys.path.insert(0,str(candidate/'kernel'))
from perry_kernel.paths import derived_store
backup=Path('/Users/bytedance/.codex/backups')/('perry-kernel-cutover-20261018-'+uuid.uuid4().hex[:10])
backup.mkdir(parents=True,mode=0o700)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def canonical(root,state):
 files=[root/'.perry/config.jsonl',root/'.perry/events.jsonl']+[root/state/(x+'.jsonl') for x in ['tasks','asks','risks','intake','cadence']]
 return {str(p.relative_to(root)):sha(p) if p.is_file() else None for p in files}
receipts=[]
for name,state in [('Perry','perry'),('SkyTonight','doc/perry')]:
 root=Path('/Users/bytedance/proj')/name
 before=canonical(root,state)
 db=derived_store(root)
 if db.exists():raise RuntimeError(f'Existing live kernel store needs separate inspection: {db}')
 target=backup/(name+'.tar')
 with tarfile.open(target,'w') as archive:
  archive.add(root/'.perry',arcname='.perry',recursive=True)
  archive.add(root/state,arcname=state,recursive=True)
 after=canonical(root,state)
 if after!=before:raise RuntimeError(f'Canonical state moved during backup: {name}')
 with tarfile.open(target,'r') as archive:
  members={x.name for x in archive.getmembers()}
  if '.perry/config.jsonl' not in members:raise RuntimeError('Incomplete backup')
 receipts.append({'project':str(root),'state_root':state,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'canonical':before,'live_store':str(db),'live_store_existed':False,'archive':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'verified_readable':True})
root=Path('/Users/bytedance/proj/aimark')
patch=subprocess.check_output(['git','diff','--binary','HEAD'],cwd=root)
(backup/'aimark-wip.patch').write_bytes(patch)
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
with tarfile.open(backup/'aimark-untracked.tar','w') as archive:
 for rel in filter(None,untracked):archive.add(root/rel,arcname=rel)
report={'date':'2026-10-18','backup_root':str(backup),'projects':receipts,'aimark_wip_sha256':hashlib.sha256(patch).hexdigest(),'aimark_untracked':list(filter(None,untracked)),'live_import_performed':False}
(backup/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
Path('/tmp/perry-scratch/Perry/cutover-20261018-backup-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'backup_root':str(backup),'verified_archives':[{'project':x['project'],'bytes':x['bytes'],'live_store_existed':x['live_store_existed']} for x in receipts],'aimark_untracked_count':len(report['aimark_untracked'])},indent=2))
