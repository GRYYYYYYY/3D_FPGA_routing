#!/usr/bin/env python3
"""Exercise the new reuse executor on completed real data, with zero native work."""
import copy,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resource_native_reuse import free_match
b=D/'cross_actor_resource_reuse_validation_01';b.mkdir(exist_ok=False);started=time.monotonic();prior=D/'strong_A0_fast_resource_dev_01/native_only_K4/round_000/candidate_00';role=read(prior/'registration.json')['roles']['reuse_off'];assert free_match(role,[prior])is not None
negative={}
for name,delta in [('domain_ON',dict(crossing_reuse_enabled=True)),('forced_paths',dict(fixed_target_paths=True)),('changed_pressure',dict(pressure_start=2.))]:
 r=copy.deepcopy(role);r.update(delta);negative[name]=free_match(r,[prior])is None
request=b/'changed_request.txt';lines=Path(role['request']).read_text().splitlines();lines[-1]=lines[-1].rsplit(' ',1)[0]+' 0.5';request.write_text('\n'.join(lines)+'\n');r=copy.deepcopy(role);r['request']=str(request);negative['changed_request']=free_match(r,[prior])is None;assert all(negative.values())
write(b/'registration.json',dict(question='Can exact completed OFF work be reused without new native processes while a changed resource policy obtains a fresh opposite acceptance?',source_sha256={str(p):sha(p)for p in[Path(__file__).resolve(),D/'run_serial_resource_transactions_v2.py',D/'resource_native_reuse.py',D/'current_native_reuse_resource.py',prior/'completion.json',prior/'registration.json']},native_calls_planned=0));rows={}
for name,zero in [('original_envelope_accept',False),('zero_wire_headroom_reject',True)]:
 case=b/name;case.mkdir();r=copy.deepcopy(role)
 if zero:r['fixed_resource_limits']['wirelength']=r['original_budget']['wirelength']
 write(case/'registration.json',dict(roles=dict(reused_OFF=r),source_sha256={str(b/'registration.json'):sha(b/'registration.json')},limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),current_resource_selector_after_commit=True,resource_conditions=dict(original_budget=r['original_budget'],resource_limits=r['fixed_resource_limits'])));
 with (case/'controller.log').open('w')as log:result=subprocess.run([sys.executable,str(D/'run_serial_resource_transactions_v2.py'),'--batch',str(case),'--reuse-native-batch',str(prior)],stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 assert result.returncode==0,(name,result.returncode);c=read(case/'completion.json');assert c['passed'];p=read(case/'progress.json')['reused_OFF'];d=read(case/'reused_OFF_decisions.json');assert p['native_reused']and p['native_calls_new']==0 and p['native_core_seconds_new']==0.;assert d['resources_under_timing']['accepted']is (not zero);assert read(case/'process_costs.json')==[],'Reuse should execute no subprocess';rows[name]=dict(evaluation=p['evaluation'],CPD_s=p['cpd_s'],resources=p['resources'],accepted=d['resources_under_timing']['accepted'],reason=d['resources_under_timing']['reason'],native_calls_new=p['native_calls_new'],native_core_seconds_new=p['native_core_seconds_new'],complete_local_reuse_workflow_seconds=c['complete_orchestrator_seconds'])
assert rows['original_envelope_accept']['evaluation']==rows['zero_wire_headroom_reject']['evaluation'];write(b/'completion.json',dict(passed=True,rows=rows,negative_guards=negative,native_calls=0,route_calls=0,complete_validation_seconds=time.monotonic()-started,source_sha256={str(p):sha(p)for p in[b/'registration.json',*[b/n/'completion.json'for n in rows]]},qualification='Real completed native data reused without invoking native, audit or STA subprocesses. Identical candidate gets opposite fresh budget acceptance; domain-ON/forced/pressure/request changes are rejected by matching. This establishes a prototype reuse gate, not a cold algorithm speedup. Existing paired/native-first/main jobs unchanged.'))
print(dict(rows=rows,negative=negative),flush=True)
