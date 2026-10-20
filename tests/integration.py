"""Offline integration in a disposable clone; caller checkout is read-only.

Receipts bind exact input commits, merged tree, command, transcript and result.
They are unsigned evidence, not independent review, release allocation or a
human sign-off. Verification reconstructs the tree without running the suite.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from run import snapshot


class Refused(Exception):
    pass


def sh(args, cwd):
    env = {k: v for k, v in os.environ.items() if k not in
           {'GIT_DIR', 'GIT_COMMON_DIR', 'GIT_WORK_TREE', 'PERRY_HOME',
            'PERRY_PROJECT', 'PERRY_STORE', 'PYTHONPATH'}}
    env.update(PYTHONDONTWRITEBYTECODE='1', PERRY_KERNEL_TESTING='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True)
    if result.returncode:
        raise Refused('command failed: ' + repr(args) + '\n' +
                      result.stderr.decode('utf-8', 'replace'))
    return result.stdout


def git(root, *args):
    return sh(['git', *args], root).decode().strip()


def resolve(root, ref):
    if not ref or ref.startswith('-'):
        raise Refused('input ref must not be an option')
    return git(root, 'rev-parse', '--verify', ref + '^{commit}')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def inputs(root, base, candidates):
    return [{'role': 'base', 'ref': base, 'sha': resolve(root, base)}] + [
        {'role': 'candidate', 'ref': ref, 'sha': resolve(root, ref)} for ref in candidates]


class Tree:
    def __init__(self, root, refs):
        self.root, self.refs = root, refs

    def __enter__(self):
        scratch = Path(os.environ.get('TMPDIR', '/tmp')) / 'perry-scratch' / self.root.name
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix='merge-check-', dir=scratch))
        self.path = self.tmp / 'tree'
        try:
            sh(['git', 'clone', '--shared', '--no-checkout', '--quiet', str(self.root), str(self.path)], self.root)
            git(self.path, 'config', 'user.name', 'Perry integration test')
            git(self.path, 'config', 'user.email', 'integration@localhost')
            git(self.path, 'config', 'core.hooksPath', '/dev/null')
            git(self.path, 'checkout', '--detach', self.refs[0]['sha'])
            for row in self.refs[1:]:
                git(self.path, '-c', 'commit.gpgsign=false', 'merge', '--no-ff', '--no-edit', row['sha'])
            self.tree = git(self.path, 'rev-parse', 'HEAD^{tree}')
            return self
        except BaseException:
            shutil.rmtree(self.tmp)
            raise

    def __exit__(self, *unused):
        shutil.rmtree(self.tmp)


def command(tier):
    return ['bash', 'tests/run', '--tier', tier]


def accept(root, base, candidates, tier, record=None):
    refs = inputs(root, base, candidates)
    if record:
        record = Path(record).resolve()
        if record == root or root in record.parents or record.exists():
            raise Refused('--record must be a new directory outside the caller checkout')
    with Tree(root, refs) as merged:
        if not (merged.path / 'tests/run').is_file():
            raise Refused('merged tree has no tests/run')
        env = {k: v for k, v in os.environ.items() if k not in
               {'PERRY_HOME', 'PERRY_PROJECT', 'PERRY_STORE', 'PYTHONPATH'}}
        env.update(PYTHONDONTWRITEBYTECODE='1', PERRY_KERNEL_TESTING='1')
        before = snapshot(merged.path)
        outcome = subprocess.run(command(tier), cwd=merged.path, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sys.stdout.buffer.write(outcome.stdout)
        # Fail even when a broken runner returns zero after modifying source.
        dirty = git(merged.path, 'status', '--porcelain', '--untracked-files=all')
        after = snapshot(merged.path)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        result = {'version': 1, 'inputs': refs, 'tree': merged.tree,
                  'tier': tier, 'command': command(tier),
                  'exit_code': outcome.returncode, 'source_clean': not bool(dirty or changed),
                  'transcript_sha256': digest(outcome.stdout)}
        if inputs(root, base, candidates) != refs:
            raise Refused('input refs moved during testing')
        if outcome.returncode or dirty or changed:
            raise Refused('integration suite red or changed tested tree\n' + dirty + '\n' + ', '.join(changed))
        if record:
            record.mkdir(parents=True, exist_ok=False)
            (record / 'suite.log').write_bytes(outcome.stdout)
            raw = encoded(result)
            (record / 'receipt.json').write_bytes(raw)
            (record / 'receipt.sha256').write_text(digest(raw) + '\n')
        return result


def verify(root, receipt):
    receipt = Path(receipt).resolve()
    raw = receipt.read_bytes()
    result = json.loads(raw)
    if digest(raw) != receipt.with_name('receipt.sha256').read_text().strip():
        raise Refused('receipt hash mismatch')
    if (result.get('version') != 1 or result.get('exit_code') != 0 or
            result.get('source_clean') is not True or
            result.get('tier') not in {'full', 'slow'} or
            result.get('command') != command(result['tier'])):
        raise Refused('receipt is not green source acceptance')
    if digest(receipt.with_name('suite.log').read_bytes()) != result['transcript_sha256']:
        raise Refused('transcript hash mismatch')
    refs = result['inputs']
    if not refs or refs[0]['role'] != 'base' or any(r['role'] != 'candidate' for r in refs[1:]):
        raise Refused('receipt input roles invalid')
    if inputs(root, refs[0]['ref'], [r['ref'] for r in refs[1:]]) != refs:
        raise Refused('input refs moved; receipt stale')
    with Tree(root, refs) as merged:
        if merged.tree != result['tree']:
            raise Refused('merged tree differs from receipt')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='HEAD')
    parser.add_argument('--candidate', action='append', default=[])
    parser.add_argument('--tier', choices=('full', 'slow'), default='full')
    parser.add_argument('--record', type=Path)
    parser.add_argument('--verify-receipt', type=Path)
    args = parser.parse_args(argv)
    try:
        root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel')).resolve()
        if args.verify_receipt:
            if args.record or args.candidate or args.base != 'HEAD' or args.tier != 'full':
                raise Refused('--verify-receipt cannot combine with run options')
            result = verify(root, args.verify_receipt)
        else:
            result = accept(root, args.base, args.candidate, args.tier, args.record)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Refused, OSError, ValueError, KeyError, TypeError) as exc:
        print('merge-check: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
