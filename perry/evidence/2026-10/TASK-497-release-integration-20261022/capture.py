from pathlib import Path
import json,subprocess
run=Path(__file__).parent;root='/Users/bytedance/proj/Perry'
commands={'startup':['python3','tools/document_checks.py','startup','--root',root,'--state-root','perry'],'roles':['python3','tools/roles.py','--root',root],'affected-native':['bin/perry','query','--root',root,'--input',json.dumps({'ids':['TASK-497','TASK-498','TASK-499','TASK-500'],'limit':10})],'events':['bin/perry','events','--root',root,'--input',json.dumps({'items':['TASK-497','TASK-498','TASK-499','TASK-500'],'after_seq':1935,'limit':30})]}
for name,cmd in commands.items():
 r=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
 (run/(name+'.capture.json')).write_text(json.dumps({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
 assert r.returncode==0
 print(name,'pass')
