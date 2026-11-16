"""One owner, after independent confirmation and mechanism work; no retries."""
import fcntl,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from BNN_interleaved_timing_v1 import ORDER,validate_configs,environment,finish

root=D/'BNN_interleaved_timing_03';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}
write(q/'registration.json',dict(**process_identity(os.getpid()),fixed_order=ORDER,source_sha256=bound))
try:
    prior=Path(plan['predecessor']);identity=read(prior/'registration.json')
    while not (prior/'completion.json').exists():
        live=process_identity(identity['pid'])
        assert live and live['state']!='Z' and live['start_ticks']==identity['start_ticks'],'Predecessor missing; reconcile, never restart'
        write(q/'status.json',dict(status='waiting_for_registered_robot_union',predecessor=str(prior)));time.sleep(15)
    closed=read(prior/'completion.json')
    assert closed['passed'] and closed['status']=='registered_union_mechanism_terminal','Predecessor requires reconciliation; roles unexecuted'
    serial=(D/'critical_scope_runner.lock').open('r')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    configs={r:read(root/'configs'/f'{r}.json') for r in ['native','domain']}
    validate_configs(configs['native'],configs['domain'])
    assert all(sha(f)==h for f,h in configs['native']['input_sha256'].items())
    assert shutil.disk_usage(root).free >= plan['minimum_free_bytes_at_admission']
    os.environ.update(plan['fixed_environment'])
    for k in list(os.environ):
        if k.startswith('VPR_'): del os.environ[k]
    write(root/'admission.json',dict(passed=True,environment=environment(),input_seals_verified=True,large_checks_waited_for_serial_slot=True))
    results={}
    for name in ORDER:
        assert all(sha(f)==h for f,h in bound.items())
        case=root/name;case.mkdir(exist_ok=False);(case/'queue').mkdir()
        config=root/'configs'/f"{name.split('_')[0]}.json"
        shutil.copy2(config,case/'config.json')
        write(case/'environment_before.json',environment())
        command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,str(D/'run_complete_resource_timing_joint_stream_v1.py'),'--config',str(config),'--output',str(case/'flow')]
        with (case/'queue/execution.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            ident=process_identity(child.pid);assert ident
            write(case/'queue/registration.json',dict(**ident,command=command,source_sha256=bound))
            write(q/'status.json',dict(status='running',case=name,**ident))
            code=child.wait()
        write(case/'environment_after.json',environment())
        mp=case/'measurement/completion.json';fp=case/'flow/completion.json'
        # Lost observer or live descendants require reconciliation, never overlapping a retry.
        assert mp.exists(),'Observer missing; reconcile original descendants before proceeding'
        measurement=read(mp)
        assert not measurement['live_descendants_after_command_exit'],'Descendants remain; no next role'
        complete=False;verify_code=None
        if code==0 and measurement['passed'] and fp.exists() and read(fp)['passed']:
            write(q/'status.json',dict(status='verifying_complete_case',case=name))
            with (case/'queue/verification.log').open('x') as log:
                verify_code=subprocess.run([sys.executable,str(D/'verify_complete_resource_timing_joint_stream_v1.py'),'--root',str(case)],stdout=log,stderr=subprocess.STDOUT).returncode
            complete=bool(verify_code==0 and (case/'completion.json').exists() and read(case/'completion.json')['passed'])
        row=dict(complete_verified=complete,measurement_complete=True,returncode=code,verification_returncode=verify_code,
            complete_seconds=measurement['complete_command_wall_seconds'],sampled_tree_PSS_peak_kib=measurement['sampled_tree_PSS_peak_kib'],
            sampled_tree_RSS_peak_kib=measurement['sampled_tree_RSS_peak_kib'],missing_memory_observations=measurement['missing_memory_observations'],
            observer_CPU_seconds=measurement['observer_CPU_seconds'],quality=None,
            failure_stage=None if complete else 'readonly_verification' if code==0 else 'measured_command')
        if fp.exists() and not complete:row['flow_terminal']=read(fp).get('status')
        results[name]=row;write(q/'results.json',results)
    write(q/'status.json',dict(status='comparing_complete_balanced_repetitions'))
    result=finish(root);assert result['passed']
    write(q/'completion.json',dict(passed=True,status='registered_interleaved_timing_terminal',comparison=str(root/'comparison.json'),source_sha256=bound,qualification='All four attempts accounted, including negative outcomes. Not a research stopping condition.'))
    write(q/'status.json',dict(status='terminal'))
except Exception as exc:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(exc),source_sha256=bound));traceback.print_exc();raise
