import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

parser=argparse.ArgumentParser(description='Isolated DESIGN-024 evidence driver; no semantic acceptance classifier')
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
SOURCE=args.source.resolve()
OUT=args.output.resolve()
ROOT=OUT/'project'
STORE=OUT/'isolated.db'
assert not OUT.exists(), 'Fixture run is create-only; use a new run path instead of overwriting evidence'
ROOT.mkdir(parents=True);(ROOT/'.perry/roles').mkdir(parents=True)
(ROOT/'perry').mkdir()
ACTOR={'kind':'agent','name':'synthetic-fixture-driver','session':os.environ['CODEX_THREAD_ID']}
ENV=dict(os.environ,PERRY_KERNEL_TESTING='1')
counter=0
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def native(label,args,body=None):
    global counter
    counter+=1;prefix=f'{counter:02d}-{label}'
    cmd=[str(SOURCE/'bin/perry'),*args,'--root',str(ROOT),'--store',str(STORE)]
    if body is not None:
        f=OUT/(prefix+'.input.json');write(f,json.dumps(body,ensure_ascii=False,indent=2)+'\n');cmd+=['--input','@'+str(f)]
    p=subprocess.run(cmd,env=ENV,text=True,capture_output=True)
    write(OUT/(prefix+'.result.json'),p.stdout);write(OUT/(prefix+'.command.json'),json.dumps({'argv':cmd,'exit':p.returncode,'stderr':p.stderr},indent=2))
    d=json.loads(p.stdout)
    if not d['ok']:raise RuntimeError(d)
    return d
def get(id):return native('get-'+id,['item','get'],{'id':id})['result']['item']
def create(title,summary,relations=None,attachments=None,type='task'):
    f={'title':title}
    if type=='task':f.update(summary=summary,priority='P1',verification='V3',track='main')
    return native('create',['item','create'],{'actor':ACTOR,'type':type,'fields':f,'relations':relations or [],'attachments':attachments or []})['result']['item']
policy={'version':1,'approval_ref':'Synthetic test policy for explicitly authorized isolated fixtures; not live human sign-off','rules':[{'id':'foreign','label':'Fixture cross-domain source','patterns':['docs/program']}]}
write(ROOT/'.perry/safety.json',json.dumps(policy,indent=2)+'\n')
write(ROOT/'.perry/roles/provider.md','# Role · Asset provider\n\n- Accepted by: Fixture integration reviewer\n- Default rung: V3\n- Executors: manual\n\n## May touch\n\n- write: docs/art/\n- read: docs/program/\n\n## Must escalate\n\n- Editing `docs/program` requires its actual owner.\n')
write(ROOT/'.perry/hook.md','Document root: perry\nDocument language: English\nPacks: []\n')
write(ROOT/'AGENTS.md','Synthetic project. Asset provider writes docs/art only; program owner writes docs/program. Read permission does not grant write permission.\n')
native('init',['init'],{'actor':ACTOR,'state_root':'perry','note':'Isolated synthetic procedure fixtures, never a consumer adoption.'})
native('template',['template','apply'],{'actor':ACTOR,'template':json.loads((SOURCE/'templates/process/perry.json').read_text())})
package=create('Synthetic delivery package','Package acceptance requires integration and actual human visual review.')
provider=create('Synthetic provider delivery','Source scope: provider-list. Original ID: 7. Scope: source delivery only.',relations=[{'kind':'parent','to':package['id']}])
consumer=create('Synthetic integration','Source scope: integration-list. Original ID: 7. Scope: runtime integration only.',relations=[{'kind':'parent','to':package['id']}])
unknown=create('Synthetic unassigned task','Source scope: incoming-list. Original ID: 8. No explicit domain-role association is available.')
write(ROOT/'perry/provider-spec.md','Native task: '+provider['id']+'\nRole card: project anchor/.perry/roles/provider.md\nProvider criteria: source delivery fixture command succeeds. Runtime and human review are excluded from this task, but required by the package.\n')
write(ROOT/'perry/consumer-spec.md','Native task: '+consumer['id']+'\nRole declaration: program owner, project AGENTS.md. Integration and actual human review evidence are untested.\n')
for item,name in [(provider,'provider-spec.md'),(consumer,'consumer-spec.md')]:
    i=get(item['id']);native('attach',['attach','add'],{'actor':ACTOR,'id':i['id'],'ref':name,'hash':'sha256:'+hashlib.sha256((ROOT/'perry'/name).read_bytes()).hexdigest(),'expect':{i['id']:i['seq']}})
write(ROOT/'checks/custom.py',"from pathlib import Path\np=Path(__file__).parents[1]/'docs/art/source.txt'\nassert p.read_text() == 'synthetic source A\\n'\nprint('custom source criterion passed; integration and human review not checked')\n")
write(ROOT/'docs/art/source.txt','synthetic source A\n')
proc=subprocess.run([sys.executable,str(ROOT/'checks/custom.py')],capture_output=True,text=True,cwd=ROOT)
assert proc.returncode==0
write(OUT/'custom-check.json',json.dumps({'argv':[sys.executable,'checks/custom.py'],'exit':proc.returncode,'stdout':proc.stdout,'scope':'synthetic provider source only'},indent=2))
i=get(provider['id']);native('provider-done',['item','move'],{'actor':ACTOR,'id':i['id'],'transition':'done','set':{'evidence':'Actual isolated custom-check.json: source delivery only; runtime integration and human review excluded.'},'expect':{i['id']:i['seq']}})

# Full paging is a real native operation; mapping decisions remain Agent judgments.
pages=[];body={'type':'task','limit':1};seq=None
while True:
    d=native('paged-query',['query'],body);pages.append(d)
    if seq is None:seq=d['store_seq']
    assert d['store_seq']==seq
    if not d['result']['truncated']:break
    cursor=d['result']['next_after'];assert cursor and cursor!=body.get('after');body={**body,'after':cursor}
items=[i for p in pages for i in p['result']['items']]
assert len(items)==4
write(OUT/'paging-summary.json',json.dumps({'seq':seq,'pages':len(pages),'total':len(items),'ids':[i['id'] for i in items]},indent=2))
before=native('recheck-before',['query'],{'type':'task','limit':100})
after=native('recheck-after',['query'],{'type':'task','limit':100})
assert before['store_seq']==after['store_seq'] and before['result']==after['result']
write(OUT/'source-identity-recheck.json',json.dumps({'scope_and_id':[{'scope':'provider-list','original_id':'7','native':provider['id']},{'scope':'integration-list','original_id':'7','native':consumer['id']}],'query_seq':after['store_seq'],'event_delta':0,'decision':'Existing exact matches inspected; no creates repeated. This is an author observation, not V4.'},indent=2))

packet={'root':str(ROOT),'scope':['docs/program/target.md'],'spec':'Asset provider may read but not edit docs/program; this requested write lacks that owner authority.','lane':'work','actor':ACTOR,'authorization':None}
write(OUT/'cross-domain-packet.json',json.dumps(packet,indent=2))
p=subprocess.run([sys.executable,str(SOURCE/'tools/document_checks.py'),'dispatch','--input',str(OUT/'cross-domain-packet.json')],capture_output=True,text=True)
write(OUT/'cross-domain-result.json',p.stdout);assert p.returncode==1 and json.loads(p.stdout)['blocked']

write(ROOT/'docs/design/spec.md','# Specialist specification\n\nDocument validity: current\nRevision: 2\nDomain owner: product designer\n\nSynthetic retained source, not a native approval declaration.\n')
decision=create('Synthetic decision draft','',attachments=[{'ref':'../docs/design/spec.md','hash':'sha256:'+hashlib.sha256((ROOT/'docs/design/spec.md').read_bytes()).hexdigest()}],type='design')
get(decision['id'])
write(ROOT/'perry/criteria.md','# Synthetic criterion results\n\n| Condition | Required | Subject | Actual result | Evaluator | Evidence |\n|---|---|---|---|---|---|\n| Source A bytes | yes | candidate A | passed | synthetic fixture command | custom-check.json |\n| Runtime behavior | yes | candidate B | failed | fixture observation, not live runtime | synthetic negative input |\n| Device review | yes | candidate B | untested | none | none |\n| Visual approval | yes | candidate B | untested | actual human required | none |\n\nNo overall pass is asserted.\n')
write(ROOT/'research/source.md','# Synthetic research source\n\nThis fixture states that source support and a human-facing explanation are the deliverable. No numeric measurement is required.\n')
write(ROOT/'research/brief.md','Review method: inspect research/source.md and the explanation for source support; non-Git/non-code subject. Immutable bytes retained in the external evidence bundle.\n')
outside=OUT/'outside.txt';write(outside,'Synthetic out-of-anchor reference; not a private file.\n');(ROOT/'perry/outside-link').symlink_to(outside)
write(OUT/'reference-path-observations.json',json.dumps({'agreed_root':str(ROOT),'domain_ref':'../docs/design/spec.md','resolved_domain':str((ROOT/'perry/../docs/design/spec.md').resolve()),'symlink_ref':'outside-link','resolved_symlink':str((ROOT/'perry/outside-link').resolve()),'escape':not (ROOT/'perry/outside-link').resolve().is_relative_to(ROOT)},indent=2))

# Preserve the actual safety refusal and repair only the intentionally created fixture link.
+p=subprocess.run([sys.executable,str(SOURCE/'tools/document_checks.py'),'startup','--root',str(ROOT),'--state-root','perry'],capture_output=True,text=True)
+write(OUT/'symlink-startup-refusal.json',p.stdout);assert json.loads(p.stdout)['recovery']['blocking']
+link=ROOT/'perry/outside-link';assert link.is_symlink() and link.resolve()==outside.resolve();link.unlink()
+write(OUT/'repair-note.txt','Removed only the intentional synthetic out-of-root symlink after preserving the startup refusal. No native state query or write occurred while recovery was blocking.\n')
+
+snap=OUT/'git-snapshot-source';snap.mkdir();subprocess.run(['git','init','-q',str(snap)],check=True)
write(snap/'untracked.txt','before capture\n');saved=OUT/'retained-capture/untracked.txt';saved.parent.mkdir();shutil.copy2(snap/'untracked.txt',saved)
old_hash=hashlib.sha256(saved.read_bytes()).hexdigest();write(snap/'untracked.txt','changed after capture\n');new_hash=hashlib.sha256((snap/'untracked.txt').read_bytes()).hexdigest();assert old_hash!=new_hash
status=subprocess.check_output(['git','-C',str(snap),'status','--porcelain'],text=True)
write(OUT/'snapshot-observations.json',json.dumps({'source_root':str(snap),'retained_bytes':str(saved),'status':status,'old_sha256':old_hash,'current_sha256':new_hash,'same':old_hash==new_hash,'limits':'One finite untracked source fixture; not a consumer backup.'},indent=2))

# All required native evidence is captured before installing the interruption marker.
final=native('final-native',['query'],{'limit':100})
write(OUT/'case-index.json',json.dumps({'root':str(ROOT),'store':str(STORE),'source_checkout':str(SOURCE),'package':package['id'],'provider':provider['id'],'consumer':consumer['id'],'missing_role':unknown['id'],'draft_design':decision['id'],'final_seq':final['store_seq'],'cases':{'S01':['final-native','provider-spec.md'],'S02':['source-identity-recheck.json'],'S03':['paging-summary.json','provider-spec.md','consumer-spec.md'],'S04':['cross-domain-packet.json','cross-domain-result.json'],'S05':['docs/design/spec.md','draft_design'],'S06':['custom-check.json','perry/criteria.md'],'S07':['perry/criteria.md'],'S08':['checks/custom.py','custom-check.json','research/brief.md'],'S09':['snapshot-observations.json','retained-capture/untracked.txt'],'S10':['partial-native-receipt.json','interrupted-startup.json']}},indent=2))
write(OUT/'partial-native-receipt.json',json.dumps({'actual_completed_provider':provider['id'],'native_seq':final['store_seq'],'remaining':'Consumer/package acceptance pending; original source still has a legacy lifecycle writer. No activation occurred.'},indent=2))
write(ROOT/'.perry/adoption/fixture.md','---\nadoption: 1\nstage: commit\nstep: board\nupdated: "2026-10-22T00:00:00Z"\n---\n\n# Synthetic interrupted adoption\n\nPending actual resume choice. The source writer is not retired. An existing native receipt does not authorize replay.\n')
p=subprocess.run([sys.executable,str(SOURCE/'tools/document_checks.py'),'startup','--root',str(ROOT),'--state-root','perry'],capture_output=True,text=True)
write(OUT/'interrupted-startup.json',p.stdout);assert json.loads(p.stdout)['interrupted']
print(json.dumps({'root':str(ROOT),'store':str(STORE),'native_calls':counter,'case_inputs':10,'last_action':'startup reported interrupted adoption; no subsequent fixture state reads/writes or automatic resume'},indent=2))
