"""DESIGN-023 F: additive native migration, refusal and measurement boundaries."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COVERS = ('tools/goals_decide_migrate.py','templates/process/perry.json',
          'goals/','decide/','bin/perry-goals','bin/perry-decide')
spec = importlib.util.spec_from_file_location('goals_decide_migrate', ROOT/'tools/goals_decide_migrate.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)
TEMPLATE = json.loads((ROOT/'templates/process/perry.json').read_text())
ACTOR = {'kind':'agent','name':'F-test','session':'isolated-F-test'}


def lines(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(M.encoded(r)+'\n' for r in rows))


class NativeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.source = self.work/'source'
        self.s = self.source/'perry'
        lines(self.source/'.perry/config.jsonl',[{'kind':'setting','key':'state_root','label':'State root','value':'perry','order':0}])
        self.s.mkdir()
        (self.s/'OKR.md').write_text('# Overall narrative\n')
        self.root = self.work/'anchor'
        (self.root/'.perry').mkdir(parents=True)
        self.k = M.Kernel(self.root,self.work/'store.db')
        self.k.call('init',{'actor':ACTOR,'state_root':'perry'})
        old = copy.deepcopy(TEMPLATE)
        old['version']=1
        old['types']={k:v for k,v in old['types'].items() if k in ('task','ask','risk')}
        old['relations']={}
        self.k.call('template apply',{'actor':ACTOR,'template':old})
        self.task = self.k.call('item create',{'actor':ACTOR,'type':'task','fields':{'title':'Original task','summary':'Preserve','priority':'P1','verification':'V5'}})['result']['item']
        self.k.call('item create',{'actor':ACTOR,'type':'ask','fields':{'question':'Preserve ask'}})
        self.k.call('item create',{'actor':ACTOR,'type':'risk','fields':{'concern':'Preserve risk'}})
        self.ph='001-test'
        (self.s/'phase').mkdir()
        (self.s/'phase'/f'{self.ph}.md').write_text('# Phase\n\n> **Status**: active\n> **Started**: 2026-09-01\n> **Source**: OKR.md v2\n\n## Phase Focus\nTest\n')
        (self.s/'phase/CURRENT').write_text(self.ph+'\n')
        self.overall=[]
        for v in ('v1: 2026-08-01','v2: 2026-09-01'):
            self.overall += [{'kind':'objective','id':'O-1','version':v,'title':'Objective','heading':'Objective 1 — Objective'},
                             {'kind':'kr','id':'O1-KR1','version':v,'objective_id':'O-1','text':'Do not parse 99 from prose','metric':'99 successes'}]
        lines(self.s/'okr.jsonl',self.overall)
        self.linkage=[{'kind':'objective','phase':self.ph,'id':'O1','title':'Phase objective'},
                      {'kind':'kr','phase':self.ph,'id':'P001-O1-KR1','objective':'O1','title':'Phase KR','linked':'O1-KR1','target':9,'current':8},
                      {'kind':'edge','task':self.task['id'],'kr':'P001-O1-KR1'},
                      {'kind':'check','kr':'P001-O1-KR1','id':'a','label':'Condition A','direction':'increase','baseline':0,'target':10,'declared_at':'2026-09-01T00:00:00Z'},
                      {'kind':'measurement','kr':'P001-O1-KR1','check':'a','value':4,'asserted_at':'2026-09-02T00:00:00Z','evidence':'evidence/result.md'},
                      {'kind':'check','kr':'P001-O1-KR1','id':'b','label':'Condition B','direction':'at_most','target':2,'declared_at':'2026-09-01T00:00:00Z'}]
        lines(self.s/'linkage.jsonl',self.linkage)
        (self.s/'evidence').mkdir()
        (self.s/'evidence/result.md').write_text('Actual historic evidence\n')
        self.write_doc('DESIGN-001','design','locked')
        self.write_doc('ADR-001','decisions','archived')
        lines(self.s/'tasks.jsonl',[{'id':self.task['id'],'design_refs':['DESIGN-001']}])

    def write_doc(self, ident, directory, status):
        (self.s/directory).mkdir(exist_ok=True)
        p=self.s/directory/(ident+'-example.md')
        p.write_text(f'# {ident}: Example\n\n> Status: {status}\n> Date: 2026-09-01\n> Linked OKR: O1-KR1 (OKR.md v2)\n\n## Context\nFacts only.\n')
        return p

    def plan(self):
        return M.Plan(self.source).build(self.k.items())

    def test_rekeys_versions_retains_labels_and_refuses_ambiguous_join(self):
        p=self.plan()
        goals=[r for r in p.records.values() if r.type=='kr' and r.fields.get('goal_level')=='overall']
        self.assertEqual(len({r.key for r in goals}),2)
        self.assertEqual({r.fields['legacy_id'] for r in goals},{'O1-KR1'})
        with self.assertRaisesRegex(M.Refused,'ambiguous'):
            p.resolve('O1-KR1')
        self.assertIn(('aligned_to','phase:001-test:kr:P001-O1-KR1',goals[1].key),p.edges)

    def test_unknowns_are_not_inferred_and_latest_measurement_is_exact(self):
        rows=self.linkage+[{'kind':'measurement','kr':'P001-O1-KR1','check':'a','value':7,'asserted_at':'2026-09-03T00:00:00Z'},
                           {'kind':'measurement','kr':'P001-O1-KR1','check':'a','value':2,'asserted_at':'2026-09-01T00:00:00Z'}]
        lines(self.s/'linkage.jsonl',rows)
        p=self.plan()
        checks=[r for r in p.records.values() if r.type=='check']
        self.assertEqual([r.fields['check_metric']['current'] for r in checks],[7,None])
        self.assertTrue(all('measure' not in r.fields for r in p.records.values() if r.type=='kr'))
        self.assertIn('"current":8',p.records['phase:001-test:kr:P001-O1-KR1'].fields['legacy_record'])

    def test_additive_migration_idempotency_replay_and_derived_metrics(self):
        p=self.plan(); original=self.k.items()
        result=M.apply(p,self.k)
        after={i['id']:i for i in self.k.items()}
        for old in original:self.assertEqual(after[old['id']],old)
        checks=[i for i in after.values() if i['type']=='check']
        self.assertEqual(checks[0]['fields']['check_metric']['fraction'],0.4)
        self.assertIsNone(checks[1]['fields']['check_metric']['met'])
        kr=after[result['mapping']['phase:001-test:kr:P001-O1-KR1']]
        self.assertEqual(kr['rollup']['members'],2)
        self.assertIsNone(kr['rollup']['met'])
        seq=result['store_seq']
        again=M.apply(self.plan(),self.k)
        self.assertEqual(again['store_seq'],seq)
        export=self.root/'perry/export'
        before={p.name:p.read_bytes() for p in export.iterdir()}
        restored=self.work/'restored';(restored/'.perry').mkdir(parents=True)
        import shutil
        shutil.copytree(export,restored/'perry/export')
        k=M.Kernel(restored,self.work/'restored.db')
        k.call('import',{'state_root':'perry'})
        k.call('export')
        self.assertEqual(before,{p.name:p.read_bytes() for p in (restored/'perry/export').iterdir()})
        with self.assertRaisesRegex(M.Refused,'store_not_empty'):
            k.call('import',{'state_root':'perry'})

    def test_plan_is_a_real_no_write_and_partial_failure_is_recorded(self):
        import contextlib
        import io
        args=['--source',str(self.source),'--root',str(self.root),'--store',str(self.work/'store.db'),'--work',str(self.work)]
        before=self.k.items()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.main(args+['--dry-run']),0)
        self.assertEqual(self.k.items(),before)
        self.assertTrue((self.work/'plan.json').is_file())
        broken=copy.deepcopy(self.linkage)
        broken[3]['target']='invalid numeric input'
        lines(self.s/'linkage.jsonl',broken)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.main(args+['--apply']),1)
        failure=json.loads((self.work/'result.json').read_text())
        self.assertTrue(failure['partial'])
        self.assertTrue(Path(failure['commands']).is_file())
        self.assertIn('metric_invalid',failure['error'])

    def test_qualified_supersession_is_not_a_whole_item_replacement(self):
        self.write_doc('ADR-002','decisions','active')
        path=self.s/'decisions/ADR-002-example.md'
        path.write_text(path.read_text().replace('> Date:', '> Supersedes: ADR-001 § 2 (one clause only)\n> Date:'))
        p=self.plan()
        self.assertIn(('amends','adr:ADR-002','adr:ADR-001'),p.edges)
        self.assertNotIn(('supersedes','adr:ADR-002','adr:ADR-001'),p.edges)

    def test_source_change_is_refused_and_never_repaired(self):
        p=self.plan();(self.s/'OKR.md').write_text('changed')
        with self.assertRaisesRegex(M.Refused,'source changed'):p.unchanged()

    def test_sparse_filenames_report_real_primitive_gap_without_placeholder(self):
        self.write_doc('ADR-003','decisions','active')
        p=self.plan()
        self.assertTrue(any('ADR' in r for r in p.requirements))
        before=self.k.items()
        with self.assertRaisesRegex(M.Refused,'prefix-floor'):M.apply(p,self.k)
        self.assertEqual(self.k.items(),before)
        self.assertEqual(p.document()['prefix_ceilings']['ADR'],3)

    def test_native_conflict_and_orphan_measurement_refuse(self):
        rows=self.linkage+[{'kind':'measurement','kr':'P001-O1-KR1','check':'absent','value':1}]
        lines(self.s/'linkage.jsonl',rows)
        with self.assertRaisesRegex(M.Refused,'orphan measurement'):self.plan()
        lines(self.s/'linkage.jsonl',self.linkage)
        p=self.plan();result=M.apply(p,self.k)
        ident=result['mapping']['overall:v2: 2026-09-01:kr:O1-KR1']
        item=self.k.call('item get',{'id':ident})['result']['item']
        self.k.call('item update',{'actor':ACTOR,'id':ident,'set':{'metric_text':'concurrent edit'},'expect':{ident:item['seq']}})
        with self.assertRaisesRegex(M.Refused,'native item changed'):M.apply(self.plan(),self.k)

    def test_unmanaged_native_goal_refuses_instead_of_duplicating_current_state(self):
        self.k.call('template apply',{'actor':ACTOR,'template':TEMPLATE})
        self.k.call('item create',{'actor':ACTOR,'type':'objective','fields':{'title':'Existing native goal without migration identity'}})
        before=self.k.items()
        with self.assertRaisesRegex(M.Refused,'lack a matching migration identity'):
            M.apply(self.plan(),self.k)
        self.assertEqual(self.k.items(),before)

    def test_recovery_marker_refuses_without_repair(self):
        marker=self.s/'.perry-task-transaction.json'
        marker.write_text('{"incomplete":"leave bytes alone"}')
        with self.assertRaisesRegex(M.Refused,'recovery is blocking'):self.plan()
        self.assertEqual(marker.read_text(),'{"incomplete":"leave bytes alone"}')

    def test_design_review_status_maps_to_native_review(self):
        self.write_doc('DESIGN-001','design','in_review')
        plan = self.plan()
        self.assertEqual(plan.records['design:DESIGN-001'].state, 'design_review')
        M.apply(plan, self.k)
        item = next(i for i in self.k.items() if i['type'] == 'design')
        self.assertEqual(item['state'], 'design_review')

    def test_missing_unknown_or_negated_design_status_refuses_before_writes(self):
        before = self.k.items()
        for status in ['', 'unknown', 'not locked', 'design unlocked']:
            self.write_doc('DESIGN-001','design',status)
            with self.assertRaisesRegex(M.Refused, 'recognized declared status'):
                self.plan()
            self.assertEqual(self.k.items(), before)

    def test_phase_pointer_mismatch_refuses(self):
        (self.s/'phase/CURRENT').write_text('002-other')
        with self.assertRaisesRegex(M.Refused,'pointer disagreement'):self.plan()

    def test_phase_revision_is_preserved_and_folded(self):
        rows=self.linkage+[{'kind':'kr_revision','kr':'P001-O1-KR1','okr_version':'','op':'restate','fields':{'title':'Approved replacement'},'reason':'actual decision','revised_at':'2026-09-04T00:00:00Z','actor':'goals'}]
        lines(self.s/'linkage.jsonl',rows)
        r=self.plan().records['phase:001-test:kr:P001-O1-KR1']
        self.assertEqual(r.fields['title'],'Approved replacement')
        self.assertIn('actual decision',r.fields['legacy_record'])

    def test_real_approval_shape_and_v5_human_guard_remain(self):
        self.k.call('template apply',{'actor':ACTOR,'template':TEMPLATE})
        r=self.k.call('item create',{'actor':ACTOR,'type':'objective','fields':{'title':'Draft'}})['result']['item']
        with self.assertRaisesRegex(M.Refused,'guard_refused'):
            self.k.call('item move',{'actor':ACTOR,'id':r['id'],'transition':'approve'})
        with self.assertRaisesRegex(M.Refused,'guard_refused'):
            self.k.call('item move',{'actor':ACTOR,'id':self.task['id'],'transition':'done','set':{'evidence':'human sign-off attached'}})


class FrozenWriters(unittest.TestCase):
    def test_writers_refuse_before_any_root_or_recovery_read(self):
        with tempfile.TemporaryDirectory() as td:
            absent=Path(td)/'absent'
            for tool, verbs in [('perry-goals',['commit','link','objective','check','measure','kr','draft','phase']),('perry-decide',['bootstrap','new','supersede','status'])]:
                for verb in verbs:
                    for tail in ([],['--dry-run']):
                        p=subprocess.run([str(ROOT/'bin'/tool),verb,'--root',str(absent),'--json',*tail],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(ROOT),'PERRY_KERNEL_TESTING':'1'})
                        self.assertEqual(p.returncode,1,(tool,verb,p.stdout,p.stderr))
                        self.assertFalse(json.loads(p.stdout)['written'])
                        self.assertIn('read-only',json.loads(p.stdout)['refused'])
                        self.assertFalse(absent.exists())

    def test_flag_order_and_help_cannot_reenable_a_frozen_writer(self):
        with tempfile.TemporaryDirectory() as td:
            for tool,verb in [('perry-goals','commit'),('perry-decide','new')]:
                p=subprocess.run([str(ROOT/'bin'/tool),'--root',td,verb,'--json'],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(ROOT)})
                self.assertEqual(p.returncode,1,p.stderr)
                self.assertFalse(json.loads(p.stdout)['written'])
                h=subprocess.run([str(ROOT/'bin'/tool),verb,'--unknown','--help'],capture_output=True,text=True,env={**os.environ,'PERRY_HOME':str(ROOT)})
                self.assertEqual(h.returncode,0,h.stderr)
                self.assertIn('read-only',h.stdout)
                self.assertEqual(list(Path(td).iterdir()),[])

    def test_template_preserves_work_contract_and_adds_no_kernel_vocabulary(self):
        old=json.loads(subprocess.check_output(['git','show','b9be4d39f52ce1266534215b999c9db408b03bc5:templates/process/perry.json'],cwd=ROOT,text=True))
        for typ in ('task','ask','risk'):self.assertEqual(TEMPLATE['types'][typ],old['types'][typ])
        self.assertEqual(set(TEMPLATE['types']),{'task','ask','risk',*M.NEW_TYPES})


if __name__=='__main__':unittest.main()
