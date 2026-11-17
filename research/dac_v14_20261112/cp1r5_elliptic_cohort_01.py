"""External cohort administration; executes the immutable CP1 entry, never edits it."""
import json,os,subprocess,sys,shutil,hashlib,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from seed_census_analysis_pool_v2 import process_identity
from endpoint_timing_policy_streaming_v2 import compare
from packed_input_contract_v1 import classify_initial_failure
ROOT=D/'cp1r5_elliptic_pair_01'

class InputAdmissionError(Exception):pass

def verify_copy_source(source,row):
    source=Path(source)
    if not source.is_file():raise InputAdmissionError('Physical input unavailable: '+str(source))
    if source.stat().st_size!=row['bytes'] or sha(source)!=row['sha256']:
        raise InputAdmissionError('Physical bytes differ from preregistered provenance: '+str(source))

def classify_actual_initial_failure(manifest,stdout,initial_legal_present=False):
    if manifest.get('execution_status')=='timeout' and not initial_legal_present:
        return 'initial_routing_execution_timeout'
    return classify_initial_failure(manifest,stdout)

def environment():
    env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH'] and not k.startswith('VPR_')}
    env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    return env

def confirmation_arguments(plan,item):
    return ['--native',item['configs']['native'],'--domain',item['configs']['domain'],'--packing-manifest',item['packing_manifest'],'--forbid-prefix',str(D.parents[1])]

def measured_command(plan,item,arm,case):
    release=Path(plan['release']);runtime=release/'runtime'
    return ['/usr/bin/python3',str(runtime/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--','/usr/bin/python3',str(runtime/'supervise_method_phase.py'),'--receipt',str(case/'supervision.json'),'--','/usr/bin/python3',str(release/'confirmation.py'),'run-arm',*confirmation_arguments(plan,item),'--arm',arm,'--case',str(case)]

def provision(plan,item):
    """Called only by the lock-owning queue, before measured routing."""
    target=Path(item['workspace']);assert not (target/'provisioning.json').exists()
    assert shutil.disk_usage(target).free>80*1024**3
    copied=[]
    for key,row in item['copies'].items():
        source=Path(row['source']);dest=Path(row['destination']);assert not dest.exists()
        verify_copy_source(source,row)
        dest.parent.mkdir(exist_ok=True);shutil.copyfile(source,dest);assert sha(dest)==row['sha256']
        dest.chmod(0o444);copied.append(key)
    command=['/usr/bin/python3',str(Path(plan['release'])/'confirmation.py'),'check',*confirmation_arguments(plan,item)]
    result=subprocess.run(command,cwd=plan['release'],env=environment(),capture_output=True,text=True,timeout=120)
    (target/'admission.stdout').write_text(result.stdout);(target/'admission.stderr').write_text(result.stderr)
    assert result.returncode==0,result.stderr[-2000:]
    admission=json.loads(result.stdout);assert admission['passed']
    write(target/'provisioning.json',dict(passed=True,physical_files=copied,physical_hashes_verified=True,admission=admission,native_calls=0,scope='Serial-slot input packaging; outside measured algorithm time. Each measured command rechecks physical bytes.'))

def run_arm(plan,item,arm):
    case=Path(item['workspace'])/arm;case.mkdir(exist_ok=False);(case/'queue').mkdir()
    command=measured_command(plan,item,arm,case)
    with (case/'launcher.log').open('x') as log:
        child=subprocess.Popen(command,cwd=plan['release'],env=environment(),stdout=log,stderr=subprocess.STDOUT)
        identity=process_identity(child.pid);assert identity
        external_bound={f:h for f,h in plan['source_sha256'].items() if not Path(f).resolve().is_relative_to(D.parents[1])}
        write(case/'queue/registration.json',dict(**identity,command=command,source_sha256=external_bound))
        write(ROOT/'active_child.json',dict(input=item['id'],arm=arm,**identity,case=str(case)))
        write(ROOT/'queue/status.json',dict(status='running_confirmation_arm',input=item['id'],arm=arm,case=str(case),**identity))
        code=child.wait()
    measurement=read(case/'measurement/completion.json');supervision=read(case/'supervision.json')
    assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants'],'Surviving processes require reconciliation'
    verified=False;verification_seconds=None
    if code==0 and supervision['passed']:
        runtime=Path(plan['release'])/'runtime'
        verification_start=time.monotonic()
        with (case/'verification.log').open('x') as log:
            check=subprocess.run(['/usr/bin/python3',str(runtime/'guarded_entry.py'),'--forbid-prefix',str(D.parents[1]),'--script',str(runtime/'verify_complete_unified_method_v1.py'),'--root',str(case)],cwd=runtime,env=environment(),stdout=log,stderr=subprocess.STDOUT)
        verification_seconds=time.monotonic()-verification_start
        verified=check.returncode==0 and (case/'completion.json').exists() and read(case/'completion.json')['passed']
    status='complete_legal_verified' if verified else 'execution_or_verification_failed'
    initial=case/'flow/resource_flow/initial/runs/state/manifest.json'
    if code and initial.exists():status=classify_actual_initial_failure(read(initial),(initial.parent/'stdout.log').read_text(),(case/'flow/resource_flow/initial/completion.json').exists())
    release_evidence=read(case/'confirmation_input.json') if (case/'confirmation_input.json').exists() else None
    if verified:
        assert release_evidence and release_evidence['release_manifest_sha256']==plan['release_manifest_sha256']
        assert release_evidence['configuration_sha256'][arm]==sha(item['configs'][arm])
    return dict(status=status,case=str(case),command_returncode=code,independent_research_verification_seconds=verification_seconds,quality=None if not verified else {k:read(case/'completion.json')[k] for k in ['CPD_ns','resources']},complete_seconds=measurement['complete_command_wall_seconds'],sampled_PSS_kib=measurement['sampled_tree_PSS_peak_kib'],missing_memory_observations=measurement['missing_memory_observations'],measurement=str(case/'measurement/completion.json'),supervision=str(case/'supervision.json'),confirmation_admission=release_evidence)

def compare_pair(plan,item,results):
    assert set(results)=={'native','domain'};files=[ROOT/'plan.json',Path(__file__).resolve()];paired=None;own_root={}
    for arm,row in results.items():
        files += [Path(row['measurement']),Path(row['supervision'])]
        if row['status']=='complete_legal_verified':
            case=Path(row['case']);done=read(case/'flow/completion.json');ini=Path(done['initial_state']);fin=Path(done['final_state'])
            own_root[arm]=compare(read(ini/'endpoint_vector.json'),read(fin/'endpoint_vector.json'))
            files += [case/'completion.json',case/'flow/completion.json',case/'confirmation_input.json',ini/'endpoint_vector.json',fin/'endpoint_vector.json']
    if len(own_root)==2:
        cases={arm:Path(row['case']) for arm,row in results.items()};done={arm:read(case/'flow/completion.json') for arm,case in cases.items()};initial={arm:Path(r['initial_state']) for arm,r in done.items()};final={arm:Path(r['final_state']) for arm,r in done.items()}
        run=lambda state:Path(read(state/'completion.json')['run'])
        bodies={arm:route_body(run(state)/'routed.route') for arm,state in initial.items()}
        vectors={arm:read(state/'endpoint_vector.json') for arm,state in initial.items()}
        matched=bodies['native']==bodies['domain'] and vectors['native']==vectors['domain']
        paired=dict(matched_initial_route_and_full_vector=matched,initial_route_body_sha256=bodies)
        if matched:
            quality={arm:read(case/'completion.json') for arm,case in cases.items()};delta={key:quality['domain']['resources'][key]-quality['native']['resources'][key] for key in ['wirelength','SB_pairs','CB_sources']}
            delta.update(CPD_ns=quality['domain']['CPD_ns']-quality['native']['CPD_ns'],complete_seconds=results['domain']['complete_seconds']-results['native']['complete_seconds'])
            endpoint=compare(read(final['native']/'endpoint_vector.json'),read(final['domain']/'endpoint_vector.json'));assert endpoint['compatible']
            n=quality['native']['resources'];denom=n['SB_pairs']+n['CB_sources']
            paired.update(delta_domain_minus_native=delta,endpoint_changes=endpoint,SB_reduction_percent=None if n['SB_pairs']==0 else -100*delta['SB_pairs']/n['SB_pairs'],SB_plus_CB_reduction_percent=None if denom==0 else -100*(delta['SB_pairs']+delta['CB_sources'])/denom)
        else:paired['qualification']='Different actual roots: retain both outputs but no causal domain/release delta.'
    result=dict(passed=True,input=item['id'],release_manifest_sha256=plan['release_manifest_sha256'],registered_roles=2,verified_legal_roles=len(own_root),results=results,own_initial_to_final_endpoint_changes=own_root,matched_comparison=paired,source_sha256={str(f):sha(f) for f in files},qualification='Prospective CP1r5 pair on one new-to-CP1 public mapped sequential circuit with fresh placement on the existing Hybrid-O architecture family. Two arms are one input. Not unseen holdout, external application timing or interleaved speedup. Domain+release treatment remains combined; separate ablations identify mechanisms. Scientific failures are retained.')
    write(ROOT/(item['id']+'_comparison.json'),result);return result

def execute(plan):
    outcomes={}
    for item in plan['inputs']:
        assert all(sha(f)==h for f,h in plan['source_sha256'].items())
        write(ROOT/'queue/status.json',dict(status='provisioning_under_serial_lock',input=item['id']))
        before=time.monotonic();admission_failure=item.get('admission_failure')
        if not admission_failure:
            try:provision(plan,item)
            except InputAdmissionError as error:admission_failure=repr(error)
        write(ROOT/(item['id']+'_provisioning_cost.json'),dict(seconds=time.monotonic()-before,scope='Input provisioning/research admission, outside measured algorithm commands',admission_failure=admission_failure))
        if admission_failure:
            rows={arm:dict(status='unexecuted_physical_input_admission_failed',quality=None,complete_seconds=None,measurement=None,supervision=None,native_calls_new=0,reason=admission_failure) for arm in plan['fixed_arm_order']}
            result=dict(passed=True,input=item['id'],registered_roles=2,verified_legal_roles=0,unexecuted_roles=2,results=rows,matched_comparison=None,own_initial_to_final_endpoint_changes={},qualification='Input bytes/provenance failed admission. Both roles remain preregistered and unexecuted; no zero algorithm cost, legal quality, router-failure or infeasibility claim.')
            write(ROOT/(item['id']+'_results.json'),rows);write(ROOT/(item['id']+'_comparison.json'),result);outcomes[item['id']]=result;continue
        results={}
        for arm in plan['fixed_arm_order']:
            assert all(sha(f)==h for f,h in plan['source_sha256'].items())
            results[arm]=run_arm(plan,item,arm);write(ROOT/(item['id']+'_results.json'),results)
        outcomes[item['id']]=compare_pair(plan,item,results)
    write(ROOT/'comparison.json',dict(passed=True,registered_inputs=len(plan['inputs']),registered_roles=2*len(plan['inputs']),verified_legal_roles=sum(r['verified_legal_roles'] for r in outcomes.values()),unexecuted_admission_roles=sum(r.get('unexecuted_roles',0) for r in outcomes.values()),input_comparisons={key:str(ROOT/(key+'_comparison.json')) for key in outcomes},release_manifest_sha256=plan['release_manifest_sha256'],qualification='Every preregistered input/role retained, including input admission, timeout, no-cut/no-gain and degraded outcomes. Packing/provisioning/public reconstruction and independent research verification costs are distinct from complete measured run-arm time. No matrix or ordinary-negative stopping condition for research.'))
