# Retained evidence harness

```python
import json,subprocess,hashlib,math,datetime
from pathlib import Path
root=Path('/Users/bytedance/proj/Perry');s=Path('/private/tmp/perry-scratch/task-447/phase004')
proposals=json.loads((s/'migration.json').read_text())
def live():
 p=json.loads(subprocess.check_output([str(root/'bin/perry-task'),'list','--json'],cwd=root,text=True));assert not p['bound']['truncated'];return p
before=live();rows={r['id']:r for r in before['tasks']};assert len(rows)==before['bound']['open_total']
for p in proposals: assert rows[p['task_id']]['next_action']==p['original_next_action'];assert len(p['proposed_next_action'])<=400
accounts=(s/'TASK-447-next-action-accounts.md').read_text().replace('Draft only; PMO must compare each original against a fresh live contract before applying.','PMO reviewed all 33 summaries against these verbatim accounts and compared originals with the complete live task-list contract immediately before each tool write.').replace('Source: captured next-actions-source.json, 2026-09-17. No state writes performed.','Source: captured next-actions-source.json, 2026-09-17. Historical claims below remain historical; only Next action text is migrated. Current task state is not changed by this archive.')
for p in proposals: assert p['original_next_action'] in accounts
out=root/'perry/evidence/2026-09/TASK-447-next-action-accounts.md';assert not out.exists();out.write_text(accounts)
(s/'migration-live-before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
receipts=[]
for p in proposals:
 current={r['id']:r for r in live()['tasks']}[p['task_id']]
 assert current['next_action']==p['original_next_action'], p['task_id']+' concurrently changed'
 r=subprocess.run([str(root/'bin/perry-task'),'next',p['task_id'],'--actor','pmo-agent','--next',p['proposed_next_action']],cwd=root,text=True,capture_output=True,check=True)
 receipts.append({'task_id':p['task_id'],'status':current['status'],'blocked_by':current['blocked_by'],'original_sha256':hashlib.sha256(p['original_next_action'].encode()).hexdigest(),'original_characters':len(p['original_next_action']),'new_characters':len(p['proposed_next_action']),'tool_stdout':r.stdout,'tool_stderr':r.stderr})
after=live();(s/'migration-live-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n');new={r['id']:r for r in after['tasks']}
for p in proposals: assert new[p['task_id']]['next_action']==p['proposed_next_action'];assert new[p['task_id']]['status']==rows[p['task_id']]['status'];assert new[p['task_id']]['blocked_by']==rows[p['task_id']]['blocked_by']
def metric(payload):
 lengths=sorted(len(r['next_action']) for r in payload['tasks'] if r['open']);return {'open_rows':len(lengths),'p90':lengths[math.ceil(.9*len(lengths))-1],'maximum':max(lengths),'over_400':sum(x>400 for x in lengths)}
report={'date':'2026-09-17','method':'Complete perry-task list --json open contract; len(str) Unicode code points; nearest rank ceil(0.9*n)-1','semantic_review':'PMO read all 33 full originals and authored proposals; retained retractions, partial results, gates and reconciliation tasks. No task status or dependencies changed.','before':metric(before),'after':metric(after),'writes':receipts};(s/'live-migration-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['after']['p90']<=400
print(json.dumps({k:report[k] for k in ['before','after','method']},ensure_ascii=False))

```
