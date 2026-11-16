"""Reuse the verified cohort administrator with a new output identity and labels."""
from retained_prefix_workflow import D,read,write,sha
source=D/'cp1r2_confirmation_cohort_v1.py';target=D/'cp1r3_confirmation_cohort_v1.py';assert not target.exists()
t=source.read_text();changes=[]
def replace(old,new):
    global t
    assert t.count(old)==1,old;t=t.replace(old,new);changes.append([old,new])
replace('import json,os,subprocess,sys,shutil,hashlib','import json,os,subprocess,sys,shutil,hashlib,time')
replace("ROOT=D/'cp1r2_cross_circuit_cohort_01'","ROOT=D/'cp1r3_distinct_input_cohort_01'")
replace('def environment():', '''class InputAdmissionError(Exception):pass

def verify_copy_source(source,row):
    source=Path(source)
    if not source.is_file():raise InputAdmissionError('Physical input unavailable: '+str(source))
    if source.stat().st_size!=row['bytes'] or sha(source)!=row['sha256']:
        raise InputAdmissionError('Physical bytes differ from preregistered provenance: '+str(source))

def classify_actual_initial_failure(manifest,stdout,initial_legal_present=False):
    if manifest.get('execution_status')=='timeout' and not initial_legal_present:
        return 'initial_routing_execution_timeout'
    return classify_initial_failure(manifest,stdout)

def environment():''')
replace("        assert source.stat().st_size==row['bytes'] and sha(source)==row['sha256']","        verify_copy_source(source,row)")
replace('    verified=False','    verified=False;verification_seconds=None')
replace("        with (case/'verification.log').open('x') as log:","        verification_start=time.monotonic()\n        with (case/'verification.log').open('x') as log:")
replace("        verified=check.returncode==0", "        verification_seconds=time.monotonic()-verification_start\n        verified=check.returncode==0")
replace("if code and initial.exists():status=classify_initial_failure(read(initial),(initial.parent/'stdout.log').read_text())", "if code and initial.exists():status=classify_actual_initial_failure(read(initial),(initial.parent/'stdout.log').read_text(),(case/'flow/resource_flow/initial/completion.json').exists())")
replace("return dict(status=status,case=str(case),command_returncode=code,quality=", "return dict(status=status,case=str(case),command_returncode=code,independent_research_verification_seconds=verification_seconds,quality=")
replace('Prospective CP1 pair on one known historical physical input.', 'Prospective CP1r3 pair on one known historical physical input.')
start=t.index('def execute(plan):');old=t[start:]
new='''def execute(plan):
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
'''
changes.append([old,new]);t=t[:start]+new;compile(t,str(target),'exec')
restored=t
for before,after in reversed(changes):assert restored.count(after)==1;restored=restored.replace(after,before)
assert restored==source.read_text()
target.write_text(t)
write(D/'cp1r3_cohort_administration_revision_01.json',dict(passed=True,parent=str(source),parent_sha256=sha(source),source=str(target),source_sha256=sha(target),reversible_to_parent=True,changes=changes,native_algorithm_or_frozen_release_changed=False))
print(dict(passed=True,source=str(target),native_algorithm_changed=False))
