import json,subprocess,pathlib
root=pathlib.Path('/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry')
store=pathlib.Path('/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-490-architecture')
args=[str(root/'bin/perry-architecture'),'--root',str(root),'--source-roots','bin,kernel,viewer','--exclude','tests,kernel/tests,perry,.git']
d=json.loads(subprocess.check_output(args))
components=[]
for i,f in enumerate(d['files']):
 fid=f['id']; evidence=[k for k,v in d['evidence'].items() if v.get('file',v.get('source'))==fid][:1]
 if evidence:components.append({'id':f'unit-{i}','label':fid,'description':'Observed Python source unit, responsibility held at file granularity.','uncertainty':'Static syntax only; no runtime or TypeScript coverage. Cross-file semantic ownership is not inferred.','members':[fid],'evidence':evidence})
a={'version':1,'producer':'host-agent','snapshot':d['snapshot'],'title':'Approved phase-E targets and preserved gates','components':components}
v={'snapshot':d['snapshot'],'summary':'User explicitly approved TASK-490-target-proposal.patch before application. Target semantics applied; root wrapping restored the existing 500-line cap, and the measured declared-surface count is eight rather than the proposal typo seven. Native work procedures retain independent review, criteria, high-stakes, ownership, restore and executor isolation constraints. Frozen-reader fixtures explicitly declare historical input and never bypass production retirement. Full gate remains red: acceptance and live cutover are NOT granted. This source snapshot is committed as 5daae778.', 'target_change_requested':False,'findings':[]}
(store/'approved-delivery-analysis.json').write_text(json.dumps(a,indent=2))
(store/'approved-delivery-review.json').write_text(json.dumps(v,indent=2))
for label,baseline in [('original','start-20261015T110335Z-9f43813978'),('approved','start-20261015T115421Z-7f41552ebf')]:
 p=subprocess.run(args+['--checkpoint','delivery','--task','TASK-490','--store',str(store),'--baseline',str(store/'TASK-490'/baseline),'--analysis',str(store/'approved-delivery-analysis.json'),'--review',str(store/'approved-delivery-review.json')],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 notice=json.loads(p.stdout);(store/f'approved-delivery-{label}-notice.json').write_text(json.dumps(notice,indent=2))
 p=subprocess.run(args+['--verify-checkpoint',notice['checkpoint']],capture_output=True,text=True)
 (store/f'approved-delivery-{label}-verification.json').write_text(p.stdout)
 print(label,json.dumps({'checkpoint':notice['checkpoint'],'status':notice['status'],'reasons':notice['reasons'],'verification':{k:json.loads(p.stdout).get(k) for k in ('fresh','status','reasons','verification_limit')}},ensure_ascii=False))
 if p.returncode:raise RuntimeError(p.stderr)
