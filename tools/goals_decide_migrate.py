#!/usr/bin/env python3
"""Apply a SHA256-pinned, reviewed format-1 plan using only native bin/perry.

Legacy preparation is retained at the separately pinned old release; see
reviewed-plan-migration.md. This helper never interprets legacy source records.
The CLI permits external scratch rehearsals only and grants no human authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import uuid

HOME = Path(__file__).resolve().parents[1]
ACTOR = {'kind': 'agent', 'name': 'reviewed-plan-migration',
         'session': os.environ.get('CODEX_THREAD_ID') or 'migration-process-' + uuid.uuid4().hex}
NEW_TYPES = ('objective', 'kr', 'check', 'phase', 'design', 'adr')


class Refused(ValueError):
    pass


def encoded(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused('duplicate JSON key: ' + key)
        result[key] = value
    return result


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or
            PurePosixPath(value).is_absolute() or
            any(p in ('', '.', '..') for p in value.split('/'))):
        raise Refused('unsafe relative path')
    return Path(value)


def internal(root, name):
    path = root / relative(name)
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise Refused('symlink source path: ' + name)
    if not path.resolve().is_relative_to(root):
        raise Refused('foreign source path: ' + name)
    return path


@dataclass(frozen=True)
class Record:
    key: str
    type: str
    fields: dict
    state: str
    attachments: list
    expected_id: str = ''


class Plan:
    """Read serialized facts only; recheck bytes and bounded source inventory."""
    def __init__(self, path, sha256, source=None):
        self.path = Path(path).resolve()
        if not isinstance(sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', sha256):
            raise Refused('plan SHA256 must be explicit lowercase hex')
        self.sha256 = sha256
        raw = self.path.read_bytes()
        if digest(raw) != sha256:
            raise Refused('plan SHA256 mismatch')
        self._doc = json.loads(raw, object_pairs_hook=unique_object,
                               parse_constant=lambda x: (_ for _ in ()).throw(Refused('nonfinite JSON')))
        d = self._doc
        keys = {'format','source','state_root','source_hashes','counts','warnings',
                'records','relations','legacy_records','requirements','prefix_ceilings'}
        if not isinstance(d, dict) or set(d) != keys or type(d['format']) is not int or d['format'] != 1:
            raise Refused('unsupported plan format/fields')
        if not isinstance(d['source'], str) or not Path(d['source']).is_absolute():
            raise Refused('plan source must be absolute')
        anchor = Path(source if source is not None else d['source']).absolute()
        if any(p.is_symlink() for p in (anchor, *anchor.parents)):
            raise Refused('symlink source anchor')
        self.source = anchor.resolve()
        if not self.source.is_dir():
            raise Refused('source anchor missing')
        self.state = internal(self.source, d['state_root'])
        if not self.state.is_dir():
            raise Refused('source state root missing')
        self.hashes = d['source_hashes']
        if not isinstance(self.hashes, dict) or not self.hashes:
            raise Refused('source hashes missing')
        for name, value in self.hashes.items():
            internal(self.source, name)
            if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
                raise Refused('invalid source hash')
        if (not isinstance(d['records'], list) or not isinstance(d['relations'], list) or
                not isinstance(d['counts'], dict) or not isinstance(d['legacy_records'], dict) or
                any(not isinstance(d[k], list) or any(not isinstance(x, str) for x in d[k])
                    for k in ('warnings','requirements'))):
            raise Refused('invalid plan collections')
        self.records = {}
        ids = set()
        for row in d['records']:
            if not isinstance(row, dict) or set(row) != {'key','type','fields','state','attachments','expected_id'}:
                raise Refused('invalid record fields')
            r = Record(**row)
            if not isinstance(r.key, str) or not r.key or r.key in self.records:
                raise Refused('duplicate/invalid record key')
            if r.type not in NEW_TYPES or not isinstance(r.state, str):
                raise Refused('unknown record type/state')
            if not isinstance(r.fields, dict) or r.fields.get('source_key') != r.key:
                raise Refused('record source_key mismatch')
            if not isinstance(r.expected_id, str):
                raise Refused('invalid expected ID')
            if r.type in ('design','adr'):
                prefix = 'DESIGN' if r.type == 'design' else 'ADR'
                if not re.fullmatch(prefix + r'-[0-9]{3,}', r.expected_id) or int(r.expected_id.split('-')[1]) < 1:
                    raise Refused('missing/invalid filename identity')
            elif r.expected_id:
                raise Refused('unexpected filename identity')
            if r.expected_id and r.expected_id in ids:
                raise Refused('duplicate expected ID')
            ids.add(r.expected_id)
            if not isinstance(r.attachments, list):
                raise Refused('invalid attachments')
            seen = set()
            for a in r.attachments:
                if not isinstance(a, dict) or set(a) != {'ref','hash'} or not isinstance(a['hash'], str):
                    raise Refused('invalid attachment')
                target = internal(self.source, str(relative(d['state_root']) / relative(a['ref'])))
                name = target.relative_to(self.source).as_posix()
                if a['ref'] in seen or a['hash'] != 'sha256:' + self.hashes.get(name, ''):
                    raise Refused('duplicate/unpinned attachment')
                seen.add(a['ref'])
            self.records[r.key] = r
        self.edges = set()
        for edge in d['relations']:
            if (not isinstance(edge, list) or len(edge) != 3 or
                    any(not isinstance(x, str) for x in edge)):
                raise Refused('invalid relation')
            kind, src, dst = edge
            if src not in self.records or dst not in self.records:
                raise Refused('dangling relation')
            if tuple(edge) in self.edges:
                raise Refused('duplicate relation')
            self.edges.add(tuple(edge))
        self.coverage = Counter(r.type for r in self.records.values())
        if dict(self.coverage) != d['counts'] or any(type(n) is not int for n in d['counts'].values()):
            raise Refused('plan counts mismatch')
        self.warnings, self.requirements = d['warnings'], d['requirements']
        if (not isinstance(d['prefix_ceilings'], dict) or set(d['prefix_ceilings']) != {'ADR','DESIGN'} or
                any(type(n) is not int or n < 0 for n in d['prefix_ceilings'].values())):
            raise Refused('invalid prefix ceilings')
        for r in self.records.values():
            if r.expected_id:
                prefix, n = r.expected_id.split('-')
                if int(n) > d['prefix_ceilings'][prefix]:
                    raise Refused('filename exceeds prefix ceiling')
        self._frozen = encoded(d)
        self.unchanged()

    def document(self):
        # Keep opaque raw legacy facts and every serialized field exactly.
        result = dict(self._doc)
        result['records'] = [asdict(r) for r in self.records.values()]
        result['relations'] = [list(e) for e in sorted(self.edges)]
        return result

    def unchanged(self):
        if digest(self.path.read_bytes()) != self.sha256 or encoded(self.document()) != self._frozen:
            raise Refused('reviewed plan changed')
        for name, expected in self.hashes.items():
            path = internal(self.source, name)
            if not path.is_file() or digest(path.read_bytes()) != expected:
                raise Refused('source changed: ' + name)
        # Fixed input names are inventory too: a previously absent input must
        # not silently appear after review. No contents are interpreted here.
        candidates = [self.state/n for n in ('OKR.md','okr.jsonl','linkage.jsonl','tasks.jsonl')]
        candidates += [self.source/'.perry'/n for n in ('config.jsonl','hook.md')]
        for path in candidates:
            name = path.relative_to(self.source).as_posix()
            internal(self.source, name)
            if path.exists() and name not in self.hashes:
                raise Refused('new source file: ' + name)
        # Inventory only: no Markdown/JSONL parsing, including unlisted files.
        for directory in ('phase','design','decisions'):
            base = internal(self.source, str(relative(self._doc['state_root']) / directory))
            if base.exists():
                for path in base.rglob('*'):
                    name = path.relative_to(self.source).as_posix()
                    internal(self.source, name)
                    if path.is_file() and name not in self.hashes:
                        raise Refused('new source file: ' + name)


class Kernel:
    def __init__(self, root, store, *, testing=True):
        self.root, self.store = Path(root).resolve(), Path(store).resolve()
        self.commands = []
        self.testing = testing

    def call(self, command, body=None, dry=False):
        argv = [str(HOME/'bin/perry'), *command.split(), '--root',str(self.root),'--store',str(self.store)]
        if body is not None:
            argv += ['--input','-']
        if dry:
            argv += ['--dry-run']
        env = {k:v for k,v in os.environ.items() if k not in ('PERRY_HOME','PERRY_STORE','PERRY_PROJECT','PERRY_KERNEL_TESTING')}
        if self.testing:
            env['PERRY_KERNEL_TESTING'] = '1'
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
        'check':{'check_retired':['retire']},
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


def execute(plan, kernel, template):
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
    if floor_capable:
        kernel.call('template apply',{'actor':ACTOR,'template':template,'ceilings':plan._doc['prefix_ceilings'],'note':'Preserve reviewed legacy filename ceilings'})
    plan.unchanged()
    kernel.call('export')
    return dict(mapping=mapping, protected_items=len(protected), protected_events=len(old_events['events']),
                counts=dict(Counter(i['type'] for i in after.values())), store_seq=kernel.call('query',{'limit':0})['store_seq'])


def save_commands(kernel, work):
    if not kernel.commands:
        return None
    path=work/('commands-' + uuid.uuid4().hex + '.json')
    with path.open('x') as stream:
        stream.write(encoded(kernel.commands)+'\n')
    return str(path)


def checked_template(plan, before):
    template = json.loads((HOME/'templates/process/perry.json').read_text())
    last_ids = {}
    for r in plan.records.values():
        decl = template['types'][r.type]
        if r.expected_id:
            number = int(r.expected_id.split('-')[1])
            canonical = decl['prefix'] + '-' + str(number).zfill(decl['digits'])
            if r.expected_id != canonical or number <= last_ids.get(r.type, 0):
                raise Refused('noncanonical/out-of-order filename identity: ' + r.key)
            last_ids[r.type] = number
        if r.state not in decl['states']:
            raise Refused('unknown target state: ' + r.key)
        if set(r.fields) - set(decl['fields']):
            raise Refused('unknown target field: ' + r.key)
        state = decl['initial']
        for move in transition_path(r.type, r.state):
            tr = decl['transitions'][move]
            if state not in tr['from']:
                raise Refused('invalid lifecycle path: ' + r.key)
            state = tr['to']
        if state != r.state:
            raise Refused('unsupported target lifecycle: ' + r.key)
    for kind, src, dst in plan.edges:
        if kind in ('blocks','parent'):
            continue  # Native preflight owns built-in relation constraints.
        decl = template['relations'].get(kind)
        if not decl or plan.records[src].type not in decl['from'] or plan.records[dst].type not in decl['to']:
            raise Refused('unknown/invalid relation: ' + kind)
    existing = {}
    for item in before:
        if item['type'] not in NEW_TYPES:
            continue
        key = item['fields'].get('source_key')
        if key not in plan.records:
            raise Refused('native F items lack a matching migration identity')
        if key in existing:
            raise Refused('duplicate native source_key')
        existing[key] = item
        r = plan.records[key]
        if (item['type'] != r.type or
                stored_fields(item, template) != {k:r.fields.get(k) for k in template['types'][r.type]['fields']}):
            raise Refused('native item changed since migration: ' + key)
        if r.expected_id and item['id'] != r.expected_id:
            raise Refused('legacy/native filename identity conflict: ' + key)
        states = [template['types'][r.type]['initial']]
        states += [template['types'][r.type]['transitions'][m]['to'] for m in transition_path(r.type, r.state)]
        if item['state'] not in states:
            raise Refused('native lifecycle changed: ' + key)
        if {(a['ref'],a.get('hash')) for a in item['attachments']} != {(a['ref'],a.get('hash')) for a in r.attachments}:
            raise Refused('changed/missing native attachment: ' + key)
    native_keys = {i['id']:k for k,i in existing.items()}
    for key,item in existing.items():
        for edge in item['relations']:
            if (edge['kind'], native_keys.get(edge['from']), native_keys.get(edge['to'])) not in plan.edges:
                raise Refused('native graph changed: ' + key)
    return template


def reference_field(decl):
    return decl['kind'] == 'ref' or (decl['kind'] == 'list' and reference_field(decl['of']))


def check_reference(value, decl, native):
    if value is None:
        return
    if decl['kind'] == 'list':
        if not isinstance(value, list) or any(x is None for x in value):
            raise Refused('invalid reference list')
        for part in value:
            check_reference(part, decl['of'], native)
    elif not isinstance(value, str) or value not in native or native[value]['type'] not in decl['to']:
        raise Refused('dangling/foreign native reference')


def preflight(plan, kernel, template, before):
    """Let the native CLI validate values and guards in a disposable store.

    Ref fields are checked against the real read-only query, then omitted only
    from these validation creates. No placeholder task or invented history is
    inserted to manufacture a reference or filename ID.
    """
    native = {i['id']:i for i in before}
    with tempfile.TemporaryDirectory(prefix='perry-plan-validation-') as td:
        root = Path(td).resolve()/'root'
        (root/'.perry').mkdir(parents=True)
        probe = Kernel(root, Path(td).resolve()/'validation.db')
        probe.call('init', {'actor':ACTOR,'state_root':plan._doc['state_root']})
        probe.call('template apply', {'actor':ACTOR,'template':template})
        mapping = {}
        for r in plan.records.values():
            fields = {}
            for name, value in r.fields.items():
                decl = template['types'][r.type]['fields'][name]
                if reference_field(decl):
                    check_reference(value, decl, native)
                else:
                    fields[name] = value
            item = probe.call('item create', {'actor':ACTOR,'type':r.type,'fields':fields,
                                             'attachments':r.attachments})['result']['item']
            mapping[r.key] = item['id']
            for move in transition_path(r.type, r.state):
                item = probe.call('item move', {'actor':ACTOR,'id':item['id'],'transition':move,
                                               'expect':{item['id']:item['seq']}})['result']['item']
            if item['state'] != r.state:
                raise Refused('unreconciled validation state')
        # Native checks relation cycles, endpoints and rollup rules too.
        for kind, src, dst in sorted(plan.edges):
            probe.call('rel add', {'actor':ACTOR,'kind':kind,'from':mapping[src],'to':mapping[dst]})
    plan.unchanged()


def apply(plan, kernel):
    plan.unchanged()
    if kernel.testing:
        common = Path(os.path.commonpath([kernel.root, kernel.store]))
        scratch_paths(plan.source, kernel.root, kernel.store, common)
    before = kernel.items()
    template = checked_template(plan, before)
    preflight(plan, kernel, template, before)
    return execute(plan, kernel, template)


def scratch_paths(source, root, store, work):
    if (root == work or store == work or not root.is_relative_to(work) or not store.is_relative_to(work) or
            root == source or source.is_relative_to(root) or root.is_relative_to(source) or
            work.is_relative_to(source) or store.is_relative_to(source) or source.is_relative_to(store) or store.is_relative_to(root) or
            any((a/'.git').exists() for path in (work,root,store.parent) for a in [path,*path.parents])):
        raise Refused('root/store must be distinct scratch children of external --work; source is read-only')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True, help='immutable reviewed format-1 plan')
    p.add_argument('--plan-sha256', required=True, help='independently reviewed SHA256 of exact plan bytes')
    p.add_argument('--source', type=Path, help='override source anchor; contents must match reviewed hashes')
    p.add_argument('--root', type=Path, required=True, help='explicit scratch native anchor')
    p.add_argument('--store', type=Path, required=True, help='explicit copied native scratch database')
    p.add_argument('--work', type=Path, required=True, help='external scratch output directory')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='apply to scratch only')
    mode.add_argument('--dry-run', '--plan-only', action='store_true', help='validate without target store writes (default)')
    args = p.parse_args(argv)
    plan = Plan(args.plan, args.plan_sha256, args.source)
    root, store, work = (getattr(args,k).resolve() for k in ('root','store','work'))
    scratch_paths(plan.source, root, store, work)
    if plan.path.is_relative_to(root) or plan.path == store:
        raise Refused('plan overlaps apply output')
    kernel = Kernel(root, store)
    work.mkdir(parents=True, exist_ok=True)
    result = dict(effect='plan', plan_sha256=plan.sha256, source=str(plan.source),
                  counts=dict(plan.coverage), warnings=plan.warnings, requirements=plan.requirements)
    try:
        if args.apply:
            result.update(effect='rehearsed', **apply(plan, kernel))
        else:
            before = kernel.items()
            template = checked_template(plan, before)
            preflight(plan, kernel, template, before)
    except (Refused, OSError, ValueError, KeyError) as exc:
        result.update(effect='refused', error=str(exc), partial=bool(kernel.commands),
                      next_action='Reconcile native source_key items/events and source hashes before resuming; never repeat guessed creates.')
    result['commands'] = save_commands(kernel, work)
    # Every attempt retains its own receipt, including partial native writes.
    receipt = work/('receipt-' + uuid.uuid4().hex + '.json')
    result['receipt'] = str(receipt)
    with receipt.open('x') as stream:
        stream.write(encoded(result)+'\n')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return int(result['effect'] == 'refused')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Refused, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}, ensure_ascii=True))
        sys.exit(1)
