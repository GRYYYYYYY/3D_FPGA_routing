"""Build one private TU under the shared serial slot; never modify live code."""
import argparse
import fcntl
import os
import resource
import shutil
import subprocess
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity


def build(lock_fd=None):
    root=D/'vertical_cost_baseline_dev_01';plan=read(root/'plan.json')
    if lock_fd is None:
        serial=(D/'critical_scope_runner.lock').open('r')
        lock_fd=serial.fileno()
    else:
        assert Path('/proc/self/fd',str(lock_fd)).resolve()==(D/'critical_scope_runner.lock').resolve()
    fcntl.flock(lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=root/'build';assert not out.exists(),'Never repeat an existing build attempt'
    assert plan['weights']==[0,.5,1,2]
    assert all(sha(p)==h for p,h in plan['source_sha256'].items())
    assert sha(root/'h3d_joint_native_repair.h')==plan['development_header_sha256']
    parent=D/'crossing_source_stage_01';old=read(parent/'registration.json')
    assert sha(parent/'bin/vpr')==read(parent/'binding.json')['binary_sha256']
    # Hash the actual large link inputs only now, inside the serial slot.
    assert all(sha(p)==h for p,h in old['source_sha256'].items())
    out.mkdir();(out/'bin').mkdir();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    started=time.monotonic();source=parent/'vpr_api.cpp';new_source=out/'vpr_api.cpp'
    before=source.read_text();needle='#include "'+str(parent/'h3d_joint_native_repair.h')+'"'
    assert before.count(needle)==1
    new_source.write_text(before.replace(needle,'#include "'+str(root/'h3d_joint_native_repair.h')+'"'))
    obj=out/'vpr_api.cpp.o';archive=out/'libvpr.a';binary=out/'bin/vpr'
    compile_cmd=[str(new_source) if x==str(source) else str(obj) if x==str(parent/'vpr_api.cpp.o') else x for x in old['compile_command']]
    link_cmd=[str(archive) if x==str(parent/'libvpr.a') else str(binary) if x==str(parent/'bin/vpr') else x for x in old['link_command']]
    assert str(new_source) in compile_cmd and str(obj) in compile_cmd
    assert str(archive) in link_cmd and str(binary) in link_cmd
    files=[Path(__file__).resolve(),root/'plan.json',root/'h3d_joint_native_repair.h',source,new_source,
           parent/'binding.json',parent/'registration.json',parent/'libvpr.a']
    bound={str(p):sha(p) for p in files}
    write(out/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
        compile_command=compile_cmd,link_command=link_cmd,parent_binary_sha256=sha(parent/'bin/vpr'),
        scope='Private header/TU rebuild; all unchanged archive members and link inputs preserved.'))
    phases=[]
    try:
        with (out/'build.log').open('x') as log:
            for name,command,timeout in [('compile',compile_cmd,1800),
                    ('archive_copy',['/bin/cp','--reflink=auto',str(parent/'libvpr.a'),str(archive)],180),
                    ('archive_replace',['ar','r',str(archive),str(obj)],120),
                    ('link',link_cmd,300)]:
                t=time.monotonic();code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=timeout).returncode
                phases.append(dict(phase=name,returncode=code,seconds=time.monotonic()-t));write(out/'process_costs.json',phases)
                assert code==0,name
        names=subprocess.check_output(['ar','t',str(parent/'libvpr.a')],text=True).splitlines()
        assert names==subprocess.check_output(['ar','t',str(archive)],text=True).splitlines()
        assert names.count('vpr_api.cpp.o')==1
        assert subprocess.check_output(['ar','p',str(archive),'vpr_api.cpp.o'])==obj.read_bytes()
        # Check every other archive member, not merely the number of members.
        for name in names:
            if name=='vpr_api.cpp.o':continue
            assert subprocess.check_output(['ar','p',str(parent/'libvpr.a'),name])==subprocess.check_output(['ar','p',str(archive),name]),name
        assert all(sha(p)==h for p,h in bound.items())
        write(out/'binding.json',dict(status='built_not_native_validated',binary_sha256=sha(binary),
            source_sha256=bound,parent_binary_sha256=sha(parent/'bin/vpr'),private_archive_sha256=sha(archive),
            unchanged_archive_members=len(names)-1,complete_build_seconds=time.monotonic()-started,
            new_native_or_STA_calls=0,physical_Tdel_or_graph_modified=False,
            qualification='Build integrity only. Actual zero-weight equivalence and weighted native/FULL/STA/capacity/endpoint validation remain required.'))
    except BaseException as exc:
        write(out/'failure.json',dict(error=repr(exc),phases=phases,seconds=time.monotonic()-started,
            retry=False,new_native_or_STA_calls=0));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--serial-lock-fd',type=int)
    a=p.parse_args();assert a.execute;build(a.serial_lock_fd)
