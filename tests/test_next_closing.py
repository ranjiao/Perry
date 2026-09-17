"""TASK-443: typed preference, declared procedure routes and actual next payloads.

Closing is an agent procedure, so document guards cannot certify a live host's
choice UI; independent scenario review owns that final check. No prose parser.
"""
from pathlib import Path
import json
import re
import tempfile
import unittest
import inproc
import test_next_section as fixtures

COVERS = ("reference/next.md", "reference/config.md", "bin/perry-config",
          "SKILL.md", "goals/SKILL.md", "work/SKILL.md", "decide/SKILL.md",
          "goals/reference/", "work/reference/", "decide/reference/",
          "packs/software-ops/")
ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "reference/next.md"


def routes(text):
    return re.findall(r'^\| `(router|goals|work|decide)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$', text, re.M)


def routing_errors(text, read):
    errors = []
    for lane, command, source, after in routes(text):
        body = read(source)
        if f'<!-- next-close: {lane} {command} -->' not in body or 'reference/next.md#closing-step' not in body:
            errors.append((lane, command))
        if after != command.split()[0]:
            errors.append(('wrong-after', command))
    return errors


class Routing(unittest.TestCase):
    def test_all_declared_procedures_have_a_shared_pointer(self):
        page = PAGE.read_text()
        self.assertEqual(routing_errors(page, lambda p: (ROOT / p).read_text()), [])
        expected = {
            'router': 'setup relocate adopt diagnose',
            'goals': 'init revise commit plan-phase score-phase snapshot plan-week link pivot',
            'decide': 'init new resolve lock revise supersede drop adr',
            'work': 'bootstrap plan-week triage status friday-review monday-plan midweek-check mid-phase-review end-phase-retro risk add-task close-task drop-task coordinate handoff rollover delegate dispatch autopilot digest review health-check architecture-audit runbook-check',
        }
        actual = {(l, c) for l, c, _, _ in routes(page)}
        wanted = {(l, c) for l, commands in expected.items() for c in commands.split()}
        wanted |= {('work', c) for c in ('architecture init', 'architecture review', 'incident', 'incident close', 'incident archive')}
        self.assertEqual(actual, wanted)
        self.assertEqual(len(routes(page)), len(wanted), 'duplicate routes')

    def test_each_lane_index_command_is_explicitly_classified(self):
        declared = {(lane, command.split()[0]) for lane, command, _, _ in routes(PAGE.read_text())}
        readonly = {'goals': {'krs', 'dashboard', 'help'},
                    'work': {'nudge', 'help'},
                    'decide': {'status', 'handoff', 'help'}}
        for lane in readonly:
            text = (ROOT / lane / 'SKILL.md').read_text().split('## Subcommand index', 1)[1]
            text = text.split('\n## ', 1)[0]
            # Parse declared table cells only, never classify procedure prose.
            commands = re.findall(r'^\| `([^`]+)`', text, re.M)
            self.assertTrue(commands)
            for command in commands:
                token = command.split()[0]
                self.assertTrue((lane, token) in declared or token in readonly[lane],
                                f'{lane} {token}: classify new command in the closing inventory')

    def test_deleting_any_procedures_pointer_is_detected(self):
        page = PAGE.read_text()
        for lane, command, source, _ in routes(page):
            with self.subTest(lane=lane, command=command):
                marker = f'<!-- next-close: {lane} {command} -->'
                def read(path):
                    body = (ROOT / path).read_text()
                    return body.replace(marker, '') if path == source else body
                self.assertIn((lane, command), routing_errors(page, read))

    def test_shared_protocol_keeps_the_three_suppressions_and_choice_boundary(self):
        closing = PAGE.read_text().split('## Closing step', 1)[1].split('### Procedure inventory', 1)[0]
        for phrase in ('dispatched agent sessions', 'planning in progress',
                       'settings.proactive_next_steps', '`off` skips',
                       '`primary: null`', '**no question**', 'Not now',
                       'Do not execute a recommendation merely because it was returned',
                       '--section next --after <subcommand>', 'Nonempty `conformance.rule_errors`'):
            self.assertIn(phrase, closing)
        self.assertNotIn('--after <subcommand> --compact', closing)


class Preference(unittest.TestCase):
    def test_default_roundtrip_silence_restore_and_invalid_no_write(self):
        with tempfile.TemporaryDirectory(prefix='next-closing-config-') as temp:
            root = Path(temp)
            def run(*args):
                return inproc.run('perry-config', [*args, '--root', str(root)], cwd=ROOT)
            def setting():
                result = run('show', '--json')
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)['settings'].get('proactive_next_steps', 'on')
            self.assertEqual(setting(), 'on')
            for value in ('off', 'on'):
                result = run('set', 'Proactive next steps', value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(setting(), value)
            before = (root / '.perry/config.jsonl').read_bytes()
            for invalid in ('false', 'OFF', '', 'sometimes'):
                result = run('set', 'Proactive next steps', invalid)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((root / '.perry/config.jsonl').read_bytes(), before)
            self.assertEqual(run('unset', 'Proactive next steps').returncode, 0)
            self.assertEqual(setting(), 'on')


class PayloadScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixtures.build(cls, 'closable_phase')
        cls.empty = fixtures.build(cls, 'installed_no_okr')

    def test_actual_after_payload_preserves_primary_and_alternates(self):
        result = inproc.run('perry-state', ['--root', str(self.root), '--section', 'next', '--after', 'close-task'], cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        block = json.loads(result.stdout)['next']
        self.assertEqual(block['primary']['rule'], 'R-phase-closable')
        self.assertLessEqual(len(block['alternates']), 2)
        self.assertIn('reason', block['primary'])
        # Silence is a display preference: the deterministic recommendation is unchanged.
        out = inproc.run('perry-config', ['set', '--root', str(self.root), 'Proactive next steps', 'off'], cwd=ROOT)
        self.assertEqual(out.returncode, 0, out.stderr)
        silenced = inproc.run('perry-state', ['--root', str(self.root), '--section', 'next', '--after', 'close-task'], cwd=ROOT)
        self.assertEqual(json.loads(silenced.stdout)['next'], block)

    def test_actual_no_result_does_not_require_invented_advice(self):
        result = inproc.run('perry-state', ['--root', str(self.empty), '--section', 'next', '--after', 'snapshot'], cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        block = json.loads(result.stdout)['next']
        self.assertIsNone(block['primary'])
        self.assertEqual(block['alternates'], [])


if __name__ == '__main__':
    unittest.main()
