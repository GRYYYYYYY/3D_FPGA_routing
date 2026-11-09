#!/usr/bin/env python3
"""Wait for registered owners, then collect and validate completed evidence."""
import fcntl
import json
import subprocess
import time
from lazagna_common import BASE, ROOT, PYTHON, utc, write_json


def main():
    lock=(BASE/'finalizer_owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    prefixes=('route','clock_diagnostic','native_compat','repaired_pnr','guardfix_pnr')
    while True:
        ready=all(json.loads((BASE/f'{n}_state.json').read_text())['stage']=='finished' and
                  (BASE/f'{n}_audit_summary.json').exists() for n in prefixes)
        ready &= all((BASE/f'dsp_correspondence_100_w{w}.json').exists() for w in (100,300))
        if (BASE/'clock_graph_mode_protocol.json').exists():ready &= (BASE/'clock_graph_mode_complete.json').exists()
        if ready:break
        time.sleep(5)
    for script in ('reconcile_lazagna_timeout_timing.py','collect_lazagna_study.py','validate_lazagna_study.py'):
        subprocess.run([PYTHON,ROOT/'scripts'/script],cwd=ROOT,check=True)
    write_json(BASE/'finalization.json',{'utc':utc(),'passed':True,'all_registered_owners_terminal':True,
                                      'validation':str(BASE/'validation.json')})
    print('LaZagna finalization complete',flush=True)


if __name__=='__main__':main()
