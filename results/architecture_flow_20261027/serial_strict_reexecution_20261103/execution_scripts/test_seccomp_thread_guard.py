#!/usr/bin/env python3
"""Exercise enforced no-thread semantics without attaching a tracer."""
import errno
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys

guard = Path(__file__).with_name('seccomp_thread_guard').resolve()


def run(code):
    def no_core():
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    return subprocess.run([str(guard),sys.executable,'-c',code],capture_output=True,text=True,
                          timeout=10,preexec_fn=no_core)


def main():
    p=run('import subprocess; assert subprocess.check_output(["/bin/echo","ok"]).strip()==b"ok"')
    assert p.returncode==0,(p.returncode,p.stderr)
    p=run('import threading; t=threading.Thread(target=lambda:None); t.start(); t.join()')
    assert p.returncode==-signal.SIGSYS,(p.returncode,p.stderr)
    # An inherited guard must also kill a grandchild that attempts a thread.
    p=run('import os,signal,threading; p=os.fork(); '
          'p==0 and threading.Thread(target=lambda:None).start(); '
          'p==0 and os._exit(99); r=os.waitpid(p,0)[1]; '
          'assert os.WIFSIGNALED(r) and os.WTERMSIG(r)==signal.SIGSYS')
    assert p.returncode==0,(p.returncode,p.stderr)
    p=run('import ctypes,errno; c=ctypes.CDLL(None,use_errno=True); '
          'r=c.syscall(435,0,0); assert r==-1 and ctypes.get_errno()==errno.ENOSYS')
    assert p.returncode==0,(p.returncode,p.stderr)
    p=run('import ctypes; ctypes.CDLL(None).syscall(56,0x10000,0,0,0,0)')
    assert p.returncode==-signal.SIGSYS,(p.returncode,p.stderr)
    p=run('import ctypes; ctypes.CDLL(None).syscall(0x40000000|39)')
    assert p.returncode==-signal.SIGSYS,(p.returncode,p.stderr)
    p=run('s=open("/proc/self/status").read(); assert "TracerPid:\\t0" in s and "NoNewPrivs:\\t1" in s')
    assert p.returncode==0,(p.returncode,p.stderr)
    print('seccomp guard: ordinary child, pthread, direct clone, clone3 denial, x32 denial, no tracer and inheritance passed')


if __name__=='__main__':main()
