"""Read the project's explicit skill-side high-stakes policy. No authority grant."""
import hashlib
import json
from pathlib import Path


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate safety-policy key: ' + key)
        out[key] = value
    return out


def validate(policy):
    if not isinstance(policy, dict) or set(policy) != {'version', 'approval_ref', 'rules'} or type(policy['version']) is not int or policy['version'] != 1:
        raise ValueError('safety policy needs version 1, approval_ref and rules')
    if not isinstance(policy['approval_ref'], str) or not policy['approval_ref'].strip():
        raise ValueError('safety policy has no actual review/approval reference')
    if not isinstance(policy['rules'], list) or not policy['rules']:
        raise ValueError('safety policy is unarmed')
    ids, patterns = set(), []
    for rule in policy['rules']:
        if not isinstance(rule, dict) or set(rule) != {'id', 'label', 'patterns'}:
            raise ValueError('a safety rule needs id, label and patterns')
        if any(not isinstance(rule[k], str) or not rule[k].strip() for k in ('id', 'label')) or rule['id'] in ids:
            raise ValueError('safety rule identities and labels must be nonempty and unique')
        ids.add(rule['id'])
        if not isinstance(rule['patterns'], list) or not rule['patterns']:
            raise ValueError('a safety rule has no literal patterns')
        for pattern in rule['patterns']:
            if not isinstance(pattern, str) or not pattern.strip() or any(ord(c) < 32 for c in pattern):
                raise ValueError('safety patterns are nonempty single-line literal strings')
            patterns.append(pattern)
    return list(dict.fromkeys(patterns))


def read(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('explicit existing project root required')
    parent = root / '.perry'
    path = parent / 'safety.json'
    if parent.is_symlink() or path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('safety policy must be a project-owned regular file')
    if not path.is_file():
        raise ValueError('safety policy is missing or not a regular file')
    raw = path.read_bytes()
    policy = json.loads(raw, object_pairs_hook=_unique)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
            'policy': policy, 'patterns': validate(policy)}
