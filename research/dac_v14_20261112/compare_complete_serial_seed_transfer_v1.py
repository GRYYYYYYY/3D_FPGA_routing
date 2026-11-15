"""Check seed-transfer outcomes without treating reproduced roots as new samples."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir

root=D/'complete_serial_seed_transfer_01';plan=read(root/'plan.json');closed=read(root/'queue/completion.json');observed=read(root/'queue/results.json')
assert set(observed)==set(plan['fixed_order'])
refs=dict(eltwise_native='complete_serial_seed_policy_dev_01/delay_seed_native',eltwise_domain='complete_serial_lazy_dev_01/delay_seed_paired',softmax_native='complete_serial_transfer_dev_01/softmax_native',softmax_domain='complete_serial_lazy_transfer_dev_01/softmax_paired')
files=[Path(__file__).resolve(),root/'plan.json',root/'queue/completion.json',root/'queue/results.json'];results={};pairs={}
def equal_state(x,y):
 vx,vy=[read(s/'endpoint_vector.json') for s in [x,y]]
 return dict(full_endpoint_vector_exact=all(vx[k]==vy[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),ordered_route_body_exact=route_body(run_dir(x)/'routed.route')==route_body(run_dir(y)/'routed.route'))
for name in plan['fixed_order']:
 actual=root/name;reference=D/refs[name];config=read(actual/'config.json');baseline=read(reference/'config.json');measurement=read(actual/'measurement/completion.json')
 assert all(sha(f)==h for f,h in config['input_sha256'].items())
 cmd,oldcmd=list(config['route_command']),list(baseline['route_command']);assert cmd[cmd.index('--seed')+1]=='19' and oldcmd[oldcmd.index('--seed')+1]=='11';oldcmd[oldcmd.index('--seed')+1]='19';assert cmd==oldcmd
 for k in ['domain_mode','domain_feedback','seed_order','cache_mode','initial_route_imported']:assert config[k]==baseline[k]
 files += [actual/'config.json',reference/'config.json',actual/'measurement/completion.json']
 if not observed[name]['passed']:
  results[name]=dict(status='configuration_failed',measured_failed_seconds=measurement['complete_command_wall_seconds'],quality=None,initial_root_independence=None);continue
 proof=read(actual/'explicit_policy_verification.json');prior=read(reference/'explicit_policy_verification.json');assert proof['passed'] and prior['passed']
 for receipt in [proof,prior]:assert all(sha(f)==h for f,h in receipt['source_sha256'].items())
 initial,oldinitial=[Path(x['initial_state']) for x in [proof,prior]];final,oldfinal=[Path(x['final_state']) for x in [proof,prior]]
 assert read(run_dir(initial)/'manifest.json')['command'][read(run_dir(initial)/'manifest.json')['command'].index('--seed')+1]=='19'
 initialeq=equal_state(initial,oldinitial);finaleq=equal_state(final,oldfinal);same_root=all(initialeq.values())
 same_trajectory=None;matched_legal=0;matched_skips=0
 if same_root:
  aa,bb=[read(x/'flow/repair/attempts.json') for x in [actual,reference]];same_trajectory=len(aa)==len(bb)
  for x,y in zip(aa,bb):
   same_trajectory &= all(x.get(k)==y.get(k) for k in ['round','candidate_rank','removed_pins','accepted_role'])
   tx,ty=Path(x['transaction']),Path(y['transaction'])
   same_trajectory &= all(sha(tx/f)==sha(ty/f) for f in ['request.txt','domain.txt'])
   px,py=read(tx/'progress.json'),read(ty/'progress.json');same_trajectory &= px.keys()==py.keys()
   for role in px.keys()&py.keys():
    xrow,yrow=px[role],py[role];same_trajectory &= xrow['status']==yrow['status']
    if xrow['status']==yrow['status']=='legal_evaluated':
     same_trajectory &= all(xrow[k]==yrow[k] for k in ['resources','cpd_s','policies'])
     same_trajectory &= all(equal_state(Path(xrow['evaluation']),Path(yrow['evaluation'])).values());matched_legal+=1
    elif xrow['status']==yrow['status']=='not_executed_domain_candidate_accepted':matched_skips+=1
   files += [tx/'progress.json',ty/'progress.json',tx/'request.txt',ty/'request.txt',tx/'domain.txt',ty/'domain.txt']
 results[name]=dict(status='complete_legal_configuration',route_seed=19,CPD_ns=proof['CPD_ns'],resources=proof['resources'],complete_wall_seconds=proof['complete_wall_seconds'],actual_native_work=proof['actual_native_work'],accepted_steps=proof['accepted_steps'],attempted_scopes=proof['attempted_scopes'],sampled_tree_PSS_peak_kib=proof['sampled_tree_PSS_peak_kib'],missing_memory_observations=proof['missing_memory_observations'],same_initial_state_as_seed11=same_root,initial_comparison=initialeq,final_comparison=finaleq,trajectory_exact_when_root_reproduced=same_trajectory,matched_legal_candidates=matched_legal,matched_explicit_skipped_roles=matched_skips,reference_seed11_complete_wall_seconds=prior['complete_wall_seconds'],descriptive_seconds_difference=proof['complete_wall_seconds']-prior['complete_wall_seconds'])
 files += [actual/'explicit_policy_verification.json',reference/'explicit_policy_verification.json',initial/'endpoint_vector.json',oldinitial/'endpoint_vector.json',final/'endpoint_vector.json',oldfinal/'endpoint_vector.json']
for circuit in ['eltwise','softmax']:
 names=[circuit+'_'+role for role in ['native','domain']]
 if not all(results[n]['status']=='complete_legal_configuration' for n in names):pairs[circuit]=dict(quality_comparison_available=False);continue
 proofs=[read(root/n/'explicit_policy_verification.json') for n in names]
 assert all(equal_state(*[Path(x['initial_state']) for x in proofs]).values())
 n,d=[results[k] for k in names]
 pairs[circuit]=dict(quality_comparison_available=True,same_initial_full_vector_and_ordered_body=True,domain_minus_native_resources={k:d['resources'][k]-n['resources'][k] for k in n['resources']},domain_minus_native_CPD_ns=d['CPD_ns']-n['CPD_ns'],descriptive_domain_minus_native_seconds=d['complete_wall_seconds']-n['complete_wall_seconds'])
write(root/'comparison.json',dict(passed=True,execution_cohort_all_legal=closed['passed'],registered_roles=4,successful_legal_roles=sum(x['status']=='complete_legal_configuration' for x in results.values()),results=results,pairs=pairs,source_sha256={str(f):sha(f) for f in files},qualification='Fixed seed19 complete new routing and own-current resource repair on two known circuits. Each quality/time/memory tuple belongs to its own actual full command including graph indexes, fresh route, all real candidates/checks/rollback/seals. Same initial ordered route and full vector as seed11 means seed-only variation did not create a new root and must not inflate independent samples; final/trajectory equivalence is checked rather than inferred. Different initial roots remain explicitly marked. Timing differences are descriptive shared-host single measurements with uncontrolled OS cache, not randomized repetitions or a statistical speedup or unseen-circuit confirmation. All failed roles retain denominator and failed execution cost without invented quality.'))
print(dict(passed=True,results=results,pairs=pairs),flush=True)
