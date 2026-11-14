"""Persistent private native analysis context with dynamic, isolated FULLSTA jobs.

This is an engineering component, not a complete router or acceptance policy.
Epoch rotation never restarts an already completed candidate. Physical resource
and candidate-scope audits remain the caller's responsibility.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from retained_prefix_workflow import read,write,sha


def atomic(path, value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w') as out:
        out.write(value);out.flush();os.fsync(out.fileno())
    temporary.replace(path)


def quoted(path):
    text=str(path)
    assert not any(c in text for c in '\r\n\0')
    return '"'+text.replace('\\','\\\\').replace('"','\\"')+'"'


def process_identity(pid):
    try:
        fields=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split()
        return dict(pid=pid,state=fields[0],start_ticks=fields[19])
    except FileNotFoundError:return None


class NativeAnalysisPool:
    """Own one serial loaded context; submit candidate routes only after creation."""
    def __init__(self, directory, command, static_inputs, guard, *, epoch_seconds=1800,
                 idle_seconds=300, child_seconds=1800, startup_seconds=1800,
                 memory_bytes=64*1024**3):
        self.started=time.monotonic();self.directory=Path(directory).resolve();self.directory.mkdir(exist_ok=False)
        self.lock=(self.directory/'owner.lock').open('w');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert all(isinstance(v,int) and 1<=v<=1800 for v in [epoch_seconds,idle_seconds,child_seconds,startup_seconds])
        self.guards=dict(epoch_seconds=epoch_seconds,idle_seconds=idle_seconds,child_seconds=child_seconds,startup_seconds=startup_seconds,memory_bytes=memory_bytes,disk_reserve_bytes=80*1024**3)
        self.command=list(map(str,command));assert '--analysis' in self.command and '--route' not in self.command
        assert self.command[self.command.index('--check_route')+1]=='full'
        self.guard=Path(guard).resolve();self.inputs={str(Path(p).resolve()):sha(p) for p in static_inputs}
        self.binary=Path(self.command[0]).resolve();self.binary_sha256=sha(self.binary)
        self.inputs[str(self.binary)]=self.binary_sha256;self.inputs[str(self.guard)]=sha(self.guard)
        (self.directory/'bin').mkdir();shutil.copy2(self.binary,self.directory/'bin/vpr');self.command[0]=str(self.directory/'bin/vpr')
        normalized=list(self.command);normalized[normalized.index('--route_file')+1]='<candidate loaded only by child>'
        self.identity=hashlib.sha256(json.dumps([normalized,self.inputs],sort_keys=True).encode()).hexdigest()
        self.epochs=[];self.jobs=[];self.reuse=[];self.cache={};self.process=None;self.epoch=None;self.log=None
        self.closed=False
        write(self.directory/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],command=self.command,static_input_sha256=self.inputs,identity=self.identity,guards=self.guards,source_sha256={str(Path(__file__).resolve()):sha(__file__)},qualification='Pre-route-loaded FULLSTA component; candidates submitted dynamically after previous decisions. Per-child guards, idle retirement and between-job epochs are process protections, not overall algorithm or research stops. No acceptance or physical-resource audit is inferred.'))
        self._persist()

    def _persist(self):
        write(self.directory/'epochs.json',self.epochs);write(self.directory/'jobs.json',self.jobs);write(self.directory/'reuse.json',self.reuse)

    def _start_epoch(self):
        assert not self.closed
        if self.epoch is not None:self._finish_epoch()
        assert shutil.disk_usage(self.directory).free>=self.guards['disk_reserve_bytes']
        root=self.directory/f'epoch_{len(self.epochs):03d}';root.mkdir();inbox=root/'inbox';inbox.mkdir()
        env={k:v for k,v in os.environ.items() if not k.startswith('VPR_')}
        env.update(VPR_H3D_MODE='off',VPR_H3D_ANALYSIS_QUEUE=str(inbox),VPR_H3D_ANALYSIS_EPOCH_SECONDS=str(self.guards['epoch_seconds']),VPR_H3D_ANALYSIS_IDLE_SECONDS=str(self.guards['idle_seconds']),VPR_H3D_ANALYSIS_CHILD_SECONDS=str(self.guards['child_seconds']))
        self.log=(root/'stdout.log').open('w');start=time.monotonic()
        command=['prlimit','--core=0:0','--as='+str(self.guards['memory_bytes']),'--',str(self.guard),*self.command]
        self.process=subprocess.Popen(command,cwd=root,env=env,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
        self.epoch=dict(root=str(root),pid=self.process.pid,start_ticks=process_identity(self.process.pid)['start_ticks'],started_monotonic=start,command=command,jobs=0,status='loading')
        self.epochs.append(self.epoch);self._persist()
        while not(inbox/'ready').exists():
            code=self.process.poll()
            if code is not None:
                self.epoch.update(status='startup_failed',returncode=code);self._persist();raise RuntimeError('Native pool startup failed; original logs preserved')
            if time.monotonic()-start>=self.guards['startup_seconds']:
                self.epoch['status']='startup_guard';self._persist();os.killpg(self.process.pid,signal.SIGKILL);self.process.wait();raise TimeoutError('Native pool startup guard')
            time.sleep(.02)
        pid,ticks=(inbox/'ready').read_text().split();assert int(pid)==self.process.pid and ticks==self.epoch['start_ticks']
        self.epoch.update(status='ready',startup_seconds=time.monotonic()-start);self._persist()

    def _finish_epoch(self):
        if self.epoch is None:return
        inbox=Path(self.epoch['root'])/'inbox'
        if self.process.poll() is None:atomic(inbox/'stop','stop\n')
        # Completion receipts, not observation timeouts, determine whether a
        # candidate can be retried. Do not restart a live parent after this wait.
        try:code=self.process.wait(timeout=self.guards['child_seconds']+120)
        except subprocess.TimeoutExpired:
            self.epoch['status']='parent_still_live_after_observation_wait';self._persist();raise
        self.log.close();self.epoch.update(returncode=code,complete_parent_process_seconds=time.monotonic()-self.epoch['started_monotonic'])
        retired=inbox/'retired'
        if retired.exists():self.epoch.update(status='retired',retirement=retired.read_text().strip())
        else:self.epoch['status']='unexpected_parent_terminal'
        self._persist();assert code==0 and retired.exists(),'Unexpected parent failure; no automatic candidate resubmission'
        self.epoch=None;self.process=None

    def _ensure_epoch(self):
        if self.epoch is None:self._start_epoch();return
        inbox=Path(self.epoch['root'])/'inbox'
        if (inbox/'retired').exists() or self.process.poll() is not None:self._start_epoch()

    def analyze(self, route, *, echo=True, reuse=True):
        """Analyze an immutable route; return reuse receipts with no borrowed timing."""
        assert not self.closed;requested=time.monotonic();route=Path(route).resolve();digest=sha(route)
        fingerprint=hashlib.sha256(json.dumps([self.identity,digest,bool(echo)]).encode()).hexdigest()
        if reuse and fingerprint in self.cache:
            origin=self.cache[fingerprint];record=dict(origin,reused=True,origin_job=origin['job'],origin_creation_seconds=origin['complete_request_seconds'],complete_request_seconds=time.monotonic()-requested,native_child_seconds=None,native_parent_seconds=None)
            self.reuse.append(dict(fingerprint=fingerprint,origin_job=origin['job'],origin_receipt=origin['receipt'],actual_reuse_seconds=record['complete_request_seconds'],borrowed_creation_time=False));self._persist();return record
        job=self.directory/f'job_{len(self.jobs):04d}';job.mkdir();candidate=job/'routed.route';shutil.copy2(route,candidate);assert sha(candidate)==digest;native=job/'native';native.mkdir();submissions=[]
        while True:
            self._ensure_epoch();inbox=Path(self.epoch['root'])/'inbox';index=self.epoch['jobs'];request=inbox/f'{index}.request';assert not request.exists()
            atomic(request,quoted(candidate)+' '+quoted(native)+' '+str(int(bool(echo)))+'\n');receipt=inbox/f'{index}.result'
            write(job/'registration.json',dict(fingerprint=fingerprint,epoch_pid=self.epoch['pid'],epoch_start_ticks=self.epoch['start_ticks'],index=index,original_route=str(route),route_sha256=digest,request=str(request),native_directory=str(native),static_identity=self.identity))
            submissions.append(dict(epoch_pid=self.epoch['pid'],epoch_start_ticks=self.epoch['start_ticks'],index=index,request=str(request)));write(job/'submission_history.json',submissions)
            self.epoch['status']='job_running';self._persist()
            while not receipt.exists():
                retired=inbox/'retired'
                if retired.exists():
                    reason,count,failed=retired.read_text().split();assert int(count)==index and not(inbox/f'{index}.running').exists(),'Retired parent lost a potentially executed job'
                    if reason not in ['idle','epoch']:raise RuntimeError('Native pool retired for '+reason)
                    self._finish_epoch();break
                code=self.process.poll()
                if code is not None:
                    self.epoch.update(status='unexpected_parent_terminal',returncode=code);self._persist();raise RuntimeError('Parent terminal without a job receipt; no blind resubmission')
                time.sleep(.02)
            if receipt.exists():break
        values=receipt.read_text().strip().split('\t');assert len(values)==7 and int(values[0])==index
        code,sig,timeout=int(values[2]),int(values[3]),bool(int(values[4]));native_ok=code==0 and sig==0 and not timeout
        paths=[native/'native_sta_frontier.jsonl',native/'native_sta_frontier.jsonl.constraints.echo']+([native/'timing_graph.full_precision.echo'] if echo else [])
        stdout=(native/'stdout.log').read_text() if (native/'stdout.log').exists() else ''
        complete=native_ok and all(p.is_file() for p in paths) and 'Completed routing consistency check successfully' in stdout and 'Synchronize the packed netlist to routing optimization' in stdout
        if complete:
            with paths[0].open() as stream:
                last=None
                for line in stream:last=json.loads(line)
            complete=last is not None and last.get('type')=='complete'
        assert sha(candidate)==digest and sha(route)==digest,'Candidate changed during native analysis'
        result=dict(job=str(job),native_directory=str(native),receipt=str(receipt),fingerprint=fingerprint,static_identity=self.identity,epoch_pid=self.epoch['pid'],epoch_start_ticks=self.epoch['start_ticks'],child_pid=int(values[1]),native_exit_code=code,native_signal=sig,timed_out=timeout,passed=bool(complete),reused=False,route_sha256=digest,native_child_seconds=float(values[5]),max_rss_kib=int(values[6]),complete_request_seconds=time.monotonic()-requested,native_parent_seconds=None,complete_single_configuration_seconds=None,artifact_sha256={str(p):sha(p) for p in paths if p.exists()},qualification='Child time includes fork/native LOAD/FULL/pin synchronization/STA. Shared parent startup/idle/cleanup and full algorithm costs remain separate. Exact reuse never borrows original creation time; failed candidates are cached as failures. Physical/scope audits and acceptance remain external.')
        write(job/'completion.json',result);self.jobs.append(result);self.cache[fingerprint]=result;self.epoch.update(jobs=index+1,status='ready');self._persist();return result

    def close(self):
        """Retire the parent and seal immutable inputs, without stopping the goal."""
        if self.closed:return
        self._finish_epoch();assert all(sha(p)==h for p,h in self.inputs.items()),'Static input changed during pool lifetime'
        self.closed=True
        write(self.directory/'completion.json',dict(passed=True,all_jobs_passed=all(j['passed'] for j in self.jobs),jobs=len(self.jobs),reuse_hits=len(self.reuse),epochs=len(self.epochs),epoch_guards=self.guards,complete_component_workflow_seconds=time.monotonic()-self.started,complete_single_configuration_seconds=None,static_inputs_unchanged=True,source_sha256={str(p):sha(p) for p in [self.directory/'registration.json',self.directory/'epochs.json',self.directory/'jobs.json',self.directory/'reuse.json',Path(__file__).resolve()]},qualification='Broker completion and per-job status are separate. Failed validation candidates remain failed; an epoch rotation or local workflow end never completes the overall research goal. Shared component time is not cold complete algorithm time.'))
        fcntl.flock(self.lock,fcntl.LOCK_UN);self.lock.close()
