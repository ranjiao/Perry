from pathlib import Path
import shutil,sqlite3,subprocess,json,hashlib
base=Path('/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/task-492.HqROWV')
receipts=[]
for name,sr in [('Perry','perry'),('SkyTonight','doc/perry')]:
 src=Path('/Users/bytedance/proj')/name; work=base/name;work.mkdir(exist_ok=True)
 copied=work/'source';copied.mkdir(exist_ok=True)
 for path in [sr,'.perry']:
  shutil.copytree(src/path,copied/path,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.db','*.db-wal','*.db-shm'))
 root=work/'anchor';(root/'.perry').mkdir(parents=True,exist_ok=True)
 common=Path(subprocess.check_output(['git','rev-parse','--path-format=absolute','--git-common-dir'],cwd=src,text=True).strip())
 db=common/'perry/root.db'
 print(name,db,db.exists())
 with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(work/'store.db') as dst:source.backup(dst)
 receipts.append({'source':str(src),'source_copy':str(copied),'scratch_root':str(root),'scratch_store':str(work/'store.db'),'native_source':str(db),'method':'sqlite read-only online backup; no source SQL writes','source_git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=src,text=True).strip()})
(base/'copies.json').write_text(json.dumps(receipts,indent=2)+'\n')
