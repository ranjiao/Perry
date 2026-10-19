"""Red safety demonstrations on isolated documents; no project/live state calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location('document_checks',Path(__file__).resolve().parents[1]/'tools/document_checks.py')
D=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(D)

class Safety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'.perry').mkdir();(self.root/'docs').mkdir()
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
    def packet(self):
        return dict(hook='## High-stakes operations\n- Remote `git push`\n',scope=['src/code.py'],lane='work',actor='session-actual',spec='edit src/code.py')
    def test_unarmed_and_unextractable_hook(self):
        for hook in ('','## High-stakes operations\n- publish\n'):
            p=self.packet();p['hook']=hook;self.assertTrue(D.dispatch(p)['blocked'])
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
        (self.root/'docs/plans').mkdir();(self.root/'docs/plans/draft.md').write_text('---\nstatus: draft\n---')
        self.assertEqual(D.startup(self.root,'docs')['interrupted'][0]['pipeline'],'plan')
        with self.assertRaises(ValueError):D.startup(self.root,'../outside')

if __name__=='__main__':unittest.main()
