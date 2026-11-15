"""One private subreaper per phase, including phases without a time limit."""
import subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from retained_prefix_workflow import D,read,write

def run_phase(command,directory,tag,timeout):
    directory=Path(directory);receipt=directory/(tag+'_supervision.json')
    assert not receipt.exists(),'A completed or failed phase must not be repeated'
    wrapped=[sys.executable,str(D/'supervise_method_phase.py'),'--receipt',str(receipt)]
    if timeout is not None:wrapped += ['--seconds',str(timeout)]
    wrapped += ['--',*map(str,command)]
    with (directory/(tag+'.log')).open('w') as log:
        proc=subprocess.Popen(wrapped,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        fields=Path('/proc',str(proc.pid),'stat').read_text().rsplit(')',1)[1].split()
        write(directory/'active_child.json',dict(pid=proc.pid,start_ticks=fields[19],tag=tag,command=wrapped,phase='private_subreaper'))
        code=proc.wait()
    assert receipt.exists(),'Missing supervisor receipt; preserve outputs and investigate, never retry'
    result=read(receipt);assert not result['residual_descendants']
    status='timeout' if result['status']=='wall_timeout' else ('completed' if result['passed'] else 'failed')
    assert (code==0)==result['passed']
    return SimpleNamespace(pid=proc.pid),code,status
