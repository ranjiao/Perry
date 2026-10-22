from pathlib import Path
import subprocess,json,hashlib,os
root=Path('/Users/bytedance/proj/Perry');a=root/'perry/evidence/2026-10/TASK-497-release-integration-20261022'
def call(name,cmd):
 r=subprocess.run(cmd,cwd=root,text=True,capture_output=True);(a/(name+'.json')).write_text(json.dumps({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n');assert r.returncode==0,(name,r.stderr);return json.loads(r.stdout)
def native(name,group,payload):
 p=a/(name+'.input.json');p.write_text(json.dumps(payload,indent=2)+'\n');return call(name,['bin/perry',*group,'--root',str(root),'--input','@'+str(p)])
s=call('postmerge-startup',['python3','tools/document_checks.py','startup','--root',str(root),'--state-root','perry']);assert not s['recovery']['blocking'] and not s['interrupted']
before=native('before-attachment',['item','get'],{'id':'TASK-497'})['result']['item'];assert before['state']=='done' and before['fields']['verification']=='V4'
actor={'kind':'agent','name':'PMO Release Integrator (/root/design024_integrator)','session':os.environ['CODEX_THREAD_ID']}
ref='evidence/2026-10/TASK-497-release-integration-20261022/README.md';digest='sha256:'+hashlib.sha256((a/'README.md').read_bytes()).hexdigest()
native('attachment',['attach','add'],{'actor':actor,'id':'TASK-497','ref':ref,'hash':digest,'expect':{'TASK-497':before['seq']},'note':'Authorized independent local integration receipt; original source V4 reviewer/evidence preserved. Integrated, unpublished.'})
fresh=native('after-attachment',['item','get'],{'id':'TASK-497'})['result']['item']
merge=json.loads((a/'postmerge.json').read_text())['merge']
native('integration-next-action',['item','update'],{'actor':actor,'id':'TASK-497','set':{'next_action':f'Independently integrated on local main merge {merge}; product version 0.1.32. Integrated, unpublished. No consumer activation, push, tag or public release; any such future action needs its own authority.'},'expect':{'TASK-497':fresh['seq']},'note':'Record completed authorized independent integration separately from original source V4 acceptance.'})
after=native('affected-native-after',['query'],{'ids':['TASK-497','TASK-498','TASK-499','TASK-500'],'limit':10})
for item in after['result']['items']:
 assert item['state']=='done' and item['fields']['verification']=='V4'
 if item['id']=='TASK-497':
  assert item['fields']['verified_by']==before['fields']['verified_by'] and item['fields']['evidence']==before['fields']['evidence']
  assert any(x['ref']==ref and x['hash']==digest for x in item['attachments'])
print('Native receipt complete at store_seq',after['store_seq'])
