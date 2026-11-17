"""Serial four-strength mechanism control; every new stage is charged once."""
import argparse
import copy
import fcntl
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from fixed_anchor_acceptance import decisions
from multiobjective_acceptance_v2 import decide
from seed_census_analysis_pool_v2 import process_identity

ROOT=D/'vertical_cost_baseline_dev_01'
WEIGHTS={'weight_0':0.,'weight_05':.5,'weight_1':1.,'weight_2':2.}


def clean_environment(environment):
    env={k:v for k,v in environment.items() if not k.startswith('VPR_')
         and k not in ['LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    return env


class Runner:
    def __init__(self,batch,fd):
        self.b=batch;self.fd=fd;self.costs=[];self.roles={}

    def invoke(self,script,args,tag,timeout=2400):
        assert shutil.disk_usage(D).free>=80*1024**3
        command=[sys.executable,'-B',str(D/script),*map(str,args)]
        if script in ['vertical_cost_evidence_v2.py','build_vertical_cost_baseline_01.py']:
            command+=['--serial-lock-fd',str(self.fd)]
        start=time.monotonic();status='completed';code=None
        with (self.b/(tag+'.log')).open('x') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,pass_fds=(self.fd,),env=clean_environment(os.environ))
            write(self.b/'active_child.json',dict(**process_identity(proc.pid),tag=tag,command=command,status='running'))
            try:code=proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                status='timeout';os.killpg(proc.pid,signal.SIGTERM)
                try:code=proc.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
        if code and status=='completed':status='infrastructure_error'
        self.costs.append(dict(tag=tag,command=command,returncode=code,status=status,
            complete_stage_seconds=time.monotonic()-start))
        write(self.b/'process_costs.json',self.costs)
        write(self.b/'active_child.json',dict(pid=proc.pid,tag=tag,status=status,returncode=code))
        return status

    def audit(self,name,weight,mode):
        output=self.b/('zero_equivalence.json' if mode=='zero' else name+'_verification.json')
        args=['--mode',mode,'--transaction',self.b,'--role',name,'--output',output]
        if mode=='weighted':args+=['--weight',weight]
        return self.invoke('vertical_cost_evidence_v2.py',args,name+'_readonly_admission')

    def arm(self,name,weight,reg,loaded):
        role=reg['roles'][name];self.roles[name]=dict(status='running',quality_admitted=False)
        write(self.b/'progress.json',self.roles)
        status=self.invoke('vertical_cost_baseline_dev_01/run_vertical_cost_seed_analysis.py',[
            '--source',role['source'],'--batch',self.b/name,'--native-cases',role['request'],
            '--objective',role['objective'],'--seed-order',role['seed_order'],
            '--candidate-full-sta','--expected-loaded-source-route',loaded,'--vertical-cost-weight',weight],name+'_native')
        if status!='completed':return dict(status=status,quality_admitted=False,failed_stage='native_worker')
        status=self.invoke('audit_native_feedback_objective_cached.py',[
            '--batch',self.b,'--role',name,'--cache',reg['audit_cache'],'--output',self.b/(name+'_audit')],name+'_physical_scope_audit')
        if status!='completed':return dict(status=status,quality_admitted=False,failed_stage='physical_scope_audit')
        analysis=read(self.b/(name+'_audit/analysis.json'));assert analysis['passed']
        if not analysis.get('candidate_route'):
            row=dict(status='transaction_failed_rolled_back',accepted=False,quality_admitted=False)
        else:
            evaluation=self.b/(name+'_evaluation')
            status=self.invoke('materialize_crossing_source_candidate_v1.py',[
                '--worker',self.b/name,'--output',evaluation,'--audited-route',analysis['candidate_route'],
                '--full-graph-cache',reg['full_graph_cache']],name+'_candidate_materialization')
            if status!='completed':return dict(status=status,quality_admitted=False,failed_stage='candidate_materialization')
            from state_resource_assurance import require_publication_proof
            before=read(Path(role['state'])/'endpoint_vector.json');after=read(evaluation/'endpoint_vector.json')
            old=require_publication_proof(role['state'])['resource_axes']
            new=require_publication_proof(evaluation)['resource_axes']
            policies=decisions(before,after,old,new,role['original_budget'])
            for mode in ['timing_under_resources','resources_under_timing']:
                policies[mode]=decide(mode,before,after,old,new,cpd_limit_s=role['original_budget']['CPD_s'],
                    resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,
                    resource_objectives=('SB_pairs','CB_sources'))
            write(self.b/(name+'_decisions.json'),policies)
            row=dict(status='legal_evaluated',evaluation=str(evaluation),resources=new,
                cpd_s=after['cpd_s'],policies=policies,quality_admitted=False)
        self.roles[name]=row;write(self.b/'progress.json',self.roles)
        status=self.audit(name,weight,'zero' if weight==0 else 'weighted')
        if status!='completed':return dict(**row,verification_status=status,failed_stage='independent_admission')
        proof=read(self.b/('zero_equivalence.json' if weight==0 else name+'_verification.json'))
        assert proof['passed']
        return dict(**{k:v for k,v in row.items() if k!='quality_admitted'},
            verification_status='passed',quality_admitted=row['status']=='legal_evaluated',
            rollback_verified=row['status']=='transaction_failed_rolled_back')


def execute(runner,reg,loaded):
    """Zero mismatch blocks positive strengths; ordinary weighted failures do not."""
    zero_ok=False
    for name,weight in WEIGHTS.items():
        if weight>0 and not zero_ok:
            runner.roles[name]=dict(status='not_executed_zero_equivalence_not_passed',quality_admitted=False)
        else:
            try:runner.roles[name]=runner.arm(name,weight,reg,loaded)
            except Exception as exc:
                runner.roles[name]=dict(status='infrastructure_error',error=repr(exc),quality_admitted=False)
            if weight==0:zero_ok=runner.roles[name].get('verification_status')=='passed'
        write(runner.b/'progress.json',runner.roles)
    return zero_ok


def main():
    p=argparse.ArgumentParser();p.add_argument('--serial-lock-fd',type=int,required=True)
    p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
    assert Path('/proc/self/fd',str(a.serial_lock_fd)).resolve()==(D/'critical_scope_runner.lock').resolve()
    fcntl.flock(a.serial_lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not a.batch.exists(),'Inspect existing attempt, never restart it'
    a.batch.mkdir(parents=True);start=time.monotonic();r=Runner(a.batch,a.serial_lock_fd)
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    plan=read(ROOT/'plan.json');assert plan['weights']==[0,.5,1,2]
    assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    reference=read(ROOT/'reference_role.json')
    parent=read(D/'robot_union_mechanism_02/transaction/registration.json')
    reg=dict(roles={n:copy.deepcopy(reference) for n in WEIGHTS},vertical_cost_weights=WEIGHTS,
        audit_cache=parent['audit_cache'],full_graph_cache=parent['full_graph_cache'],
        limits=dict(memory_bytes=64*1024**3,child_seconds=2400,disk_reserve_bytes=80*1024**3))
    files=[Path(__file__).resolve(),ROOT/'plan.json',ROOT/'reference_role.json',
        ROOT/'worker_preparation.json',ROOT/'run_vertical_cost_seed_analysis.py',
        D/'vertical_cost_evidence_v2.py',D/'build_vertical_cost_baseline_01.py',
        D/'audit_native_feedback_objective_cached.py',D/'materialize_crossing_source_candidate_v1.py',
        D/'fixed_anchor_acceptance.py',D/'multiobjective_acceptance_v2.py']
    reg['source_sha256']={str(f):sha(f) for f in files}
    write(a.batch/'registration.json',reg)
    write(a.batch/'execution_registration.json',dict(**process_identity(os.getpid()),
        registration_sha256=sha(a.batch/'registration.json'),source_sha256=reg['source_sha256']))
    try:
        status=r.invoke('vertical_cost_evidence_v2.py',['--mode','source-control','--output',a.batch/'source_control_reuse.json'],'source_control_readonly_admission')
        assert status=='completed','No native calls permitted before source-control admission'
        loaded=read(a.batch/'source_control_reuse.json')['source_control']['loaded_source_route']
        assert not (ROOT/'build').exists(),'An existing build attempt needs inspection, not automatic repetition'
        assert r.invoke('build_vertical_cost_baseline_01.py',['--execute'],'private_build',timeout=2700)=='completed'
        zero=execute(r,reg,loaded)
        assert all(sha(f)==h for f,h in reg['source_sha256'].items())
        write(a.batch/'completion.json',dict(status='four_strength_scope_terminal',all_roles_accounted=True,
            zero_equivalence_passed=zero,roles=r.roles,complete_scope_seconds=time.monotonic()-start,
            process_costs=r.costs,source_sha256=reg['source_sha256'],
            qualification='Actual shared imported mechanism scope including new admission/build; stage costs are nested. Historical source-control creation is reused and not newly charged. No cold whole-method runtime or independent input. Every preregistered strength retained.'))
    except BaseException as exc:
        write(a.batch/'failure.json',dict(error=repr(exc),roles=r.roles,process_costs=r.costs,
            complete_attempt_seconds=time.monotonic()-start,automatic_retry=False))
        raise


if __name__=='__main__':main()
