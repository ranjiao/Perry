# Executed integration helper

```python
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, tempfile
scratch=Path('/private/tmp/perry-scratch/integrate-okr-first/phase004')
root=Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/integrate-okr-first').resolve()
assert Path.cwd().resolve()==root
base='d345fe4e0c3c61d890926a64339b2d119c845acc'
allocation=json.loads((scratch/'allocation.json').read_text())
assert json.loads((scratch/'full-invocation.json').read_text())['exit_code']==0
receipt=json.loads((scratch/'merged-full/receipt.json').read_text())
assert receipt['status']=='green' and receipt['tier']=='full'
assert receipt['base']=={'ref':base,'sha':base}
assert receipt['candidates']==[{'name':'delivery','ref':allocation['frozen_ref'],'sha':allocation['allocation']}]
def run(*args):
 p=subprocess.run(args,cwd=root,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 print(p.stdout,end='',flush=True)
 return p.stdout.strip()
assert run('git','status','--porcelain')==''
assert run('git','rev-parse','HEAD')==allocation['allocation']
assert run('git','rev-parse',allocation['frozen_ref'])==allocation['allocation']
assert run('git','rev-parse','main')==base
artifact=scratch/'merged-full/durations.json'
assert hashlib.sha256(artifact.read_bytes()).hexdigest()==receipt['artifact_sha256']
shutil.copyfile(artifact,root/'tests/durations.json')
assert artifact.read_bytes()==(root/'tests/durations.json').read_bytes()
assert run('git','diff','--name-only')=='tests/durations.json'
run('git','diff','--check')
run('git','add','--','tests/durations.json')
assert run('git','diff','--cached','--name-only')=='tests/durations.json'
run('git','diff','--cached','--check')
run('git','commit','-m','test: record verified first-OKR integration timings')
head=run('git','rev-parse','HEAD')
(scratch/'duration-commit.txt').write_text(head+'\n')
verify=['env','-u','PYTHONPATH','-u','PERRY_PROJECT','-u','PERRY_HOME','python3','tests/merge-check','--verify-receipt',str(scratch/'merged-full/receipt.json')]
with (scratch/'receipt-verification-after-import.log').open('x') as log:
 p=subprocess.run(verify,cwd=root,stdout=log,stderr=subprocess.STDOUT)
print((scratch/'receipt-verification-after-import.log').read_text(),flush=True)
(scratch/'receipt-verification-after-import.json').write_text(json.dumps({'command':verify,'head':head,'exit_code':p.returncode,'base':receipt['base'],'candidates':receipt['candidates']},indent=2)+'\n')
if p.returncode: raise SystemExit(p.returncode)
env=os.environ.copy()
env['TMPDIR']=str(Path(tempfile.mkdtemp(prefix='slow-tmp-',dir=scratch)).resolve())
cmd=['env','-u','PYTHONPATH','-u','PERRY_PROJECT','-u','PERRY_HOME','bash','tests/run','--tier','slow','--workers','4','--results',str(scratch/'slow-results.json')]
meta={'command':cmd,'cwd':str(root),'TMPDIR':env['TMPDIR'],'head':head,'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(scratch/'slow-invocation.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Running one slow gate; log: '+str(scratch/'slow.log'),flush=True)
with (scratch/'slow.log').open('x') as log:
 result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta.update(exit_code=result.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(scratch/'slow-invocation.json').write_text(json.dumps(meta,indent=2)+'\n')
print('slow exit: '+str(result.returncode),flush=True)
print((scratch/'slow.log').read_text()[-5000:],flush=True)
raise SystemExit(result.returncode)

```
