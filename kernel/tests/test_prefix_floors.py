"""Proposed additive prefix-floor input; all state is isolated."""
import concurrent.futures
import copy
import shutil
import unittest
from support import Sandbox, ACTOR, TEMPLATE
from perry_kernel.values import INT_LIMIT

class PrefixFloors(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox(self).ready()
    def reserve(self, ceilings, *, template=TEMPLATE, flags=()):
        return self.s.run('template apply', data={'actor': ACTOR, 'template': template, 'ceilings': ceilings}, flags=flags)
    def create(self):
        return self.s.ok('item create', data={'actor': ACTOR, 'type': 'widget', 'fields': {'bench': 'north'}})['item']
    def test_identical_template_raise_writes_only_ceiling_and_next_mint_skips(self):
        first = self.create()
        before = self.s.ok('item get', data={'id': first['id']})
        r = self.reserve({'W': 23})
        self.assertTrue(r.ok, r); self.assertEqual(r.env['effect'], 'written')
        event = self.s.ok('events', data={'after_seq': r.env['events'][0]-1})['events'][0]
        self.assertEqual([c['key'] for c in event['changes']], ['ceiling:W'])
        self.assertEqual(event['items'], [])
        self.assertEqual(self.s.ok('item get', data={'id': first['id']}), before)
        self.assertEqual(self.create()['id'], 'W-024')
    def test_equal_lower_and_zero_are_unchanged(self):
        self.assertEqual(self.reserve({'W': 0}).env['effect'], 'unchanged')
        self.reserve({'W': 23})
        for floor in [0, 10, 23]:
            r = self.reserve({'W': floor}); self.assertTrue(r.ok, r)
            self.assertEqual(r.env['effect'], 'unchanged'); self.assertEqual(r.env['events'], [])
        self.assertEqual(self.create()['id'], 'W-024')
    def test_invalid_map_never_changes_history_or_prefix(self):
        before = self.s.ok('events', data={'limit': 10000})
        for ceilings in [{'missing': 4}, {'W': -1}, {'W': INT_LIMIT+1}, {'W': True}, {'W': 1.5}, {'W': '23'}, {'W': None}, [], {'W': 8, 'missing': 20}]:
            with self.subTest(ceilings=ceilings):
                r = self.reserve(ceilings); self.assertFalse(r.ok, r)
                self.assertEqual(r.code_name, 'input_invalid')
                self.assertEqual(self.s.ok('events', data={'limit': 10000}), before)
        self.assertEqual(self.create()['id'], 'W-001')
    def test_dry_run_rolls_back_new_template_and_floor(self):
        new = copy.deepcopy(TEMPLATE); new['version'] = 2
        before = self.s.ok('events', data={'limit': 10000})
        r = self.reserve({'W': 90}, template=new, flags=['--dry-run'])
        self.assertTrue(r.ok, r); self.assertEqual(r.env['effect'], 'dry_run')
        self.assertEqual(self.s.ok('events', data={'limit': 10000}), before)
        self.assertEqual(self.s.ok('template show')['version'], 1)
        self.assertEqual(self.create()['id'], 'W-001')
    def test_new_template_and_floor_replay_and_export_identically(self):
        new = copy.deepcopy(TEMPLATE); new['version'] = 2
        r = self.reserve({'W': 23, 'G': 27}, template=new); self.assertTrue(r.ok, r)
        self.create()
        source = self.s.ok('export')['dir']
        dst = Sandbox(self); destination = dst.root / dst.state_root / 'export'
        shutil.copytree(source, destination)
        imported = dst.ok('import', data={'state_root': dst.state_root})
        self.assertGreater(imported['events'], 0)
        self.assertEqual(dst.ok('query', data={'limit': 10000}), self.s.ok('query', data={'limit': 10000}))
        dst.ok('export')
        from pathlib import Path
        for name in ['items.jsonl', 'events.jsonl']:
            self.assertEqual((Path(source)/name).read_bytes(), (destination/name).read_bytes())
        item = dst.ok('item create', data={'actor': ACTOR, 'type': 'gauge'})['item']
        self.assertEqual(item['id'], 'G-28')
    def test_concurrent_reservations_and_mints_never_lower_floor_or_duplicate(self):
        def run(n):
            if n % 3 == 0:
                return self.s.cli('template apply', data={'actor': ACTOR, 'template': TEMPLATE, 'ceilings': {'W': 100 if n % 2 else 300}})
            return self.s.cli('item create', data={'actor': ACTOR, 'type': 'widget', 'fields': {'bench': 'north'}})
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(run, range(12)))
        for r in results: self.assertTrue(r.ok, r)
        ids = [r.result['item']['id'] for r in results if 'item' in r.result]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(int(self.create()['id'].split('-')[1]), 301)
    def test_template_version_or_compatibility_error_rolls_back_floor(self):
        self.create(); bad = copy.deepcopy(TEMPLATE); bad['types']['widget']['fields']['bench']['values'] = ['other']
        r = self.reserve({'W': 50}, template=bad); self.assertEqual(r.code_name, 'template_version')
        bad['version'] = 2
        r = self.reserve({'W': 50}, template=bad); self.assertEqual(r.code_name, 'template_incompatible')
        self.assertEqual(self.create()['id'], 'W-002')

if __name__ == '__main__': unittest.main()
