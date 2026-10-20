"""Red safety demonstrations on isolated documents; no project/live state calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys
import json
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))

SPEC=importlib.util.spec_from_file_location('document_checks',Path(__file__).resolve().parents[1]/'tools/document_checks.py')
D=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(D)

class Safety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'.perry').mkdir();(self.root/'docs').mkdir()
        self.policy({'version':1,'approval_ref':'isolated reviewed policy','rules':[{'id':'remote','label':'Remote publication','patterns':['git push']}]})
    def dossier(self,text):
        p=self.root/'.perry/adoption/run.md';p.parent.mkdir(exist_ok=True);p.write_text(text);return p
    def test_recovery_stops_before_dossier_read(self):
        (self.root/'docs/.perry-task-transaction.json').write_text('corrupt marker')
        self.dossier('damaged restore point')
        r=D.startup(self.root,'docs');self.assertTrue(r['recovery']['blocking']);self.assertEqual(len(r['recovery']['errors']),1);self.assertEqual(r['interrupted'],[])
    def test_malformed_and_unknown_stage_block(self):
        for text in ('no frontmatter','---\nadoption: 1\nstage: typo\n---','---\nadoption: 1\nstage: done\nstage: done\n---'):
            self.dossier(text);self.assertTrue(D.startup(self.root,'docs')['recovery']['blocking'])
    def test_interrupted_never_auto_resumes(self):
        self.dossier('---\nadoption: 1\nstage: confirm\nstep: goals\n---\n')
        r=D.startup(self.root,'docs');self.assertFalse(r['recovery']['blocking']);self.assertEqual(len(r['interrupted']),1)
        self.assertIn('never auto-resume',r['interrupted'][0]['action'])
    def test_nested_dossier_payload_remains_opaque(self):
        self.dossier('---\nadoption: 1\nstage: done\ncandidates:\n  - evidence: src/a.py\n    status: pending\n---')
        self.assertFalse(D.startup(self.root,'docs')['recovery']['blocking'])
    def test_bad_step_not_hidden_as_terminal(self):
        self.dossier('---\nadoption: 1\nstage: confirm\nstep: unknown\n---');self.assertTrue(D.startup(self.root,'docs')['recovery']['blocking'])
    def test_finished_runs_and_clean_root(self):
        self.assertFalse(D.startup(self.root,'docs')['recovery']['blocking'])
        self.dossier('---\nadoption: 1\nstage: done\n---');self.assertEqual(D.startup(self.root,'docs')['interrupted'],[])
    def policy(self, data):
        (self.root/'.perry/safety.json').write_text(json.dumps(data))
    def packet(self):
        return dict(root=str(self.root),scope=['src/code.py'],lane='work',actor={'kind':'agent','name':'fixture','session':'actual-fixture-session'},spec='edit src/code.py')
    def test_unarmed_or_unreviewed_policy_refuses(self):
        for data in ({'version':1,'approval_ref':'review','rules':[]}, {'version':1,'approval_ref':'','rules':[{'id':'x','label':'x','patterns':['publish']}]}, {'version':1,'approval_ref':'review','rules':[{'id':'x','label':'x','patterns':[]}]}):
            self.policy(data)
            with self.assertRaises(ValueError):D.dispatch(self.packet())
    def test_high_stakes_requires_actual_authorization_reference(self):
        p=self.packet();p['spec']='git push upstream main';self.assertTrue(D.dispatch(p)['blocked'])
        p['authorization']='user instruction reference';self.assertFalse(D.dispatch(p)['blocked'])
        p['spec']='original changes';p['authorization']=None;self.assertEqual(D.dispatch(p)['matches'],[])
    def test_foreign_and_lane_scope(self):
        for path in ('../foreign/evidence/a.md','~/other','<target>/x','decisions/a.md','OKR.md'):
            p=self.packet();p['scope']=[path];self.assertTrue(D.dispatch(p)['blocked'],path)
        self.assertFalse(D.dispatch(self.packet())['blocked'])
    def review(self):
        path=self.root/'proof.txt';path.write_text('actual output')
        return dict(verification='V4',evidence=[str(path)],criteria='written criteria',implementer='A',reviewer='B',verdict='PASS')
    def test_evidence_and_review_freshness(self):
        p=self.review();self.assertFalse(D.review(p)['blocked']);p['reviewer']='A';self.assertTrue(D.review(p)['blocked'])
        p=self.review();p['evidence']=['/missing/proof'];self.assertTrue(D.review(p)['blocked'])
        p=self.review();p['verdict']='FAIL';self.assertTrue(D.review(p)['blocked'])
    def test_human_boundary(self):
        p=self.review();p['verification']='V5';p['actor']={'kind':'agent','name':'A'};p['human_signoff']='claimed';self.assertTrue(D.review(p)['blocked'])
        p['actor']={'kind':'human','name':'actual signer'};p['human_signoff']=None;self.assertTrue(D.review(p)['blocked'])
    def test_symlink_and_planning_draft(self):
        (self.root/'docs/plans').mkdir();(self.root/'docs/plans/draft.md').write_text('---\nstatus: interviewing\n---')
        self.assertEqual(D.startup(self.root,'docs')['interrupted'][0]['pipeline'],'plan')
        with self.assertRaises(ValueError):D.startup(self.root,'../outside')

    def test_narrative_and_legacy_waiting_approval_are_not_auto_resumed(self):
        p=self.root/'docs/plans';p.mkdir()
        (p/'native.md').write_text('# Draft narrative\nLifecycle is a native item.\n')
        (p/'legacy.md').write_text('---\nstatus: drafted\n---')
        r=D.startup(self.root,'docs');self.assertFalse(r['recovery']['blocking']);self.assertEqual(r['interrupted'],[])
        (p/'bad.md').write_text('---\nstatus: wrong\n---')
        r=D.startup(self.root,'docs');self.assertFalse(r['recovery']['blocking']);self.assertEqual(len(r['draft_errors']),1)
    def test_unreadable_directory_and_internal_symlink_are_visible(self):
        folder=self.root/'.perry/adoption';folder.mkdir()
        original=Path.iterdir
        def denied(path):
            if path.resolve()==folder.resolve():raise PermissionError('fixture permission denied')
            return original(path)
        with patch.object(Path,'iterdir',denied):
            r=D.startup(self.root,'docs');self.assertTrue(r['recovery']['blocking']);self.assertIn('permission denied',r['recovery']['errors'][0]['error'])
        target=self.root/'other';target.mkdir();folder.rmdir();folder.symlink_to(target,target_is_directory=True)
        self.assertTrue(D.startup(self.root,'docs')['recovery']['blocking'])
    def test_non_directory_safety_ancestors_block_startup(self):
        (self.root/'docs').rmdir();(self.root/'docs').write_text('file')
        self.assertTrue(D.startup(self.root,'docs')['recovery']['blocking'])
        (self.root/'docs').unlink();(self.root/'docs').mkdir()
        (self.root/'.perry/safety.json').unlink();(self.root/'.perry').rmdir()
        (self.root/'.perry').write_text('file')
        self.assertTrue(D.startup(self.root,'docs')['recovery']['blocking'])

    def test_resolved_scope_controls_lane_ownership(self):
        packet=self.packet();packet['lane']='goals';packet['scope']=['phase/../evidence/x.md']
        self.assertTrue(D.dispatch(packet)['blocked'])
        (self.root/'decisions').mkdir()
        (self.root/'alias').symlink_to(self.root/'decisions', target_is_directory=True)
        packet['lane']='work';packet['scope']=['alias/new.md']
        self.assertTrue(D.dispatch(packet)['blocked'])
        packet['lane']='decide';self.assertFalse(D.dispatch(packet)['blocked'])

    def test_structured_database_policy_is_armed_and_cannot_be_replaced_by_hook_text(self):
        self.policy({'version':1,'approval_ref':'isolated reviewed database policy','rules':[{'id':'database','label':'Database changes','patterns':['DROP TABLE','.git/perry']}]})
        p=self.packet();p['spec']='DROP TABLE events';p['hook']='## High-stakes operations\n- harmless only'
        self.assertTrue(D.dispatch(p)['blocked'])
        p['authorization']='actual explicit fixture instruction reference';self.assertFalse(D.dispatch(p)['blocked'])
        self.assertTrue(D.dispatch(p)['policy_source']['sha256'])
        (self.root/'.perry/safety.json').unlink()
        with self.assertRaises((OSError,ValueError)):D.dispatch(p)

    def test_role_missing_or_misspelled_safety_sections_blocks(self):
        folder=self.root/'.perry/roles';folder.mkdir()
        card=folder/'review.md';header='# Reviewer\n- Accepted by: Human\n- Default rung: V4\n'
        for body in ('', '## May touch\n- src/\n## Must escalates\n- `paid-action`\n', '## Must escalate\n- `paid-action`\n'):
            card.write_text(header+body)
            packet=self.packet();packet['spec']='paid-action'
            self.assertTrue(D.dispatch(packet)['blocked'])
        card.write_text(header+'## May touch\n- src/\n## Must escalate\n- `paid-action`\n')
        packet=self.packet();packet['spec']='paid-action'
        self.assertIn('paid-action',D.dispatch(packet)['matches'])
        packet['authorization']='actual scoped fixture instruction';self.assertFalse(D.dispatch(packet)['blocked'])

    def test_role_can_add_but_never_subtract_a_project_boundary(self):
        folder=self.root/'.perry/roles';folder.mkdir()
        (folder/'review.md').write_text('# Reviewer\n- Accepted by: Human\n- Default rung: V4\n## May touch\n- src/\n## Must escalate\n- `publish`\n')
        p=self.packet();p['spec']='publish a release';self.assertTrue(D.dispatch(p)['blocked'])
        p['authorization']='actual scoped fixture instruction';self.assertFalse(D.dispatch(p)['blocked'])
        p['spec']='git push upstream';p['authorization']=None;self.assertTrue(D.dispatch(p)['blocked'])
        (folder/'review.md').write_text('# Invalid responsibility without a rung\n')
        p['spec']='edit src/code.py';self.assertTrue(D.dispatch(p)['blocked'])

if __name__=='__main__':unittest.main()
