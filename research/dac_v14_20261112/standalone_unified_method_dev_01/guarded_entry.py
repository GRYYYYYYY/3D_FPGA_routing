"""Diagnostic launcher forbidding Python reads from the historical project."""
import argparse,os,runpy,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--forbid-prefix',type=Path,required=True);p.add_argument('--script',type=Path,required=True)
a,args=p.parse_known_args();forbidden=a.forbid_prefix.resolve()
def guard(event,values):
    if event=='open' and isinstance(values[0],(str,bytes,os.PathLike)):
        name=Path(os.fsdecode(values[0])).resolve()
        if name.is_relative_to(forbidden):raise RuntimeError('Historical project read forbidden: '+str(name))
sys.addaudithook(guard);sys.argv=[str(a.script),*args];runpy.run_path(str(a.script),run_name='__main__')
