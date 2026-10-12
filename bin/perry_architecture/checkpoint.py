"""Append-only task evidence. No model, target writes, browser or task mutations."""
import hashlib
import json
from pathlib import Path
import re
import uuid
from collections import Counter
from lib import register_stamp

from .analysis import attach, changes
from .audit import compare
from .report import render


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def save(data, stage, task, store, analysis, review, rules=None, baseline=None):
    if stage not in ('start', 'delivery') or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task):
        raise ValueError('checkpoint requires start/delivery and a safe task identifier')
    store = Path(store).resolve()
    if store.is_relative_to(Path(data['root']).resolve()):
        raise ValueError('checkpoint store must be durable and outside the analyzed checkout')
    if not isinstance(review, dict) or review.get('snapshot') != data['snapshot']:
        raise ValueError('host review must reference the current snapshot')
    if (not isinstance(review.get('summary'), str) or not review['summary'].strip() or
            type(review.get('target_change_requested')) is not bool or
            not isinstance(review.get('findings'), list)):
        raise ValueError('review needs summary, findings and target_change_requested')
    for finding in review['findings']:
        if (not isinstance(finding, dict) or not all(isinstance(finding.get(k), str) and finding[k].strip()
                                                   for k in ('reason', 'target')) or
                not isinstance(finding.get('evidence'), list) or not finding['evidence'] or
                any(e not in data['evidence'] for e in finding['evidence'])):
            raise ValueError('semantic finding needs reason, target citation and valid evidence IDs')
    attach(data, analysis)
    reasons = []
    limited = False
    added_unknowns = Counter()
    base = None
    if stage == 'start':
        if baseline or rules is None:
            raise ValueError('start requires rules and no baseline')
    else:
        if rules is not None or not baseline:
            raise ValueError('delivery uses baseline rules; do not supply replacement rules')
        base, _ = load_checkpoint(baseline)
        if (base.get('version') != 1 or base.get('stage') != 'start' or base.get('task') != task or
                base.get('root') != data['root']):
            raise ValueError('baseline must be this task and checkout start checkpoint')
        previous = base['report']
        for key in ('source_roots', 'excludes', 'max_file_bytes'):
            if data['scope'][key] != previous['scope'][key]:
                raise ValueError('scan scope changed; preserve baseline scope for delivery')
        rules = base['rules']
        data['changes'] = changes(data, previous)
    target_changes = []
    if base:
        for doc in rules['documents']:
            path = (Path(data['root']) / doc['path']).resolve()
            if not path.is_relative_to(Path(data['root'])):
                raise ValueError('baseline target escapes checkout')
            raw = path.read_bytes() if path.is_file() else None
            current = hashlib.sha256(raw).hexdigest() if raw is not None else None
            if current != doc['sha256']:
                target_changes.append({'path': doc['path'], 'baseline_sha256': doc['sha256'],
                                       'current_sha256': current,
                                       'baseline_source': next(t['source'] for t in base['report']['comparison']['targets'] if t['path'] == doc['path']),
                                       'current_source': raw.decode('utf-8', errors='replace') if raw is not None else None})
    if target_changes:
        reasons.append('target_changed')
        # Keep current facts, but never present an old comparison as current.
        data['comparison'] = {'version': 1, 'snapshot': data['snapshot'], 'targets': [],
                              'results': [], 'summary': {},
                              'limits': 'Target changed or disappeared. Baseline rules were not reinterpreted; user discussion required.'}
    else:
        compare(data, rules)
        if data['comparison']['summary']['violation']:
            reasons.append('constraint_violation')
        limited = bool(unknowns(data)) or bool(data['comparison']['summary']['unknown'])
        added_unknowns = unknowns(data) - unknowns(base['report']) if base else Counter()
        if added_unknowns:
            reasons.append('new_unresolved_checks')
    coverage = data['issues'] + data['architecture']['issues']
    limited = limited or bool(coverage)
    previous_coverage = base['report']['issues'] + base['report']['architecture']['issues'] if base else []
    if not data['files'] or (base and any(i not in previous_coverage for i in coverage)):
        reasons.append('incomplete_coverage')
    if review['findings']:
        reasons.append('semantic_drift')
    if review['target_change_requested']:
        reasons.append('target_change_requested')
    stamp = register_stamp().replace('-', '').replace(':', '') + '-' + uuid.uuid4().hex[:10]
    directory = store / task / (stage + '-' + stamp)
    notice = {'stage': stage, 'task': task, 'snapshot': data['snapshot'],
              'status': 'attention' if reasons else 'limited' if limited else 'normal', 'open_report': bool(reasons),
              'reasons': reasons, 'target_changes': target_changes, 'review': review,
              'new_blind_spots': [{'kind': key[0], 'detail': json.dumps(key[1:], ensure_ascii=False),
                                   'count': count,
                                   'evidence': [eid for eid, item in data['evidence'].items()
                                                if key[0] in ('call', 'import') and item['kind'] == key[0]
                                                and item.get('source') == key[1] and item.get('statement') == key[2]]}
                                  for key, count in added_unknowns.items()],
              'baseline': str(Path(baseline).resolve()) if baseline else None,
              'baseline_sha256': digest(base) if base else None,
              'report': str(directory / 'index.html'), 'checkpoint': str(directory),
              'summary': '需要讨论架构检查结果' if reasons else ('架构检查：未发现已确认偏离，存在静态分析盲区；证据已保存。' if limited else '架构检查：所检查范围内未发现偏离；证据已保存。')}
    data['checkpoint'] = notice
    bundle = {'version': 1, 'stage': stage, 'task': task, 'root': data['root'],
              'analysis': analysis, 'review': review, 'rules': rules, 'report': data}
    directory.mkdir(parents=True, exist_ok=False)
    # Receipt is the completion marker. A partial directory is never a valid checkpoint.
    with (directory / 'bundle.json').open('x', encoding='utf-8') as stream:
        json.dump(bundle, stream, ensure_ascii=True)
    html = render(data).encode('utf-8')
    with (directory / 'index.html').open('xb') as stream:
        stream.write(html)
    receipt = {**notice, 'bundle_sha256': digest(bundle),
               'html_sha256': hashlib.sha256(html).hexdigest()}
    with (directory / 'receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=True, indent=2)
    return receipt


def load_checkpoint(directory):
    directory = Path(directory)
    bundle, receipt = read(directory / 'bundle.json'), read(directory / 'receipt.json')
    if not isinstance(bundle, dict) or not isinstance(receipt, dict) or digest(bundle) != receipt.get('bundle_sha256'):
        raise ValueError('checkpoint bundle hash mismatch')
    if hashlib.sha256((directory / 'index.html').read_bytes()).hexdigest() != receipt.get('html_sha256'):
        raise ValueError('checkpoint HTML report hash mismatch')
    recorded = {k: v for k, v in receipt.items() if k not in ('bundle_sha256', 'html_sha256')}
    if recorded != bundle.get('report', {}).get('checkpoint'):
        raise ValueError('checkpoint receipt does not match bundle')
    return bundle, receipt


def verify(data, directory):
    bundle, receipt = load_checkpoint(directory)
    if bundle['root'] != data['root'] or bundle['report']['snapshot'] != data['snapshot']:
        raise ValueError('checkpoint is stale or belongs to another checkout')
    if any(f.get('sha256') is None for f in data['files']):
        raise ValueError('cannot verify freshness: source bytes were not fingerprinted; inspect unreadable files')
    saved = bundle['report']
    expected = {d['path']: d['sha256'] for d in bundle['rules']['documents']}
    for change in saved['checkpoint']['target_changes']:
        expected[change['path']] = change['current_sha256']
    for name, sha in expected.items():
        path = (Path(data['root']) / name).resolve()
        if not path.is_relative_to(Path(data['root'])):
            raise ValueError('target escapes checkout')
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != sha:
            raise ValueError('checkpoint target changed since check: ' + name)
    if receipt['baseline']:
        base, _ = load_checkpoint(receipt['baseline'])
        if digest(base) != receipt['baseline_sha256']:
            raise ValueError('baseline changed since delivery')
    return {**receipt, 'fresh': True,
            'verification_limit': 'Fresh evidence, not semantic approval or independent review.'}


def unknowns(data):
    result = Counter()
    for item in data['imports']:
        if item['resolution'] in ('unresolved', 'ambiguous'):
            result[('import', item['source'], item['statement'], item['resolution'])] += 1
    for item in data['calls']:
        if item['resolution'] == 'unknown':
            result[('call', item['source'], item['statement'])] += 1
    for path in data['scope']['skipped_paths']:
        result[('skipped', path)] += 1
    for rule in data.get('comparison', {}).get('results', []):
        for finding in rule['unknown']:
            refs = [data['evidence'][e] for e in finding['evidence']]
            key = ('rule', rule['id'], finding['reason'], tuple(sorted(
                (r.get('source', ''), r.get('statement', ''), r.get('canonical') or '') for r in refs)))
            result[key] += 1
    return result
