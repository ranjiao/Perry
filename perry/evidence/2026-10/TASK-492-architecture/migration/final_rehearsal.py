import json,os,sqlite3,subprocess,shutil,hashlib
from pathlib import Path
base=Path(__file__).resolve().parent
home=Path.cwd()
for name,sr in [('Perry','perry'),('SkyTonight','doc/perry')]:
 old=base/name;work=base/(name+'-verified');work.mkdir(exist_ok=True)
 shutil.copytree(old/'source',work/'source',dirs_exist_ok=True)
 root=work/'anchor';(root/'.perry').mkdir(parents=True,exist_ok=True)
 live=Path('/Users/bytedance/proj')/name/'.git/perry/root.db'
 store=work/'store.db'
 if not store.exists():
  with sqlite3.connect(live.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(store) as dst:src.backup(dst)
 sys_path=str(home/'tools')
 import sys
 sys.path.insert(0,sys_path)
 import goals_decide_migrate as M
 k=M.Kernel(root,store)
 before=k.items();ev=k.call('events',{'limit':100000})['result']['events']; seq=k.call('query',{'limit':1})['store_seq']
 (work/'before-items.json').write_text(M.encoded(before)+'\n');(work/'before-events.json').write_text(M.encoded(ev)+'\n')
 cmd=['python3','tools/goals_decide_migrate.py','--source',str(work/'source'),'--root',str(root),'--store',str(store),'--work',str(work)]
 p=subprocess.run(cmd+['--dry-run'],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(home),'PERRY_KERNEL_TESTING':'1'})
 (work/'dry-run.log').write_text(p.stdout+p.stderr)
 if p.returncode:print(name,'plan refused',p.stdout);continue
 assert k.items()==before and k.call('events',{'limit':100000})['result']['events']==ev
 receipt={'source_copy':str(work/'source'),'scratch_root':str(root),'scratch_store':str(store),'old_item_count':len(before),'old_event_count':len(ev),'dry_run_store_unchanged':True,'starting_store_seq':seq}
 p=subprocess.run(cmd+['--apply'],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(home),'PERRY_KERNEL_TESTING':'1'})
 (work/'apply.log').write_text(p.stdout+p.stderr)
 receipt['apply_exit']=p.returncode;receipt['apply_result']=json.loads(p.stdout)
 if p.returncode:
  receipt['refusal_store_unchanged']=k.items()==before and k.call('events',{'limit':100000})['result']['events']==ev
 else:
  original_after={i['id']:i for i in k.items()}; assert all(original_after[i['id']]==i for i in before)
  assert k.call('events',{'limit':100000})['result']['events'][:len(ev)]==ev
  receipt['original_items_events_exact']=True
  first={p.name:p.read_bytes() for p in (root/sr/'export').iterdir()}
  p=subprocess.run(cmd+['--apply'],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(home),'PERRY_KERNEL_TESTING':'1'})
  (work/'idempotent.log').write_text(p.stdout+p.stderr)
  assert p.returncode==0,p.stdout+p.stderr
  receipt['idempotency']=json.loads(p.stdout);assert receipt['idempotency']['commands'] is None
  assert first=={p.name:p.read_bytes() for p in (root/sr/'export').iterdir()}
  restored=work/'replay';(restored/'.perry').mkdir(parents=True,exist_ok=True)
  shutil.copytree(root/sr/'export',restored/sr/'export',dirs_exist_ok=True)
  k2=M.Kernel(restored,work/'replay.db');k2.call('import',{'state_root':sr});k2.call('export')
  assert first=={p.name:p.read_bytes() for p in (restored/sr/'export').iterdir()}
  receipt['replay_export_byte_identical']=True
  try:k2.call('import',{'state_root':sr})
  except M.Refused as exc:receipt['repeat_import_refused']='store_not_empty' in str(exc)
  else:raise AssertionError('nonempty import allowed')
 plan=json.loads((work/'plan.json').read_text())
 actual=Path('/Users/bytedance/proj')/name
 mismatch=[]
 for rel,h in plan['source_hashes'].items():
  path=actual/rel
  if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=h:mismatch.append(rel)
 receipt['actual_source_hash_mismatches']=mismatch
 receipt['source_counts']=plan['counts'];receipt['filename_ceilings']=plan['prefix_ceilings']
 (work/'verification.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
 print(name, {key:value for key,value in receipt.items() if key not in ['apply_result','idempotency']})
