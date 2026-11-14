#!/usr/bin/env python3
"""Report objective/filter isolation, including the failed unconstrained path."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

b=D/'native_objective_dev_01';done=read(b/'completion.json');reg=read(b/'registration.json')
old=D/'current_sta_near_native_dev_01/endpoint_step_002/runs/state/joint_native.log';new=b/'weighted_soft/runs/state/joint_native.log'
def neutral(lines):
 result=[]
 for line in lines:
  v=line.split()
  if v[0]=='MODE':continue
  if v[0]=='QUERY':v=v[:-1]
  if v[0]=='COMPLETE':v=v[:4]+v[-1:]
  result.append(v)
 return result
assert neutral(old.read_text().splitlines())==neutral(new.read_text().splitlines())
rows=[];sources=[b/'completion.json',b/'registration.json',b/'process_costs.json',old,new,D/'native_objective_stage_01/binding.json',D/'native_objective_stage_01/build_result.json']
for mode,r in done['roles'].items():
 state=b/mode;rd=Path(read(state/'completion.json')['run']);log=rd/'joint_native.log';lines=log.read_text().splitlines();assert lines[0]=='MODE '+mode
 assert lines[-1].endswith('occupancy_restored')
 eq=read(b/(mode+'_reference_equivalence.json'));attempts=[x for x in lines if x.startswith('ATTEMPT ')];conflicts=[]
 for line in lines:
  v=line.split()
  if v[0]=='FAIL_EDGE' and int(v[4])+1>int(v[5]):conflicts.append(dict(node=int(v[2]),occupancy=int(v[4]),capacity=int(v[5])))
 row=dict(mode=mode,status=r['status'],native_attempts=len(attempts),native_transaction_seconds=float(lines[-1].split()[4]),conflicting_nodes=conflicts,whole_wrapper=read(state/'completion.json')['timing'])
 if mode=='physical_soft':assert r['status']=='transaction_failed_rolled_back' and conflicts
 else:
  assert r['status']=='legal_candidate' and eq['identical'] and r['reused_candidate_FULL_STA']
  row.update(cpd_ns=r['cpd_ns'],decisions=r['decisions'],exact_candidate_reference=eq['reused_state'])
 rows.append(row);sources += [state/'completion.json',log,b/(mode+'_reference_equivalence.json')]
 if (b/(mode+'_decision.json')).exists():sources.append(b/(mode+'_decision.json'))
assert done['roles']['physical_capacity']['decisions']['endpoint_vector']['accepted']
assert not done['roles']['weighted_capacity']['decisions']['endpoint_vector']['accepted']
write(D/'native_objective_summary_01.json',dict(passed=True,rows=rows,default_control_non_time_trace_exact=True,new_native_processes=4,new_native_search_calls=sum(r['native_attempts'] for r in rows),
 complete_orchestrator_seconds=done['complete_orchestrator_seconds'],build_seconds=read(D/'native_objective_stage_01/build_result.json')['wall_seconds'],
 conclusion='Native physical objective plus hard occupancy/retained-extension filtering reproduces the exact capacity candidate. Filtering alone retains the mixed-cost plateau; physical objective alone returns an overused path. This case supports objective/constraint composition, not a unique external search-engine quality advantage.',
 qualification='Default control neutrality verified for this matched state. Zero-RC architecture and fixed retained scope; native float arithmetic remains native and finalSTA exact. Three candidate FULL/STA reuses are explicit, not new full evaluations or cold-start timing.',
 research_complete=False,new_work_pushed=False,source_sha256={str(p):sha(p) for p in sources}))
print([(r['mode'],r['status'],r['native_attempts']) for r in rows],flush=True)
