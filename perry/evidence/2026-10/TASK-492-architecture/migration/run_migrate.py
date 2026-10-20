import subprocess,os,sys
from pathlib import Path
base=Path(__file__).resolve().parent
for name in sys.argv[1:] or ['Perry','SkyTonight']:
 work=base/name
 cmd=['python3','tools/goals_decide_migrate.py','--source',str(work/'source'),'--root',str(work/'anchor'),'--store',str(work/'store.db'),'--work',str(work)]
 if os.environ.get('REHEARSE')=='1':cmd+=['--apply']
 p=subprocess.run(cmd,text=True,capture_output=True,env={**os.environ,'PERRY_HOME':os.getcwd(),'PERRY_KERNEL_TESTING':'1'})
 (work/('apply.log' if '--apply' in cmd else 'plan.log')).write_text(p.stdout+p.stderr)
 print(name,p.returncode,p.stdout[:2000])
