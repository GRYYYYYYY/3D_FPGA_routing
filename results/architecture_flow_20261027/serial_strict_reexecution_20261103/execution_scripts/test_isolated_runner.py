#!/usr/bin/env python3
"""Safety checks for monitoring, failure preservation and output isolation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.append(str(Path(__file__).resolve().parents[4]/'scripts'))
import flatland_experiment_io as io


def main():
    with tempfile.TemporaryDirectory(prefix='strict_runner_test_') as temporary:
        io.BASE = Path(temporary)
        (io.BASE/'runtime_dependency_binding.json').write_text(json.dumps(dict(sha256={},missing=[])))
        worker = ('import threading,time; '
                  't=threading.Thread(target=lambda:time.sleep(0.7)); '
                  't.start();time.sleep(0.6);t.join()')
        parent = ('import subprocess,sys; '
                  f'p=subprocess.Popen([sys.executable,"-c",{worker!r}]);p.wait()')
        threaded = io.run('threaded', ['/usr/bin/python3','-c',parent],timeout=5)
        assert threaded['execution_status']=='completed'
        assert threaded['status']=='thread_constraint_violated'
        assert threaded['process_tree_observation']['peak_threads']>=2
        assert threaded['thread_syscall_trace']['clone_thread_flag_lines']>0
        assert (io.BASE/'runs/threaded/manifest.json').exists()
        try:
            io.run('threaded',['/bin/true'],timeout=5)
        except FileExistsError:
            pass
        else:
            raise AssertionError('Existing receipt must not be overwritten')
        failed = io.run('failed',['/usr/bin/python3','-c','import sys,time;time.sleep(.2);sys.exit(7)'],timeout=5)
        assert failed['execution_status']=='failed' and failed['returncode']==7
        assert failed['status']=='failed'
        timed = io.run('timeout',['/usr/bin/python3','-c','import time;time.sleep(3)'],timeout=.3)
        assert timed['execution_status']=='timeout' and timed['status']=='timeout'
        single = io.run('single',['/usr/bin/python3','-c','import time;time.sleep(.2)'],timeout=5)
        assert single['execution_status']=='completed' and single['status']=='completed'
        assert single['process_tree_observation']['samples']>0
        assert not single['process_tree_observation']['violation_observed']
        assert single['thread_syscall_trace']['clone_thread_flag_lines']==0
        core_limit = io.run('core_limit', ['/usr/bin/python3','-c',
            'import resource; assert resource.getrlimit(resource.RLIMIT_CORE)==(0,0)'],timeout=5)
        assert core_limit['status']=='completed' and core_limit['execution_limit']['core_dump_bytes']==0
        dependency = io.BASE/'dependency.dat'
        dependency.write_text('registered')
        from lazagna_common import sha256
        (io.BASE/'runtime_dependency_binding.json').unlink()
        (io.BASE/'runtime_dependency_binding.json').write_text(json.dumps(
            dict(sha256={str(dependency): sha256(dependency)}, missing=[])))
        # Clear the old binding's cached identity only for this isolated test.
        io._cache.clear()
        dependency.write_text('tampered')
        try:
            io.run('tampered',['/bin/true'],timeout=5)
        except RuntimeError as error:
            assert 'hash mismatch' in str(error)
        else:
            raise AssertionError('Changed dependency must prevent execution')
        assert not (io.BASE/'runs/tampered/manifest.json').exists()
        (io.BASE/'runtime_dependency_binding.json').unlink()
        try:
            io.run('missing_binding',['/bin/true'],timeout=5)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing dependency binding must prevent execution')
        assert not (io.BASE/'runs/missing_binding/manifest.json').exists()
        print(json.dumps(dict(passed=True,checks=['child thread detected','existing receipt protected',
            'failed and timed-out receipts preserved','single process observed',
            'clone/clone3 trace detects a child thread', 'tampered dependency rejected',
            'missing binding rejected', 'core dumps disabled in child'],
            qualification='Synthetic tests do not prove complete tracing across all environments.')))


if __name__=='__main__':
    main()
