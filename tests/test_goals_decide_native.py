"""Reviewed format-1 plan application only; retired preparer tests are not run."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COVERS = ('tools/goals_decide_migrate.py',)
spec = importlib.util.spec_from_file_location('goals_decide_migrate', ROOT/'tools/goals_decide_migrate.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)
TEMPLATE = json.loads((ROOT/'templates/process/perry.json').read_text())
ACTOR = {'kind':'agent','name':'reviewed-plan-test','session':'isolated-plan-test'}


class ReviewedPlan(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='reviewed-plan-test-')
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name).resolve()
        self.source = self.work/'source'
        self.s = self.source/'perry'
        for directory in ('phase','design','decisions'):
            (self.s/directory).mkdir(parents=True)
        # Deliberately opaque invalid Markdown/JSONL: final helper only hashes.
        (self.s/'OKR.md').write_bytes(b'not a document\xff')
        (self.s/'phase/current').write_bytes(b'opaque pointer')
        (self.s/'design/DESIGN-003.md').write_bytes(b'raw unparsed source')
        self.root = self.work/'anchor'
        (self.root/'.perry').mkdir(parents=True)
        self.store = self.work/'target.db'
        self.k = M.Kernel(self.root,self.store)
        self.k.call('init',{'actor':ACTOR,'state_root':'perry'})
        old = copy.deepcopy(TEMPLATE)
        old['version']=1
        old['types']={k:v for k,v in old['types'].items() if k in ('task','ask','risk')}
        old['relations']={}
        self.k.call('template apply',{'actor':ACTOR,'template':old})
        self.task = self.k.call('item create',{'actor':ACTOR,'type':'task','fields':{'title':'Original','summary':'Preserve original task','priority':'P1','verification':'V5'}})['result']['item']
        self.k.call('item create',{'actor':ACTOR,'type':'ask','fields':{'question':'Preserve ask'}})
        self.k.call('item create',{'actor':ACTOR,'type':'risk','fields':{'concern':'Preserve risk'}})
        self.k.commands.clear()
        hashes={p.relative_to(self.source).as_posix():M.digest(p.read_bytes()) for p in self.source.rglob('*') if p.is_file()}
        self.doc=dict(format=1,source=str(self.source),state_root='perry',source_hashes=hashes,
                      counts={},warnings=['unknown current remains unknown'],records=[],relations=[],
                      legacy_records={'opaque':[{'kind':'unknown','raw':'exact legacy fact'}]},
                      requirements=['prefix-floor requires reviewed generic capability'],prefix_ceilings={'ADR':0,'DESIGN':3})
        for version in ('v1','v2'):
            obj=f'overall:{version}:objective:O-1';kr=f'overall:{version}:kr:O1-KR1'
            self.record(obj,'objective','goal_active',legacy_id='O-1',legacy_scope=version,okr_version=version)
            self.record(kr,'kr','goal_active',legacy_id='O1-KR1',legacy_scope=version,okr_version=version,work_items=[self.task['id']])
            self.doc['relations'].append(['parent',kr,obj])
        # KR membership is a template rollup, not a guessed source join.
        for key, metric in [('unmeasured',{'current':None,'baseline':0,'target':10,'direction':'up'}),
                            ('down',{'current':4,'baseline':None,'target':2,'direction':'down'})]:
            self.record(key,'check','check_declared',check_metric=metric)
        self.record('design:DESIGN-003','design','design_review',expected_id='DESIGN-003',
                    implemented_by=[self.task['id']])
        self.doc['records'][-1]['attachments']=[{'ref':'design/DESIGN-003.md','hash':'sha256:'+hashes['perry/design/DESIGN-003.md']},
                                                     {'ref':'OKR.md','hash':'sha256:'+hashes['perry/OKR.md']}]
        self.doc['relations'] += [['aligned_to','overall:v2:kr:O1-KR1','overall:v2:objective:O-1'],
                                  ['aligned_to','design:DESIGN-003','overall:v2:kr:O1-KR1']]
        self.path=self.work/'reviewed.json'
        self.freeze()

    def record(self,key,typ,state,expected_id='',**extra):
        fields=dict(title=key,source_key=key,legacy_id=key,legacy_scope='',
                    source_hash=M.digest(key.encode()),legacy_record=M.encoded({'opaque':key}),approval_ref='historical reviewed source')
        fields.update(extra)
        self.doc['records'].append(dict(key=key,type=typ,state=state,fields=fields,attachments=[],expected_id=expected_id))
        self.doc['counts'][typ]=self.doc['counts'].get(typ,0)+1

    def freeze(self):
        self.doc['relations'].sort()
        self.path.write_text(M.encoded(self.doc)+'\n')
        self.sha=M.digest(self.path.read_bytes())
        return M.Plan(self.path,self.sha)

    def plan(self):
        return M.Plan(self.path,self.sha)

    def snapshot(self):
        return (self.k.items(),self.k.call('events',{'limit':100000})['result'])

    def args(self):
        return ['--plan',str(self.path),'--plan-sha256',self.sha,'--root',str(self.root),
                '--store',str(self.store),'--work',str(self.work)]

    def test_review_state_version_graph_metrics_and_exact_work_event_prefix(self):
        before,events=self.snapshot()
        result=M.apply(self.plan(),self.k)
        after={i['id']:i for i in self.k.items()}
        for old in before:self.assertEqual(after[old['id']],old)
        now=self.k.call('events',{'limit':100000})['result']['events']
        self.assertEqual(now[:len(events['events'])],events['events'])
        mapping=result['mapping']
        self.assertNotEqual(mapping['overall:v1:kr:O1-KR1'],mapping['overall:v2:kr:O1-KR1'])
        for version in ('v1','v2'):
            item=after[mapping[f'overall:{version}:kr:O1-KR1']]
            self.assertEqual(item['fields']['legacy_id'],'O1-KR1')
            self.assertEqual(item['fields']['legacy_scope'],version)
            self.assertIsNone(item['fields']['measure'])
        self.assertEqual(after['DESIGN-003']['state'],'design_review')
        for key in ('unmeasured','down'):
            self.assertIsNone(after[mapping[key]]['fields']['check_metric']['fraction'])
        self.assertIsNone(after[mapping['unmeasured']]['fields']['check_metric']['met'])
        self.assertEqual(after[mapping['down']]['fields']['check_metric']['current'],4)
        self.assertFalse(after[mapping['down']]['fields']['check_metric']['met'])
        self.assertEqual(self.plan().document(),self.doc)
        created=self.k.call('item create',{'actor':ACTOR,'type':'design','fields':{'title':'Next actual design'}})['result']['item']
        self.assertEqual(created['id'],'DESIGN-004')

    def test_repeat_no_events_and_export_import_replay_bytes(self):
        first=M.apply(self.plan(),self.k)
        export=self.root/'perry/export'
        before={p.name:p.read_bytes() for p in export.iterdir()}
        second=M.apply(self.plan(),self.k)
        self.assertEqual(first['store_seq'],second['store_seq'])
        self.assertEqual(first['mapping'],second['mapping'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in export.iterdir()})
        restored=self.work/'restored'
        (restored/'.perry').mkdir(parents=True)
        shutil.copytree(export,restored/'perry/export')
        k=M.Kernel(restored,self.work/'replay.db')
        k.call('import',{'state_root':'perry'})
        k.call('export')
        self.assertEqual(before,{p.name:p.read_bytes() for p in (restored/'perry/export').iterdir()})
        with self.assertRaisesRegex(M.Refused,'store_not_empty'):
            k.call('import',{'state_root':'perry'})

    def test_default_and_explicit_plan_only_leave_target_bytes_and_events(self):
        before=self.snapshot(); db=self.store.read_bytes()
        for mode in ([],['--dry-run'],['--plan-only']):
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(M.main(self.args()+mode),0)
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.store.read_bytes(),db)
        self.assertEqual(len(list(self.work.glob('receipt-*.json'))),3)
        self.assertFalse(list(self.work.glob('commands-*.json')))

    def test_bad_hash_and_changed_plan_refuse_without_commands(self):
        before=self.snapshot()
        with self.assertRaisesRegex(M.Refused,'SHA256 mismatch'):M.Plan(self.path,'0'*64)
        p=self.plan();self.path.write_bytes(self.path.read_bytes()+b' ')
        with self.assertRaisesRegex(M.Refused,'plan changed'):M.apply(p,self.k)
        self.assertEqual(self.snapshot(),before)
        self.assertFalse(self.k.commands)

    def test_source_mutation_deletion_and_added_directory_files_refuse(self):
        before=self.snapshot(); path=self.s/'OKR.md';original=path.read_bytes()
        for change in ('mutate','delete'):
            p=self.plan()
            if change=='mutate':path.write_bytes(b'changed')
            else:path.unlink()
            with self.assertRaisesRegex(M.Refused,'source changed'):M.apply(p,self.k)
            path.write_bytes(original)
        for directory in ('phase','design','decisions'):
            p=self.plan();extra=self.s/directory/'new.txt';extra.write_bytes(b'new')
            with self.assertRaisesRegex(M.Refused,'new source file'):M.apply(p,self.k)
            extra.unlink()
        self.assertEqual(self.snapshot(),before)

    def test_source_override_copy_has_identical_plan_and_facts(self):
        copied=self.work/'source-copy';shutil.copytree(self.source,copied)
        plan=M.Plan(self.path,self.sha,source=copied)
        self.assertEqual(plan.document(),self.doc)
        M.apply(plan,self.k)
        self.assertEqual(plan.source,copied)

    def test_traversal_foreign_and_symlink_sources_refuse(self):
        for name in ('../escape','/foreign','perry/../escape','perry//bad'):
            d=copy.deepcopy(self.doc); d['source_hashes'][name]='0'*64
            self.path.write_text(M.encoded(d))
            with self.assertRaises(M.Refused):M.Plan(self.path,M.digest(self.path.read_bytes()))
        self.freeze()
        original=self.s/'OKR.md';original.unlink();original.symlink_to(self.path)
        with self.assertRaisesRegex(M.Refused,'symlink'):self.plan()

    def test_added_symlink_directory_refuses_without_following(self):
        p=self.plan();(self.s/'phase/foreign').symlink_to(self.work,target_is_directory=True)
        with self.assertRaisesRegex(M.Refused,'symlink'):M.apply(p,self.k)

    def test_duplicate_json_keys_records_expected_ids_and_relations_refuse(self):
        self.path.write_text('{"format":1,"format":1}')
        with self.assertRaisesRegex(M.Refused,'duplicate JSON'):M.Plan(self.path,M.digest(self.path.read_bytes()))
        for kind in ('record','id','relation'):
            self.doc=copy.deepcopy(self.doc)
            if kind=='record':self.doc['records'].append(copy.deepcopy(self.doc['records'][0]))
            elif kind=='id':
                r=copy.deepcopy(self.doc['records'][-1]);r['key']='another';r['fields']['source_key']='another';self.doc['records'].append(r)
            else:self.doc['relations'].append(self.doc['relations'][0])
            with self.assertRaisesRegex(M.Refused,'duplicate'):self.freeze()
            self.doc['records']=self.doc['records'][:7];self.doc['relations']=self.doc['relations'][:2]

    def test_dangling_graph_unknown_type_state_and_field_refuse_before_target_writes(self):
        base=copy.deepcopy(self.doc); before=self.snapshot()
        for bad in ('graph','type','state','field','metric','ref'):
            self.doc=copy.deepcopy(base)
            if bad=='graph':self.doc['relations'].append(['aligned_to','missing','unmeasured'])
            if bad=='type':self.doc['records'][0]['type']='foreign'
            if bad=='state':self.doc['records'][0]['state']='not_a_state'
            if bad=='field':self.doc['records'][0]['fields']['unknown']='no'
            if bad=='metric':self.doc['records'][4]['fields']['check_metric']['current']='99 from prose'
            if bad=='ref':self.doc['records'][1]['fields']['work_items']=['TASK-999']
            with self.assertRaises(M.Refused):M.apply(self.freeze(),self.k)
            self.assertEqual(self.snapshot(),before,bad)
            self.assertFalse(self.k.commands,bad)

    def test_surrogate_metric_keys_and_unknown_relation_refuse_before_writes(self):
        original=copy.deepcopy(self.doc);before=self.snapshot()
        for bad in ('surrogate','metric_key','relation'):
            self.doc=copy.deepcopy(original)
            if bad=='surrogate':self.doc['records'][0]['fields']['title']='\ud800'
            if bad=='metric_key':self.doc['records'][4]['fields']['check_metric']['fraction']=0.9
            if bad=='relation':self.doc['relations'].append(['unknown','unmeasured','down'])
            with self.assertRaises(M.Refused):M.apply(self.freeze(),self.k)
            self.assertEqual(self.snapshot(),before)
            self.assertFalse(self.k.commands)

    def test_post_load_record_edit_is_not_a_reviewed_plan(self):
        plan=self.plan();plan.records['unmeasured'].fields['check_metric']['current']=9
        with self.assertRaisesRegex(M.Refused,'plan changed'):M.apply(plan,self.k)
        self.assertFalse(self.k.commands)

    def test_guard_missing_approval_refuses_before_template_apply(self):
        self.doc['records'][0]['fields'].pop('approval_ref')
        before=self.snapshot()
        with self.assertRaisesRegex(M.Refused,'guard_refused'):M.apply(self.freeze(),self.k)
        self.assertEqual(self.snapshot(),before)
        self.assertFalse(self.k.commands)

    def test_native_conflict_and_unmanaged_native_goal_refuse(self):
        M.apply(self.plan(),self.k)
        ident=next(i for i in self.k.items() if i['type']=='kr')['id']
        self.k.call('item update',{'actor':ACTOR,'id':ident,'set':{'metric_text':'concurrent edit'}})
        before=self.snapshot();self.k.commands.clear()
        with self.assertRaisesRegex(M.Refused,'native item changed'):M.apply(self.plan(),self.k)
        self.assertEqual(self.snapshot(),before);self.assertFalse(self.k.commands)
        self.k.call('item create',{'actor':ACTOR,'type':'objective','fields':{'title':'Unmanaged'}})
        with self.assertRaises(M.Refused):M.apply(self.plan(),self.k)

    def test_partial_failure_receipt_unique_logs_and_safe_resume(self):
        call=M.Kernel.call
        def fail(kernel, command, body=None, dry=False):
            if kernel.store==self.store and command=='rel add':raise M.Refused('injected interruption')
            return call(kernel,command,body,dry)
        with patch.object(M.Kernel,'call',fail),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.main(self.args()+['--apply']),1)
        receipt=json.loads(next(self.work.glob('receipt-*.json')).read_text())
        self.assertTrue(receipt['partial']);self.assertTrue(Path(receipt['commands']).is_file())
        with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(M.main(self.args()+['--apply']),0)
        self.assertEqual(len(list(self.work.glob('receipt-*.json'))),2)
        self.assertEqual(len(list(self.work.glob('commands-*.json'))),2)
        seq=self.k.call('query',{'limit':0})['store_seq']
        self.assertEqual(M.apply(self.plan(),self.k)['store_seq'],seq)

    def test_native_lifecycle_approval_and_human_v5_guards_remain(self):
        M.apply(self.plan(),self.k)
        item=self.k.call('item create',{'actor':ACTOR,'type':'objective','fields':{'title':'Draft'}})['result']['item']
        with self.assertRaisesRegex(M.Refused,'guard_refused'):
            self.k.call('item move',{'actor':ACTOR,'id':item['id'],'transition':'approve'})
        with self.assertRaisesRegex(M.Refused,'guard_refused'):
            self.k.call('item move',{'actor':ACTOR,'id':self.task['id'],'transition':'done','set':{'evidence':'signoff wording grants no authority'}})
        item=self.k.call('item move',{'actor':ACTOR,'id':item['id'],'transition':'approve','set':{'approval_ref':'test fixture decision'}})['result']['item']
        self.assertEqual(item['state'],'goal_active')

    def test_native_wrapper_explicit_store_testing_env_and_no_compatibility_imports(self):
        with patch.dict(os.environ,{'PERRY_STORE':'/foreign/live','PERRY_PROJECT':'/foreign','PERRY_HOME':'/foreign'}):
            self.k.call('describe')
        text=(ROOT/'tools/goals_decide_migrate.py').read_text()
        import ast
        imports=[n for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any('perry_kernel' in ast.unparse(n) or 'parsers' in ast.unparse(n) or 'lib'==getattr(n,'module',None) for n in imports))
        self.assertNotIn('bin/perry-kernel',text)
        self.assertFalse((ROOT/'bin/perry-kernel').exists())

    def test_cli_requires_hash_and_rejects_live_layout_and_consent_flags(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/goals_decide_migrate.py'),'--plan',str(self.path)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('--plan-sha256',result.stderr)
        for root,store,work in [(self.source,self.store,self.work),(self.root,self.root/'db',self.work),
                                (ROOT/'scratch',ROOT/'scratch.db',ROOT)]:
            with self.assertRaises(M.Refused):M.scratch_paths(self.source,root,store,work)
        with self.assertRaises(SystemExit),contextlib.redirect_stderr(io.StringIO()):
            M.main(self.args()+['--approve','true'])


if __name__=='__main__':unittest.main()
