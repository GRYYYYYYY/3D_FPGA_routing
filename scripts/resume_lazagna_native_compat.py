#!/usr/bin/env python3
"""Transfer scheduler ownership while preserving every live VPR/time process."""
import concurrent.futures
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import time
from lazagna_common import BASE,sha256,utc,write_json
from run_lazagna_routes import run_one
from run_vpr import parse_metrics


def alive(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().split(')')[1].split()[0]!='Z'
    except FileNotFoundError:return False


def adopt(job):
    directory=BASE/'runs'/job['name'];receipt=directory/'manifest.json';m=json.loads(receipt.read_text())
    if m['status']=='running':
        deadline=dt.datetime.fromisoformat(m['start_utc']).timestamp()+m['timeout_seconds'];timed_out=False
        while alive(m['pid']):
            if time.time()>=deadline:
                timed_out=True;os.killpg(m['pid'],signal.SIGTERM)
                for _ in range(10):
                    if not alive(m['pid']):break
                    time.sleep(1)
                if alive(m['pid']):os.killpg(m['pid'],signal.SIGKILL)
                break
            time.sleep(2)
        log=(directory/'time.txt').read_text(errors='replace')
        code=re.search(r'Exit status: (\d+)',log);sig=re.search(r'Command terminated by signal (\d+)',log)
        if timed_out:rc=-15;status='timeout'
        elif sig:rc=-int(sig[1]);status='failed'
        elif code:rc=int(code[1]);status='completed' if rc==0 else 'failed'
        else:raise RuntimeError('Exited adopted job has no GNU time exit receipt')
        end=time.time() if timed_out else (directory/'time.txt').stat().st_mtime
        m.update(status=status,returncode=rc,finish_utc=dt.datetime.fromtimestamp(end,dt.timezone.utc).isoformat(),
                 wall_seconds=end-dt.datetime.fromisoformat(m['start_utc']).timestamp(),
                 supervisor_adopted=True,adoption_receipt=str(BASE/'native_compat_scheduler_transfer.json'))
        write_json(receipt,m)
    log=(directory/'stdout.log').read_text(errors='replace');metrics=parse_metrics(log)
    success=m['status']=='completed' and metrics['native_full_check_passed'] and metrics['routing_success_reported']
    if success:classification='native_legal_pending_independent_audit'
    elif m['status']=='timeout':classification='timeout'
    elif 'Routing failed' in log or 'Circuit is unroutable' in log:classification='routing_failure'
    else:classification='tool_or_input_failure'
    primary=BASE/'runs'/f"paper_primary_{job['case']}_w300"
    paths=[primary/'packed.net',primary/'fixed.place',directory/'routed.route']
    outputs={p.name:{'path':str(p),'sha256':sha256(p)} for p in paths if p.exists()}
    result=dict(state=m['status'],classification=classification,native_legal=success,metrics=metrics,outputs=outputs,
                directory=str(directory),run_manifest=str(receipt))
    write_json(directory/'result.json',result);return result


def main():
    path=BASE/'native_compat_state.json';transfer=BASE/'native_compat_scheduler_transfer.json'
    if transfer.exists():raise RuntimeError('Transfer already performed')
    current=json.loads(path.read_text());previous=current['owner_pid']
    if not alive(previous):raise RuntimeError('Expected original scheduler to be alive')
    # Freeze only the orchestration process. Popen used separate process groups
    # for /usr/bin/time + VPR; these continue computing throughout the transfer.
    os.kill(previous,signal.SIGSTOP)
    current=json.loads(path.read_text());snapshots={}
    try:
        for j in current['jobs']:
            if j['state']=='running':
                m=json.loads((BASE/'runs'/j['name']/'manifest.json').read_text())
                assert m['status'] in ['running','completed','failed','timeout']
                if m['status']=='running':assert m.get('pid') and os.getpgid(m['pid'])==m['pid']
                snapshots[j['name']]=m
        write_json(transfer,{'utc':utc(),'previous_owner':previous,'new_owner':os.getpid(),'previous_state':current,
                   'live_manifests':snapshots,'reason':'Increase scheduler concurrency from 4 to 8 while preserving running VPR jobs, exact commands and original deadlines.',
                   'actions':'SIGSTOP/SIGKILL only previous Python scheduler PID; no signal to solver process groups during ownership transfer.'})
    except BaseException:
        os.kill(previous,signal.SIGCONT);raise
    os.kill(previous,signal.SIGKILL)
    lock=(BASE/'native_compat_owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
    current.update(owner_pid=os.getpid(),workers=8,resumed_utc=utc());write_json(path,current)
    pending={};jobs=current['jobs']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for j in jobs:
            if j['state']=='running':pending[pool.submit(adopt,j)]=j
        while pending or any(j['state']=='queued' for j in jobs):
            parents={j['name']:j for j in json.loads((BASE/'clock_diagnostic_state.json').read_text())['jobs']}
            for j in jobs:
                if len(pending)>=8:break
                if j['state']!='queued':continue
                old=parents[f"native_ideal_{j['case']}_w{j['width']}_i200"]
                if old['state'] in ['queued','running']:continue
                log=BASE/'runs'/old['name']/'stdout.log'
                if not log.exists() or 'unknown net $undef' not in log.read_text(errors='replace'):
                    j['state']='not_needed_no_constant_merge_failure';write_json(path,current);continue
                primary={'directory':str(BASE/'runs'/f"paper_primary_{j['case']}_w300")}
                j['state']='running';pending[pool.submit(run_one,j,primary,'ideal',True)]=j;write_json(path,current)
            for f in list(pending):
                if not f.done():continue
                j=pending.pop(f)
                try:j.update(f.result())
                except Exception as e:j.update(state='supervisor_error',error=repr(e))
                write_json(path,current);print(j['name'],j['state'],j.get('native_legal'),j.get('error'),flush=True)
            time.sleep(2)
    current.update(stage='finished',finished_utc=utc());write_json(path,current)


if __name__=='__main__':main()
