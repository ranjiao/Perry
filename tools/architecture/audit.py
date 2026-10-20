"""Evaluate explicit constraints derived by an agent from cited target text.

This validates provenance and checks code; it cannot certify the interpretation
of prose. No target file is ever changed and no Check: command is executed.
"""
import fnmatch
import hashlib
from pathlib import Path


def compare(data, ruleset):
    if not isinstance(ruleset, dict) or type(ruleset.get('version')) is not int or ruleset.get('version') != 1:
        raise ValueError('rules version must be 1')
    documents, rules = ruleset.get('documents'), ruleset.get('rules')
    if not isinstance(documents, list) or not documents or not isinstance(rules, list) or not rules:
        raise ValueError('rules need target documents and nonempty rules')
    root = Path(data['root']).resolve()
    texts, targets = {}, []
    for doc in documents:
        if not isinstance(doc, dict) or not isinstance(doc.get('path'), str):
            raise ValueError('invalid target document')
        path = (root / doc['path']).resolve(strict=True)
        if not path.is_relative_to(root) or Path(doc['path']).is_absolute():
            raise ValueError('target document must be inside project')
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != doc.get('sha256'):
            raise ValueError('stale target rules: ' + doc['path'])
        text = raw.decode('utf-8')
        texts[doc['path']] = text.splitlines()
        targets.append({'path': doc['path'], 'sha256': digest, 'source': text})

    def patterns(rule, key):
        value = rule.get(key)
        if not isinstance(value, list) or not value or any(not isinstance(p,str) or not p for p in value):
            raise ValueError('nonempty pattern array required: ' + key)
        return value

    def matches(value, pats):
        return any(fnmatch.fnmatchcase(value, p) for p in pats)

    results, ids = [], set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get('id'), str) or not rule['id'] or rule['id'] in ids:
            raise ValueError('rule id missing or duplicate')
        ids.add(rule['id'])
        ref = rule.get('source', {})
        if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
            raise ValueError('invalid rule source')
        lines = texts.get(ref.get('path'))
        start, end = ref.get('line'), ref.get('end_line')
        if (lines is None or type(start) is not int or type(end) is not int or
                not 1 <= start <= end <= len(lines) or
                '\n'.join(lines[start-1:end]) != ref.get('quote')):
            raise ValueError('rule needs exact target quote and line range: ' + rule['id'])
        selected = [f for f in data['files'] if matches(f['id'], patterns(rule, 'scope'))]
        paths = {f['id'] for f in selected}
        violations, unknown = [], []
        for skipped in data['scope']['skipped_paths']:
            if matches(skipped.rstrip('/') + ('/__excluded__' if skipped.endswith('/') else ''), rule['scope']) or any(p.split('*')[0].startswith(skipped) for p in rule['scope']):
                unknown.append({'reason': 'excluded path overlaps rule scope: ' + skipped, 'evidence': []})
        if not selected:
            unknown.append({'reason': 'scope has no scanned files', 'evidence': []})
        bad = [f['id'] for f in selected if f['status'] != 'parsed']
        if bad:
            unknown.append({'reason': 'unparsed files: ' + ', '.join(bad), 'evidence': []})
        for issue in data['issues']:
            if issue['path'] in paths and issue['kind'] in ('symbol-depth-limit', 'call-depth-limit'):
                unknown.append({'reason': issue['kind'] + ': ' + issue['path'], 'evidence': []})
        kind = rule.get('kind')
        if kind == 'forbid-import':
            forbidden = patterns(rule, 'forbidden_paths')
            for item in data['imports']:
                if item['source'] not in paths:
                    continue
                key = f"import:{item['id']}"
                if item['resolution'] == 'internal' and any(matches(p, forbidden) for p in item['targets']):
                    violations.append({'reason': 'forbidden import target', 'evidence': [key]})
                elif item['resolution'] in ('unresolved', 'ambiguous'):
                    unknown.append({'reason': 'import target is not resolved', 'evidence': [key]})
            for issue in data['issues']:
                if issue['path'] in paths and issue['kind'] == 'dynamic-import-context':
                    unknown.append({'reason': 'dynamic import context: ' + issue['path'], 'evidence': []})
        elif kind == 'forbid-call':
            forbidden = patterns(rule, 'forbidden_calls')
            origin = rule.get('origin', 'any')
            if origin not in ('any', 'stdlib', 'internal'):
                raise ValueError('invalid call origin')
            for item in data['calls']:
                if item['source'] not in paths:
                    continue
                if (item['resolution'] == 'lexical-reference' and item['canonical'] and
                        (origin == 'any' or item['origin'] == origin) and matches(item['canonical'], forbidden)):
                    violations.append({'reason': 'forbidden lexical call reference (not execution proof)',
                                       'evidence': [item['id']]})
                elif item['resolution'] == 'unknown':
                    unknown.append({'reason': 'call target is not resolved', 'evidence': [item['id']]})
        else:
            raise ValueError('unsupported rule kind: ' + str(kind))
        results.append({'id': rule['id'], 'kind': kind, 'source': ref,
                        'scope': rule['scope'], 'constraint': forbidden,
                        'status': 'violation' if violations else 'unknown' if unknown else 'no_observed_violation',
                        'checked_files': len(selected), 'violations': violations, 'unknown': unknown})
    data['comparison'] = {'version': 1, 'snapshot': data['snapshot'], 'targets': targets,
                          'interpretation': 'Agent-derived rules; exact citations are validated, semantic equivalence is not certified.',
                          'results': results,
                          'summary': {status: sum(r['status'] == status for r in results)
                                      for status in ('violation', 'unknown', 'no_observed_violation')},
                          'limits': 'Only the supplied rules and scanned Python scope were checked. No whole-architecture compliance claim.'}
    return data
