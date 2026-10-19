#!/usr/bin/env python3
"""Read-only skill safety facts. No state writer, task judge, or authority grant.

JSON v1 on stdout; exit 1 means STOP, 2 means invalid input. All paths are
explicit. This helper reads small safety documents, never SQLite or exports.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

STAGES = {
    'adoption': {'scan', 'harvest', 'infer', 'confirm', 'commit', 'done', 'abandoned'},
    'diagnosis': {'scan', 'read', 'interview', 'prescribe', 'execute', 'done', 'abandoned'},
}
STEPS = {
    ('adoption', 'confirm'): {'state_root','goals','phase','clusters','attribution','transcriptions'},
    ('adoption', 'commit'): {'config','okr','phase','design','board','linkage','decisions','knowledge','architecture','risks'},
    ('diagnosis', 'interview'): {'q1','q2','q3','q4','q5','q6','audience','attachment'},
}


def inside(root, relative):
    root = root.resolve()
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError('explicit nonempty relative path required')
    if Path(relative).is_absolute() or relative.startswith(('~', '$', '<', '{')):
        raise ValueError('foreign or unresolved path: ' + relative)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('path escapes root: ' + relative)
    return path


def frontmatter(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        raise ValueError('missing bounded frontmatter')
    result = {}
    for line in lines[1:lines[1:].index('---')+1]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*):\s*(.*)', line)
        # Read only safety scalars; nested dossier payloads remain opaque.
        if not m or m[1] not in ('adoption','diagnosis','stage','step','status','updated'):
            continue
        if m[1] in result:
            raise ValueError('duplicate safety frontmatter field')
        result[m[1]] = m[2].strip().strip('"\'')
    return result


def startup(root, state_root):
    """Fail closed before any normal state read; never repair a legacy marker."""
    root = root.resolve()
    state = inside(root, state_root)
    recovery = {'blocking': False, 'errors': []}
    out = {'version': 1, 'recovery': recovery, 'interrupted': []}
    marker = state / '.perry-task-transaction.json'
    if marker.exists() or marker.is_symlink():
        recovery['blocking'] = True
        recovery['errors'].append({'path': str(marker), 'error': 'pending legacy transaction; recover with the pinned pre-cutover release, never delete this marker'})
        return out  # no dossier/config/store read after this STOP
    for folder, discriminator in (('adoption', 'adoption'), ('diagnose', 'diagnosis')):
        directory = inside(root, '.perry/' + folder)
        for path in sorted(directory.glob('*.md')):
            try:
                if not path.resolve().is_relative_to(root):
                    raise ValueError('dossier symlink escapes project')
                fm = frontmatter(path)
                if fm.get(discriminator) != '1' or fm.get('stage') not in STAGES[discriminator]:
                    raise ValueError('missing/unknown pipeline version or stage')
                stage, step = fm['stage'], fm.get('step', '')
                if step and (discriminator,stage) in STEPS and step not in STEPS[discriminator,stage]:
                    raise ValueError('unknown pipeline step')
                if step and discriminator == 'diagnosis' and stage == 'execute' and not re.fullmatch(r'rx-\d+', step):
                    raise ValueError('unknown execute step')
                if stage not in ('done','abandoned'):
                    out['interrupted'].append({'path':str(path),'pipeline':discriminator,'stage':stage,'step':step,'updated':fm.get('updated'),'action':'ask user; never auto-resume'})
            except (OSError, ValueError, UnicodeError) as exc:
                recovery['errors'].append({'path':str(path),'error':str(exc)})
    # Planning drafts are evidence, not kernel state. Unknown shape cannot hide a run.
    for path in sorted((state/'plans').glob('**/*.md')):
        try:
            if not path.resolve().is_relative_to(root):
                raise ValueError('planning draft escapes project')
            fm = frontmatter(path)
            if fm.get('status') not in ('draft','approved','finalized','abandoned'):
                raise ValueError('unknown planning status; manual inspection required')
            if fm['status'] not in ('finalized','abandoned'):
                out['interrupted'].append({'path':str(path),'pipeline':'plan','stage':fm['status'],'action':'ask user; never auto-resume'})
        except (OSError, ValueError, UnicodeError) as exc:
            recovery['errors'].append({'path':str(path),'error':str(exc)})
    recovery['blocking'] = bool(recovery['errors'])
    if recovery['blocking']:
        out['interrupted'] = []  # malformed restore point is not a resumable run
    return out


def hook_fragments(hook):
    section = re.search(r'^## High-stakes operations\s*\n(.*?)(?=^## |\Z)', hook, re.M|re.S)
    if not section:
        return [], ['missing High-stakes operations section']
    bullets = re.findall(r'^[-*] (.+)$', section[1], re.M)
    fragments, errors = [], []
    for bullet in bullets:
        spans = re.findall(r'`([^`]+)`', bullet)
        if not spans:
            errors.append('unextractable high-stakes bullet: ' + bullet)
        fragments.extend(spans)
    if not fragments:
        errors.append('high-stakes list is unarmed')
    return fragments, errors


def dispatch(packet):
    errors=[]
    hook=packet.get('hook'); spec=packet.get('spec'); paths=packet.get('scope')
    if not isinstance(hook,str) or not isinstance(spec,str) or not isinstance(paths,list) or not paths:
        raise ValueError('dispatch needs hook text, spec text and nonempty scope array')
    fragments, faults = hook_fragments(hook); errors.extend(faults)
    matches = [f for f in fragments if re.search(r'(?<!\w)' + re.escape(f) + r'(?!\w)', spec + '\n' + '\n'.join(paths), re.I)]
    if matches and not packet.get('authorization'):
        errors.append('high-stakes operation needs actual user authorization; matching is only a screening fact')
    if packet.get('lane') not in ('goals','work','decide'):
        errors.append('unknown lane')
    lane = packet.get('lane')
    for rel in paths:
        try:
            inside(Path('/explicit-project-root'),rel)
            # Evidence ownership remains lane-owned even with native item state.
            part = next((s for s in Path(rel).parts if s in ('decisions','design','evidence','weekly','handoff','phase','OKR.md')),None)
            owner = {'decisions':'decide','design':'decide','evidence':'work','weekly':'work','handoff':'work','phase':'goals','OKR.md':'goals'}.get(part)
            if owner and owner != lane:
                errors.append('another lane owns ' + rel)
        except ValueError as exc:
            errors.append(str(exc))
    if not packet.get('actor'):
        errors.append('actual actor/session required')
    if not spec.strip():
        errors.append('missing written scope/criteria')
    return {'version':1,'armed':bool(fragments) and not faults,'matches':matches,'errors':errors,'blocked':bool(errors),'limit':'Does not judge naming versus doing, adequacy, or authenticity of authorization. Skill must read the spec and instruction source.'}


def review(packet):
    rung=packet.get('verification')
    if rung not in ('V1','V2','V3','V4','V5','V6'):
        raise ValueError('unknown verification rung')
    errors=[]
    evidence=packet.get('evidence')
    if not isinstance(evidence,list) or not evidence or any(not isinstance(p,str) or not Path(p).is_file() for p in evidence):
        errors.append('existing evidence files required; semantic adequacy remains with reviewer')
    if not isinstance(packet.get('criteria'),str) or not packet['criteria'].strip():
        errors.append('written acceptance criteria required')
    if rung in ('V4','V5','V6'):
        if not packet.get('implementer') or not packet.get('reviewer') or packet['implementer']==packet['reviewer']:
            errors.append('fresh independent reviewer required; implementation cannot self-award V4')
        if packet.get('verdict') != 'PASS':
            errors.append('independent criterion-bounded PASS required')
    if rung in ('V5','V6'):
        actor=packet.get('actor') or {}
        if actor.get('kind') != 'human' or not actor.get('name') or not packet.get('human_signoff'):
            errors.append('actual named human and attached sign-off required; do not fabricate either')
    return {'version':1,'blocked':bool(errors),'errors':errors,'limit':'Structural facts only; no identity authentication, acceptance decision or state transition.'}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    start=sub.add_parser('startup'); start.add_argument('--root',required=True);start.add_argument('--state-root',required=True)
    for name in ('dispatch','review'):
        sub.add_parser(name).add_argument('--input',required=True)
    if '--help' in argv or '-h' in argv:
        parser.print_help();return 0
    args=parser.parse_args(argv)
    try:
        if args.command=='startup':
            root=Path(args.root)
            if not root.is_absolute() or not root.is_dir():
                raise ValueError('root must be an existing absolute project directory')
            result=startup(root.resolve(),args.state_root)
            blocked=result['recovery']['blocking'] or bool(result['interrupted'])
        else:
            packet=json.loads(Path(args.input).read_text(encoding='utf-8'))
            if not isinstance(packet,dict):raise ValueError('input must be an object')
            result={'dispatch':dispatch,'review':review}[args.command](packet);blocked=result['blocked']
        print(json.dumps(result,ensure_ascii=True,indent=2));return int(blocked)
    except (OSError,ValueError,TypeError) as exc:
        print(json.dumps({'version':1,'error':str(exc)},ensure_ascii=True));return 2

if __name__=='__main__':
    sys.exit(main())
