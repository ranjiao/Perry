#!/usr/bin/env python3
"""One-shot DESIGN-023 F adapter. Reads frozen legacy sources; calls CLI only.

No kernel imports, live-store discovery, SQL writes, prose measurement, or guessed
linkage. Apply is deliberately restricted to explicit rehearsal paths. The saved
commands are reviewable activation inputs; root owns approved live replay.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

HOME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HOME / 'viewer'), str(HOME / 'bin')]
import parsers as P
import perry_md_store as MD
import lib

ACTOR = {'kind': 'agent', 'name': 'goals-decide-migration',
         'session': os.environ.get('CODEX_THREAD_ID') or 'goals-decide-' + uuid.uuid4().hex}
NEW_TYPES = ('objective', 'kr', 'check', 'phase', 'design', 'adr')


class Refused(ValueError):
    pass


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def version(label):
    m = re.match(r'v\d+\b', label or '')
    return m.group() if m else label or ''


def meaningful(value):
    return value not in (None, '', '—', '-', 'TBD', '(none)')


@dataclass
class Record:
    key: str
    type: str
    fields: dict
    state: str
    attachments: list
    expected_id: str = ''


class Plan:
    def __init__(self, source: Path):
        self.source = source.resolve()
        self.state = P.resolve_state_root(self.source)
        if not self.state.is_dir() or not self.state.is_relative_to(self.source):
            raise Refused('source has no internal state root')
        recovery = P.scan_recovery(self.state,self.source)
        if recovery['blocking']:
            raise Refused('source recovery is blocking: '+encoded(recovery))
        self.records = {}
        self.edges = set()
        self.hashes = self.source_hashes()
        self.warnings = []
        self.coverage = Counter()
        self.goal_index = []
        self.phases = {}
        self.work_refs = {}
        self.native_ids = set()
        self.source_records = {}
        self.requirements = []

    def source_hashes(self):
        # Only the bounded F inputs and referenced measurement attachments.
        # Unrelated work evidence (including this run's architecture evidence)
        # is not a dependency of the one-shot migration.
        paths = {self.state / n for n in ('OKR.md','okr.jsonl','linkage.jsonl','tasks.jsonl')}
        for directory in ('phase','design','decisions'):
            paths.update((self.state/directory).rglob('*'))
        paths.update(self.source/'.perry'/n for n in ('config.jsonl','hook.md'))
        for r in P.load_linkage_store(self.state) or []:
            if isinstance(r,dict) and r.get('kind') == 'measurement' and isinstance(r.get('evidence'),str):
                path = self.state/r['evidence']
                if path.is_relative_to(self.state):
                    paths.add(path)
        return {str(p.relative_to(self.source)):digest(p.read_bytes()) for p in sorted(paths)
                if p.is_file() and p.is_relative_to(self.source)}

    def unchanged(self):
        if self.source_hashes() != self.hashes:
            raise Refused('source changed during planning/rehearsal; take a new copy')

    def read(self, name, loader):
        p = self.state / name
        rows = loader(self.state)
        if rows is None and p.exists():
            raise Refused(f'unreadable source store: {p}')
        if not all(isinstance(r, dict) for r in (rows or [])):
            raise Refused(f'non-object record in {p}')
        self.source_records[name] = rows or []
        return rows or []

    def attachment(self, path):
        p = self.state / path
        if not p.is_file():
            raise Refused(f'missing attachment: {p}')
        return {'ref': path, 'hash': 'sha256:' + digest(p.read_bytes())}

    def add(self, key, typ, raw, title, label, scope, state, path, extra=None, expected_id=''):
        if key in self.records:
            raise Refused(f'duplicate legacy identity: {key}')
        fields = dict(title=title or label or key, legacy_id=label, legacy_scope=scope,
                      source_key=key, source_hash=digest(encoded(raw).encode()), legacy_record=encoded(raw))
        fields.update(extra or {})
        if state in ('goal_retired','phase_dropped','design_superseded','design_dropped','adr_superseded','adr_expired','adr_archived') and not fields.get('reason'):
            fields['reason'] = 'Historical source metadata: ' + label
        r = Record(key, typ, fields, state, [self.attachment(path)] if path else [], expected_id)
        self.records[key] = r
        self.coverage[typ] += 1
        return key

    def edge(self, kind, src, dst):
        if src not in self.records or dst not in self.records:
            raise Refused(f'dangling planned relation: {kind} {src} {dst}')
        self.edges.add((kind, src, dst))

    def resolve(self, label, ver='', phase='', context=''):
        candidates = [r for r in self.goal_index if label in r['labels']]
        if ver:
            candidates = [r for r in candidates if version(r['scope']) == version(ver)]
        elif phase and not label.startswith('P') and self.phases.get(phase, {}).get('version'):
            candidates = [r for r in candidates if version(r['scope']) == self.phases[phase]['version']]
        if len(candidates) != 1:
            raise Refused(f'ambiguous/unresolved legacy linkage {context}: {label!r} version={ver!r} phase={phase!r}; candidates={[r["key"] for r in candidates]}')
        return candidates[0]['key']

    def build(self, native):
        self.native_ids = {r['id'] for r in native}
        self.native_tasks = {r['id'] for r in native if r['type'] == 'task'}
        self.build_phases()
        self.build_overall()
        self.build_linkage()
        self.build_decide()
        self.unchanged()
        return self

    def build_phases(self):
        pointer = P.read_phase_pointer(self.state)
        for path in sorted((self.state / 'phase').glob('*.md')):
            if not re.match(r'\d{3}-', path.stem):
                continue
            raw_text = path.read_text()
            phase = P.parse_phase(path.stem, raw_text)
            headers = P.adr_header_fields(raw_text)
            source = headers.get('source', '')
            vm = re.search(r'\bv\d+\b', source)
            status = headers.get('status', '')
            if status not in ('active', 'scored', 'draft', 'dropped'):
                raise Refused(f'unknown phase status {path}: {status}')
            if status == 'active' and pointer != path.stem:
                raise Refused(f'active phase/pointer disagreement: {path.stem} / {pointer}')
            key = 'phase:' + path.stem
            self.add(key, 'phase', {'headers': headers}, path.stem, path.stem, '', 'phase_' + status,
                     str(path.relative_to(self.state)), {'phase_slug': path.stem, 'started_on': headers.get('started', ''),
                        'source_version': vm.group() if vm else '', 'approval_ref': 'historical source: ' + str(path.relative_to(self.state)),
                        'close_evidence': 'historical scored header' if status == 'scored' else '',
                        'retro_ref': str(path.relative_to(self.state)) if status == 'scored' else ''})
            self.phases[path.stem] = dict(key=key, version=vm.group() if vm else '')
        if pointer and pointer not in self.phases:
            raise Refused(f'phase pointer has no document: {pointer}')

    def build_overall(self):
        rows = self.read('okr.jsonl', P.load_okr_store)
        raw_rows = list(rows)
        # Archive is a real source, not a guess from a later identical version.
        for path in sorted((self.state / 'phase' / 'snapshots').glob('okr-v*.md')):
            _, sites = MD.scan_okr(path.read_text())
            archive = []
            for site in sites:
                rec = {'kind': site['kind'], **site['values']}
                if rec['kind'] not in ('objective', 'kr'):
                    continue
                if rec['kind'] == 'objective':
                    ordinal = re.search(r'\d+', rec['heading'])
                    if not ordinal:
                        raise Refused(f'no objective ordinal in {path}')
                    rec['id'] = 'O-' + ordinal.group()
                rec['_attachment'] = str(path.relative_to(self.state))
                archive.append(rec)
            versions = {version(r.get('version')) for r in rows if r.get('kind') in ('objective', 'kr')}
            rows += [r for r in archive if version(r.get('version')) not in versions]
        views, errors = lib.kr_revisions(rows, 'okr.jsonl')
        if errors:
            raise Refused('invalid overall revisions: ' + encoded(errors))
        folded = lib.fold_kr_records(rows, 'okr.jsonl')
        self.version_records = [r for r in raw_rows if r['kind'] == 'version']
        current = max((version(r.get('version')) for r in rows if r.get('kind') == 'objective'), key=lambda s: int(s[1:]) if re.fullmatch(r'v\d+', s) else -1, default='')
        for kind in ('objective', 'kr'):
            for r in folded:
                if r['kind'] != kind:
                    continue
                scope = r.get('version', '')
                if not scope:
                    raise Refused('overall record without version: ' + encoded(r))
                key = f'overall:{scope}:{kind}:{r.get("id", "")}'
                view = views.get(lib.kr_revision_key(r, 'okr.jsonl'), {}) if kind == 'kr' else {}
                retired = view.get('status') == 'withdrawn'
                state = 'goal_retired' if retired else 'goal_active'
                raw = {'record': r, 'revisions': view.get('revisions', []), 'source_records':[x for x in rows if (x.get('kind')=='kr' and x.get('id')==r.get('id') and x.get('version')==r.get('version')) or (x.get('kind')=='kr_revision' and x.get('kr')==r.get('id') and x.get('okr_version')==r.get('version'))]}
                extra = dict(okr_version=scope, goal_level='overall', approval_ref='historical source: ' + r.get('_attachment', 'OKR.md'),
                             reason=view.get('withdrawn_reason', '') if retired else '')
                if kind == 'kr':
                    extra.update(metric_text=r.get('metric', ''), due_text=r.get('deadline', ''), stretch=str(r.get('stretch', '')).lower() in ('yes', 'true', 'stretch'))
                key = self.add(key, kind, raw, r.get('title', r.get('text', '')), r.get('id', ''), scope, state, r.get('_attachment', 'OKR.md'), extra)
                labels = [r.get('id', '')]
                km = re.fullmatch(r'KR-O(\d+)\.(\d+)', r.get('id', ''))
                if kind == 'kr' and km:
                    labels.append(f'O{km[1]}-KR{km[2]}')
                if kind == 'objective':
                    labels += [r.get('id', '').replace('-', '')]
                    self.goal_index.append(dict(key=key, labels=labels, scope=scope))
                else:
                    self.goal_index.append(dict(key=key, labels=labels, scope=scope))
                    obj = r.get('objective_id')
                    if not obj:
                        matches = [o for o in folded if o['kind'] == 'objective' and o.get('version') == scope and o.get('heading') == r.get('objective')]
                        if len(matches) != 1:
                            raise Refused('ambiguous overall objective for ' + key)
                        obj = matches[0]['id']
                    self.edge('retired_from' if retired else 'parent', key, self.resolve(obj, scope, context=key))
                if version(scope) != current:
                    self.warnings.append(key + ': historical version retained, not automatically retired')
        # Commitments are real goal promises; no new item type is needed.
        for n, r in enumerate(raw_rows):
            if r['kind'] == 'commitment':
                self.add('commitment:' + str(r.get('id', n)), 'objective', r, r.get('promise', r.get('commitment', 'Commitment')), r.get('id', ''), 'commitments', 'goal_active', 'OKR.md', {'goal_level': 'commitment', 'due_text': str(r.get('due', '')), 'approval_ref': 'historical commitment source'})
            elif r['kind'] not in ('objective', 'kr', 'version', 'kr_revision'):
                raise Refused('unsupported OKR kind: ' + encoded(r))
        for record in self.version_records:
            owners = [r for r in self.records.values() if r.type=='objective' and r.fields.get('goal_level')=='overall' and version(r.fields.get('okr_version'))==version(record.get('version'))]
            if not owners:
                raise Refused('version history without scoped objective: '+encoded(record))
            owners[0].fields['version_record']=encoded(record)

    def build_linkage(self):
        rows = self.read('linkage.jsonl', P.load_linkage_store)
        views, errors = lib.kr_revisions(rows, 'linkage.jsonl')
        if errors:
            raise Refused('invalid phase revisions: ' + encoded(errors))
        folded = lib.fold_kr_records(rows, 'linkage.jsonl')
        for kind in ('objective', 'kr'):
            for r in folded:
                if r['kind'] != kind:
                    continue
                phase = r.get('phase', '')
                if phase not in self.phases:
                    raise Refused('linkage phase missing: ' + encoded(r))
                scope = 'phase:' + phase
                key = f'{scope}:{kind}:{r["id"]}'
                view = views.get(lib.kr_revision_key(r, 'linkage.jsonl'), {}) if kind == 'kr' else {}
                retired = view.get('status') == 'withdrawn'
                extra = dict(goal_level='phase', approval_ref='historical source: linkage.jsonl', reason=view.get('withdrawn_reason', '') if retired else '')
                if kind == 'kr':
                    extra.update(metric_text=r.get('metric', ''), due_text=r.get('due', ''), stretch=bool(r.get('stretch', False)))
                self.add(key, kind, {'record': r, 'revisions': view.get('revisions', []), 'source_records':[x for x in rows if (x.get('kind') in ('objective','kr') and x.get('kind')==kind and x.get('id')==r['id'] and x.get('phase')==phase) or (x.get('kind')=='kr_revision' and x.get('kr')==r['id'])]}, r.get('title', ''), r['id'], scope, 'goal_retired' if retired else 'goal_active', 'phase/' + phase + '.md', extra)
                self.goal_index.append(dict(key=key, labels=[r['id']], scope=scope))
                self.edge('in_phase', key, self.phases[phase]['key'])
                if kind == 'objective':
                    self.edge('parent', key, self.phases[phase]['key'])
                else:
                    self.edge('retired_from' if retired else 'parent', key, self.resolve(r['objective'], scope, context=key))
                    if meaningful(r.get('linked')):
                        self.edge('aligned_to', key, self.resolve(r['linked'], phase=phase, context=key))
                    if any(r.get(k) is not None for k in ('target', 'current')):
                        # Legacy scalar assertions have no typed direction/baseline.
                        # Preserve bytes but never synthesize a measured current.
                        self.warnings.append(key + ': scalar target/current retained as legacy facts; no direction or measurement inferred')
        # Typed task references avoid touching pre-existing task seqs/identities.
        for r in rows:
            kind = r['kind']
            if kind == 'edge':
                ver = r.get('okr_version', '') or self.edge_version(r)
                target = self.resolve(r['kr'], ver, context=encoded(r))
                self.require_task(r['task'])
                self.work_refs.setdefault(target, set()).add(r['task'])
            elif kind in ('project', 'unlinked', 'agent'):
                phase = r.get('phase', '')
                if phase not in self.phases:
                    raise Refused('registry record without known phase: ' + encoded(r))
                f = {'project':'project_registry', 'unlinked':'unlinked_tasks', 'agent':'agent_assignments'}[kind]
                self.records[self.phases[phase]['key']].fields.setdefault(f, []).append(encoded(r))
                if kind == 'project' and meaningful(r.get('kr')):
                    self.resolve(r['kr'], context=encoded(r))
            elif kind not in ('objective', 'kr', 'check', 'measurement', 'kr_revision'):
                raise Refused('unsupported linkage kind: ' + encoded(r))
        for k, refs in self.work_refs.items():
            self.records[k].fields['work_items'] = sorted(refs)
        declared = lib.kr_checks(rows)
        for (kr, ver), checks in declared.items():
            owner = self.resolve(kr, ver, context='check owner')
            for entry in checks:
                c, measurement = entry['check'], entry['measurement']
                direction = {'increase':'up','at_least':'up','decrease':'down','at_most':'down','done':'up'}.get(c.get('direction'))
                if not direction:
                    raise Refused('unknown check direction: ' + encoded(c))
                target = 1 if c['direction'] == 'done' else c.get('target')
                baseline = c.get('baseline') if c['direction'] in ('increase','decrease') else None
                raw = {'declarations':[r for r in rows if r['kind']=='check' and (r.get('kr'),r.get('okr_version',''),r.get('id'))==(kr,ver,c['id'])],
                       'measurements':[r for r in rows if r['kind']=='measurement' and (r.get('kr'),r.get('okr_version',''),r.get('check'))==(kr,ver,c['id'])]}
                extra = dict(check_metric={'target':target,'direction':direction,'baseline':baseline,'current':measurement['value'] if measurement else None},
                             measured_at=measurement.get('asserted_at','') if measurement else '', evidence_ref=measurement.get('evidence','') if measurement else '',
                             command_text=c.get('command',''), measurement_origin='legacy assertion' if measurement else 'unmeasured')
                key = 'check:' + owner + ':' + c['id']
                self.add(key, 'check', raw, c.get('label',''), c['id'], owner, 'check_declared', 'linkage.jsonl', extra)
                self.edge('parent', key, owner)
                if measurement and meaningful(measurement.get('evidence')):
                    ref = measurement['evidence']
                    att = {'ref':ref}
                    if (self.state/ref).is_file():
                        att['hash']='sha256:'+digest((self.state/ref).read_bytes())
                    self.records[key].attachments.append(att)
        for r in rows:
            if r['kind'] == 'measurement' and not any(c['check']['id'] == r['check'] for c in declared.get((r['kr'],r.get('okr_version','')), [])):
                raise Refused('orphan measurement: ' + encoded(r))

    def edge_version(self, edge):
        """Only explicit typed task→design metadata can disambiguate a version."""
        if edge['kr'].startswith('P'):
            return ''
        tasks = P.load_task_store(self.state) or []
        refs = next((r.get('design_refs', []) for r in tasks if r['id'] == edge['task']), [])
        versions = set()
        for doc in P.walk_design(self.state):
            if doc.id not in refs:
                continue
            vm = re.search(r'\bv\d+\b', doc.linked_okr)
            labels = re.findall(r'O\d+-KR\d+|KR-O\d+\.\d+', doc.linked_okr)
            if vm and edge['kr'] in labels:
                versions.add(vm.group())
        if len(versions) == 1:
            self.warnings.append('Version resolved by declared task design_refs and design Linked OKR: ' + edge['task'])
            return versions.pop()
        return ''

    def require_task(self, item):
        if item not in self.native_tasks:
            raise Refused('legacy task reference not in copied native store: ' + item)

    def build_decide(self):
        docs = P.walk_design(self.state)
        docs.sort(key=lambda x: x.id)
        for doc in docs:
            text = (self.state / doc.rel).read_text()
            headers = P.adr_header_fields(text)
            raw_status = doc.status_raw.strip().strip('*` ').lower()
            match = re.match(r'^(?:design\s+)?(in_review|in review|review|draft|locked|superseded|dropped|abandoned)(?=$|[\s(（:：—–·])', raw_status)
            if not match:
                raise Refused('design without a recognized declared status: ' + doc.rel)
            status = {'in_review': 'review', 'in review': 'review',
                      'abandoned': 'dropped'}.get(match[1], match[1])
            key = 'design:' + doc.id
            self.add(key, 'design', headers, doc.title, doc.id, '', 'design_' + status, doc.rel,
                     dict(decided_on=doc.date, locked_on=doc.locked, linked_okr_text=doc.linked_okr,
                          author_text=headers.get('author',''), implementation_owner=headers.get('implementation owner',''),
                          approval_ref='historical source: ' + doc.rel), expected_id=doc.id)
        for adr in P.read_adr_records(self.state):
            key = 'adr:' + adr['id']
            headers = P.adr_header_fields((self.state/adr['path']).read_text())
            if not meaningful(headers.get('status')):
                raise Refused('ADR without declared status: '+adr['path'])
            self.add(key, 'adr', {**adr,'headers':headers}, adr['title'], adr['id'], '', 'adr_' + adr['status'], adr['path'],
                     dict(decided_on=adr['date'], decision_type=adr['type'], deciders_text=adr['deciders'], sunset_text=adr['sunset'],
                          approval_ref='historical source: ' + adr['path']), expected_id=adr['id'])
        # File ceilings must be attainable with real records and current primitives.
        for typ, prefix in [('design','DESIGN'), ('adr','ADR')]:
            ids = [r.expected_id for r in self.records.values() if r.type == typ]
            if ids != [f'{prefix}-{n:03d}' for n in range(1,len(ids)+1)]:
                self.requirements.append(f'{prefix}: sparse filenames need approved prefix-floor primitive; see tools/TASK-492-kernel-proposal.md')
        for doc in docs:
            key = 'design:' + doc.id
            linked = doc.linked_okr
            vm = re.search(r'\bv\d+\b', linked)
            phase_ids = re.findall(r'P\d{3}-O\d+-KR\d+', linked)
            phase = next((p for p in self.phases if any(k.startswith('P'+p[:3]+'-') for k in phase_ids)), '')
            labels = re.findall(r'P\d{3}-O\d+-KR\d+|O\d+-KR\d+|KR-O\d+\.\d+', linked)
            for match in re.finditer(r'(O\d+)-KR(\d+)[–—](O\d+)-KR(\d+)',linked):
                if match[1]!=match[3] or not 0<=int(match[4])-int(match[2])<=100:
                    raise Refused('unsupported goal range: '+linked)
                labels += [f'{match[1]}-KR{n}' for n in range(int(match[2]),int(match[4])+1)]
            for label in dict.fromkeys(labels):
                self.edge('aligned_to', key, self.resolve(label, vm.group() if vm and not label.startswith('P') else '', phase, key))
        for r in list(self.records.values()):
            if r.type not in ('design','adr'):
                continue
            raw = json.loads(r.fields['legacy_record'])
            for name in ('supersedes','superseded_by'):
                label = raw.get(name,'')
                if meaningful(label):
                    labels = re.findall(r'(?:DESIGN|ADR)-\d+', label)
                    if not labels:
                        raise Refused('unparsed successor metadata: ' + r.key)
                    for ident in labels:
                        target = ('design:' if ident.startswith('DESIGN') else 'adr:') + ident
                        kind = 'supersedes' if re.fullmatch(r'(?:DESIGN|ADR)-\d+',label.strip()) else 'amends'
                        self.edge(kind, r.key if name=='supersedes' else target, target if name=='supersedes' else r.key)
        tasks = P.load_task_store(self.state)
        if tasks is None and (self.state/'tasks.jsonl').exists():
            raise Refused('unreadable legacy task metadata')
        refs = {}
        for task in tasks or []:
            for label in task.get('design_refs', []) or []:
                key = ('adr:' if label.startswith('ADR') else 'design:') + label
                if key not in self.records:
                    raise Refused('dangling task design_refs: ' + label)
                self.require_task(task['id'])
                refs.setdefault(key,set()).add(task['id'])
        for key, ids in refs.items():
            self.records[key].fields['implemented_by'] = sorted(ids)

    def document(self):
        return dict(format=1, source=str(self.source), state_root=str(self.state.relative_to(self.source)),
                    source_hashes=self.hashes, counts=dict(self.coverage), warnings=self.warnings,
                    records=[asdict(r) for r in self.records.values()], relations=sorted(self.edges),
                    legacy_records=self.source_records, requirements=self.requirements, prefix_ceilings={p:max([int(r.expected_id.split('-')[1]) for r in self.records.values() if r.type==t],default=0) for t,p in [('design','DESIGN'),('adr','ADR')]})


class Kernel:
    def __init__(self, root, store):
        self.root, self.store = Path(root).resolve(), Path(store).resolve()
        self.commands = []

    def call(self, command, body=None, dry=False):
        argv = [str(HOME/'bin/perry-kernel'), *command.split(), '--root',str(self.root),'--store',str(self.store)]
        if body is not None:
            argv += ['--input','-']
        if dry:
            argv += ['--dry-run']
        env = {**os.environ,'PERRY_HOME':str(HOME),'PERRY_KERNEL_TESTING':'1'}
        env.pop('PERRY_STORE',None);env.pop('PERRY_PROJECT',None)
        p = subprocess.run(argv,input=encoded(body) if body is not None else None,text=True,capture_output=True,env=env)
        try:
            result = json.loads(p.stdout)
        except ValueError as exc:
            raise Refused(f'kernel invalid response {command}: {p.stderr}') from exc
        if p.returncode or not result.get('ok') or str(result.get('surface','')).split('.')[0] != '1':
            raise Refused(f'kernel refused {command}: {encoded(result)}')
        if not dry and result['effect']=='written':
            self.commands.append({'command':command,'input':body,'store_seq':result['store_seq']})
        return result

    def items(self):
        items, body = [], {'limit':10000}
        while True:
            d = self.call('query',body)['result']; items += d['items']
            if not d['truncated']:
                return items
            body['after'] = d['next_after']


def transition_path(typ, target):
    return {
        'objective':{'goal_active':['approve'],'goal_retired':['withdraw']},
        'kr':{'goal_active':['approve'],'goal_retired':['withdraw']},
        'phase':{'phase_active':['activate'],'phase_scored':['activate','score'],'phase_dropped':['drop']},
        'design':{'design_review':['review'],'design_locked':['lock'],'design_superseded':['lock','supersede'],'design_dropped':['drop']},
        'adr':{'adr_active':['accept'],'adr_superseded':['accept','supersede'],'adr_expired':['accept','expire'],'adr_archived':['accept','archive']}
    }.get(typ,{}).get(target,[])


def stored_fields(item, template):
    fields = dict(item['fields'])
    for key, decl in template['types'][item['type']]['fields'].items():
        if decl['kind'] == 'metric' and fields.get(key) is not None:
            fields[key] = {k:v for k,v in fields[key].items() if k not in ('met','fraction')}
    return fields


def apply(plan, kernel):
    declaration = kernel.call('describe')['result']
    floor_capable = any(c['name']=='template apply' and 'ceilings' in c.get('input',{}) for c in declaration['commands'])
    if plan.requirements and not floor_capable:
        raise Refused('; '.join(plan.requirements))
    before = kernel.items()
    unmanaged = [i['id'] for i in before if i['type'] in NEW_TYPES and i['fields'].get('source_key') not in plan.records]
    if unmanaged:
        raise Refused('native F items lack a matching migration identity: '+encoded(unmanaged))
    old_events = kernel.call('events',{'limit':100000})['result']
    if old_events['truncated']:
        raise Refused('event history exceeds bounded reconciliation; paginate before activation')
    template = json.loads((HOME/'templates/process/perry.json').read_text())
    kernel.call('template apply',{'actor':ACTOR,'template':template})
    existing = {i['fields'].get('source_key'):i for i in kernel.items() if i['type'] in NEW_TYPES and i['fields'].get('source_key')}
    if len(existing) != sum(i['type'] in NEW_TYPES and bool(i['fields'].get('source_key')) for i in kernel.items()):
        raise Refused('duplicate native source_key')
    mapping = {}
    for r in plan.records.values():
        item = existing.get(r.key)
        if item:
            if item['type'] != r.type or stored_fields(item, template) != {k:r.fields.get(k) for k in template['types'][r.type]['fields']}:
                raise Refused('native item changed since migration: ' + r.key)
            if r.expected_id and item['id'] != r.expected_id:
                raise Refused('legacy/native filename identity conflict: ' + r.key)
        else:
            body = {'actor':ACTOR,'type':r.type,'fields':r.fields,'attachments':r.attachments,'note':'Migrate factual source '+r.key}
            preview = kernel.call('item create',body,dry=True)['result']['item']
            if r.expected_id and preview['id'] != r.expected_id:
                prefix, number = r.expected_id.rsplit('-',1)
                actual_prefix, actual_number = preview['id'].rsplit('-',1)
                if floor_capable and actual_prefix==prefix and int(actual_number)<int(number):
                    kernel.call('template apply',{'actor':ACTOR,'template':template,'ceilings':{prefix:int(number)-1},'note':'Reserve actually issued legacy filename floor before '+r.expected_id})
                    preview = kernel.call('item create',body,dry=True)['result']['item']
                if preview['id'] != r.expected_id:
                    raise Refused('prefix floor/native identity conflict: '+r.key+'; requires approved generic primitive')
            item = kernel.call('item create',body)['result']['item']
        mapping[r.key] = item['id']
        path = transition_path(r.type,r.state)
        for move in path:
            if item['state'] == r.state:
                break
            decl = template['types'][r.type]['transitions'][move]
            if item['state'] not in decl['from']:
                continue
            body = dict(actor=ACTOR,id=item['id'],transition=move,expect={item['id']:item['seq']},set={})
            if move in ('withdraw','drop','supersede','archive','expire') and not item['fields'].get('reason'):
                body['set']['reason']='Historical source metadata: '+r.fields['legacy_id']
            item = kernel.call('item move',body)['result']['item']
        if item['state'] != r.state:
            raise Refused('unreconciled native state: ' + r.key)
        actual_att = {(a['ref'],a.get('hash')) for a in item['attachments']}
        if not {(a['ref'],a.get('hash')) for a in r.attachments} <= actual_att:
            raise Refused('changed/missing native attachment: ' + r.key)
    actual = {i['id']:i for i in kernel.items()}
    for kind,src,dst in sorted(plan.edges):
        sid,tid = mapping[src],mapping[dst]
        if not any(e['kind']==kind and e['from']==sid and e['to']==tid for e in actual[sid]['relations']):
            kernel.call('rel add',dict(actor=ACTOR,kind=kind,**{'from':sid,'to':tid},expect={sid:actual[sid]['seq'],tid:actual[tid]['seq']}))
            actual[sid] = kernel.call('item get',{'id':sid})['result']['item']
            actual[tid] = kernel.call('item get',{'id':tid})['result']['item']
    after = {i['id']:i for i in kernel.items()}
    protected = [i for i in before if i['type'] not in NEW_TYPES]
    if any(after[i['id']] != i for i in protected):
        raise Refused('pre-existing work item changed')
    new_events = kernel.call('events',{'limit':100000})['result']
    if new_events['events'][:len(old_events['events'])] != old_events['events']:
        raise Refused('pre-existing events changed')
    plan.unchanged()
    kernel.call('export')
    return dict(mapping=mapping, protected_items=len(protected), protected_events=len(old_events['events']),
                counts=dict(Counter(i['type'] for i in after.values())), store_seq=kernel.call('query',{'limit':0})['store_seq'])


def save_commands(kernel, work):
    if not kernel.commands:
        return None
    n=1
    while (work/f'commands-{n}.json').exists():
        n+=1
    path=work/f'commands-{n}.json'
    path.write_text(encoded(kernel.commands)+'\n')
    return str(path)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='read-only legacy project anchor, copied filesystem preferred')
    p.add_argument('--root',type=Path,required=True,help='explicit scratch project anchor')
    p.add_argument('--store',type=Path,required=True,help='explicit copied native scratch store')
    p.add_argument('--work',type=Path,required=True,help='external output directory containing scratch root and store')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true',help='apply to scratch only; default plan/dry-run never writes store')
    mode.add_argument('--dry-run',action='store_true',help='emit plan and source hashes without any store write')
    args=p.parse_args(argv)
    source,root,store,work=(getattr(args,k).resolve() for k in ('source','root','store','work'))
    if not root.is_relative_to(work) or not store.is_relative_to(work) or source==root or work.is_relative_to(source) or any((a/'.git').exists() for a in [work,*work.parents]):
        raise Refused('root/store must be scratch children of external --work; source is read-only and distinct')
    kernel=Kernel(root,store)
    plan=Plan(source).build(kernel.items())
    work.mkdir(parents=True,exist_ok=True)
    (work/'plan.json').write_text(encoded(plan.document())+'\n')
    result={'effect':'plan','counts':dict(plan.coverage),'warnings':plan.warnings,'requirements':plan.requirements}
    if args.apply:
        try:
            result={'effect':'rehearsed',**apply(plan,kernel)}
        except (Refused,OSError,ValueError,KeyError) as exc:
            result={'effect':'refused','error':str(exc),'commands':save_commands(kernel,work),
                    'partial':bool(kernel.commands),'next_action':'Reconcile native source_key items/events and source hashes before resuming; never repeat guessed creates.'}
            (work/'result.json').write_text(encoded(result)+'\n')
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 1
        result['commands']=save_commands(kernel,work)
    (work/'result.json').write_text(encoded(result)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except (Refused,OSError,ValueError,KeyError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False))
        sys.exit(1)
