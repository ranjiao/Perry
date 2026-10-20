#!/usr/bin/env python3
"""Read-only finite retirement source audit. This never accepts proposals,
activates a project, runs a native command, or establishes consumer migration.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r'[0-9a-f]{64}\Z')
COMMIT = re.compile(r'[0-9a-f]{40}\Z')
MOVED = {'kernel', 'skill_procedure', 'retained_skill_helper'}
DISPOSITIONS = MOVED | {'proposed_drop', 'dropped'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


# Immutable source proposal only. These constants bind the original reviewed
# revision even when its cherry-picked source commit is not reachable in a clone.
# A manifest cannot supply replacement paths, hashes, revision identity or approval.
PREFIX_FLOOR_PROPOSAL = {'inventory_base': 'b9be4d39f52ce1266534215b999c9db408b03bc5', 'revision_commit': '32bcf99c0832676c7c5ae125621cf88107c70dec', 'revision_parent': 'b9be4d39f52ce1266534215b999c9db408b03bc5', 'production_diff_sha256': 'b7a8a59a27c25e51c5fcd58c644179a64fd84fd77618d7fcd24f23e2cc135354', 'files': {'kernel/perry_kernel/commands.py': {'before': '170093b162a3c397af5d86f873a57de13c31b27fa99784adfc1055c29a3b1c88', 'after': 'bd440612281f1ce163579ba7dd44c1bc83f3ca3c075ea29ea6d666c821586715'}, 'kernel/perry_kernel/surface.py': {'before': 'ec24110fbebd2684556387dda05a8ad67cd2f5d7c35c6f95d219038c5f843552', 'after': 'd038e40fc13e488312d7f24c0d328c534d8769bf2214d6e8922115207e048b5e'}}}


def proposed_kernel_revision(base, originals, candidates):
    proposal = PREFIX_FLOOR_PROPOSAL
    if base != proposal['inventory_base'] or set(originals) != set(candidates):
        return None
    changed = {name for name in originals if originals[name] != candidates[name]}
    if changed != set(proposal['files']):
        return None
    for name, hashes in proposal['files'].items():
        if digest(originals[name]) != hashes['before'] or digest(candidates[name]) != hashes['after']:
            return None
    return {'revision_commit': proposal['revision_commit'],
            'revision_parent': proposal['revision_parent'],
            'production_diff_sha256': proposal['production_diff_sha256'],
            'paths': sorted(proposal['files']),
            'acceptance': 'PROPOSAL', 'approval': 'PENDING_USER_APPROVAL'}


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError('cannot read immutable Git input: ' + ' '.join(args))
    return result.stdout


def local(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('expected a nonempty repository-relative path')
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('path escapes checkout')
    return path


def source_path(value):
    # Inventory source citations are a path, or path:line/section/entrypoint.
    return re.split(r'[:#]', value, maxsplit=1)[0] if isinstance(value, str) else ''


def keys(rows):
    return [(row.get('kind'), row.get('key')) for row in rows]


def wrapper_ast(raw):
    tree = ast.parse(raw)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        tree.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def audit(root, manifest='release/retirement/disposition.json'):
    root = Path(root).resolve()
    errors = []

    def error(code, detail):
        errors.append({'code': code, 'detail': str(detail)})

    result = {'version': 1, 'acceptance': 'PROPOSAL', 'errors': errors,
              'consumer_acceptance': 'not assessed',
              'limitations': ['Source inventory, hashes and paths only; no semantic equivalence or safety review approval.',
                             'Consumer declarations are reported, not verified migration or live activation.',
                             'Local unsigned inventory provenance still requires independent review and named user acceptance.']}
    try:
        data = json.loads(local(root, manifest).read_text())
        if type(data.get('version')) is not int or data['version'] != 1 or not COMMIT.fullmatch(str(data.get('base', ''))):
            raise ValueError('manifest version/base invalid')
        base = data['base']
        declaration = data.get('kernel_revision_proposal')
        if declaration is not None and declaration != {
                'revision_commit': PREFIX_FLOOR_PROPOSAL['revision_commit'],
                'approval': 'PENDING_USER_APPROVAL'}:
            error('kernel_revision_identity', 'manifest cannot replace the fixed source proposal or claim approval')
        if data.get('acceptance', 'PROPOSAL') != 'PROPOSAL':
            error('approval_claim', 'manifest acceptance must remain PROPOSAL')
        tree_paths = set(git(root, 'ls-tree', '-rz', '--name-only', base).decode().split('\0')) - {''}
        index_path = local(root, data.get('source_inventory_path'))
        raw = index_path.read_bytes()
        if not SHA.fullmatch(str(data.get('source_inventory_sha256', ''))) or digest(raw) != data['source_inventory_sha256']:
            error('inventory_hash', 'source inventory bytes differ from manifest')
        original = json.loads(raw)
        original_rows, rows = original.get('rows'), data.get('rows')
        if original.get('base') != base or not isinstance(original_rows, list) or not isinstance(rows, list):
            raise ValueError('source inventory/manifest rows or base invalid')
        if any(not isinstance(r, dict) for r in original_rows + rows):
            raise ValueError('inventory rows must be objects')
        original_keys, actual_keys = keys(original_rows), keys(rows)
        if any(not isinstance(k, str) or not k for pair in original_keys + actual_keys for k in pair):
            raise ValueError('row kind/key must be nonempty strings')
        if len(set(original_keys)) != len(original_keys) or len(set(actual_keys)) != len(actual_keys):
            error('duplicate_row', 'kind/key identities must be unique')
        if set(original_keys) != set(actual_keys):
            error('inventory_identity', {'missing': sorted(set(original_keys) - set(actual_keys)),
                                         'extra': sorted(set(actual_keys) - set(original_keys))})
        if type(data.get('inventory_rows')) is not int or data['inventory_rows'] != len(original_rows) or len(rows) != len(original_rows):
            error('inventory_count', 'declared count must match both finite inventories')
        originals = dict(zip(original_keys, original_rows))
        source_hashes = {}
        covered = set()
        for row in rows:
            identity = (row['kind'], row['key'])
            if row.get('acceptance') != 'PROPOSAL':
                error('approval_claim', identity)
            if row.get('disposition') not in DISPOSITIONS:
                error('disposition', identity)
            for field in ('source', 'successor', 'reason'):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    error('row_shape', f'{identity}: missing {field}')
            prior = originals.get(identity)
            if prior and row.get('source') != prior.get('source'):
                error('source_identity', identity)
            if prior and prior.get('row_sha256') is not None and row.get('row_sha256') != prior['row_sha256']:
                error('original_row_identity', identity)
            name = source_path(row.get('source'))
            if name in tree_paths:
                covered.add(name)
                if name not in source_hashes:
                    source_hashes[name] = digest(git(root, 'show', base + ':' + name))
                if row.get('source_sha256') != source_hashes[name]:
                    error('source_hash', identity)
                if prior and prior.get('source_sha256') not in (None, source_hashes[name]):
                    error('original_source_hash', identity)
            elif name:
                error('source_missing_at_base', identity)
            if row.get('disposition') in MOVED:
                paths = row.get('successor_paths')
                if not isinstance(paths, list) or not paths:
                    error('successor_missing', identity)
                else:
                    for path in paths:
                        try:
                            if not local(root, path).exists():
                                error('successor_missing', f'{identity}: {path}')
                        except ValueError as exc:
                            error('successor_path', f'{identity}: {exc}')
        test_path = local(root, 'tests/test-disposition.json')
        test_data = json.loads(test_path.read_text())
        if test_data.get('base') != base or test_data.get('version') != 1:
            error('test_inventory', 'test disposition base/version mismatch')
        for row in test_data.get('rows', []):
            name = row.get('source')
            if name in tree_paths:
                covered.add(name)
                expected = source_hashes.get(name) or digest(git(root, 'show', base + ':' + name))
                if row.get('source_sha256') != expected:
                    error('test_source_hash', name)
            if str(row.get('acceptance', '')).upper() != 'PROPOSAL':
                error('approval_claim', name)
        required = {p for p in tree_paths if p.split('/')[0] in {'bin', 'schema', 'viewer', 'tests'}}
        if required - covered:
            error('file_disposition_missing', sorted(required - covered))
        product = {p for p in tree_paths if p.startswith('kernel/perry_kernel/')}
        current = {str(p.relative_to(root)) for p in (root / 'kernel/perry_kernel').rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts}
        if current != product:
            error('kernel_product_changed', sorted(current ^ product))
        originals = {name: git(root, 'show', base + ':' + name)
                     for name in sorted(product & current)}
        candidates = {name: (root / name).read_bytes() for name in originals}
        pending = proposed_kernel_revision(base, originals, candidates)
        if pending is not None:
            result['proposed_kernel_revision'] = pending
            result['pending_user_approval'] = True
        else:
            for name in originals:
                if candidates[name] != originals[name]:
                    error('kernel_product_changed', name)
        entries = sorted(p.name for p in (root / 'bin').iterdir())
        if entries != ['perry']:
            error('bin_surface', entries)
        wrapper = root / 'bin/perry'
        if wrapper.is_file():
            expected = git(root, 'show', base + ':bin/perry-kernel')
            if not wrapper.read_bytes().startswith(b'#!/usr/bin/env python3\n'):
                error('native_wrapper_shebang', 'native wrapper requires its Python shebang')
            if wrapper_ast(wrapper.read_bytes()) != wrapper_ast(expected):
                error('native_wrapper_changed', 'wrapper executable AST differs from immutable native wrapper')
            if not wrapper.stat().st_mode & 0o111:
                error('native_wrapper_mode', 'bin/perry is not executable')
        consumers = data.get('consumers')
        if not isinstance(consumers, list) or any(not isinstance(c, dict) for c in consumers):
            error('consumer_shape', 'consumers must be an explicit list of objects')
            consumers = []
        for consumer in consumers:
            if consumer.get('acceptance') != 'PROPOSAL':
                error('approval_claim', consumer.get('path', 'consumer'))
        if data.get('consumer_path') is not None or data.get('consumer_sha256') is not None:
            consumer_bytes = local(root, data.get('consumer_path')).read_bytes()
            if digest(consumer_bytes) != data.get('consumer_sha256'):
                error('consumer_hash', 'consumer artifact bytes differ from manifest')
            consumer_data = json.loads(consumer_bytes)
            if (consumer_data.get('version') != 1 or consumer_data.get('base') != base or
                    consumer_data.get('consumers') != consumers):
                error('consumer_inventory', 'consumer artifact identity/declarations differ')
        result.update(base=base, inventory_rows=len(rows), source_files_covered=len(covered),
                      consumers=consumers, pending_user_acceptance=True)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        error('invalid_input', exc)
    result['ok'] = not errors
    result['status'] = ('source_checks_pass_with_pending_kernel_revision'
                        if result['ok'] and result.get('pending_user_approval')
                        else 'source_checks_pass' if result['ok'] else 'source_checks_fail')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest', default='release/retirement/disposition.json')
    parser.add_argument('--summary', action='store_true', help='report consumer counts rather than every declaration')
    args = parser.parse_args(argv)
    if not args.root.is_absolute():
        parser.error('--root must be absolute')
    result = audit(args.root, args.manifest)
    if args.summary and 'consumers' in result:
        consumers = result.pop('consumers')
        result['consumer_count'] = len(consumers)
        result['consumer_status_counts'] = dict(Counter(str(c.get('status', 'unknown')) for c in consumers))
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
