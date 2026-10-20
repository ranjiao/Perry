from pathlib import Path
import json,re,shutil,subprocess
primary=Path('/Users/bytedance/proj/Perry')
work=Path('/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry')
scratch=Path('/tmp/perry-scratch/Perry')
checks=primary/'perry/evidence/2026-10/TASK-490-checks'
ansi=re.compile(r'\x1b\[[0-9;]*m')
for name in ['test-migration-full','approved-target-final-full','migrated-regressions','last-targeted','last-two','final-doc-gates','readers2','approved-delivery.py','more-fixtures.py']:
 source=scratch/f'task490-{name}'
 if not source.exists():source=scratch/f'task490-{name}.log'
 if source.exists():(checks/('approved-'+source.name.removeprefix('task490-'))).write_text(ansi.sub('',source.read_text()))
log=ansi.sub('',(scratch/'task490-approved-target-final-full.log').read_text())
failed=re.findall(r'✗ (test_\w+)\.py',log)
rows=[]
for name in failed:
 start=log.index('✗ '+name+'.py');end=log.find('✗ test_',start+5)
 section=log[start:end if end!=-1 else None]
 ids=re.findall(r'^\s+(?:FAIL|ERROR)\s+(\S+)',section,re.M)
 rows.append({'module':name,'status':'unresolved','named_failure_ids':ids,
              'classification':'Review each criterion; do not infer obsolescence from a legacy-writer refusal.'})
report={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=work,text=True).strip(),
        'command':'bash tests/run','exit_code':1,'failed_modules':len(failed),
        'module_summary':re.findall(r'^\d+ modules.*$',log,re.M),
        'failure_summary':re.findall(r'^✗ \d+ of.*$',log,re.M),
        'tree_guard_unchanged':'✓ nothing under '+str(work)+' moved' in log,
        'unresolved':rows,
        'scope_note':'Named IDs may be shortened by the runner. Do not treat this list as exhaustive assertions or all obsolete tests.'}
(checks/'approved-final-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print({k:report[k] for k in ['commit','failed_modules','module_summary','failure_summary','tree_guard_unchanged']})
