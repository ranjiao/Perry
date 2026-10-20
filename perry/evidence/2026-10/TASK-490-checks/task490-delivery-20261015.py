import json,subprocess,pathlib
root=pathlib.Path('/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry')
store=pathlib.Path('/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-490-architecture')
baseline=store/'TASK-490/start-20261015T110335Z-9f43813978'
args=[str(root/'bin/perry-architecture'),'--root',str(root),'--source-roots','bin,kernel,viewer','--exclude','tests,kernel/tests,perry,.git']
d=json.loads(subprocess.check_output(args))
components=[]
for i,f in enumerate(d['files']):
 fid=f['id'];e=[k for k,v in d['evidence'].items() if v.get('file',v.get('source'))==fid][:1]
 if e:components.append({'id':f'unit-{i}','label':fid,'description':'Observed Python source unit; file-level current responsibilities.','uncertainty':'Static syntax only, no runtime or TypeScript coverage; cross-file semantic ownership not inferred.','members':[fid],'evidence':e})
a={'version':1,'producer':'host-agent','snapshot':d['snapshot'],'title':'Cutover implementation source units','components':components}
main=next(k for k in d['evidence'] if k.startswith('bin/perry-task::main@'))
v={'snapshot':d['snapshot'],'summary':'The isolated branch retires legacy writes and recovery side effects on reads. Kernel tests and two imported-project rehearsals passed. Full legacy repository gate failed and is not waived. Governing bin target still describes the old work writer; target edits and live cutover are not accepted.', 'target_change_requested':True,'findings':[{'reason':'Phase-E implementation intentionally retires the legacy work writer, while the pinned bin target still calls perry-task the lane writer. Prepare a target-document revision for user confirmation before integration; do not claim full acceptance.', 'target':'bin/ARCHITECTURE.md:31-33', 'evidence':[main]}]}
for name,data in [('delivery-analysis.json',a),('delivery-review.json',v)]: (store/name).write_text(json.dumps(data,indent=2))
p=subprocess.run(args+['--checkpoint','delivery','--task','TASK-490','--store',str(store),'--baseline',str(baseline),'--analysis',str(store/'delivery-analysis.json'),'--review',str(store/'delivery-review.json')],capture_output=True,text=True)
print(p.stdout);print(p.stderr)
if p.returncode:raise SystemExit(p.returncode)
notice=json.loads(p.stdout);(store/'delivery-notice.json').write_text(json.dumps(notice,indent=2))
p=subprocess.run(args+['--verify-checkpoint',notice['checkpoint']],capture_output=True,text=True)
print(p.stdout);print(p.stderr)
(store/'delivery-verification.json').write_text(p.stdout)
raise SystemExit(p.returncode)
