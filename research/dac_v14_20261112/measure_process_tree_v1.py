"""Measure a complete command, retaining the distinction between RSS and PSS.

GNU time supplies a waited-child RSS high-water mark. Simultaneous tree RSS/PSS
is sampled independently; it is never called an exact peak or added to RSS.
The observer is outside the measured command and its overhead is disclosed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import threading
import time


def proc_stat(pid):
    try:
        fields=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split()
        return dict(pid=int(pid),state=fields[0],ppid=int(fields[1]),start_ticks=fields[19])
    except (FileNotFoundError,ProcessLookupError):return None


def sample_tree(root,known):
    all_processes={}
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            value=proc_stat(entry.name)
            if value:all_processes[value['pid']]=value
    chosen={p for p,ticks in known.items() if p in all_processes and all_processes[p]['start_ticks']==ticks}
    if root in all_processes:chosen.add(root)
    while True:
        descendants={p for p,v in all_processes.items() if v['ppid'] in chosen}
        if descendants<=chosen:break
        chosen|=descendants
    rss=pss=0;missing=[];live=[]
    for pid in sorted(chosen):
        stat=all_processes[pid];known[pid]=stat['start_ticks']
        if stat['state']=='Z':continue
        live.append(pid)
        try:
            values={line.split(':',1)[0]:int(line.split()[1]) for line in
                    (Path('/proc')/str(pid)/'smaps_rollup').read_text().splitlines()[1:] if ':' in line}
            rss+=values['Rss'];pss+=values['Pss']
        except (FileNotFoundError,ProcessLookupError,PermissionError):missing.append(pid)
    return dict(live_pids=live,sum_RSS_kib=rss,sum_PSS_kib=pss,missing_memory_pids=missing)


def measure(command,output,interval=0.5):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    assert 0.05<=interval<=5
    started=time.monotonic();cpu_start=time.process_time();known={};samples=0;maxrss=maxpss=0;missed=0
    launch=['/usr/bin/time','-v','-o',str(output/'gnu_time.txt'),'--',*map(str,command)]
    with (output/'stdout.log').open('x') as log, (output/'memory_samples.jsonl').open('x') as stream:
        process=subprocess.Popen(launch,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        finished={};done=threading.Event()
        def wait_command():
            finished['returncode']=process.wait();finished['time']=time.monotonic();done.set()
        waiter=threading.Thread(target=wait_command);waiter.start()
        stat=proc_stat(process.pid)
        registration=dict(owner_pid=os.getpid(),owner_start_ticks=proc_stat(os.getpid())['start_ticks'],
            measured_pid=process.pid,measured_start_ticks=stat['start_ticks'] if stat else None,
            command=list(map(str,command)),launch_command=launch,sample_interval_seconds=interval,
            scope='Fresh command plus all discovered descendants, including descendants that create new process groups.')
        (output/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
        while True:
            sample=sample_tree(process.pid,known);sample['elapsed_seconds']=time.monotonic()-started
            stream.write(json.dumps(sample)+'\n');stream.flush();samples+=1
            maxrss=max(maxrss,sample['sum_RSS_kib']);maxpss=max(maxpss,sample['sum_PSS_kib'])
            missed+=len(sample['missing_memory_pids'])
            if done.wait(interval):break
        waiter.join();code=finished['returncode']
        last=sample_tree(process.pid,known)
    elapsed=finished['time']-started
    gnu={}
    if (output/'gnu_time.txt').exists():
        for line in (output/'gnu_time.txt').read_text().splitlines():
            if ':' in line:
                key,value=line.strip().rsplit(':',1);gnu[key]=value.strip()
    result=dict(passed=code==0 and not last['live_pids'],returncode=code,
        complete_command_wall_seconds=elapsed,
        waited_process_RSS_high_water_kib=int(gnu['Maximum resident set size (kbytes)']) if 'Maximum resident set size (kbytes)' in gnu else None,
        sampled_tree_RSS_peak_kib=maxrss,sampled_tree_PSS_peak_kib=maxpss,
        samples=samples,sample_interval_seconds=interval,missing_memory_observations=missed,
        observer_CPU_seconds=time.process_time()-cpu_start,process_identities=known,
        live_descendants_after_command_exit=last['live_pids'],
        qualification='Wall ends at the independent wait-thread terminal receipt and includes command startup, all awaited phases and final result writing. GNU RSS is a process high-water statistic, not simultaneous tree memory. Summed RSS double-counts shared pages; sampled summed PSS apportions them and can miss transient peaks. OS page cache is uncontrolled; no cache flush or cold-storage claim. Observer CPU is separate and observation overhead is not calibrated away.')
    (output/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--interval',type=float,default=.5);parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();cmd=args.command
    if cmd and cmd[0]=='--':cmd=cmd[1:]
    assert cmd
    result=measure(cmd,args.output,args.interval)
    print(json.dumps(result),flush=True)
    raise SystemExit(0 if result['passed'] else 1)
