from pathlib import Path
import os,json,re,subprocess,sys,tempfile,hashlib,shutil,urllib.parse
root=Path('/Users/bytedance/proj/Perry');out=Path(Path('/tmp/perry-scratch/Perry/doc-audit-current').read_text());env={k:v for k,v in os.environ.items() if k not in ('PERRY_HOME','PERRY_PROJECT','PERRY_STORE','PERRY_KERNEL_TESTING')};env.update(PERRY_KERNEL_TESTING='1',PYTHONDONTWRITEBYTECODE='1')
project=Path(tempfile.mkdtemp(prefix='native-example-',dir=out));store=project/'fixture-native.db';(project/'.perry').mkdir();actor={'kind':'agent','name':'isolated-doc-example','session':'doc-audit-fixture-only'};receipts=[]
def call(command,body=None,ok=True):
 argv=[sys.executable,str(root/'bin/perry'),*command.split(),'--root',str(project),'--store',str(store)]
 if body is not None:argv+=['--input','-']
 p=subprocess.run(argv,input=json.dumps(body) if body is not None else None,capture_output=True,text=True,env=env);data=json.loads(p.stdout);assert data['ok']==ok,(command,data,p.stderr);assert (p.returncode==0)==ok
 receipts.append({'command':command,'input':body,'response':data});return data
call('init',{'actor':actor,'state_root':'perry'});call('template apply',{'actor':actor,'template':json.loads((root/'templates/process/perry.json').read_text())})
blocks=re.findall(r'```json\n(.*?)\n```',(root/'reference/kernel.md').read_text(),re.S);query=json.loads(blocks[0]);body=json.loads(blocks[1]);body['actor']=actor
for i in range(2):
 body['fields']['title']='Isolated documented task '+str(i);body['fields']['summary']='Check the documented native create/query example on a temporary store.';call('item create',body)
query['limit']=1;first=call('query',query);assert first['result']['total']==2 and first['result']['truncated'];next_query=dict(query,after=first['result']['next_after']);last=call('query',next_query);assert not last['result']['truncated'] and first['result']['items'][0]['id']!=last['result']['items'][0]['id']
# Shape success is never a fabricated human acceptance: V5 Agent closure must refuse.
body['fields']['verification']='V5';body['fields']['title']='Isolated V5 guard';item=call('item create',body)['result']['item'];seq=call('query',{'limit':0})['store_seq'];refused=call('item move',{'actor':actor,'id':item['id'],'transition':'done','expect':{item['id']:item['seq']},'set':{'evidence':'isolated fixture, no real acceptance'}},ok=False);assert refused['store_seq']==seq
# Validate the delivered role narrative with only its two mandatory safety sections.
role_project=Path(tempfile.mkdtemp(prefix='role-example-',dir=out));(role_project/'.perry/roles').mkdir(parents=True);policy=json.loads((root/'templates/internal/safety_POLICY_TEMPLATE.json').read_text());policy['approval_ref']='ISOLATED STRUCTURAL FIXTURE, NOT USER CONSENT';(role_project/'.perry/safety.json').write_text(json.dumps(policy))
role=(root/'work/templates/role_card_TEMPLATE.md').read_text();role=re.sub(r'\{\{[^}]*\}\}','fixture',role);role=role.replace('- Default rung: fixture','- Default rung: V3');role=re.sub(r'## Context\n.*?(?=## May touch)', '', role, flags=re.S);target=role_project/'.perry/roles/fixture.md';target.write_text(role)
def roles(expected):
 p=subprocess.run([sys.executable,str(root/'tools/roles.py'),'--root',str(role_project)],capture_output=True,text=True,env=env);d=json.loads(p.stdout);assert p.returncode==expected,(p.returncode,d);return d
positive=roles(0);target.write_text(role.split('## Must escalate')[0]);negative=roles(1);assert negative['errors']
# The dispatch scratch recipe must give distinct directories even with one project basename.
text=(root/'work/reference/dispatch.md').read_text();recipe=re.search(r'```sh\n(.*?)\n```',text,re.S)[1];paths=[]
for i in range(2):
 p=subprocess.run(['bash','-c',recipe+'\nprintf "%s\\n" "$PERRY_SCRATCH"'],cwd=root,capture_output=True,text=True,check=True,env=dict(env,TMPDIR=str(out)));paths.append(p.stdout.strip())
assert paths[0]!=paths[1] and all(Path(p).is_dir() and not Path(p).is_relative_to(root) for p in paths)
# Global checks of the entire finite shipped-document set.
before=json.loads((out/'inventory-before.json').read_text());broken=[];links=0;changed=[];after=[]
for record in before:
 name=record['path'];p=root/name;text=p.read_text();b=p.read_bytes();sha=hashlib.sha256(b).hexdigest();entry=dict(record,lines=len(text.splitlines()),sha256=sha);after.append(entry)
 if sha!=record['sha256']:changed.append(name)
 for target in re.findall(r'\]\(([^)\s]+)\)',text):
  if '://' in target or target.startswith(('#','mailto:')):continue
  target=urllib.parse.unquote(target.split('#')[0]);links+=1
  if target and not(p.parent/target).exists():broken.append({'path':name,'target':target})
assert not broken,broken
protected=json.loads((out/'protected.json').read_text());assert all((root/p).is_file() and hashlib.sha256((root/p).read_bytes()).hexdigest()==sha for p,sha in protected.items())
# No source logic or process declaration changes are part of this audit.
process_before=protected['templates/process/perry.json'];assert process_before==hashlib.sha256((root/'templates/process/perry.json').read_bytes()).hexdigest()
(out/'inventory-after.json').write_text(json.dumps(after,indent=2)+'\n');(out/'native-example-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n');(out/'role-example.json').write_text(json.dumps({'positive_without_Context_Loads':positive,'missing_safety_section_rejected':negative},indent=2)+'\n')
result={'documents_scanned':len(before),'changed_documents':changed,'local_links_checked':links,'broken_links':broken,'native_examples':'create and complete query pagination pass; agent V5 closure refused without mutation','role_examples':'optional Context/Loads omitted successfully; missing mandatory safety heading refuses','scratch_unique_directories':paths,'protected_source_project_files_byte_identical':len(protected),'process_template_unchanged':True,'self_audit_only':True};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'changed_documents':len(changed)},ensure_ascii=False))
