"""Validate host-agent interpretation against a specific fact snapshot."""
import hashlib
import json
import re


def attach(data, proposal):
    if not isinstance(proposal, dict) or type(proposal.get('version')) is not int or proposal.get('version') != 1:
        raise ValueError('analysis version must be 1')
    if proposal.get('snapshot') != data['snapshot']:
        raise ValueError('stale analysis: generate interpretation for the current snapshot')
    if proposal.get('producer') != 'host-agent':
        raise ValueError('analysis producer must be host-agent')
    files = {f['id']: f for f in data['files']}
    symbols = {s['id']: s for s in data['symbols']}
    units = {**{f: {'id': f, 'file': f, 'line': 1} for f in files},
             **{s: dict(item, file=item['file']) for s, item in symbols.items()}}
    owners, nodes, issues = {}, [], []
    seen = set()

    def visit(items, parent=''):
        if not isinstance(items, list) or not items:
            raise ValueError('analysis components must be a nonempty array')
        for item in items:
            if not isinstance(item, dict):
                raise ValueError('component must be an object')
            slug = item.get('id', '')
            if not isinstance(slug, str) or not re.fullmatch('[a-z][a-z0-9_-]*', slug):
                raise ValueError('component id must be a lowercase slug')
            key = f'{parent}/{slug}' if parent else slug
            if key in seen or key == 'unmapped':
                raise ValueError('duplicate or reserved component: ' + key)
            seen.add(key)
            for field in ('label', 'description', 'uncertainty'):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError('component needs label, description and uncertainty: ' + key)
            layer = item.get('layer', 0)
            if type(layer) is not int or not 0 <= layer <= 10:
                raise ValueError('invalid layer: ' + key)
            evidence = item.get('evidence', [])
            if not isinstance(evidence, list) or any(not isinstance(e, str) or e not in data['evidence'] for e in evidence):
                raise ValueError('invalid component evidence: ' + key)
            node = {k: item[k] for k in ('label', 'description', 'uncertainty')}
            node.update(id=key, parent=parent, layer=layer, evidence=evidence, files=[], symbols=[])
            nodes.append(node)
            if 'children' in item:
                if 'members' in item:
                    raise ValueError('branch cannot declare members')
                visit(item['children'], key)
            else:
                members = item.get('members')
                if not isinstance(members, list) or not members or not evidence:
                    raise ValueError('leaf needs explicit members and evidence: ' + key)
                selected = set()
                for member in members:
                    module_only = isinstance(member, str) and member.startswith('module:')
                    member = member[7:] if module_only else member
                    if not isinstance(member, str) or member not in units:
                        raise ValueError('unknown member: ' + str(member))
                    selected.add(member)
                    if member in files and not module_only:
                        selected.update(s for s, entry in symbols.items() if entry['file'] == member)
                member_files = {units[m]['file'] for m in selected}
                if any(data['evidence'][e]['source'] not in member_files for e in evidence):
                    raise ValueError('leaf evidence must belong to its members: ' + key)
                for member in sorted(selected):
                    if member in owners:
                        raise ValueError('overlapping member: ' + member)
                    owners[member] = key
    visit(proposal.get('components'))
    unassigned = sorted(set(units) - set(owners))
    if unassigned:
        nodes.append({'id': 'unmapped', 'parent': '', 'label': '尚未解释的代码',
                      'description': '需要分析或存在覆盖缺口', 'uncertainty': '没有职责判断',
                      'layer': 0, 'evidence': [], 'files': [], 'symbols': []})
        for key in unassigned:
            owners[key] = 'unmapped'
        issues.append({'path': 'unmapped', 'kind': 'unassigned', 'candidates': unassigned})
    by_id = {n['id']: n for n in nodes}
    for unit, owner in owners.items():
        key = owner
        while key:
            node = by_id[key]
            node['files'].append(units[unit]['file'])
            if unit in symbols:
                node['symbols'].append(unit)
            key = node['parent']
    for n in nodes:
        n['files'] = sorted(set(n['files']))
        n['symbols'] = sorted(set(n['symbols']))

    def unit_at(path, line):
        candidates = [s for s in symbols.values() if s['file'] == path and s['line'] <= line <= s['end_line']]
        return min(candidates, key=lambda s: s['end_line']-s['line'])['id'] if candidates else path

    edges = {}
    def edge(a, b, evidence):
        source, target = owners[a], owners[b]
        if source != target:
            edges.setdefault((source, target), set()).add(evidence)
    for item in data['imports']:
        for target in item['targets'] if item['resolution'] == 'internal' else []:
            edge(unit_at(item['source'], item['line']), target, f"import:{item['id']}")
    for call in data['calls']:
        if call['target_symbol']:
            edge(call['owner'] or call['source'], call['target_symbol'], call['id'])
    data['architecture'] = {
        'version': 2, 'title': proposal.get('title', '代码职责现状'),
        'basis': '宿主 agent 基于当前静态证据生成；职责是推断，不是目标架构或合规认证。',
        'snapshot': data['snapshot'], 'producer': 'host-agent',
        'model_sha256': hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest(),
        'nodes': nodes, 'owners': owners, 'units': list(units.values()), 'issues': issues,
        'scope_aliases': {},
        'edges': [{'source': a, 'target': b, 'imports': sorted(e)} for (a,b),e in sorted(edges.items())]}
    return data


def changes(data, previous):
    if not isinstance(previous, dict) or not isinstance(previous.get('files'), list) or not isinstance(previous.get('snapshot'), str):
        raise ValueError('previous must be a fact/report snapshot')
    if previous.get('root') != data['root']:
        raise ValueError('previous snapshot belongs to a different project root')
    old = {f['id']: f for f in previous['files']}
    new = {f['id']: f for f in data['files']}
    current_nodes = {n['id']: n for n in data.get('architecture', {}).get('nodes', [])}
    old_nodes = {n['id']: n for n in previous.get('architecture', {}).get('nodes', [])}
    return {'base_snapshot': previous['snapshot'], 'snapshot': data['snapshot'],
            'added': sorted(new.keys()-old.keys()), 'removed': sorted(old.keys()-new.keys()),
            'changed': sorted(f for f in new.keys() & old.keys() if new[f]['sha256'] != old[f]['sha256']),
            'components_added': sorted(current_nodes.keys()-old_nodes.keys()),
            'components_removed': sorted(old_nodes.keys()-current_nodes.keys()),
            'components_changed': sorted(k for k in current_nodes.keys() & old_nodes.keys()
                                         if current_nodes[k] != old_nodes[k]),
            'note': 'Component IDs are agent-supplied; renames are additions/removals, not proven semantic moves.'}
