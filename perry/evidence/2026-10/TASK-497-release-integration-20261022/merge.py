from pathlib import Path
import subprocess,json
run=Path(__file__).parent;root=Path('/Users/bytedance/proj/Perry');base='3f663a10379a9bf9d2b33678e8950456bddfbbdf';head='c4fbc75de7ea067e9360d9df7a74b7ebe3fe5934'
def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
for name in ['direct-full','release-final','merge-slow','receipt-verify']:assert json.loads((run/(name+'.json')).read_text())['exit']==0,name
receipt=json.loads((run/'merge-slow/receipt.json').read_text());assert receipt['tree']==git('rev-parse',f'{head}^{{tree}}') and receipt['source_clean'] is True and receipt['exit_code']==0
assert git('branch','--show-current')=='main' and git('rev-parse','HEAD')==base and not git('status','--porcelain')
cmd=['git','merge','--no-ff',head,'-m','Integrate independently reviewed DESIGN-024 procedure contracts (0.1.30-0.1.32)']
r=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
(run/'actual-merge.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'base':base,'candidate':head},indent=2)+'\n')
assert r.returncode==0
merge=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}')
assert tree==receipt['tree'] and git('rev-parse','HEAD^1')==base and git('rev-parse','HEAD^2')==head
check=subprocess.run(['git','diff','--check',base,'HEAD'],cwd=root,text=True,capture_output=True);assert check.returncode==0
assert not git('status','--porcelain') and(root/'VERSION').read_text()=='0.1.32\n'
report={'base':base,'candidate':head,'merge':merge,'tree':tree,'receipt_tree_equal':True,'parents':[git('rev-parse','HEAD^1'),git('rev-parse','HEAD^2')],'version':'0.1.32','primary_branch':'main','clean':True,'diff_check':{'exit':check.returncode,'stdout':check.stdout,'stderr':check.stderr},'candidate_to_actual_tree_diff':git('diff','--name-only',head,merge)}
(run/'postmerge.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
