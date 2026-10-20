import json, subprocess, pathlib, os, hashlib
base=pathlib.Path('/tmp/perry-scratch/Perry')
cli=pathlib.Path('/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry/bin/perry-kernel')
actor={'kind':'agent','name':'codex-cutover-rehearsal','session':os.environ.get('CODEX_THREAD_ID','task490-rehearsal')}
results=[]
for project in ('perry','sky'):
    work=base/f'task490-flow-{project}-20261015-v2'
    live='/Users/bytedance/proj/'+('Perry' if project=='perry' else 'SkyTonight')
    migration=subprocess.run([str(cli.parent/'perry-kernel-migrate'),'--root',live,'--work',str(work),'--json'],capture_output=True,text=True)
    assert migration.returncode==0, migration.stderr
    assert json.loads(migration.stdout)['reconciled']
    calls=[]
    def run(command, data=None, expect_error=False):
        args=[str(cli),*command.split(),'--root',str(work/'anchor'),'--store',str(work/'store.db')]
        if data is not None:
            inp=base/f'task490-{project}-rehearsal-input.json';inp.write_text(json.dumps(data));args+=['--input','@'+str(inp)]
        cp=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'PERRY_KERNEL_TESTING':'1'})
        d=json.loads(cp.stdout)
        calls.append({'command':command,'code':cp.returncode,'effect':d.get('effect'),'error':(d.get('error') or {}).get('code')})
        if expect_error:
            assert not d['ok'], d
        else:
            assert cp.returncode==0 and d['ok'], (command,cp.stdout,cp.stderr)
        return d.get('result',d)
    start=run('query',{'type':'task','terminal':False,'count_by':['state','priority'],'limit':2})
    # Page a real imported project, never substitute a row count from one page.
    read_ids=[];cursor=None
    while True:
        q={'type':'task','limit':37}
        if cursor:q['after']=cursor
        page=run('query',q);read_ids.extend(x['id'] for x in page['items'])
        if not page['truncated']:break
        cursor=page['next_after'];assert cursor
    assert len(set(read_ids))==len(read_ids)==page['total']
    def create(typ,fields):
        return run('item create',{'actor':actor,'type':typ,'fields':fields})['item']
    task=create('task',{'title':'Cutover rehearsal task','summary':'Exercise kernel work lifecycle in a disposable imported project copy.','priority':'P1','owner':'Coding Agent','track':'intake','verification':'V3','next_action':'Check work transitions'})
    ask=create('ask',{'question':'May the isolated rehearsal proceed?'})
    risk=create('risk',{'concern':'This rehearsal must not touch a live store.'})
    tid=task['id'];aid=ask['id'];rid=risk['id']
    run('rel add',{'actor':actor,'kind':'blocks','from':aid,'to':tid})
    blocked=run('item get',{'id':tid})['item'];assert aid in blocked['blocked_by']
    run('item move',{'actor':actor,'id':tid,'transition':'block','set':{'reason':f'Awaiting {aid}'},'expect':{tid:blocked['seq']}})
    run('item move',{'actor':actor,'id':aid,'transition':'answer','set':{'answer':'This is scripted rehearsal data, not a real human approval.'}})
    unblocked=run('item get',{'id':tid})['item'];assert not unblocked['blocked_by']
    run('item move',{'actor':actor,'id':tid,'transition':'start','expect':{tid:unblocked['seq']}})
    run('attach add',{'actor':actor,'id':tid,'ref':'evidence/rehearsal.md'})
    run('item update',{'actor':actor,'id':tid,'set':{'next_action':'Submit verified rehearsal'}})
    run('item move',{'actor':actor,'id':tid,'transition':'submit'})
    run('item move',{'actor':actor,'id':tid,'transition':'done'},True)
    run('item move',{'actor':actor,'id':tid,'transition':'done','set':{'evidence':'Scripted isolated rehearsal passed; not production acceptance.'}})
    run('item move',{'actor':actor,'id':rid,'transition':'clear','set':{'reason':'All calls named the isolated store and anchor.'}})
    run('rel remove',{'actor':actor,'kind':'blocks','from':aid,'to':tid})
    run('events',{'items':[tid],'limit':3})
    # Optimistic concurrency must refuse rather than overwrite.
    run('item update',{'actor':actor,'id':tid,'set':{'next_action':'Must not land'},'expect':{tid:1}},True)
    exported=run('export')
    export=pathlib.Path(exported['dir'])
    assert export.is_dir(), list((work/'anchor').iterdir())
    results.append({'project':project,'imported_task_count':len(read_ids),'query_total':start['total'],'calls':calls,'all_expected_outcomes':True})
(base/'task490-rehearsal-results.json').write_text(json.dumps(results,indent=2))
for result in results:print(result['project'],result['imported_task_count'],len(result['calls']),'calls: expected outcomes passed')
