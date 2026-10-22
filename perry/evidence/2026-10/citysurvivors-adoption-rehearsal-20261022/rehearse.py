"""Finite one-run audit driver. Explicit isolated roots/stores only; no live mode."""
import argparse, collections, gzip, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run',required=True,help='New external directory; must not exist')
parser.add_argument('--bundle',required=True,help='Read-only authored migration bundle')
parser.add_argument('--perry',default='/Users/bytedance/proj/Perry')
args=parser.parse_args()
RUN=Path(args.run).resolve()
PERRY=Path(args.perry).resolve()
SOURCE=Path('/Users/bytedance/proj/wargame/CitySurvivors').resolve()
OUT=Path(args.bundle).resolve()
assert not RUN.exists() and not RUN.is_relative_to(SOURCE) and not RUN.is_relative_to(PERRY)
assert not RUN.is_relative_to(OUT) and not OUT.is_relative_to(RUN)
RUN.mkdir(parents=True)
EVID=RUN/'evidence'; EVID.mkdir(exist_ok=False)
PLAN=json.loads((OUT/'mapping-plan.json').read_text())
RECORDS=PLAN['records']; SOURCES={r['id']:r for r in RECORDS}
CAPTURE=RUN/'restored-source-capture'
shutil.copytree(OUT/'source-capture',CAPTURE)
assert hashlib.sha256((OUT/'source-storage.json').read_bytes()).hexdigest()==PLAN['source_storage_sha256']
for relative,entry in json.loads((OUT/'source-storage.json').read_text()).items():
 target=(CAPTURE/relative).resolve();archive=(OUT/entry['artifact']).resolve()
 assert target.is_relative_to(CAPTURE) and archive.is_relative_to(OUT) and not target.exists()
 assert entry['encoding']=='gzip' and hashlib.sha256(archive.read_bytes()).hexdigest()==entry['archive_sha256']
 data=gzip.decompress(archive.read_bytes());assert hashlib.sha256(data).hexdigest()==entry['source_sha256']
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
def validate_capture(folder):
 manifest=json.loads((OUT/'source-manifest.json').read_text())
 assert hashlib.sha256((OUT/'source-manifest.json').read_bytes()).hexdigest()==PLAN['source_manifest_sha256'], 'manifest changed'
 assert hashlib.sha256((PERRY/'templates/process/perry.json').read_bytes()).hexdigest()==PLAN['template_sha256'], 'process template changed'
 for entry in manifest['entries']:
  path=(folder/entry['path']).resolve()
  assert path.is_relative_to(folder.resolve()) and path.is_file(), 'source root/reference escape'
  assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'], 'captured source changed: '+entry['path']
validate_capture(CAPTURE)
ACTOR={'kind':'agent','name':'CitySurvivors isolated rehearsal work','session':os.environ['CODEX_THREAD_ID']}
ENV={k:v for k,v in os.environ.items() if k not in ('PERRY_STORE','PERRY_PROJECT','PERRY_HOME')}
ENV['PERRY_KERNEL_TESTING']='1'
N=0; COMMANDS=[]

def save(name,value):
 p=EVID/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return p

def checked(root,store):
 root=root.resolve();store=store.resolve()
 assert root.is_relative_to(RUN) and store.is_relative_to(RUN)
 assert root!=SOURCE and not root.is_relative_to(SOURCE)
 assert (root/'REHEARSAL-ONLY').is_file()

def call(root,store,label,args,body=None,error=None):
 global N
 checked(root,store);N+=1
 stem=f'{N:03d}-{root.name}-{label}'
 command=[str(PERRY/'bin/perry'),*args,'--root',str(root),'--store',str(store)]
 if body is not None:
  inp=save('traces/'+stem+'.input.json',body);command+=['--input','@'+str(inp)]
 p=subprocess.run(command,cwd=root,env=ENV,text=True,capture_output=True)
 save('traces/'+stem+'.command.json',{'argv':command,'PERRY_KERNEL_TESTING':'1','exit':p.returncode})
 (EVID/'traces'/(stem+'.stdout')).write_text(p.stdout)
 (EVID/'traces'/(stem+'.stderr')).write_text(p.stderr)
 d=json.loads(p.stdout)
 COMMANDS.append({'n':N,'root':str(root),'store':str(store),'label':label,'command':d['command'],'ok':d['ok'],'effect':d['effect'],'store_seq':d.get('store_seq'),'error':d.get('error')})
 if error:assert not d['ok'] and d['error']['code']==error,d
 else:assert p.returncode==0 and d['ok'],d
 return d

def helper(label,args):
 p=subprocess.run(['python3',str(PERRY/'tools/document_checks.py'),*args],env=ENV,text=True,capture_output=True)
 (EVID/(label+'.stdout')).write_text(p.stdout);(EVID/(label+'.stderr')).write_text(p.stderr)
 d=json.loads(p.stdout);save(label+'.json',{'exit':p.returncode,'result':d});return d

def root_new(name,init=True):
 root=RUN/name;shutil.copytree(CAPTURE,root)
 shutil.copytree(OUT/'proposed-config/.perry',root/'.perry')
 (root/'REHEARSAL-ONLY').write_text('Isolated trial. Never a live CitySurvivors root.\n')
 policy=json.loads((root/'.perry/safety.json').read_text())
 policy['approval_ref']='Actual user2026-10-22 authorized isolated rehearsal only; this temporary policy is not approved or installed for live activation.'
 (root/'.perry/safety.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
 (root/'perry/evidence').mkdir(parents=True)
 store=RUN/'stores'/(name+'.db');store.parent.mkdir(exist_ok=True)
 for rec in RECORDS:
  ref='evidence/'+rec['id']+'-source-spec.md'
  text='# '+rec['id']+' 隔离迁移候选\n\n'
  text+='本文件不是实际任务领取、验收或live状态。来源仅为冻结快照，状态/优先级/验证层级建议均待原维护者核对。\n\n'
  text+='- Source identity: '+rec['source_identity']+'\n- Responsible role: '+rec['responsible_role']+'\n- Lifecycle writer: '+rec['lifecycle_writer']+'\n'
  text+='- Source: `../'+rec['scope']+'` line '+str(rec['line'])+'\n- Subject: captured bytes; no engine/asset/runtime revalidation\n'
  text+='- Role card: `.perry/roles/'+({'策划':'planner','美术':'art','程序':'program'}[rec['lifecycle_writer']])+'.md`\n'
  text+='\n## 原始时点输入（历史引述）\n\n'+rec['raw']+'\n\n## 接管后边界\n\n'
  text+='原始来源不被改写为完成。保留交付/接入/设备/真人/用户确认的层次；缺失必需证据不关单；父包不自动完成。依赖原文仅表示输入关系，不自动转换成要求任务终态的blocks边。\n'
  text+='正式接管前逐项确认：当前业务状态、执行角色、生命周期写者、优先级、验收层级、可用输入与采用版本。未确认项不进入live。\n'
  (root/'perry'/ref).write_text(text)
 if init:
  call(root,store,'init',['init'],{'actor':ACTOR,'state_root':'perry','note':'Isolated experiment only; no live setup or adoption approval.'})
  call(root,store,'template',['template','apply'],{'actor':ACTOR,'template':json.loads((PERRY/'templates/process/perry.json').read_text())})
 return root,store

def query(root,store,label):
 items=[];after=None;seq=None;pages=[]
 while True:
  body={'type':'task','limit':7}
  if after:body['after']=after
  d=call(root,store,label,['query'],body);r=d['result']
  if seq is None:seq=d['store_seq']
  assert d['store_seq']==seq
  items+=r['items'];pages.append({'seq':seq,'ids':[x['id'] for x in r['items']],'truncated':r['truncated'],'next_after':r['next_after']})
  if not r['truncated']:break
  assert r['next_after'] and r['next_after']!=after
  after=r['next_after']
 assert len(items)==r['total'] and len({i['id'] for i in items})==len(items)
 return items,seq,pages

def get(root,store,i):return call(root,store,'get-'+i,['item','get'],{'id':i})['result']['item']

def ensure(root,store,rows,label):
 items,before,pages=query(root,store,label+'-before')
 existing=collections.defaultdict(list)
 for i in items:existing[i['fields']['summary'].split(';')[0]].append(i)
 mapping={};created=[];matched=[]
 for r in rows:
  same=existing[r['source_identity']]
  assert len(same)<=1,('ambiguous scoped source identity',r['source_identity'])
  if same:item=same[0];matched.append(r['id'])
  else:
   item=call(root,store,'create-'+r['id'],['item','create'],{'actor':ACTOR,'type':'task','fields':r['native_fields'],'note':'Simulation of proposed source mapping; no live execution or acceptance.'})['result']['item']
   created.append(r['id'])
   for ref in ['evidence/'+r['id']+'-source-spec.md','../'+r['scope']]:
    path=(root/'perry'/ref).resolve();assert path.is_relative_to(root.resolve())
    call(root,store,'attach-'+r['id'],['attach','add'],{'actor':ACTOR,'id':item['id'],'ref':ref,'hash':'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),'expect':{item['id']:item['seq']}})
    item=get(root,store,item['id'])
   if r['proposed_state']=='review':
    call(root,store,'review-'+r['id'],['item','move'],{'actor':ACTOR,'id':item['id'],'transition':'submit','set':{'next_action':'仅隔离导入候选，等待原维护者对账及实际验收，不表示V4通过。'},'expect':{item['id']:item['seq']}})
  mapping[r['id']]=item['id']
 _,after,_=query(root,store,label+'-after')
 return mapping,{'created':created,'matched':matched,'seq_before':before,'seq_after':after,'before_pages':pages}

root,store=root_new('trial-main')
startup=helper('startup-main',['startup','--root',str(root),'--state-root','perry'])
assert not startup['recovery']['blocking'] and not startup['interrupted']
roles=subprocess.run(['python3',str(PERRY/'tools/roles.py'),'--root',str(root)],env=ENV,text=True,capture_output=True)
(EVID/'roles.stdout').write_text(roles.stdout);(EVID/'roles.stderr').write_text(roles.stderr)
rd=json.loads(roles.stdout);assert roles.returncode==0 and rd['declared']==3 and not rd['errors']
save('roles-result.json',rd)
mapping,first=ensure(root,store,RECORDS,'initial')
def ensure_graph(root,store,mapping,label):
 created=0
 for r in RECORDS:
  if not r['parent_source_id']:continue
  child=get(root,store,mapping[r['id']]);parent=get(root,store,mapping[r['parent_source_id']])
  actual=[e for e in child['relations'] if e['kind']=='parent' and e['from']==child['id']]
  if actual:
   assert len(actual)==1 and actual[0]['to']==parent['id'], 'conflicting existing parent'
   continue
  call(root,store,label+'-'+r['id'],['rel','add'],{'actor':ACTOR,'kind':'parent','from':child['id'],'to':parent['id'],'expect':{child['id']:child['seq'],parent['id']:parent['seq']}})
  created+=1
 return created
assert ensure_graph(root,store,mapping,'parent')==15
mapping2,repeat=ensure(root,store,RECORDS,'repeat')
assert mapping==mapping2 and not repeat['created'] and repeat['seq_before']==repeat['seq_after']
assert ensure_graph(root,store,mapping2,'repeat-parent')==0
items,seq,pages=query(root,store,'complete')
assert len(items)==32 and not any(i['state']=='done' for i in items)
for i in items:
 for a in i['attachments']:
  target=(root/'perry'/a['ref']).resolve();assert target.is_relative_to(root.resolve()) and target.is_file()
  assert a['hash']=='sha256:'+hashlib.sha256(target.read_bytes()).hexdigest()
role_view={role:[r['id'] for r in RECORDS if r['responsible_role']==role] for role in ['策划','美术','程序']}
save('mapping-result.json',{'native_scope':'isolated trial-main only; never copy these IDs into live records','mapping':mapping,'first_apply':first,'repeat_apply':repeat,'capture_seq':seq,'pages':pages,'roles':role_view,'states':dict(collections.Counter(i['state'] for i in items))})

# Actual structural checks plus explicit agent interpretation; helper is not an ACL.
for label,scope in [('art-owned',['docs/art/asset-delivery.md']),('art-cross-role',['docs/tech/hud-layout-editor.md']),('domain-design-lexical',['docs/design/prototype-scope.md'])]:
 packet={'root':str(root),'scope':scope,'spec':'Isolated role-scope demonstration only, no domain source edit.','lane':'work','actor':ACTOR,'authorization':'Actual user authorized isolated rehearsal only; no live or cross-role domain edits.'}
 p=save(label+'-packet.json',packet);d=helper(label,['dispatch','--input',str(p)])
 if label=='art-owned':assert not d['blocked']
 if label=='domain-design-lexical':assert d['blocked']
save('role-judgments.json',{'art-owned':'ALLOW only within isolated task scope; no actual domain edit performed',
 'art-cross-role':'REFUSE by agent: program-owned file outside art May touch, even if structural helper passes. Handoff to program owner required.',
 'domain-design-lexical':'REFUSE automated dispatch: actual helper classifies design path as decide-owned. Preserve raw refusal; no bypass or permission expansion. Manual original-owner work requires its own authority.'})

# Real stale-write and V4 shape refusals, with no fabricated human or verifier.
i=get(root,store,mapping['CS-080']);old=i['seq']
call(root,store,'fresh-update',['item','update'],{'actor':ACTOR,'id':i['id'],'set':{'next_action':'Simulation: package remains pending actual criteria.'},'expect':{i['id']:old}})
call(root,store,'stale-update',['item','update'],{'actor':ACTOR,'id':i['id'],'set':{'next_action':'Must refuse stale write'},'expect':{i['id']:old}},error='stale_write')
i=get(root,store,mapping['CS-080'])
call(root,store,'unverified-v4-close',['item','move'],{'actor':ACTOR,'id':i['id'],'transition':'done','set':{'evidence':'evidence/CS-080-source-spec.md'},'expect':{i['id']:i['seq']}},error='guard_refused')

# Partial activation and explicit synthetic resume, using another private root/store.
partial,pstore=root_new('trial-partial')
partmap,part=ensure(partial,pstore,RECORDS[:5],'partial')
dossier=partial/'.perry/adoption/2026-10-22-dossier.md';dossier.parent.mkdir()
dossier.write_text('---\nadoption: 1\nstage: commit\nstep: board\nupdated: "2026-10-22T00:00:00Z"\n---\n\n# Isolated partial simulation\n\nFive original receipts retained; live activation forbidden.\n')
interrupted=helper('partial-interrupted',['startup','--root',str(partial),'--state-root','perry'])
assert interrupted['interrupted']
save('partial-stop.json',{'stop_after_startup':True,'no_native_call_before_choice':True,'completed_source_ids':list(partmap),'remaining_count':27})
save('resume-choice.json',{'simulated':True,'actor':'fixture owner choice, not human approval','choice':'Resume','scope':'same32 candidate mappings in trial-partial only','stage':'commit','step':'board','authority_for_live':False})
resumemap,resume=ensure(partial,pstore,RECORDS,'explicit-simulated-resume')
assert len(resumemap)==32 and len(resume['created'])==27 and len(resume['matched'])==5
assert ensure_graph(partial,pstore,resumemap,'resume-parent')==15
partial_items,pseq,_=query(partial,pstore,'resume-graph-complete')
assert sum(1 for i in partial_items for e in i['relations'] if e['kind']=='parent' and e['from']==i['id'])==15
assert ensure_graph(partial,pstore,resumemap,'resume-repeat-parent')==0
dossier.write_text(dossier.read_text().replace('stage: commit\nstep: board','stage: done'))
helper('partial-done',['startup','--root',str(partial),'--state-root','perry'])
save('partial-resume-result.json',{'initial':part,'resume':resume,'mapping':resumemap,'no_duplicate_creates':True,'parent_edges':15,'graph_repeated_creates':0,'limit':'Isolated mapping and graph replay only; no asset activation or real human consent.'})

# Export/replay recovery using the actual native contract. Never copy SQLite.
call(root,store,'export',['export'])
original,oseq,_=query(root,store,'post-export')
replay,rstore=root_new('trial-replay',init=False)
shutil.copytree(root/'perry/export',replay/'perry/export')
call(replay,rstore,'import',['import'],{'state_root':'perry'})
restored,rseq,_=query(replay,rstore,'replayed')
assert original==restored and oseq==rseq
call(replay,rstore,'duplicate-import',['import'],{'state_root':'perry'},error='store_not_empty')
save('recovery-result.json',{'source_seq':oseq,'replay_seq':rseq,'items_equal':True,'count':len(restored),'store_copy':False,'duplicate_import':'store_not_empty'})
shutil.copytree(root/'perry/export',EVID/'native-export')
save('post-replay-items.json',original)

# Ambiguous exact source identity must stop creates; the kernel itself permits this duplicate.
ambiguous,astore=root_new('trial-ambiguous',init=False)
shutil.copytree(root/'perry/export',ambiguous/'perry/export')
call(ambiguous,astore,'import',['import'],{'state_root':'perry'})
call(ambiguous,astore,'plant-duplicate',['item','create'],{'actor':ACTOR,'type':'task','fields':RECORDS[0]['native_fields'],'note':'Deliberate isolated ambiguity input; not live.'})
before_amb,ambseq,_=query(ambiguous,astore,'ambiguous-before')
try:
 ensure(ambiguous,astore,RECORDS,'ambiguous-reconcile')
 raise RuntimeError('Ambiguity was incorrectly accepted')
except AssertionError as error:
 assert 'ambiguous scoped source identity' in str(error)
 after_amb,afterseq,_=query(ambiguous,astore,'ambiguous-after')
 assert before_amb==after_amb and ambseq==afterseq
 save('ambiguity-refusal.json',{'actual_error':str(error),'before_seq':ambseq,'after_seq':afterseq,'population':len(after_amb),'additional_creates':0,'limit':'Agent reconciliation refuses; no native uniqueness guarantee.'})
# A changed captured input refuses before importing any record from it.
drift=RUN/'changed-source';shutil.copytree(CAPTURE,drift)
(drift/'todo.md').write_bytes((drift/'todo.md').read_bytes()+b'\nchanged trial input\n')
try:
 validate_capture(drift)
 raise RuntimeError('Changed source was incorrectly accepted')
except AssertionError as error:
 assert 'captured source changed' in str(error)
 save('changed-input-refusal.json',{'actual_error':str(error),'source':'isolated changed-source only','native_calls_after_changed_capture':0})

# Produce a proposed selective retirement preview in a copy, never the source repo.
preview=EVID/'todo-preview'
for file in ['todo.md','docs/art/todo.md','docs/tech/todo.md']:
 lines=(OUT/'source-capture')/file
 output=lines.read_text().splitlines()
 for r in RECORDS:
  if r['scope']!=file:continue
  cells=list(r['cells'].values());headers=list(r['cells'])
  for n,h in enumerate(headers):
   if h.startswith('状态'):cells[n]='演练预览：该条目接管后状态仅查Perry；trial ID '+mapping[r['id']]+'，不是live ID'
  output[r['line']-1]='| '+' | '.join(cells)+' |'
 t=preview/file;t.parent.mkdir(parents=True,exist_ok=True);t.write_text('\n'.join(output)+'\n')

changed=[]
manifest=json.loads((OUT/'source-manifest.json').read_text())
for e in manifest['entries']:
 if hashlib.sha256((SOURCE/e['path']).read_bytes()).hexdigest()!=e['sha256']:changed.append(e['path'])
save('source-freshness.json',{'checked_paths':len(manifest['entries']),'changed_since_capture':changed,'live_perry_exists':(SOURCE/'.perry').exists(),'live_document_root_exists':(SOURCE/'perry').exists(),'limit':'Finite read-only comparison, not a complete source freeze or code/asset rollback backup.'})
assert not (SOURCE/'.perry').exists() and not (SOURCE/'perry').exists()
save('native-command-audit.json',COMMANDS)
summary={'result':'PASS within isolated mapping/replay bounds','records':32,'link_only_inventory':225,'parent_edges':15,'native_calls':N,'initial_pages':len(pages),'repeat_additional_creates':0,'partial_resume_new':27,'partial_resume_matched':5,'export_replay_count':32,'ambiguous_source_refused':True,'changed_input_refused':True,'partial_graph_edges':15,'all_business_acceptance_pending':True,'source_drift':changed,'live_activation':False,'temporary_roots':[str(root),str(partial),str(replay)],'stores':[str(store),str(pstore),str(rstore)]}
save('summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
