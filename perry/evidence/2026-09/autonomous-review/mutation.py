import pathlib,subprocess,tarfile,io,os,time,shutil
base=pathlib.Path(__file__).resolve().parent;src=base/'reviewer';p=base/'mutation-413';ref='8972f7599012c8a676414b5324f904a968f5e517';rel='bin/perry-task'
subprocess.run(['git','clone','--shared','--no-checkout',str(src),str(p)],check=True)
subprocess.run(['git','-C',str(p),'update-ref','HEAD',ref],check=True)
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','-C',str(src),'archive',ref]))) as t:t.extractall(p)
subprocess.run(['git','-C',str(p),'read-tree','HEAD'],check=True)
true=subprocess.check_output(['git','-C',str(src),'show',f'{ref}:{rel}']);f=p/rel
assert f.read_bytes()==true
lines=true.decode().splitlines(keepends=True);assert lines[7887]=='    open_total = sum(1 for task in rows if task["open"])\n';lines[7887]='    open_total = total\n'
env=dict(os.environ,PERRY_HOME=str(p),PYTHONDONTWRITEBYTECODE='1');env.pop('PERRY_PROJECT',None)
def clear():
 for x in p.rglob('__pycache__'):shutil.rmtree(x)
 time.sleep(1.1)
def run(label,args):
 with (base/(label+'.log')).open('w') as log:r=subprocess.run(args,cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT)
 print(label,r.returncode,flush=True);return r.returncode
try:
 f.write_text(''.join(lines));clear()
 assert run('mutation-413-targeted',['python3','-m','unittest','discover','-s','tests','-p','test_bin_argument_contract.py','-k','mixed_status_totals'])!=0
 assert run('mutation-413-affected',['bash','tests/run','--tier','affected','--base','edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e'])!=0
finally:
 f.write_bytes(subprocess.check_output(['git','-C',str(src),'show',f'{ref}:{rel}']));clear()
 assert f.read_bytes()==subprocess.check_output(['git','-C',str(src),'show',f'{ref}:{rel}'])
 print('restore independently verified against git show '+ref+':'+rel,flush=True)
assert run('restored-413-targeted',['python3','-m','unittest','discover','-s','tests','-p','test_bin_argument_contract.py','-k','mixed_status_totals'])==0
assert run('restored-413-affected',['bash','tests/run','--tier','affected','--base','edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e'])==0
