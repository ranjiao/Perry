"""DESIGN-023 Goal 4: a method addition is template/prose, zero kernel edit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ACTOR={'kind':'agent','name':'method-data-demo','session':'isolated-method-demo'}


def kernel_digest():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'kernel/perry_kernel').glob('*.py')}


class MethodData(unittest.TestCase):
    def test_method_change_only_template_and_prose(self):
        before=kernel_digest()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'.perry').mkdir();store=root/'candidate.db'
            env={k:v for k,v in os.environ.items() if k not in ('PERRY_HOME','PERRY_STORE','PERRY_PROJECT')}
            env.update(PERRY_KERNEL_TESTING='1',PYTHONDONTWRITEBYTECODE='1')
            def call(words,data):
                proc=subprocess.run([sys.executable,str(ROOT/'bin/perry'),*words,'--root',str(root),'--store',str(store),'--json','--input',json.dumps(data)],env=env,capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
                return json.loads(proc.stdout)['result']
            call(['init'],dict(actor=ACTOR,state_root='documents'))
            template=json.loads((ROOT/'templates/process/perry.json').read_text())
            # Same kernel, an additional field declared only as process data.
            template['version']+=1
            template['types']['task']['fields']['delivery_channel']={'kind':'enum','values':['internal','external']}
            (root/'method.json').write_text(json.dumps(template))
            (root/'SKILL.md').write_text('For each task record delivery_channel as internal or external.\n')
            call(['template','apply'],dict(actor=ACTOR,template=template))
            created=call(['item','create'],dict(actor=ACTOR,type='task',fields=dict(title='Demonstration',summary='Prove process field is data',priority='P2',verification='V3',delivery_channel='external')))
            item=call(['item','get'],dict(id=created['item']['id']))['item']
            self.assertEqual(item['fields']['delivery_channel'],'external')
            self.assertEqual(before,kernel_digest())

if __name__=='__main__':unittest.main()
