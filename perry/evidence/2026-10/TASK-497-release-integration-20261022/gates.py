from pathlib import Path
import subprocess,json,sys,time
run=Path(__file__).parent
root=Path('/Users/bytedance/.codex/worktrees/design024-release-integration/Perry')
def call(name,cmd):
 start=time.time();print(name,flush=True)
 with (run/(name+'.log')).open('w')as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
 (run/(name+'.json')).write_text(json.dumps({'command':cmd,'cwd':str(root),'exit':r.returncode,'seconds':time.time()-start,'log':str(run/(name+'.log'))},indent=2)+'\n')
 print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
if sys.argv[1]=='full':
 call('release-c4',['python3','release/manage.py','check','--base','3f663a10379a9bf9d2b33678e8950456bddfbbdf','--ref','c4fbc75de7ea067e9360d9df7a74b7ebe3fe5934'])
 call('direct-full',['bash','tests/run','--tier','full'])
else:
 head=sys.argv[1]
 call('release-final',['python3','release/manage.py','check','--base','3f663a10379a9bf9d2b33678e8950456bddfbbdf','--ref',head])
 call('merge-slow',['python3','tests/merge-check','--base','3f663a10379a9bf9d2b33678e8950456bddfbbdf','--candidate',head,'--tier','slow','--record',str(run/'merge-slow')])
 call('receipt-verify',['python3','tests/merge-check','--verify-receipt',str(run/'merge-slow/receipt.json')])
