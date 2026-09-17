# Executed integration helper

```python
from pathlib import Path
import datetime, json, os, subprocess, tempfile
scratch=Path('/private/tmp/perry-scratch/integrate-okr-first/phase004')
root=Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/integrate-okr-first').resolve()
assert Path.cwd().resolve()==root
assert not (scratch/'merged-full').exists()
env=os.environ.copy()
env['TMPDIR']=str(Path(tempfile.mkdtemp(prefix='full-tmp-',dir=scratch)).resolve())
cmd=['env','-u','PYTHONPATH','-u','PERRY_PROJECT','-u','PERRY_HOME','python3','tests/merge-check','--base','d345fe4e0c3c61d890926a64339b2d119c845acc','delivery=codex/okr-first-gate-input-20260917','--tier','full','-j','4','--record',str(scratch/'merged-full')]
meta={'command':cmd,'cwd':str(root),'TMPDIR':env['TMPDIR'],'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(scratch/'full-invocation.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Running one merged-full gate; log: '+str(scratch/'merged-full.log'),flush=True)
with (scratch/'merged-full.log').open('x') as log:
 result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta.update(exit_code=result.returncode,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
(scratch/'full-invocation.json').write_text(json.dumps(meta,indent=2)+'\n')
print('merged-full exit: '+str(result.returncode),flush=True)
print((scratch/'merged-full.log').read_text()[-14000:],flush=True)
raise SystemExit(result.returncode)

```
