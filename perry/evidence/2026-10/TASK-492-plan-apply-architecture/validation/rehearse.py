import hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
scratch=Path(__file__).parent.resolve()/'final';scratch.mkdir(); home=Path.cwd()
spec=importlib.util.spec_from_file_location('apply_helper',home/'tools/goals_decide_migrate.py');M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M;spec.loader.exec_module(M)
pinned=Path('/Users/bytedance/.codex/worktrees/goals-decide-kernel/Perry')
assert subprocess.check_output(['git','-C',str(pinned),'rev-parse','HEAD'],text=True).strip()=='1c5ccd851aec14d6d2e524b8237f508b1efde4f0'
base=Path('/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/task-492.HqROWV')
for name,sr in [('Perry','perry'),('SkyTonight','doc/perry')]:
 work=scratch/(name+'-native'); work.mkdir();source=work/'source';old=base/(name+'-final');oldplan=json.loads((old/'plan.json').read_text())
 for rel in oldplan['source_hashes']:
  dest=source/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/'source'/rel,dest)
 root=work/'anchor';(root/'.perry').mkdir(parents=True)
 shutil.copytree(old/'source'/sr/'export',root/sr/'export')
 k=M.Kernel(root,work/'store.db');k.call('import',{'state_root':sr}); before=k.items();events=k.call('events',{'limit':100000})['result']['events']
 (work/'before-items.json').write_text(M.encoded(before))
 prepare="""import json,sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1]+'/tools')\nimport goals_decide_migrate as P\np=P.Plan(Path(sys.argv[2])).build(json.loads(Path(sys.argv[3]).read_text()))\nPath(sys.argv[4]).write_text(P.encoded(p.document())+'\\n')\n"""
 env={k:v for k,v in os.environ.items() if k not in ('PERRY_HOME','PERRY_PROJECT','PERRY_STORE')};env.update(PYTHONDONTWRITEBYTECODE='1',PERRY_KERNEL_TESTING='1')
 subprocess.run([sys.executable,'-B','-c',prepare,str(pinned),str(source),str(work/'before-items.json'),str(work/'plan.json')],env=env,check=True,capture_output=True,text=True)
 sha=M.digest((work/'plan.json').read_bytes()); plan=M.Plan(work/'plan.json',sha)
 args=[sys.executable,str(home/'tools/goals_decide_migrate.py'),'--plan',str(work/'plan.json'),'--plan-sha256',sha,'--root',str(root),'--store',str(work/'store.db'),'--work',str(work)]
 receipt=dict(helper_sha256=M.digest((home/'tools/goals_decide_migrate.py').read_bytes()),project=name,preparer='1c5ccd851aec14d6d2e524b8237f508b1efde4f0',plan_sha256=sha,source=str(source),starting_items=len(before),starting_events=len(events),counts=plan._doc['counts'])
 for mode in ['--dry-run','--apply','--apply']:
  run=subprocess.run(args+[mode],text=True,capture_output=True,env=env)
  attempt=len(receipt.get('attempts',[]));(work/f'cli-{attempt}.log').write_text(run.stdout+run.stderr)
  value=json.loads(run.stdout);receipt.setdefault('attempts',[]).append(value)
  if run.returncode:raise RuntimeError((name,mode,value.get('error')))
  if mode=='--dry-run':assert k.items()==before and k.call('events',{'limit':100000})['result']['events']==events
 after={i['id']:i for i in k.items()};assert all(after[i['id']]==i for i in before)
 assert k.call('events',{'limit':100000})['result']['events'][:len(events)]==events
 assert receipt['attempts'][1]['store_seq']==receipt['attempts'][2]['store_seq']
 export=root/sr/'export'; expected={p.name:p.read_bytes() for p in export.iterdir()}
 replay=work/'replay';(replay/'.perry').mkdir(parents=True);shutil.copytree(export,replay/sr/'export')
 rk=M.Kernel(replay,work/'replay.db');rk.call('import',{'state_root':sr});rk.call('export')
 assert expected=={p.name:p.read_bytes() for p in (replay/sr/'export').iterdir()}
 receipt.update(original_items_exact=True,original_event_prefix_exact=True,idempotent=True,replay_byte_identical=True,export_hashes={n:M.digest(b) for n,b in expected.items()})
 (work/'verification.json').write_text(json.dumps(receipt,ensure_ascii=True,indent=2));print(name,sha,receipt['counts'],flush=True)
