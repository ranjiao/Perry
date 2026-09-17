import os,sys,pathlib,subprocess,json,tempfile
root=pathlib.Path(sys.argv[1]).resolve(); os.environ['PERRY_HOME']=str(root); os.environ.pop('PERRY_PROJECT',None)
sys.path[:0]=[str(root/'tests'),str(root/'bin')]
from task_writer_support import Project
p=Project()
def call(tool,*args):
 r=subprocess.run([str(root/'bin'/tool),*args],capture_output=True,text=True,cwd=p.root)
 print(json.dumps({'tool':tool,'args':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}));return r
def snapshot():return {str(f.relative_to(p.root)):f.read_bytes() for f in p.root.rglob('*') if f.is_file()}
if sys.argv[2]=='counts':
 for i in range(6):assert p.run('add','--title',f'independent row {i}')[0]==0
 f=p.root/'evidence.md';f.write_text('Independent fixture evidence.\n')
 assert p.run('done','TASK-001','--evidence','evidence.md','--rung','V3')[0]==0
 assert p.run('drop','TASK-002','--reason','fixture')[0]==0
 for tid,status in [('TASK-003','blocked'),('TASK-004','review'),('TASK-005','in_progress')]:assert p.run('status',tid,'--status',status,'--reason','fixture')[0]==0
 before=snapshot()
 for extra,total,op,cl,winop,wincl,n,tr in [(('--all','--limit','1'),6,4,2,0,1,1,True),(('--all','--limit','3'),6,4,2,1,2,3,True),(('--all','--limit','0'),6,4,2,4,2,6,False),(('--limit','1'),4,4,0,1,0,1,True)]:
  r=call('perry-task','list','--json','--root',str(p.root),*extra);assert r.returncode==0
  d=json.loads(r.stdout);b=d['bound'];assert (b['total'],b['open_total'],b['closed_total'],d['open'],d['closed'],b['returned'],b['truncated'])==(total,op,cl,winop,wincl,n,tr)
  assert len(d['tasks'])==n
  if tr:assert f'{n} of {total}' in r.stderr and '`bound.open_total` is 4' in r.stderr
  else:assert not r.stderr
 assert snapshot()==before
 import lib
 decl={'name':'probe','flags':[{'name':'--read'},{'name':'--write'}],'subcommands':[{'name':'read','flags':['--read']},{'name':'write','flags':['--write']}]}
 for sub,yes,no in [('read','--read','--write'),('write','--write','--read')]:
  err=lib.parse_surface(decl,[sub,'--xyzzy'])['error'];print(err);flags=err.split('Accepted flags: ')[1].split(', ');assert yes in flags and no not in flags and '--help' in flags and '-h' in flags
 err=lib.parse_surface(decl,['--xyzzy','read'])['error'];assert 'Declared flags (select a subcommand' in err;print(err)
 for tool,lead,yes,no in [('perry-task',('add',),'--title','--all'),('perry-task',('list',),'--all','--title'),('perry-config',('show',),'--root','--mode'),('perry-state',(),'--section','--title')]:
  r=call(tool,*lead,'--root',str(p.root),'--xyzzy');assert r.returncode==2
  flags=r.stderr.split('Accepted flags: ')[1].splitlines()[0].split(', ');assert yes in flags and no not in flags and '--help' in flags and '-h' in flags
 assert snapshot()==before
else:
 before=snapshot()
 for tool,args in [('perry',('list',)),('perry-detect-host',()),('perry-explain',('V4','--root',str(p.root)))]:
  r=call(tool,*args,'--xyzzy');assert r.returncode==2 and not r.stdout and '--xyzzy' in r.stderr
 for level in ['phase','overall']:
  for flags in [(),('--json',)]:
   r=call('perry-goals','krs','stray','--root',str(p.root),'--level',level,*flags);assert r.returncode==2
   if flags:assert set(json.loads(r.stdout))=={'refused'}
   else:assert not r.stdout and 'stray' in r.stderr
 for args in [('--help','--xyzzy'),('-h','--xyzzy'),('--xyzzy','--help')]:
  r=call('perry-detect-host',*args);assert r.returncode==2 and not r.stdout
 for tool,args in [('perry',('list','--json')),('perry',('list','--tools')),('perry',('list','-h')),('perry-detect-host',()),('perry-detect-host',('-h',)),('perry-explain',('V4',))]:assert call(tool,*args).returncode==0
 assert snapshot()==before
 from test_bin_argument_contract import TestAnUndeclaredFlagIsRefusedWithASubcommandInFront as Sweep
 s=Sweep();s.setUp()
 try:
  s.test_the_lead_table_covers_every_shipped_tool();s.test_every_tool_refuses_with_exit_2();print('Independent invocation of complete twenty-tool sweep: PASS')
 finally:s.doCleanups()
print('ALL INDEPENDENT PROBES PASS')
